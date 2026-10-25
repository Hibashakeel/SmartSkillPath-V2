import os
import re
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "outputs",
    "cleaned_data"
)


# =========================================================
# CAREER KEYWORDS
# =========================================================

CAREER_KEYWORDS = {

    "Data Scientist": [
        "data scientist",
        "data science"
    ],

    "Data Analyst": [
        "data analyst",
        "data analysis",
        "business analyst"
    ],

    "Machine Learning Engineer": [
        "machine learning engineer",
        "machine learning",
        "ml engineer"
    ],

    "Software Engineer": [
        "software engineer",
        "software developer"
    ],

    "Web Developer": [
        "web developer",
        "web development",
        "full stack",
        "full-stack"
    ],

    "Backend Developer": [
        "backend developer",
        "back-end developer",
        "backend"
    ],

    "Frontend Developer": [
        "frontend developer",
        "front-end developer",
        "frontend"
    ],

    "DevOps Engineer": [
        "devops",
        "dev ops"
    ],

    "Cloud Engineer": [
        "cloud engineer",
        "cloud computing",
        "cloud architect"
    ],

    "Cybersecurity Analyst": [
        "cybersecurity",
        "cyber security",
        "security analyst",
        "information security"
    ],

    "Database Administrator": [
        "database administrator",
        "database admin",
        "dba"
    ],

    "Business Intelligence Analyst": [
        "business intelligence analyst",
        "business intelligence",
        "bi analyst"
    ]
}


# =========================================================
# GENERIC WORDS TO IGNORE
# =========================================================

GENERIC_SKILLS = {
    "build",
    "building",
    "development",
    "develop",
    "design",
    "designer",
    "management",
    "manager",
    "communication",
    "teamwork",
    "leadership",
    "planning",
    "problem solving",
    "problem-solving",
    "research",
    "innovation",
    "support",
    "testing",
    "documentation",
    "technical",
    "professional",
    "tools",
    "technology",
    "solutions",
    "software",
    "applications",
    "application",
    "systems",
    "system",
    "knowledge",
    "experience",
    "skills",
    "skill"
}


# =========================================================
# CLEAN SKILL
# =========================================================

def normalize_skill(skill):

    if pd.isna(skill):
        return ""

    skill = str(skill).strip().lower()

    skill = re.sub(
        r"^[\s,;|()\[\]{}]+",
        "",
        skill
    )

    skill = re.sub(
        r"[\s,;|()\[\]{}]+$",
        "",
        skill
    )

    skill = re.sub(
        r"\s+",
        " ",
        skill
    )

    return skill.strip()


# =========================================================
# SPLIT SKILLS
# =========================================================

def split_skills(value):

    if pd.isna(value):
        return []

    value = str(value).strip()

    if not value:
        return []

    parts = re.split(
        r"[;,|]+",
        value
    )

    skills = []

    for part in parts:

        skill = normalize_skill(part)

        if not skill:
            continue

        if len(skill) < 2:
            continue

        if skill in GENERIC_SKILLS:
            continue

        skills.append(skill)

    return list(
        dict.fromkeys(skills)
    )


# =========================================================
# LOAD DATASET
# =========================================================

def load_dataset():

    file_path = os.path.join(
        DATA_DIR,
        "IT_Job_Roles_Skills_Processed.csv"
    )

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Dataset not found:\n{file_path}"
        )

    try:

        df = pd.read_csv(
            file_path,
            encoding="utf-8"
        )

    except:

        df = pd.read_csv(
            file_path,
            encoding="latin1"
        )

    return df


# =========================================================
# BUILD ROLE PROFILES
# =========================================================

def build_role_profiles():

    df = load_dataset()

    profiles = []

    for _, row in df.iterrows():

        job_title = str(
            row.get(
                "Job Title",
                ""
            )
        ).strip()

        if not job_title:
            continue

        skills = split_skills(
            row.get(
                "Skills",
                ""
            )
        )

        certifications = split_skills(
            row.get(
                "Certifications",
                ""
            )
        )

        if not skills:
            continue

        profiles.append({

            "title": job_title,

            "skills": skills,

            "certifications": certifications
        })

    return profiles


# =========================================================
# FIND CAREER RELEVANT JOBS
# =========================================================

def find_relevant_roles(
    profiles,
    career
):

    keywords = CAREER_KEYWORDS.get(
        career,
        [career.lower()]
    )

    relevant = []

    for profile in profiles:

        title = profile[
            "title"
        ].lower()

        for keyword in keywords:

            if keyword in title:

                relevant.append(
                    profile
                )

                break

    return relevant


# =========================================================
# RECOMMENDATION
# =========================================================

