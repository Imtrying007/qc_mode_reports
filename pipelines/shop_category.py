import pandas as pd
import numpy as np
import os

# -----------------------------------------
# Paths
# -----------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")


# -----------------------------------------
# Shop Category Pipeline
# -----------------------------------------
def run_shop_category():

    print("Starting Shop Category Pipeline...")
    print("-" * 40)

    input_path = os.path.join(DATA_DIR, "analytic.csv")
    output_path = os.path.join(DATA_DIR, "shopwise.csv")

    # -----------------------------------------
    # Load data
    # -----------------------------------------
    shop_df = pd.read_csv(input_path)
    print("analytic.csv loaded successfully")

    # -----------------------------------------
    # Normalize text columns
    # -----------------------------------------
    shop_df['qc_class_name'] = shop_df['qc_class_name'].astype(str).str.lower()
    shop_df['qc_competition'] = shop_df['qc_competition'].astype(str).str.lower()
    shop_df['category_name'] = shop_df['category_name'].astype(str)

    # -----------------------------------------
    # Vectorized flags
    # -----------------------------------------
    self_flag = shop_df['qc_competition'] == 'self'
    comp_flag = shop_df['qc_competition'] == 'competitor'
    sticker_flag = shop_df['qc_class_name'].str.contains('sticker', na=False)
    others_flag = shop_df['qc_class_name'].str.contains('other', na=False)
    incorrect_flag = shop_df['ai_correct'] == False

    # -----------------------------------------
    # Groupby
    # -----------------------------------------
    group_cols_shop = ['category_id', 'category_name', 'shop_id']

    shop_agg = shop_df.groupby(group_cols_shop).agg(

        self_count=('qc_competition',
            lambda x: (
                self_flag.loc[x.index] &
                ~sticker_flag.loc[x.index]
            ).sum()
        ),

        comp_count=('qc_competition',
            lambda x: (
                comp_flag.loc[x.index] &
                ~sticker_flag.loc[x.index] &
                ~others_flag.loc[x.index]
            ).sum()
        ),

        others_count=('qc_class_name',
            lambda x: (
                comp_flag.loc[x.index] &
                others_flag.loc[x.index]
            ).sum()
        ),

        sticker_count=('qc_class_name',
            lambda x: sticker_flag.loc[x.index].sum()
        ),

        incorrect_self=('qc_competition',
            lambda x: (
                self_flag.loc[x.index] &
                incorrect_flag.loc[x.index]
            ).sum()
        ),

        incorrect_comp=('qc_competition',
            lambda x: (
                comp_flag.loc[x.index] &
                incorrect_flag.loc[x.index] &
                ~sticker_flag.loc[x.index] &
                ~others_flag.loc[x.index]
            ).sum()
        ),

        incorrect_others=('qc_class_name',
            lambda x: (
                others_flag.loc[x.index] &
                incorrect_flag.loc[x.index]
            ).sum()
        ),

        total_image_count=('test_image_id', 'nunique')

    ).reset_index()

    print("Shop-level aggregation completed")

    # -----------------------------------------
    # Metrics
    # -----------------------------------------
    shop_agg['SPI'] = (
        shop_agg['self_count'] - shop_agg['incorrect_self']
    ) / shop_agg['self_count']

    shop_agg['CPI'] = (
        shop_agg['comp_count'] - shop_agg['incorrect_comp']
    ) / shop_agg['comp_count']

    shop_agg['NPD'] = (
        shop_agg['others_count'] /
        (shop_agg['self_count'] +
         shop_agg['comp_count'] +
         shop_agg['others_count'])
    )

    shop_agg['total_count'] = (
        shop_agg['self_count'] +
        shop_agg['comp_count'] +
        shop_agg['others_count']
    )

    shop_agg['total_incorrect'] = (
        shop_agg['incorrect_self'] +
        shop_agg['incorrect_comp'] +
        shop_agg['incorrect_others']
    )

    shop_agg['accuracy'] = (
        shop_agg['total_count'] -
        shop_agg['total_incorrect']
    ) / shop_agg['total_count']

    print("Metrics calculated")

    # -----------------------------------------
    # AI Grade
    # -----------------------------------------
    F = shop_agg['accuracy']
    G = shop_agg['SPI']
    H = shop_agg['NPD']

    not_blank = (~F.isna()) & (~G.isna()) & (~H.isna())

    shop_agg['Ai_grade'] = ""

    shop_agg.loc[not_blank & (F>0.95) & (H<0.1) & (G>0.95), 'Ai_grade'] = "A"
    shop_agg.loc[not_blank & (F>0.95) & (H<0.1) & (G<=0.95), 'Ai_grade'] = "D"
    shop_agg.loc[not_blank & (F>0.95) & (H>=0.1) & (H<0.3) & (G>0.95), 'Ai_grade'] = "B"
    shop_agg.loc[not_blank & (F>0.95) & (H>=0.1) & (H<0.3) & (G<=0.95), 'Ai_grade'] = "E"
    shop_agg.loc[not_blank & (F>0.95) & (H>=0.3) & (G>0.95), 'Ai_grade'] = "C"
    shop_agg.loc[not_blank & (F>0.95) & (H>=0.3) & (G<=0.95), 'Ai_grade'] = "F"
    shop_agg.loc[not_blank & (F<=0.95) & (G>0.95) & (H<0.1), 'Ai_grade'] = "B"
    shop_agg.loc[not_blank & (F<=0.95) & (G>0.95) & (H>=0.1), 'Ai_grade'] = "C"
    shop_agg.loc[not_blank & (F<=0.95) & (G<=0.95) & (H<0.3), 'Ai_grade'] = "D"
    shop_agg.loc[not_blank & (F<=0.95) & (G<=0.95) & (H>=0.3), 'Ai_grade'] = "F"

    print("AI grading completed")

    # -----------------------------------------
    # Recommendation
    # -----------------------------------------
    shop_agg['recommendation'] = ""

    shop_agg.loc[not_blank & (F>0.95) & (H<0.1) & (G>0.95),
        'recommendation'] = "Sturdy category, no recommendations"

    shop_agg.loc[not_blank & (F>0.95) & (H<0.1) & (G<=0.95),
        'recommendation'] = "Hard category, needs active interference and group addition"

    shop_agg.loc[not_blank & (F>0.95) & (H>=0.1) & (H<0.3) & (G>0.95),
        'recommendation'] = "Category is okay, recommend adding new products"

    shop_agg.loc[not_blank & (F>0.95) & (H>=0.1) & (H<0.3) & (G<=0.95),
        'recommendation'] = "Too many products need to be added as groups"

    shop_agg.loc[not_blank & (F>0.95) & (H>=0.3) & (G>0.95),
        'recommendation'] = "Category okay but many products missing"

    shop_agg.loc[not_blank & (F>0.95) & (H>=0.3) & (G<=0.95),
        'recommendation'] = "Ignored category, immediate escalation"

    shop_agg.loc[not_blank & (F<=0.95) & (G>0.95) & (H<0.1),
        'recommendation'] = "Competitor SKU dataset issue or GT category"

    shop_agg.loc[not_blank & (F<=0.95) & (G>0.95) & (H>=0.1),
        'recommendation'] = "GT category ok, MT needs attention"

    shop_agg.loc[not_blank & (F<=0.95) & (G<=0.95) & (H<0.3),
        'recommendation'] = "Hard GT category or dataset issue"

    shop_agg.loc[not_blank & (F<=0.95) & (G<=0.95) & (H>=0.3),
        'recommendation'] = "Ignored category, immediate escalation"

    print("Recommendations added")

    # -----------------------------------------
    # Final Columns
    # -----------------------------------------
    final_cols_shop = [
        'category_id','category_name','shop_id','total_image_count',
        'self_count','comp_count','others_count','sticker_count',
        'incorrect_self','incorrect_comp','incorrect_others',
        'SPI','CPI','NPD','total_count','total_incorrect','accuracy',
        'Ai_grade','recommendation'
    ]

    shop_summary = shop_agg[final_cols_shop]

    # -----------------------------------------
    # Save CSV
    # -----------------------------------------
    shop_summary.to_csv(output_path, index=False)

    print("shopwise.csv created successfully")
    print("-" * 40)


# -----------------------------------------
# Entry Point
# -----------------------------------------
if __name__ == "__main__":
    run_shop_category()