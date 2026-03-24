import pandas as pd
import os

# -----------------------------------------
# Paths
# -----------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")


# -----------------------------------------
# Main Pipeline
# -----------------------------------------
def run_main_file():

    print("Starting Main Pipeline...")
    print("-" * 40)

    qc_path = os.path.join(DATA_DIR, "qc_mode.csv")
    cgc_path = os.path.join(DATA_DIR, "cgc.csv")
    output_path = os.path.join(DATA_DIR, "analytic.csv")

    # -----------------------------------------
    # Step 1: Load CSVs
    # -----------------------------------------
    df = pd.read_csv(qc_path)
    cgc = pd.read_csv(cgc_path)

    print("QC Mode and CGC loaded successfully")

    # -----------------------------------------
    # Step 2: Normalize column names
    # -----------------------------------------
    df.columns = df.columns.str.strip().str.lower()
    cgc.columns = cgc.columns.str.strip().str.lower()

    # -----------------------------------------
    # Step 3: Normalize values
    # -----------------------------------------
    df['competition'] = df['competition'].astype(str).str.strip().str.lower()
    cgc['competition'] = cgc['competition'].astype(str).str.strip().str.lower()

    df['ai_correct'] = (
        df['ai_correct']
        .astype(str)
        .str.strip()
        .str.lower()
        .map({'true': True, 'false': False})
    )

    for col in ['class_id', 'qc_group_id', 'category_id']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in ['class_id', 'group_id', 'category_id']:
        cgc[col] = pd.to_numeric(cgc[col], errors='coerce')

    # -----------------------------------------
    # Step 4: Backup original competition
    # -----------------------------------------
    df['qc_competition'] = df['competition'].copy()

    # -----------------------------------------
    # Step 5: Deduplicate CGC
    # -----------------------------------------
    cgc_unique = cgc.drop_duplicates(
        subset=['class_id', 'group_id', 'category_id']
    )

    print("CGC deduplicated")

    # -----------------------------------------
    # Step 6: Create mapping
    # -----------------------------------------
    cgc_map = cgc_unique.set_index(
        ['class_id', 'group_id', 'category_id']
    )['competition'].to_dict()

    # -----------------------------------------
    # Step 7: Vectorized update
    # -----------------------------------------
    df['key'] = list(zip(
        df['qc_class_id'],
        df['qc_group_id'],
        df['category_id']
    ))

    mask = df['ai_correct'] == False

    df.loc[mask, 'qc_competition'] = (
        df.loc[mask, 'key']
        .map(cgc_map)
        .fillna(df.loc[mask, 'qc_competition'])
    )

    print("Competition updated for incorrect AI predictions")

    # -----------------------------------------
    # Step 8: Save output
    # -----------------------------------------
    df.to_csv(output_path, index=False)

    print("analytic.csv created successfully")
    print("-" * 40)


# -----------------------------------------
# Entry Point
# -----------------------------------------
if __name__ == "__main__":
    run_main_file()