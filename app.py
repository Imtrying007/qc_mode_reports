import streamlit as st
import os
import subprocess

# ----------------------------------------
# Project Paths
# ----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PIPELINE_DIR = os.path.join(BASE_DIR, "pipelines")

# ----------------------------------------
# Page Config
# ----------------------------------------
st.set_page_config(
    page_title="QC Transformation Pipeline",
    page_icon="📊",
    layout="wide"
)

st.title("📊 QC Transformation Pipeline")
st.write("Upload QC Mode and CGC CSV files to run the pipeline.")

# ----------------------------------------
# Create Data Folder
# ----------------------------------------
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------------------
# File Upload
# ----------------------------------------
qc_mode_file = st.file_uploader(
    "Upload QC Mode CSV File",
    type=["csv"]
)

cgc_file = st.file_uploader(
    "Upload CGC CSV File",
    type=["csv"]
)

# ----------------------------------------
# Save Files
# ----------------------------------------
def save_file(uploaded_file, path):
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())

# ----------------------------------------
# Pipeline Execution Function
# ----------------------------------------
def run_script(script_name):
    script_path = os.path.join(PIPELINE_DIR, script_name)

    result = subprocess.run(
        ["python", script_path],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    return result

# ----------------------------------------
# Run Pipeline
# ----------------------------------------
if qc_mode_file and cgc_file:

    if st.button("🚀 Run QC Transformation Pipeline"):

        try:
            # Save files
            qc_path = os.path.join(DATA_DIR, "qc_mode.csv")
            cgc_path = os.path.join(DATA_DIR, "cgc.csv")

            save_file(qc_mode_file, qc_path)
            save_file(cgc_file, cgc_path)

            st.success("Files saved successfully ✅")

            # ----------------------------------------
            # Pipeline Order
            # ----------------------------------------
            pipeline_scripts = [
                "main_file.py",
                "image_level.py",
                "shop_category.py",
                "summary.py",
                "notes.py"
            ]

            st.subheader("Pipeline Execution")

            all_success = True

            for script in pipeline_scripts:

                st.info(f"Running {script}...")

                result = run_script(script)

                if result.returncode != 0:
                    st.error(f"{script} failed ❌")
                    st.code(result.stderr)
                    all_success = False
                    break

                else:
                    st.success(f"{script} completed ✅")
                    st.code(result.stdout)

            # ----------------------------------------
            # Run Excel Generation
            # ----------------------------------------
            if all_success:

                st.info("Running excel_generation.py...")

                result = run_script("excel_generation.py")

                if result.returncode != 0:
                    st.error("excel_generation.py failed ❌")
                    st.code(result.stderr)

                else:
                    st.success("Excel file generated successfully ✅")

                    excel_path = os.path.join(DATA_DIR, "final_output.xlsx")

                    if os.path.exists(excel_path):
                        with open(excel_path, "rb") as f:
                            st.download_button(
                                "⬇️ Download Final Excel",
                                f,
                                "final_output.xlsx"
                            )
                    else:
                        st.warning("final_output.xlsx not found")

        except Exception as e:
            st.error(str(e))