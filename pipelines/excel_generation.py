import os
import pandas as pd

# ----------------------------------------
# Paths
# ----------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")


# ----------------------------------------
# Excel Generation
# ----------------------------------------
def run_excel_generation():

    print("Starting Excel Generation...")
    print("-" * 40)

    shop_path = os.path.join(DATA_DIR, "shopwise.csv")
    image_path = os.path.join(DATA_DIR, "image_wise.csv")
    summary_path = os.path.join(DATA_DIR, "summary.csv")
    notes_path = os.path.join(DATA_DIR, "notes.csv")

    output_excel = os.path.join(DATA_DIR, "final_output.xlsx")

    files_added = 0

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:

        if os.path.exists(shop_path):
            shop_df = pd.read_csv(shop_path)
            shop_df.to_excel(writer, sheet_name="shopwise", index=False)
            print("shopwise.csv added to Excel")
            files_added += 1
        else:
            print("shopwise.csv not found")

        if os.path.exists(image_path):
            image_df = pd.read_csv(image_path)
            image_df.to_excel(writer, sheet_name="image_wise", index=False)
            print("image_wise.csv added to Excel")
            files_added += 1
        else:
            print("image_wise.csv not found")

        if os.path.exists(summary_path):
            summary_df = pd.read_csv(summary_path)
            summary_df.to_excel(writer, sheet_name="summary", index=False)
            print("summary.csv added to Excel")
            files_added += 1
        else:
            print("summary.csv not found")

        if os.path.exists(notes_path):
            notes_df = pd.read_csv(notes_path)
            notes_df.to_excel(writer, sheet_name="notes", index=False)
            print("notes.csv added to Excel")
            files_added += 1
        else:
            print("notes.csv not found")

    if files_added == 0:
        print("No CSV files found. Excel not created.")
    else:
        print("-" * 40)
        print("final_output.xlsx created in data folder")


# ----------------------------------------
# Entry Point
# ----------------------------------------
if __name__ == "__main__":
    run_excel_generation()