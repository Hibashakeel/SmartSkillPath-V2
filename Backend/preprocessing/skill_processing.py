import pandas as pd
import os
import re
import time

# =========================================================
# SMART SKILLPATH - SKILL PROCESSING
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLEAN_DIR = os.path.join(
    BASE_DIR,
    "outputs",
    "cleaned_data"
)

OUTPUT_DIR = CLEAN_DIR

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================================================
# LOAD DATA
# =========================================================

file1 = os.path.join(
    CLEAN_DIR,
    "IT_Job_Roles_Skills_Clean.csv"
)

file2 = os.path.join(
    CLEAN_DIR,
    "JobsDatasetProcessed_Clean.csv"
)

file3 = os.path.join(
    CLEAN_DIR,
    "JobsDataset_Clean.csv"
)

print("======================================")
print("       LOADING DATASETS")
print("======================================")

df1 = pd.read_csv(file1, encoding="utf-8")
df2 = pd.read_csv(file2, encoding="utf-8")
df3 = pd.read_csv(file3, encoding="utf-8")

print("Dataset 1:", len(df1))
print("Dataset 2:", len(df2))
print("Dataset 3:", len(df3))


# =========================================================
# CLEAN SKILL
# =========================================================

def clean_skill(skill):

    skill = str(skill).lower().strip()

    skill = re.sub(r"\s+", " ", skill)

    skill = skill.strip(" ,.;:-")

    return skill


# =========================================================
# SPLIT SKILLS
# =========================================================

def split_skills(text):

    if pd.isna(text):
        return []

    text = str(text)

    parts = re.split(r"[,;|]", text)

    skills = []

    for part in parts:

        skill = clean_skill(part)

        if skill and len(skill) > 1:
            skills.append(skill)

    return list(dict.fromkeys(skills))


# =========================================================
# DATASET 1
# =========================================================

print("\nProcessing Dataset 1...")

df1["Skill_List"] = (
    df1["Skills"]
    .fillna("")
    .apply(split_skills)
)

df1["Certification_List"] = (
    df1["Certifications"]
    .fillna("")
    .apply(split_skills)
)


# =========================================================
# DATASET 2
# =========================================================

print("Processing Dataset 2...")

df2["Skill_List"] = (
    df2["IT Skills"]
    .fillna("")
    .apply(split_skills)
)


# =========================================================
# CREATE SKILL VOCABULARY
# =========================================================

print("\nCreating skill vocabulary...")

all_skills = set()


# Skills from Dataset 1
for skill_list in df1["Skill_List"]:

    for skill in skill_list:

        if skill:
            all_skills.add(skill)


# Skills from Dataset 2
for skill_list in df2["Skill_List"]:

    for skill in skill_list:

        if skill:
            all_skills.add(skill)


# =========================================================
# COMMON IT SKILLS
# =========================================================

common_it_skills = [

    "python",
    "java",
    "c",
    "c++",
    "c#",
    "javascript",
    "typescript",
    "php",
    "ruby",
    "go",
    "kotlin",
    "swift",

    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "oracle",
    "firebase",

    "html",
    "css",
    "react",
    "angular",
    "vue",
    "node.js",

    "machine learning",
    "deep learning",
    "artificial intelligence",
    "data science",
    "data analysis",
    "data mining",
    "statistics",
    "statistical analysis",
    "data visualization",
    "data wrangling",

    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",

    "cloud computing",
    "aws",
    "azure",
    "google cloud",
    "gcp",

    "docker",
    "kubernetes",
    "terraform",
    "ansible",

    "linux",
    "windows",
    "networking",
    "cybersecurity",
    "information security",

    "hadoop",
    "spark",
    "mapreduce",

    "etl",
    "data warehousing",
    "data lakes",
    "big data",

    "git",
    "github",
    "gitlab",

    "ci/cd",
    "devops",
    "automation",

    "programming",
    "software development",
    "software engineering",

    "api",
    "rest api",
    "restful api",

    "power bi",
    "tableau",

    "excel"
]


for skill in common_it_skills:
    all_skills.add(skill)


# =========================================================
# CLEAN FINAL SKILL LIST
# =========================================================

filtered_skills = set()

for skill in all_skills:

    skill = clean_skill(skill)

    if not skill:
        continue

    if len(skill) <= 1 and skill != "c":
        continue

    filtered_skills.add(skill)


all_skills = sorted(filtered_skills)


# =========================================================
# SAVE UNIQUE SKILLS
# =========================================================

skill_df = pd.DataFrame({
    "Skill": all_skills
})

skill_output = os.path.join(
    OUTPUT_DIR,
    "unique_it_skills.csv"
)

