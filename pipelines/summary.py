import pandas as pd
import numpy as np
import os

# ----------------------------------------
# Paths
# ----------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")


def run_summary():

    print("Starting Summary Pipeline...")
    print("-" * 40)

    input_path = os.path.join(DATA_DIR, "analytic.csv")
    output_path = os.path.join(DATA_DIR, "summary.csv")

    # -----------------------------------------
    # Load data
    # -----------------------------------------
    agg_df = pd.read_csv(input_path)

    print("Data loaded successfully")

    # Normalize text columns
    agg_df['qc_class_name'] = agg_df['qc_class_name'].astype(str).str.lower()
    agg_df['qc_competition'] = agg_df['qc_competition'].astype(str).str.lower()
    agg_df['category_name'] = agg_df['category_name'].astype(str)

    # -----------------------------------------
    # Vectorized flags
    # -----------------------------------------
    self_flag = agg_df['qc_competition'] == 'self'
    comp_flag = agg_df['qc_competition'] == 'competitor'
    sticker_flag = agg_df['qc_class_name'].str.contains('sticker', na=False)
    others_flag = agg_df['qc_class_name'].str.contains('other', na=False)
    incorrect_flag = agg_df['ai_correct'] == False

    # -----------------------------------------
    # Grouping
    # -----------------------------------------
    group_cols_cat = ['category_id', 'category_name']

    cat_agg = agg_df.groupby(group_cols_cat).agg(
        self_count=('qc_competition', lambda x: (self_flag.loc[x.index]).sum() - (self_flag.loc[x.index] & sticker_flag.loc[x.index]).sum()),
        comp_count=('qc_competition', lambda x: (comp_flag.loc[x.index]).sum() - (comp_flag.loc[x.index] & sticker_flag.loc[x.index]).sum() - ((comp_flag.loc[x.index] & others_flag.loc[x.index]).sum())),
        others_count=('qc_class_name', lambda x: (comp_flag.loc[x.index] & others_flag.loc[x.index]).sum()),
        sticker_count=('qc_class_name', lambda x: sticker_flag.loc[x.index].sum()),
        incorrect_self=('qc_competition', lambda x: (self_flag.loc[x.index] & incorrect_flag.loc[x.index]).sum()),
        incorrect_comp=('qc_competition',
            lambda x: (
                comp_flag.loc[x.index] &
                incorrect_flag.loc[x.index] &
                ~sticker_flag.loc[x.index] &
                ~others_flag.loc[x.index]
            ).sum()
        ),
        incorrect_others=('qc_class_name', lambda x: (others_flag.loc[x.index] & incorrect_flag.loc[x.index]).sum()),
        total_image_count=('test_image_id', 'nunique'),
        total_image_count_per_shop=('shop_id', 'nunique')
    ).reset_index()

    # -----------------------------------------
    # Metrics
    # -----------------------------------------
    cat_agg['SPI'] = (cat_agg['self_count'] - cat_agg['incorrect_self']) / cat_agg['self_count']
    cat_agg['CPI'] = (cat_agg['comp_count'] - cat_agg['incorrect_comp']) / cat_agg['comp_count']
    cat_agg['NPD'] = cat_agg['others_count'] / (cat_agg['self_count'] + cat_agg['comp_count'] + cat_agg['others_count'])
    cat_agg['total_count'] = cat_agg['self_count'] + cat_agg['comp_count'] + cat_agg['others_count']
    cat_agg['total_incorrect'] = cat_agg['incorrect_self'] + cat_agg['incorrect_comp'] + cat_agg['incorrect_others']
    cat_agg['accuracy'] = (cat_agg['total_count'] - cat_agg['total_incorrect']) / cat_agg['total_count']

    # -----------------------------------------
    # Save CSV
    # -----------------------------------------
    category_summary = cat_agg

    category_summary.to_csv(output_path, index=False)

    print("summary.csv created successfully")
    print("-" * 40)


# ----------------------------------------
# Entry Point
# ----------------------------------------
if __name__ == "__main__":
    run_summary()