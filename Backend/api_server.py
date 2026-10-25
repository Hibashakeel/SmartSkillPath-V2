"""API adapter for the SmartSkillPath web UI. The existing Streamlit model remains unchanged."""
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Literal
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from model.recommendation_model import recommend_skills

DB = Path(
    os.environ.get(
        "SMARTSKILLPATH_DB", str(ROOT / "smartskillpath_users.db")
    )
)
MAX_ROADMAP_ITEMS = 100
MAX_SAVED_RECOMMENDATIONS = 100
MAX_RESULT_BYTES = 100_000
SENSITIVE_RESULT_KEYS = {
    "password",
    "passwordhash",
    "salt",
    "token",
    "accesstoken",
    "refreshtoken",
    "secret",
    "apikey",
    "authorization",
    "credential",
    "credentials",
}


@contextmanager
def connect():
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    """Apply repeatable, additive schema creation without replacing existing tables."""
    with connect() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "email TEXT UNIQUE NOT NULL,"
            "salt TEXT NOT NULL,"
            "password_hash TEXT NOT NULL,"
            "token TEXT UNIQUE)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS goals ("
            "user_id INTEGER NOT NULL,"
            "goal TEXT NOT NULL,"
            "position INTEGER NOT NULL,"
            "FOREIGN KEY(user_id) REFERENCES users(id))"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS career_goals ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "user_id INTEGER NOT NULL,"
            "title TEXT NOT NULL CHECK(length(title) <= 200),"
            "target_career TEXT NOT NULL CHECK(length(target_career) <= 100),"
            "description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 2000),"
            "target_date TEXT,"
            "status TEXT NOT NULL DEFAULT 'active' "
            "CHECK(status IN ('active', 'paused', 'completed')),"
            "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_career_goals_user "
            "ON career_goals(user_id, id)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS saved_recommendations ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "user_id INTEGER NOT NULL,"
            "career TEXT NOT NULL CHECK(length(career) <= 100),"
            "selected_skills TEXT NOT NULL,"
            "results TEXT NOT NULL,"
            "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_saved_recommendations_user "
            "ON saved_recommendations(user_id, id)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS roadmap_items ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "user_id INTEGER NOT NULL,"
            "title TEXT NOT NULL CHECK(length(title) <= 200),"
            "description TEXT NOT NULL CHECK(length(description) <= 2000),"
            "status TEXT NOT NULL DEFAULT 'not_started' "
            "CHECK(status IN ('not_started', 'in_progress', 'completed')),"
            "phase TEXT NOT NULL DEFAULT 'Skill Development' "
            "CHECK(length(phase) <= 80),"
            "priority TEXT NOT NULL DEFAULT 'medium' "
            "CHECK(priority IN ('high', 'medium', 'low')),"
            "position INTEGER NOT NULL CHECK(position >= 0),"
            "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            "FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)"
        )
        roadmap_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(roadmap_items)")
        }
        if "phase" not in roadmap_columns:
            connection.execute(
                "ALTER TABLE roadmap_items ADD COLUMN phase TEXT NOT NULL "
                "DEFAULT 'Skill Development' CHECK(length(phase) <= 80)"
            )
        if "priority" not in roadmap_columns:
            connection.execute(
                "ALTER TABLE roadmap_items ADD COLUMN priority TEXT NOT NULL "
                "DEFAULT 'medium' CHECK(priority IN ('high', 'medium', 'low'))"
            )
        roadmap_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(roadmap_items)")
        }
        if "goal_id" not in roadmap_columns:
            connection.execute(
                "ALTER TABLE roadmap_items ADD COLUMN goal_id INTEGER "
                "REFERENCES career_goals(id) ON DELETE CASCADE"
            )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_roadmap_items_user_position "
            "ON roadmap_items(user_id, position, id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_roadmap_items_goal_position "
            "ON roadmap_items(user_id, goal_id, position, id)"
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SmartSkillPath API",
    version="1.0.0",
    description="API adapter for existing SmartSkillPath recommendation model",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendationInput(BaseModel):
    career: str = Field(min_length=2, max_length=100)
    current_skills: list[str] = Field(min_length=1, max_length=50)


class AuthInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class GoalsInput(BaseModel):
    goals: list[str] = Field(max_length=100)