skill_df.to_csv(
    skill_output,
    index=False,
    encoding="utf-8"
)

print("\nUnique IT skills:", len(skill_df))
print("Saved:", skill_output)


# =========================================================
# PREPARE SKILL EXTRACTION
# =========================================================

print("\nPreparing skill extraction...")

multi_word_skills = []
single_word_skills = []


for skill in all_skills:

    if " " in skill:
        multi_word_skills.append(skill)

    else:
        single_word_skills.append(skill)


# Longest skills first
multi_word_skills.sort(
    key=len,
    reverse=True
)

single_word_skills.sort(
    key=len,
    reverse=True
)


# =========================================================
# CREATE REGEX PATTERNS
# =========================================================

print("Creating regex patterns...")


# Multi-word pattern
if multi_word_skills:

    multi_pattern = re.compile(
        r"(?<!\w)(" +
        "|".join(
            re.escape(skill)
            for skill in multi_word_skills
        ) +
        r")(?!\w)",
        re.IGNORECASE
    )

else:

    multi_pattern = None


# Single-word pattern
if single_word_skills:

    single_pattern = re.compile(
        r"(?<!\w)(" +
        "|".join(
            re.escape(skill)
            for skill in single_word_skills
        ) +
        r")(?!\w)",
        re.IGNORECASE
    )

else:

    single_pattern = None


# =========================================================
# EXTRACT SKILLS
# =========================================================

def extract_skills_from_description(text):

    if pd.isna(text):
        return ""

    text = str(text).lower()

    found = set()


    # -----------------------------------------------------
    # Multi-word skills
    # -----------------------------------------------------

    if multi_pattern:

        matches = multi_pattern.findall(text)

        for match in matches:

            skill = clean_skill(match)

            if skill:
                found.add(skill)


    # -----------------------------------------------------
    # Single-word skills
    # -----------------------------------------------------

    if single_pattern:

        matches = single_pattern.findall(text)

        for match in matches:

            skill = clean_skill(match)

            if skill:
                found.add(skill)


    # -----------------------------------------------------
    # Return skills
    # -----------------------------------------------------

    return ", ".join(
        sorted(found)
    )


# =========================================================
# DATASET 3 SKILL EXTRACTION
# =========================================================

total = len(df3)

print("\n======================================")
print(" EXTRACTING SKILLS FROM JOB DESCRIPTIONS")
print("======================================")

print("Total descriptions:", total)
print("Please wait...\n")


start_time = time.time()

extracted_skills = []


for index, description in enumerate(
    df3["Description"].fillna("")
):

    result = extract_skills_from_description(
        description
    )

    extracted_skills.append(result)


    # Show progress every 500 records
    if (index + 1) % 500 == 0:

        elapsed = time.time() - start_time

        percentage = (
            (index + 1) / total
        ) * 100

        print(
            f"Processed: {index + 1}/{total} "
            f"({percentage:.1f}%) "
            f"| Time: {elapsed:.1f} seconds"
        )


# Add extracted skills column
df3["Extracted_Skills_Text"] = extracted_skills


# =========================================================
# EXTRACTION COMPLETED
# =========================================================

total_time = time.time() - start_time

print("\n======================================")
print(" SKILL EXTRACTION COMPLETED")
print("======================================")

print(
    f"Total processing time: "
    f"{total_time / 60:.2f} minutes"
)


# =========================================================
# SAVE DATASET 1
# =========================================================

output_df1 = os.path.join(
    OUTPUT_DIR,
    "IT_Job_Roles_Skills_Processed.csv"
)

df1.to_csv(
    output_df1,
    index=False,
    encoding="utf-8"
)


# =========================================================
# SAVE DATASET 2
# =========================================================

output_df2 = os.path.join(
    OUTPUT_DIR,
    "JobsDatasetProcessed_Processed.csv"
)

df2.to_csv(
    output_df2,
    index=False,
    encoding="utf-8"
)


# =========================================================
# SAVE DATASET 3
# =========================================================

output_df3 = os.path.join(
    OUTPUT_DIR,
    "JobsDataset_Processed.csv"
)

df3.to_csv(
    output_df3,
    index=False,
    encoding="utf-8"
)


# =========================================================
# FINAL OUTPUT
# =========================================================

print("\n======================================")
print("       SKILL PROCESSING COMPLETED")
print("======================================")

print("\nCreated files:")

print("1. unique_it_skills.csv")
print("2. IT_Job_Roles_Skills_Processed.csv")
print("3. JobsDatasetProcessed_Processed.csv")
print("4. JobsDataset_Processed.csv")

print("\nDataset 3 records processed:", len(df3))

print("\n======================================")
