"""
Streamlit application (ran locally) for a user to design
at least one paleontological label.

To Run: uv run streamlit run app.py
"""

import io
import logging
import pathlib
import time

import streamlit as st
import toml


def st_load_toml(uploaded_toml_file):
    ext = pathlib.Path(uploaded_toml_file.name).suffix.lower()
    try:
        as_txt_from_bytesio = io.TextIOWrapper(
            uploaded_toml_file, encoding="utf-8"
        )
        if ext == ".toml":
            label_config = toml.load(as_txt_from_bytesio)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    st.success(f"Loaded {uploaded_toml_file.name}.")
    return label_config


def main() -> None:
    # initiate logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # initiate session time tracking
    start_time = time.time()

    # title block and opening message
    st.title("Paleontology Label Maker")
    st.markdown(
        "_paleo-labels is an application for writing precisely formatted "
        "labels singularly or in bulk for use with paleontological "
        "specimens, collections, and excursions. Enjoy!_"
    )

    # have user choose upload pathway
    mode = st.radio(
        label="Which File Type Do You Want To Upload?",
        options=("Template", "Label"),
        index=0,  # default to option 0
    )

    # template and label file upload
    uploaded_file = None
    if mode == "Template":
        uploaded_file = st.file_uploader(
            label="Upload Template", type=["toml"], key="template_file"
        )
    elif mode == "Label":
        uploaded_file = st.file_uploader(
            label="Upload Label", type=["toml"], key="label_file"
        )

    # uploaded file ingestion and loading
    if uploaded_file is not None:
        label_config = st_load_toml(uploaded_file)
        logger.info(f"Uploaded file:\n{uploaded_file.name}")
        print(label_config)

    # record session time
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Session lasted around: {duration // 60} minutes.")


if __name__ == "__main__":
    main()
