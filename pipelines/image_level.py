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
# Image Level Pipeline
# -----------------------------------------
def run_image_level():

    print("Starting Image Level Pipeline...")
    print("-" * 40)

    input_path = os.path.join(DATA_DIR, "analytic.csv")
    output_path = os.path.join(DATA_DIR, "image_wise.csv")

    # -----------------------------------------
    # Load data
    # -----------------------------------------
    img_df = pd.read_csv(input_path)
    print("analytic.csv loaded successfully")

    # -----------------------------------------
    # Normalize text columns
    # -----------------------------------------
    img_df['qc_class_name'] = img_df['qc_class_name'].astype(str).str.lower()
    img_df['qc_competition'] = img_df['qc_competition'].astype(str).str.lower()
    img_df['category_name'] = img_df['category_name'].astype(str)

    # -----------------------------------------
    # Vectorized flags
    # -----------------------------------------
    self_flag = img_df['qc_competition'] == 'self'
    comp_flag = img_df['qc_competition'] == 'competitor'
    sticker_flag = img_df['qc_class_name'].str.contains('sticker', na=False)
    others_flag = img_df['qc_class_name'].str.contains('other', na=False)
    incorrect_flag = img_df['ai_correct'] == False

    # -----------------------------------------
    # Groupby
    # -----------------------------------------
    group_cols_img = [
        'category_id',
        'category_name',
        'shop_id',
        'test_image_id',
        'file_path'
    ]

    img_agg = img_df.groupby(group_cols_img).agg(

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
                incorrect_flag.loc[x.index] &
                ~sticker_flag.loc[x.index]
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
                comp_flag.loc[x.index] &
                others_flag.loc[x.index] &
                incorrect_flag.loc[x.index]
            ).sum()
        )

    ).reset_index()

    print("Image level aggregation completed")

    # -----------------------------------------
    # Metrics
    # -----------------------------------------
    img_agg['total_count'] = (
        img_agg['self_count'] +
        img_agg['comp_count'] +
        img_agg['others_count']
    )

    img_agg['total_incorrect'] = (
        img_agg['incorrect_self'] +
        img_agg['incorrect_comp'] +
        img_agg['incorrect_others']
    )

    img_agg['accuracy'] = (
        img_agg['total_count'] - img_agg['total_incorrect']
    ) / img_agg['total_count']

    img_agg['SPI'] = (
        img_agg['self_count'] - img_agg['incorrect_self']
    ) / img_agg['self_count']

    img_agg['CPI'] = (
        img_agg['comp_count'] - img_agg['incorrect_comp']
    ) / img_agg['comp_count']

    img_agg['NPD'] = (
        img_agg['others_count'] /
        (img_agg['self_count'] +
         img_agg['comp_count'] +
         img_agg['others_count'])
    )

    print("Metrics calculated")

    # -----------------------------------------
    # AI Grade
    # -----------------------------------------
    F = img_agg['accuracy']
    G = img_agg['SPI']
    H = img_agg['NPD']

    not_blank = (~F.isna()) & (~G.isna()) & (~H.isna())

    img_agg['Ai_grade'] = ""

    img_agg.loc[not_blank & (F>0.95) & (H<0.1) & (G>0.95), 'Ai_grade'] = "A"
    img_agg.loc[not_blank & (F>0.95) & (H<0.1) & (G<=0.95), 'Ai_grade'] = "D"
    img_agg.loc[not_blank & (F>0.95) & (H>=0.1) & (H<0.3) & (G>0.95), 'Ai_grade'] = "B"
    img_agg.loc[not_blank & (F>0.95) & (H>=0.1) & (H<0.3) & (G<=0.95), 'Ai_grade'] = "E"
    img_agg.loc[not_blank & (F>0.95) & (H>=0.3) & (G>0.95), 'Ai_grade'] = "C"
    img_agg.loc[not_blank & (F>0.95) & (H>=0.3) & (G<=0.95), 'Ai_grade'] = "F"
    img_agg.loc[not_blank & (F<=0.95) & (G>0.95) & (H<0.1), 'Ai_grade'] = "B"
    img_agg.loc[not_blank & (F<=0.95) & (G>0.95) & (H>=0.1), 'Ai_grade'] = "C"
    img_agg.loc[not_blank & (F<=0.95) & (G<=0.95) & (H<0.3), 'Ai_grade'] = "D"
    img_agg.loc[not_blank & (F<=0.95) & (G<=0.95) & (H>=0.3), 'Ai_grade'] = "F"

    print("AI grading completed")

    # -----------------------------------------
    # Final Columns
    # -----------------------------------------
    final_cols_img = [
        'category_id','category_name','shop_id','file_path','test_image_id',
        'self_count','comp_count','others_count','sticker_count',
        'incorrect_self','incorrect_comp','incorrect_others',
        'SPI','CPI','NPD','total_count','total_incorrect','accuracy',
        'Ai_grade'
    ]

    image_summary = img_agg[final_cols_img]

    # -----------------------------------------
    # Save CSV
    # -----------------------------------------
    image_summary.to_csv(output_path, index=False)

    print("image_wise.csv created successfully")
    print("-" * 40)


# -----------------------------------------
# Entry Point
# -----------------------------------------
if __name__ == "__main__":
    run_image_level()