"""
Streamlit application (ran locally) for a user to design
at least one paleontological label.
"""

import logging
import pathlib
import time

import streamlit as st
import toml


def main() -> None:
    # initiate logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # initiate session time tracking
    start_time = time.time()

    # title block and upload options
    st.title("Paleontology Label Maker")
    label_template = st.file_uploader("Upload Label Template", type=["toml"])

    # read in toml template file
    if label_template is not None:
        ext = pathlib.Path(label_template.name).suffix.lower()
        try:
            if ext == ".toml":
                with open(label_template) as f:
                    label_config = toml.load(f)
        except ValueError as e:
            st.error(str(e))
            st.stop()
        st.success(f"Loaded {label_template.name}.")
    logger.info(f"Uploaded file:\n {label_template.name}")

    # convert toml contents into selection boxes
    print(label_config)

    # record end time
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Session lasted around: {duration // 60} minutes.")


if __name__ == "__main__":
    main()
