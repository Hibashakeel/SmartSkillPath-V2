import pandas as pd
import os

# =========================================================
# SMART SKILLPATH - DATA CLEANING
# =========================================================

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "cleaned_data")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================================================
# LOAD CSV WITH AUTOMATIC ENCODING
# =========================================================

def load_csv(file_path):
    encodings = ["utf-8", "latin1", "cp1252"]

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"Loaded: {os.path.basename(file_path)}")
            print(f"Encoding: {encoding}")
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise ValueError(f"Could not read file: {file_path}")


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text_columns(df):
    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = (
                df[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    return df


# =========================================================
# DATASET 1
# =========================================================

file1 = os.path.join(DATA_DIR, "IT_Job_Roles_Skills.csv")

df1 = load_csv(file1)

print("\n========== DATASET 1 ==========")
print("Original Rows:", len(df1))
print("Columns:", df1.columns.tolist())

df1 = clean_text_columns(df1)

# Remove duplicate rows
df1 = df1.drop_duplicates()

# Clean important columns
for column in ["Job Title", "Job Description", "Skills", "Certifications"]:
    if column in df1.columns:
        df1[column] = (
            df1[column]
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

# Save
output1 = os.path.join(
    OUTPUT_DIR,
    "IT_Job_Roles_Skills_Clean.csv"
)

df1.to_csv(output1, index=False, encoding="utf-8")

print("Clean Rows:", len(df1))
print("Saved:", output1)


# =========================================================
# DATASET 2
# =========================================================

file2 = os.path.join(DATA_DIR, "JobsDatasetProcessed.csv")

df2 = load_csv(file2)

print("\n========== DATASET 2 ==========")
print("Original Rows:", len(df2))
print("Columns:", df2.columns.tolist())

df2 = clean_text_columns(df2)

# Remove duplicate rows
df2 = df2.drop_duplicates()

# Clean important text columns
for column in [
    "Query",
    "Job Title",
    "Description",
    "IT Skills",
    "Soft Skills",
    "Education",
    "Experience"
]:
    if column in df2.columns:
        df2[column] = (
            df2[column]
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

output2 = os.path.join(
    OUTPUT_DIR,
    "JobsDatasetProcessed_Clean.csv"
)

df2.to_csv(output2, index=False, encoding="utf-8")

print("Clean Rows:", len(df2))
print("Saved:", output2)


# =========================================================
# DATASET 3 - 10,000 JOB POSTINGS
# =========================================================

file3 = os.path.join(DATA_DIR, "JobsDataset.csv")

df3 = load_csv(file3)

print("\n========== DATASET 3 ==========")
print("Original Rows:", len(df3))
print("Columns:", df3.columns.tolist())

df3 = clean_text_columns(df3)

# Remove duplicate rows
df3 = df3.drop_duplicates()

# Clean important columns
for column in [
    "Query",
    "Job Title",
    "Description"
]:
    if column in df3.columns:
        df3[column] = (
            df3[column]
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

output3 = os.path.join(
    OUTPUT_DIR,
    "JobsDataset_Clean.csv"
)

df3.to_csv(output3, index=False, encoding="utf-8")

print("Clean Rows:", len(df3))
print("Saved:", output3)


# =========================================================
# FINAL SUMMARY
# =========================================================

print("\n======================================")
print("       DATA CLEANING COMPLETED")
print("======================================")

print("Dataset 1:", len(df1), "records")
print("Dataset 2:", len(df2), "records")
print("Dataset 3:", len(df3), "records")

print("\nTotal records:", len(df1) + len(df2) + len(df3))

print("\nCleaned files are available in:")
print(OUTPUT_DIR)

print("\n======================================")