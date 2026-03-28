import pandas as pd
import os

# -----------------------------------------
# Paths
# -----------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")


# -----------------------------------------
# Notes Pipeline
# -----------------------------------------
def run_notes():

    print("Starting Notes Pipeline...")
    print("-" * 40)

    input_path = os.path.join(DATA_DIR, "analytic.csv")
    output_path = os.path.join(DATA_DIR, "notes.csv")

    # -----------------------------------------
    # Load data
    # -----------------------------------------
    df = pd.read_csv(input_path)
    print("analytic.csv loaded successfully")

    # -----------------------------------------
    # Filter ai_correct = False
    # -----------------------------------------
    false_df = df[df["ai_correct"] == False]
    print(f"Total incorrect rows: {len(false_df)}")

    # -----------------------------------------
    # Grouping
    # -----------------------------------------
    result = (
        false_df
        .groupby(["category_id","category_name", "qc_class_name", "class_name"])
        .size()
        .reset_index(name="count")
    )

    # -----------------------------------------
    # Add total per category
    # -----------------------------------------
    result["total_count"] = result.groupby("category_name")["count"].transform("sum")

    # -----------------------------------------
    # Add ratio column (rounded decimal)
    # -----------------------------------------
    result["category_ratio"] = (
        result["count"] / result["total_count"]
    ).round(4)

    # rename the columns
    result = result.rename(columns={
        "qc_class_name": "actual",
        "class_name": "predicted"
    })

    # -----------------------------------------
    # Sorting
    # -----------------------------------------
    result = result.sort_values(
        ["category_name", "count"],
        ascending=[True, False]
    )

    print("Notes aggregation completed")

    # -----------------------------------------
    # Save CSV
    # -----------------------------------------
    result.to_csv(output_path, index=False)

    print("notes.csv created successfully")
    print("-" * 40)


# -----------------------------------------
# Entry Point
# -----------------------------------------
if __name__ == "__main__":
    run_notes()