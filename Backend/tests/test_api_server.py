import asyncio
import hashlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError
from fastapi import HTTPException

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import api_server


class ApiPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "test_users.db"
        self.original_database = api_server.DB
        api_server.DB = self.database
        salt = "existing-user-salt"
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", b"existing-password", salt.encode(), 240000
        ).hex()
        connection = sqlite3.connect(self.database)
        try:
            with connection:
                connection.execute(
                    "CREATE TABLE users ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "email TEXT UNIQUE NOT NULL,"
                    "salt TEXT NOT NULL,"
                    "password_hash TEXT NOT NULL,"
                    "token TEXT UNIQUE)"
                )
                connection.execute(
                    "CREATE TABLE goals ("
                    "user_id INTEGER NOT NULL,"
                    "goal TEXT NOT NULL,"
                    "position INTEGER NOT NULL,"
                    "FOREIGN KEY(user_id) REFERENCES users(id))"
                )
                connection.execute(
                    "INSERT INTO users(id,email,salt,password_hash,token) "
                    "VALUES(1,?,?,?,?)",
                    (
                        "existing@example.com",
                        salt,
                        password_hash,
                        "existing-user-token",
                    ),
                )
                connection.execute(
                    "INSERT INTO goals(user_id,goal,position) VALUES(1,?,0)",
                    ("Existing goal",),
                )
        finally:
            connection.close()
        api_server.init_db()
        api_server.init_db()
        self.existing_token = "existing-user-token"
        self.new_user = api_server.register(
            api_server.AuthInput(
                email="second@example.com",
                password="a-valid-password",
            )
        )
        self.new_token = self.new_user["token"]

    def tearDown(self):
        api_server.DB = self.original_database
        self.temp_dir.cleanup()

    def test_migration_is_repeatable_and_preserves_existing_data(self):
        connection = sqlite3.connect(self.database)
        try:
            existing_user = connection.execute(
                "SELECT email,salt,password_hash,token FROM users WHERE id=1"
            ).fetchone()
            goals = connection.execute(
                "SELECT goal FROM goals WHERE user_id=1 ORDER BY position"
            ).fetchall()
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        finally:
            connection.close()
        self.assertEqual(existing_user[0], "existing@example.com")
        self.assertEqual(existing_user[1], "existing-user-salt")
        self.assertEqual(existing_user[2], api_server.password_hash(
            "existing-password", "existing-user-salt"
        ))
        self.assertEqual(existing_user[3], self.existing_token)
        self.assertEqual(goals, [("Existing goal",)])
        self.assertTrue(
            {
                "saved_recommendations",
                "roadmap_items",
                "career_goals",
            }.issubset(tables)
        )

    def test_app_startup_migrates_the_configured_database(self):
        original_database = api_server.DB
        with tempfile.TemporaryDirectory() as directory:
            api_server.DB = Path(directory) / "startup_test.db"

            async def start_and_stop():
                async with api_server.lifespan(api_server.app):
                    pass

            try:
                asyncio.run(start_and_stop())
                connection = sqlite3.connect(api_server.DB)
                try:
                    tables = {
                        row[0]
                        for row in connection.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        )
                    }
                finally:
                    connection.close()
            finally:
                api_server.DB = original_database
        self.assertTrue(
            {
                "users",
                "goals",
                "saved_recommendations",
                "roadmap_items",
                "career_goals",
            }
            .issubset(tables)
        )

    def test_legacy_goals_remain_compatible(self):
        self.assertEqual(
            api_server.get_goals("Bearer " + self.existing_token),
            {"goals": ["Existing goal"]},
        )
        self.assertEqual(
            api_server.save_goals(
                api_server.GoalsInput(goals=["Updated goal"]),
                "Bearer " + self.existing_token,
            ),
            {"saved": 1},
        )
        self.assertEqual(
            api_server.get_goals("Bearer " + self.existing_token),
            {"goals": ["Updated goal"]},
        )

    def test_existing_login_and_recommendation_contracts(self):
        login = api_server.login(
            api_server.AuthInput(
                email="existing@example.com",
                password="existing-password",
            )
        )
        self.assertEqual(login["email"], "existing@example.com")
        self.assertNotEqual(login["token"], self.existing_token)

        result = {
            "skill_gap": ["Python"],
            "recommended_skills": ["Python"],
            "certifications": [],
            "matching_roles": [],
        }
        with patch.object(api_server, "recommend_skills", return_value=result) as model:
            response = api_server.recommend(
                api_server.RecommendationInput(
                    career="Data Analyst",
                    current_skills=["SQL", "Excel"],
                )
            )
        self.assertEqual(response, result)
        model.assert_called_once_with("SQL, Excel", "Data Analyst")

    def test_saved_recommendations_require_auth_and_are_private(self):
        payload = api_server.SavedRecommendationInput(
            career="Data Analyst",
            selected_skills=["SQL", "Excel"],
            results={
                "skill_gap": ["Python"],
                "recommended_skills": ["Python"],
                "certifications": [],
                "matching_roles": [],
            },
        )
        with self.assertRaises(HTTPException) as unauthenticated:
            api_server.save_recommendation(payload, None)
        self.assertEqual(unauthenticated.exception.status_code, 401)

        saved = api_server.save_recommendation(
            payload, "Bearer " + self.existing_token
        )
        self.assertEqual(saved["career"], "Data Analyst")
        self.assertEqual(saved["selected_skills"], ["SQL", "Excel"])
        self.assertEqual(saved["results"]["skill_gap"], ["Python"])
        self.assertNotIn("user_id", saved)
        self.assertNotIn("token", saved)
        self.assertEqual(
            api_server.get_recommendations("Bearer " + self.existing_token)[
                "recommendations"
            ],
            [saved],
        )
        with self.assertRaises(HTTPException) as isolated:
            api_server.get_recommendation(
                saved["id"], "Bearer " + self.new_token
            )
        self.assertEqual(isolated.exception.status_code, 404)
        with self.assertRaises(HTTPException):
            api_server.get_recommendations("Bearer invalid-token")
        self.assertEqual(
            api_server.get_recommendations("Bearer " + self.new_token)[
                "recommendations"
            ],
            [],
        )

    def test_recommendation_payload_limits_and_sensitive_fields(self):
        with self.assertRaises(ValidationError):
            api_server.SavedRecommendationInput(
                career="Data Analyst",
                selected_skills=["SQL"],
                results={"token": "must not be stored"},
            )
        with self.assertRaises(ValidationError):
            api_server.SavedRecommendationInput(
                career="Data Analyst",
                selected_skills=["SQL"],
                results={"metadata": {"passwordHash": "must not be stored"}},
            )
        with self.assertRaises(ValidationError):
            api_server.SavedRecommendationInput(
                career="Data Analyst",
                selected_skills=["x" * 101],
                results={},
            )
        with self.assertRaises(ValidationError):
            api_server.SavedRecommendationInput(
                career="Data Analyst",
                selected_skills=["SQL"],
                results={"large": "x" * 100_001},
            )

    def test_roadmap_crud_progress_and_user_isolation(self):
        with self.assertRaises(HTTPException) as unauthenticated:
            api_server.get_roadmap(authorization=None)
        self.assertEqual(unauthenticated.exception.status_code, 401)

        item = api_server.create_roadmap_item(
            api_server.RoadmapItemInput(
                title="Learn Python",
                description="Practice the fundamentals.",
            ),
            "Bearer " + self.existing_token,
        )
        second_item = api_server.create_roadmap_item(
            api_server.RoadmapItemInput(title="Build a project"),
            "Bearer " + self.existing_token,
        )
        self.assertEqual(item["position"], 0)
        self.assertEqual(second_item["position"], 1)
        self.assertEqual(
            api_server.get_roadmap(
                authorization="Bearer " + self.existing_token
            )["items"],
            [item, second_item],
        )
        updated = api_server.update_roadmap_progress(
            item["id"],
            api_server.ProgressInput(status="completed"),
            "Bearer " + self.existing_token,
        )
        self.assertEqual(updated["status"], "completed")

        with self.assertRaises(HTTPException) as foreign_update:
            api_server.update_roadmap_progress(
                item["id"],
                api_server.ProgressInput(status="in_progress"),
                "Bearer " + self.new_token,
            )
        self.assertEqual(foreign_update.exception.status_code, 404)
        self.assertEqual(
            api_server.get_roadmap(
                authorization="Bearer " + self.new_token
            )["items"],
            [],
        )

        renamed = api_server.update_roadmap_item(
            second_item["id"],
            api_server.RoadmapItemUpdate(title="Build a portfolio"),
            "Bearer " + self.existing_token,
        )
        self.assertEqual(renamed["title"], "Build a portfolio")
        with self.assertRaises(ValidationError):
            api_server.RoadmapItemInput(title=" " * 3)

    def test_multiple_career_goals_keep_roadmaps_and_progress_independent(self):
        authorization = "Bearer " + self.existing_token
        first_goal = api_server.create_career_goal(
            api_server.CareerGoalInput(
                title="Frontend path",
                target_career="Frontend Developer",
                roadmap_steps=[
                    api_server.RoadmapDraftStep(
                        title="Learn accessibility",
                        phase="Fundamentals",
                        priority="high",
                        status="in_progress",
                    ),
                    api_server.RoadmapDraftStep(
                        title="Build a project",
                        phase="Practical Projects",
                    ),
                ],
            ),
            authorization,
        )
        second_goal = api_server.create_career_goal(
            api_server.CareerGoalInput(
                title="Data path",
                target_career="Data Analyst",
            ),
            authorization,
        )
        zero_step_goal = api_server.create_career_goal(
            api_server.CareerGoalInput(
                title="Cloud path",
                target_career="Cloud Engineer",
            ),
            authorization,
        )
        other_user_goal = api_server.create_career_goal(
            api_server.CareerGoalInput(
                title="Private goal",
                target_career="Cybersecurity Analyst",
            ),
            "Bearer " + self.new_token,
        )
        second_goal_item = api_server.create_roadmap_item(
            api_server.RoadmapItemInput(
                title="Analyze a sample dataset",
                goal_id=second_goal["id"],
            ),
            authorization,
        )
        other_user_item = api_server.create_roadmap_item(
            api_server.RoadmapItemInput(
                title="Private roadmap step",
                goal_id=other_user_goal["id"],
            ),
            "Bearer " + self.new_token,
        )

        first_items = api_server.get_roadmap(
            first_goal["id"], authorization
        )["items"]
        self.assertEqual(len(first_items), 2)
        self.assertEqual(first_items[0]["phase"], "Fundamentals")
        self.assertEqual(first_items[0]["priority"], "high")
        self.assertEqual(first_items[0]["status"], "in_progress")
        self.assertEqual(
            api_server.get_roadmap(second_goal["id"], authorization)["items"],
            [second_goal_item],
        )
        with self.assertRaises(HTTPException) as foreign_goal:
            api_server.get_roadmap(
                other_user_goal["id"], authorization
            )
        self.assertEqual(foreign_goal.exception.status_code, 404)

        completed = api_server.update_roadmap_progress(
            first_items[0]["id"],
            api_server.ProgressInput(status="completed"),
            authorization,
        )
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(
            api_server.get_roadmap(first_goal["id"], authorization)["items"][0]["status"],
            "completed",
        )
        updated_first_goal = api_server.get_career_goal(
            first_goal["id"], authorization
        )
        self.assertEqual(updated_first_goal["completed_steps"], 1)
        self.assertEqual(updated_first_goal["total_steps"], 2)
        self.assertEqual(updated_first_goal["progress_percent"], 50)
        self.assertEqual(updated_first_goal["remaining_steps"], 1)
        empty_goal = api_server.get_career_goal(
            zero_step_goal["id"], authorization
        )
        self.assertEqual(empty_goal["progress_percent"], 0)
        self.assertEqual(empty_goal["remaining_steps"], 0)
        api_server.update_career_goal(
            first_goal["id"],
            api_server.CareerGoalUpdate(title="Updated frontend path"),
            authorization,
        )
        self.assertEqual(
            api_server.get_career_goal(
                second_goal["id"], authorization
            )["title"],
            "Data path",
        )

        reordered = api_server.reorder_goal_roadmap(
            first_goal["id"],
            api_server.RoadmapOrderInput(
                item_ids=[first_items[1]["id"], first_items[0]["id"]]
            ),
            authorization,
        )
        self.assertEqual(
            [item["id"] for item in reordered["items"]],
            [first_items[1]["id"], first_items[0]["id"]],
        )
        with self.assertRaises(HTTPException) as invalid_order:
            api_server.reorder_goal_roadmap(
                first_goal["id"],
                api_server.RoadmapOrderInput(item_ids=[first_items[0]["id"]]),
                authorization,
            )
        self.assertEqual(invalid_order.exception.status_code, 409)

        with self.assertRaises(HTTPException) as foreign_delete:
            api_server.delete_career_goal(
                first_goal["id"], "Bearer " + self.new_token
            )
        self.assertEqual(foreign_delete.exception.status_code, 404)
        self.assertEqual(
            api_server.delete_career_goal(
                first_goal["id"], authorization
            ),
            {"deleted": True},
        )
        self.assertEqual(
            api_server.get_roadmap(second_goal["id"], authorization)["items"],
            [second_goal_item],
        )
        self.assertEqual(
            api_server.get_roadmap(
                other_user_goal["id"], "Bearer " + self.new_token
            )["items"],
            [other_user_item],
        )

    def test_career_goal_endpoints_require_authentication(self):
        payload = api_server.CareerGoalInput(
            title="Frontend path",
            target_career="Frontend Developer",
        )
        with self.assertRaises(HTTPException) as unauthenticated:
            api_server.create_career_goal(payload, None)
        self.assertEqual(unauthenticated.exception.status_code, 401)

    def test_logout_revokes_token(self):
        self.assertEqual(
            api_server.logout("Bearer " + self.new_token), {"ok": True}
        )
        with self.assertRaises(HTTPException) as revoked:
            api_server.get_roadmap(
                authorization="Bearer " + self.new_token
            )
        self.assertEqual(revoked.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