def recommend_skills(
    current_skills,
    desired_career
):

    # -----------------------------------------------------
    # USER SKILLS
    # -----------------------------------------------------

    user_skills = split_skills(
        current_skills
    )

    user_skill_set = {
        skill.lower()
        for skill in user_skills
    }

    # -----------------------------------------------------
    # LOAD DATA
    # -----------------------------------------------------

    profiles = build_role_profiles()

    # -----------------------------------------------------
    # CAREER FILTER
    # -----------------------------------------------------

    relevant_roles = find_relevant_roles(
        profiles,
        desired_career
    )

    # If no exact career roles found,
    # use all roles as fallback
    if not relevant_roles:

        relevant_roles = profiles

    # -----------------------------------------------------
    # CREATE ROLE DOCUMENTS
    # -----------------------------------------------------

    role_documents = []

    for role in relevant_roles:

        document = " ".join(
            role["skills"]
        )

        role_documents.append(
            document
        )

    # -----------------------------------------------------
    # STUDENT DOCUMENT
    # -----------------------------------------------------

    student_document = " ".join(
        user_skills
    )

    # -----------------------------------------------------
    # TF-IDF
    # -----------------------------------------------------

    documents = [
        student_document
    ] + role_documents

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1
    )

    matrix = vectorizer.fit_transform(
        documents
    )

    student_vector = matrix[0]

    role_vectors = matrix[1:]

    similarity_scores = cosine_similarity(
        student_vector,
        role_vectors
    )[0]

    # -----------------------------------------------------
    # RANK ROLES
    # -----------------------------------------------------

    ranked_roles = []

    for role, score in zip(
        relevant_roles,
        similarity_scores
    ):

        ranked_roles.append(
            (
                role,
                float(score)
            )
        )

    ranked_roles.sort(
        key=lambda x: x[1],
        reverse=True
    )

    # TOP 5 ROLES
    top_roles = ranked_roles[:5]

    # -----------------------------------------------------
    # MATCHING JOB ROLES
    # -----------------------------------------------------

    matching_roles = []

    for role, score in top_roles:

        matching_roles.append({

            "role": role["title"],

            "similarity": round(
                score * 100,
                2
            )
        })

    # =====================================================
    # SKILL RECOMMENDATION
    # =====================================================

    skill_scores = {}

    skill_frequency = {}

    for role, similarity in top_roles:

        # Minimum weight so even low similarity
        # relevant roles can contribute
        weight = max(
            similarity,
            0.10
        )

        for skill in role["skills"]:

            skill = normalize_skill(
                skill
            )

            if not skill:
                continue

            if skill in GENERIC_SKILLS:
                continue

            # Don't recommend existing skills
            if skill in user_skill_set:
                continue

            # ML similarity score
            skill_scores[skill] = (
                skill_scores.get(
                    skill,
                    0
                )
                + weight
            )

            # Frequency among top jobs
            skill_frequency[skill] = (
                skill_frequency.get(
                    skill,
                    0
                )
                + 1
            )

    # -----------------------------------------------------
    # FINAL SKILL SCORE
    # -----------------------------------------------------

    final_skill_scores = {}

    for skill in skill_scores:

        ml_score = skill_scores[
            skill
        ]

        frequency = skill_frequency[
            skill
        ]

        # Combination of:
        # 70% ML relevance
        # 30% frequency
        final_score = (
            ml_score * 0.70
        ) + (
            frequency * 0.30
        )

        final_skill_scores[
            skill
        ] = final_score

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    ranked_skills = sorted(
        final_skill_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # -----------------------------------------------------
    # ONLY TOP 5
    # -----------------------------------------------------

    recommended_skills = [
        skill
        for skill, score
        in ranked_skills[:5]
    ]

    # =====================================================
    # SKILL GAP
    # =====================================================

    # Skill gap now means:
    # "Top skills the student should focus on next"
    #
    # NOT every skill found in the dataset.

    skill_gap = recommended_skills.copy()

    # =====================================================
    # CERTIFICATIONS
    # =====================================================

    certification_scores = {}

    for role, similarity in top_roles:

        weight = max(
            similarity,
            0.10
        )

        for certification in role[
            "certifications"
        ]:

            certification = normalize_skill(
                certification
            )

            if not certification:
                continue

            certification_scores[
                certification
            ] = (
                certification_scores.get(
                    certification,
                    0
                )
                + weight
            )

    ranked_certifications = sorted(
        certification_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    certifications = [
        cert
        for cert, score
        in ranked_certifications[:3]
    ]

    # =====================================================
    # RESULT
    # =====================================================

    return {

        "skill_gap": skill_gap,

        "recommended_skills":
            recommended_skills,

        "certifications":
            certifications,

        "matching_roles":
            matching_roles
    }


# =========================================================
# TEST MODEL
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("SMART SKILLPATH ML MODEL")
    print("=" * 60)

    career = input(
        "\nEnter desired IT career: "
    ).strip()

    skills = input(
        "Enter your current skills "
        "(comma separated): "
    ).strip()

    result = recommend_skills(
        skills,
        career
    )

    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)

    print(
        "\nCareer:",
        career
    )

    print(
        "\nCurrent Skills:",
        skills
    )

    print(
        "\nTop Recommended Skills:"
    )

    if result["recommended_skills"]:

        for skill in result[
            "recommended_skills"
        ]:

            print(
                " -",
                skill
            )

    else:

        print(
            " - No recommendations found"
        )

    print(
        "\nRecommended Certifications:"
    )

    if result["certifications"]:

        for cert in result[
            "certifications"
        ]:

            print(
                " -",
                cert
            )

    else:

        print(
            " - No certifications found"
        )

    print(
        "\nMatching Job Roles:"
    )

    if result["matching_roles"]:

        for role in result[
            "matching_roles"
        ]:

            print(
                f" - {role['role']} "
                f"({role['similarity']}% match)"
            )

    else:

        print(
            " - No matching roles found"
        )

    print()
    print("=" * 60)