class SavedRecommendationInput(BaseModel):
    career: str = Field(min_length=2, max_length=100)
    selected_skills: list[str] = Field(min_length=1, max_length=50)
    results: dict[str, Any]

    @field_validator("career")
    @classmethod
    def trim_career(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Career must contain at least 2 characters.")
        return value

    @field_validator("selected_skills")
    @classmethod
    def validate_skills(cls, value: list[str]) -> list[str]:
        normalized = [skill.strip() for skill in value]
        if any(not skill or len(skill) > 100 for skill in normalized):
            raise ValueError("Each selected skill must contain 1 to 100 characters.")
        return normalized

    @field_validator("results")
    @classmethod
    def validate_results(cls, value: dict[str, Any]) -> dict[str, Any]:
        pending = [(value, 0)]
        inspected = 0
        while pending:
            item, depth = pending.pop()
            inspected += 1
            if inspected > 10_000 or depth > 50:
                raise ValueError("Results contain too many nested values.")
            if isinstance(item, dict):
                for key, child in item.items():
                    normalized_key = "".join(
                        character
                        for character in str(key).casefold()
                        if character.isalnum()
                    )
                    if normalized_key in SENSITIVE_RESULT_KEYS:
                        raise ValueError("Results must not contain credentials or tokens.")
                    pending.append((child, depth + 1))
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)
        try:
            encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
            size = len(encoded.encode("utf-8"))
        except (TypeError, ValueError, UnicodeError) as exc:
            raise ValueError("Results must be valid JSON.") from exc
        if size > MAX_RESULT_BYTES:
            raise ValueError("Results must not exceed 100 KB.")
        return value


RoadmapStatus = Literal["not_started", "in_progress", "completed"]


class RoadmapDraftStep(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    phase: str = Field(default="Skill Development", min_length=1, max_length=80)
    priority: Literal["high", "medium", "low"] = "medium"
    status: RoadmapStatus = "not_started"

    @field_validator("title", "phase")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field must not be empty.")
        return value

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str) -> str:
        return value.strip()


class RoadmapItemInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: RoadmapStatus = "not_started"
    position: int | None = Field(default=None, ge=0, le=1_000_000)
    phase: str = Field(default="Skill Development", min_length=1, max_length=80)
    priority: Literal["high", "medium", "low"] = "medium"
    goal_id: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title must not be empty.")
        return value

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str) -> str:
        return value.strip()


class RoadmapItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: RoadmapStatus | None = None
    position: int | None = Field(default=None, ge=0, le=1_000_000)
    phase: str | None = Field(default=None, min_length=1, max_length=80)
    priority: Literal["high", "medium", "low"] | None = None

    @field_validator("title", "phase")
    @classmethod
    def trim_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field must not be empty.")
        return value

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one roadmap field must be supplied.")
        if any(getattr(self, name) is None for name in self.model_fields_set):
            raise ValueError("Roadmap fields cannot be null.")
        return self


class ProgressInput(BaseModel):
    status: RoadmapStatus


class RoadmapOrderInput(BaseModel):
    item_ids: list[int] = Field(min_length=1, max_length=100)

    @field_validator("item_ids")
    @classmethod
    def validate_item_ids(cls, value: list[int]) -> list[int]:
        if any(item_id <= 0 for item_id in value) or len(set(value)) != len(value):
            raise ValueError("Roadmap item IDs must be unique positive integers.")
        return value


CareerGoalStatus = Literal["active", "paused", "completed"]


class CareerGoalInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    target_career: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=2000)
    target_date: str | None = Field(default=None, max_length=10)
    roadmap_steps: list[RoadmapDraftStep] = Field(
        default_factory=list, max_length=100
    )

    @field_validator("title", "target_career")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field must not be empty.")
        return value

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str) -> str:
        return value.strip()

    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        from datetime import date

        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise ValueError("Target date must be a valid YYYY-MM-DD date.") from exc


class CareerGoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    target_career: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    target_date: str | None = Field(default=None, max_length=10)
    status: CareerGoalStatus | None = None

    @field_validator("title", "target_career")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field must not be empty.")
        return value

    @field_validator("description")
    @classmethod
    def trim_optional_description(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("target_date")
    @classmethod
    def validate_optional_target_date(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        from datetime import date

        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise ValueError("Target date must be a valid YYYY-MM-DD date.") from exc

    @model_validator(mode="after")
    def require_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one goal field must be supplied.")
        if any(
            getattr(self, name) is None
            for name in self.model_fields_set
            if name != "target_date"
        ):
            raise ValueError("Goal fields cannot be null.")
        return self


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 240000
    ).hex()


def user_from_token(token):
    if not token:
        return None
    with connect() as connection:
        return connection.execute(
            "SELECT id,email FROM users WHERE token=?", (token,)
        ).fetchone()


def require_user(authorization):
    token = (
        authorization.removeprefix("Bearer ").strip()
        if authorization
        else None
    )
    user = user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in again.")
    return user


def recommendation_record(row):
    return {
        "id": row["id"],
        "career": row["career"],
        "selected_skills": json.loads(row["selected_skills"]),
        "results": json.loads(row["results"]),
        "created_at": row["created_at"],
    }


def roadmap_record(row):
    return {
        "id": row["id"],
        "goal_id": row["goal_id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "phase": row["phase"],
        "priority": row["priority"],
        "position": row["position"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def career_goal_record(connection, row):
    counts = connection.execute(
        "SELECT COUNT(*) AS total_steps, "
        "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_steps "
        "FROM roadmap_items WHERE user_id=? AND goal_id=?",
        (row["user_id"], row["id"]),
    ).fetchone()
    total = counts["total_steps"]
    completed = counts["completed_steps"] or 0
    next_steps = connection.execute(
        "SELECT id,title,status,position FROM roadmap_items "
        "WHERE user_id=? AND goal_id=? AND status!='completed' "
        "ORDER BY position,id LIMIT 3",
        (row["user_id"], row["id"]),
    ).fetchall()
    return {
        "id": row["id"],
        "title": row["title"],
        "target_career": row["target_career"],
        "description": row["description"],
        "target_date": row["target_date"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "completed_steps": completed,
        "total_steps": total,
        "progress_percent": round(completed / total * 100) if total else 0,
        "remaining_steps": total - completed,
        "next_steps": [dict(step) for step in next_steps],
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": "existing recommendation model loaded on request",
    }


@app.post("/api/recommend")
def recommend(payload: RecommendationInput):
    try:
        result = recommend_skills(
            ", ".join(payload.current_skills), payload.career
        )
        # Ensure a predictable JSON object for the frontend.
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Recommendation failed. Check that the cleaned datasets and Python dependencies are installed.",
        ) from exc


@app.post("/api/auth/register")
def register(payload: AuthInput):
    email = payload.email.lower().strip()
    salt = secrets.token_hex(16)
    ph = password_hash(payload.password, salt)
    token = secrets.token_urlsafe(32)
    try:
        with connect() as connection:
            connection.execute(
                "INSERT INTO users(email,salt,password_hash,token) VALUES(?,?,?,?)",
                (email, salt, ph, token),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Please sign in.",
        )
    return {"email": email, "token": token}


@app.post("/api/auth/login")
def login(payload: AuthInput):
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email=?",
            (payload.email.lower().strip(),),
        ).fetchone()
    if not row or password_hash(payload.password, row["salt"]) != row["password_hash"]:
        raise HTTPException(
            status_code=401, detail="Email or password is incorrect."
        )
    token = secrets.token_urlsafe(32)
    with connect() as connection:
        connection.execute(
            "UPDATE users SET token=? WHERE id=?", (token, row["id"])
        )
    return {"email": row["email"], "token": token}


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    with connect() as connection:
        connection.execute(
            "UPDATE users SET token=NULL WHERE id=?", (user["id"],)
        )
    return {"ok": True}


@app.get("/api/goals")
def get_goals(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    with connect() as connection:
        rows = connection.execute(
            "SELECT goal FROM goals WHERE user_id=? ORDER BY position",
            (user["id"],),
        ).fetchall()
    return {"goals": [row["goal"] for row in rows]}


@app.post("/api/goals")
def save_goals(
    payload: GoalsInput, authorization: str | None = Header(default=None)
):
    user = require_user(authorization)
    with connect() as connection:
        connection.execute(
            "DELETE FROM goals WHERE user_id=?", (user["id"],)
        )
        connection.executemany(
            "INSERT INTO goals(user_id,goal,position) VALUES(?,?,?)",
            [
                (user["id"], goal[:300], position)
                for position, goal in enumerate(payload.goals)
            ],
        )
    return {"saved": len(payload.goals)}


@app.post("/api/career-goals", status_code=201)
def create_career_goal(
    payload: CareerGoalInput,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            "INSERT INTO career_goals"
            "(user_id,title,target_career,description,target_date) "
            "VALUES(?,?,?,?,?)",
            (
                user["id"],
                payload.title,
                payload.target_career,
                payload.description,
                payload.target_date,
            ),
        )
        goal_id = cursor.lastrowid
        if len(payload.roadmap_steps) > MAX_ROADMAP_ITEMS:
            raise HTTPException(
                status_code=422,
                detail=f"A roadmap can contain at most {MAX_ROADMAP_ITEMS} steps.",
            )
        connection.executemany(
            "INSERT INTO roadmap_items"
            "(user_id,goal_id,title,description,status,phase,priority,position) "
            "VALUES(?,?,?,?,?,?,?,?)",
            [
                (
                    user["id"],
                    goal_id,
                    step.title,
                    step.description,
                    step.status,
                    step.phase,
                    step.priority,
                    position,
                )
                for position, step in enumerate(payload.roadmap_steps)
            ],
        )
        row = connection.execute(
            "SELECT * FROM career_goals WHERE id=? AND user_id=?",
            (goal_id, user["id"]),
        ).fetchone()
        result = career_goal_record(connection, row)
    return result


@app.get("/api/career-goals")
def get_career_goals(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM career_goals WHERE user_id=? ORDER BY id",
            (user["id"],),
        ).fetchall()
        goals = [career_goal_record(connection, row) for row in rows]
    return {"goals": goals}


@app.get("/api/career-goals/{goal_id}")
def get_career_goal(
    goal_id: int,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM career_goals WHERE id=? AND user_id=?",
            (goal_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Career goal not found.")
        return career_goal_record(connection, row)


@app.patch("/api/career-goals/{goal_id}")
def update_career_goal(
    goal_id: int,
    payload: CareerGoalUpdate,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    changes = payload.model_dump(exclude_unset=True)
    assignments = ", ".join(f"{column}=?" for column in changes)
    values = list(changes.values())
    values.extend([user["id"], goal_id])
    with connect() as connection:
        cursor = connection.execute(
            f"UPDATE career_goals SET {assignments}, "
            "updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND id=?",
            values,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Career goal not found.")
        row = connection.execute(
            "SELECT * FROM career_goals WHERE id=? AND user_id=?",
            (goal_id, user["id"]),
        ).fetchone()
        return career_goal_record(connection, row)


@app.delete("/api/career-goals/{goal_id}")
def delete_career_goal(
    goal_id: int,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        cursor = connection.execute(
            "DELETE FROM career_goals WHERE id=? AND user_id=?",
            (goal_id, user["id"]),
        )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Career goal not found.")
    return {"deleted": True}


@app.post("/api/recommendations", status_code=201)
def save_recommendation(
    payload: SavedRecommendationInput,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    selected_skills = json.dumps(payload.selected_skills, ensure_ascii=False)
    results = json.dumps(payload.results, ensure_ascii=False, allow_nan=False)
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        count = connection.execute(
            "SELECT COUNT(*) FROM saved_recommendations WHERE user_id=?",
            (user["id"],),
        ).fetchone()[0]
        if count >= MAX_SAVED_RECOMMENDATIONS:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A user can save at most "
                    f"{MAX_SAVED_RECOMMENDATIONS} recommendations."
                ),
            )
        cursor = connection.execute(
            "INSERT INTO saved_recommendations"
            "(user_id,career,selected_skills,results) VALUES(?,?,?,?)",
            (user["id"], payload.career, selected_skills, results),
        )
        row = connection.execute(
            "SELECT * FROM saved_recommendations WHERE id=? AND user_id=?",
            (cursor.lastrowid, user["id"]),
        ).fetchone()
    return recommendation_record(row)


@app.get("/api/recommendations")
def get_recommendations(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM saved_recommendations "
            "WHERE user_id=? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
    return {"recommendations": [recommendation_record(row) for row in rows]}


@app.get("/api/recommendations/{recommendation_id}")
def get_recommendation(
    recommendation_id: int,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM saved_recommendations WHERE id=? AND user_id=?",
            (recommendation_id, user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return recommendation_record(row)


@app.delete("/api/recommendations/{recommendation_id}")
def delete_recommendation(
    recommendation_id: int,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        cursor = connection.execute(
            "DELETE FROM saved_recommendations WHERE id=? AND user_id=?",
            (recommendation_id, user["id"]),
        )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return {"deleted": True}


@app.post("/api/roadmap", status_code=201)
def create_roadmap_item(
    payload: RoadmapItemInput,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if payload.goal_id is not None:
            goal = connection.execute(
                "SELECT id FROM career_goals WHERE id=? AND user_id=?",
                (payload.goal_id, user["id"]),
            ).fetchone()
            if not goal:
                raise HTTPException(status_code=404, detail="Career goal not found.")
        count = connection.execute(
            "SELECT COUNT(*) FROM roadmap_items "
            "WHERE user_id=? AND goal_id IS ?",
            (user["id"], payload.goal_id),
        ).fetchone()[0]
        if count >= MAX_ROADMAP_ITEMS:
            raise HTTPException(
                status_code=409,
                detail=f"A roadmap can contain at most {MAX_ROADMAP_ITEMS} items.",
            )
        position = payload.position
        if position is None:
            position = connection.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 "
                "FROM roadmap_items WHERE user_id=? AND goal_id IS ?",
                (user["id"], payload.goal_id),
            ).fetchone()[0]
        cursor = connection.execute(
            "INSERT INTO roadmap_items"
            "(user_id,goal_id,title,description,status,phase,priority,position) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                user["id"],
                payload.goal_id,
                payload.title,
                payload.description,
                payload.status,
                payload.phase,
                payload.priority,
                position,
            ),
        )
        row = connection.execute(
            "SELECT * FROM roadmap_items WHERE id=? AND user_id=?",
            (cursor.lastrowid, user["id"]),
        ).fetchone()
    return roadmap_record(row)


@app.get("/api/roadmap")
def get_roadmap(
    goal_id: int | None = None,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        if goal_id is None:
            rows = connection.execute(
                "SELECT * FROM roadmap_items WHERE user_id=? "
                "ORDER BY position, id",
                (user["id"],),
            ).fetchall()
        else:
            owned_goal = connection.execute(
                "SELECT id FROM career_goals WHERE id=? AND user_id=?",
                (goal_id, user["id"]),
            ).fetchone()
            if not owned_goal:
                raise HTTPException(status_code=404, detail="Career goal not found.")
            rows = connection.execute(
                "SELECT * FROM roadmap_items "
                "WHERE user_id=? AND goal_id=? ORDER BY position,id",
                (user["id"], goal_id),
            ).fetchall()
    return {"items": [roadmap_record(row) for row in rows]}


@app.patch("/api/roadmap/{item_id}")
def update_roadmap_item(
    item_id: int,
    payload: RoadmapItemUpdate,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    changes = payload.model_dump(exclude_unset=True)
    assignments = ", ".join(f"{column}=?" for column in changes)
    values = list(changes.values())
    values.extend([user["id"], item_id])
    with connect() as connection:
        cursor = connection.execute(
            f"UPDATE roadmap_items SET {assignments}, "
            "updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND id=?",
            values,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Roadmap item not found.")
        row = connection.execute(
            "SELECT * FROM roadmap_items WHERE user_id=? AND id=?",
            (user["id"], item_id),
        ).fetchone()
    return roadmap_record(row)


@app.patch("/api/roadmap/{item_id}/progress")
def update_roadmap_progress(
    item_id: int,
    payload: ProgressInput,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        cursor = connection.execute(
            "UPDATE roadmap_items SET status=?, updated_at=CURRENT_TIMESTAMP "
            "WHERE user_id=? AND id=?",
            (payload.status, user["id"], item_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Roadmap item not found.")
        row = connection.execute(
            "SELECT * FROM roadmap_items WHERE user_id=? AND id=?",
            (user["id"], item_id),
        ).fetchone()
    return roadmap_record(row)


@app.put("/api/career-goals/{goal_id}/roadmap/order")
def reorder_goal_roadmap(
    goal_id: int,
    payload: RoadmapOrderInput,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        goal = connection.execute(
            "SELECT id FROM career_goals WHERE id=? AND user_id=?",
            (goal_id, user["id"]),
        ).fetchone()
        if not goal:
            raise HTTPException(status_code=404, detail="Career goal not found.")
        actual_ids = [
            row["id"]
            for row in connection.execute(
                "SELECT id FROM roadmap_items "
                "WHERE user_id=? AND goal_id=? ORDER BY position,id",
                (user["id"], goal_id),
            ).fetchall()
        ]
        if len(actual_ids) != len(payload.item_ids) or set(actual_ids) != set(
            payload.item_ids
        ):
            raise HTTPException(
                status_code=409,
                detail="The submitted order must include every roadmap item for this goal exactly once.",
            )
        connection.executemany(
            "UPDATE roadmap_items SET position=?, updated_at=CURRENT_TIMESTAMP "
            "WHERE user_id=? AND goal_id=? AND id=?",
            [
                (position, user["id"], goal_id, item_id)
                for position, item_id in enumerate(payload.item_ids)
            ],
        )
        rows = connection.execute(
            "SELECT * FROM roadmap_items WHERE user_id=? AND goal_id=? "
            "ORDER BY position,id",
            (user["id"], goal_id),
        ).fetchall()
    return {"items": [roadmap_record(row) for row in rows]}


@app.delete("/api/roadmap/{item_id}")
def delete_roadmap_item(
    item_id: int,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    with connect() as connection:
        cursor = connection.execute(
            "DELETE FROM roadmap_items WHERE user_id=? AND id=?",
            (user["id"], item_id),
        )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Roadmap item not found.")
    return {"deleted": True}
