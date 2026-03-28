import streamlit as st
import os
import subprocess
import uuid

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
qc_mode_file = st.file_uploader("Upload QC Mode CSV File", type=["csv"])
cgc_file = st.file_uploader("Upload CGC CSV File", type=["csv"])

# ----------------------------------------
# Save Files
# ----------------------------------------
def save_file(uploaded_file, filename_prefix):
    # """Save uploaded file with a unique name."""
    # unique_name = f"{filename_prefix}_{uuid.uuid4().hex}.csv"
    unique_name = f"{filename_prefix}.csv"
    path = os.path.join(DATA_DIR, unique_name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

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

    run_button = st.button("🚀 Run QC Transformation Pipeline")

    if run_button:
        try:
            # Save files with unique names
            qc_path = save_file(qc_mode_file, "qc_mode")
            cgc_path = save_file(cgc_file, "cgc")

            st.success("Files saved successfully ✅")

            # Pipeline scripts order
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

            # Run Excel Generation
            if all_success:
                st.info("Running excel_generation.py...")
                result = run_script("excel_generation.py")

                if result.returncode != 0:
                    st.error("excel_generation.py failed ❌")
                    st.code(result.stderr)
                else:
                    st.success("Excel file generated successfully ✅")

                    # Store output paths in session_state for persistent downloads
                    st.session_state['summary_path'] = os.path.join(DATA_DIR, "summary.csv")
                    st.session_state['notes_path'] = os.path.join(DATA_DIR, "notes.csv")
                    st.session_state['excel_path'] = os.path.join(DATA_DIR, "final_output.xlsx")

        except Exception as e:
            st.error(f"Pipeline failed: {str(e)}")

# ----------------------------------------
# Download Section
# ----------------------------------------
st.subheader("⬇️ Download Files")

if 'summary_path' in st.session_state and os.path.exists(st.session_state['summary_path']):
    with open(st.session_state['summary_path'], "rb") as f:
        st.download_button(
            "Download summary.csv",
            f,
            "summary.csv"
        )

if 'notes_path' in st.session_state and os.path.exists(st.session_state['notes_path']):
    with open(st.session_state['notes_path'], "rb") as f:
        st.download_button(
            "Download notes.csv",
            f,
            "notes.csv"
        )

if 'excel_path' in st.session_state and os.path.exists(st.session_state['excel_path']):
    with open(st.session_state['excel_path'], "rb") as f:
        st.download_button(
            "Download final_output.xlsx",
            f,
            "final_output.xlsx"
        )