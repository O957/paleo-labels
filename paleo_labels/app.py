"""
Streamlit app for creating labels from TOML or manual
entry. Users can upload a label TOML or manually
enter key-value pairs. An optional style TOML can
adjust font and margin settings. The generated label
is previewed and downloadable as a PDF.

To Run: uv run streamlit run ./paleo_labels/app.py
"""

import io
import logging
import pathlib
import time
from io import BytesIO

import streamlit as st
import toml
from reportlab.pdfgen import canvas
from streamlit.runtime.uploaded_file_manager import UploadedFile


def load_toml(uploaded_file: UploadedFile) -> dict:
    """
    Load a TOML configuration (either a label or a style)
    from an uploaded file.

    Parameters
    ----------
    uploaded_file : UploadedFile
        The label or style for a label, uploaded as a toml
        file.

    Returns
    -------
    dict
        Parsed TOML configuration.

    Raises
    ------
    SystemExit
        If the file is not a .toml or parsing fails.
    """
    ext = pathlib.Path(uploaded_file.name).suffix.lower()
    if ext != ".toml":
        st.error("Unsupported file type. Please upload a .toml file.")
        st.stop()
    try:
        text_wrapper = io.TextIOWrapper(uploaded_file, encoding="utf-8")
        config = toml.load(text_wrapper)
    except Exception as e:
        st.error(f"Error parsing TOML: {e}")
        st.stop()
    st.success(f"Loaded {uploaded_file.name}")
    return config


def generate_label_pdf(
    label_data: dict,
    style: dict,
    width_in: float = 1.0,
    height_in: float = 2.0,
) -> bytes:
    """
    Generate a printable PDF for a label from provided
    data and optional style settings. All text uses a
    dynamically resized uniform font size so that the
    widest line fits within the label width.

    Parameters
    ----------
    label_data : dict
        Dictionary of header-value pairs for the label.
    style : dict
        Optional style settings (e.g., font_name,
        font_size, margin) loaded from a TOML.
    width_in : float, optional
        Width of the label in inches.
    height_in : float, optional
        Height of the label in inches.

    Returns
    -------
    bytes
        Raw bytes of the generated PDF file.
    """
    buffer = BytesIO()
    width_pt = width_in * 72
    height_pt = height_in * 72
    c = canvas.Canvas(buffer, pagesize=(width_pt, height_pt))

    font_name = style.get("font_name", "Helvetica")
    base_font_size = style.get("font_size", 12)
    margin = style.get("margin", 10)

    lines = [f"{key}: {value}" for key, value in label_data.items()]
    max_width = width_pt - 2 * margin
    max_text_width = max(
        (c.stringWidth(line, font_name, base_font_size) for line in lines),
        default=0,
    )

    font_size = base_font_size
    if max_text_width > max_width:
        scaled = int(base_font_size * max_width / max_text_width)
        font_size = max(scaled, 4)

    c.setFont(font_name, font_size)
    line_height = font_size + 2
    y = height_pt - margin

    for line in lines:
        if y < margin:
            c.showPage()
            c.setFont(font_name, font_size)
            y = height_pt - margin
        c.drawString(margin, y, line)
        y -= line_height

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def init_logging() -> logging.Logger:
    """
    Initialize logging for the application.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


def get_label_config() -> dict:
    """
    Render sidebar UI to obtain label data either from
    a TOML upload or manual entry.

    Returns
    -------
    dict
        Collected label key-value pairs.
    """
    st.sidebar.title("Options")
    source = st.sidebar.radio("Label Source", ["Upload TOML", "Manual Entry"])
    label_config: dict = {}

    if source == "Upload TOML":
        uploaded = st.sidebar.file_uploader(
            "Upload Label TOML", type=["toml"], key="label_file"
        )
        if uploaded:
            label_config = load_toml(uploaded)
    else:
        if "num_rows" not in st.session_state:
            st.session_state.num_rows = 1
        if st.sidebar.button("Add Row"):
            st.session_state.num_rows += 1
        for i in range(st.session_state.num_rows):
            cols = st.sidebar.columns(2)
            st.session_state.setdefault(f"key_{i}", "")
            st.session_state.setdefault(f"value_{i}", "")
            k = cols[0].text_input(
                f"Field {i + 1} Key",
                value=st.session_state[f"key_{i}"],
                key=f"field_key_{i}",
            )
            v = cols[1].text_input(
                f"Field {i + 1} Value",
                value=st.session_state[f"value_{i}"],
                key=f"field_value_{i}",
            )
            st.session_state[f"key_{i}"] = k
            st.session_state[f"value_{i}"] = v
        for i in range(st.session_state.num_rows):
            k = st.session_state.get(f"key_{i}", "").strip()
            v = st.session_state.get(f"value_{i}", "").strip()
            if k:
                label_config[k] = v
    return label_config


def get_style_config() -> dict:
    """
    Render sidebar UI to optionally upload a style TOML.

    Returns
    -------
    dict
        Parsed style configuration or empty.
    """
    style_config: dict = {}
    uploaded = st.sidebar.file_uploader(
        "Upload Style TOML (Optional)", type=["toml"], key="style_file"
    )
    if uploaded:
        style_config = load_toml(uploaded)
    return style_config


def display_preview_and_download(
    label_config: dict, style_config: dict
) -> None:
    """
    Display label preview in main area and provide a
    download button for the generated PDF.

    Parameters
    ----------
    label_config : dict
        Collected label key-value pairs.
    style_config : dict
        Parsed style settings.
    """
    st.title("Specimen(s) Label Maker")
    if label_config:
        st.subheader("Preview")
        for k, v in label_config.items():
            st.markdown(f"**{k}:** {v}")
        pdf_bytes = generate_label_pdf(label_config, style_config)
        st.download_button(
            label="Download PDF Label",
            data=pdf_bytes,
            file_name="paleo_label.pdf",
            mime="application/pdf",
        )
    else:
        st.info(
            "Please provide label data via TOML upload or manual entry in "
            "the sidebar."
        )


def main() -> None:
    """
    Main entry point for the Streamlit application.
    Initializes logging, orchestrates UI collection, and
    handles PDF rendering and download.
    """
    logger = init_logging()
    start = time.time()

    label_cfg = get_label_config()
    style_cfg = get_style_config()
    display_preview_and_download(label_cfg, style_cfg)

    duration = time.time() - start
    logger.info(f"Session duration: {duration:.2f}s")


if __name__ == "__main__":
    main()
