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
    except (toml.TomlDecodeError, UnicodeDecodeError) as e:
        st.error(f"Error parsing TOML: {e}")
        st.stop()
    st.success(f"Loaded {uploaded_file.name}")
    return config


def generate_label_pdf(
    label_data: dict,
    style: dict,
    width_in: float = 1.0,
    height_in: float = 2.0,
    rotate_text: bool = False,
) -> bytes:
    """
    Generate a printable PDF for a label from provided
    data and optional style settings. The font size is
    automatically calculated to fit exactly within the
    specified dimensions with proper padding.

    Parameters
    ----------
    label_data : dict
        Dictionary of header-value pairs for the label.
    style : dict
        Optional style settings (e.g., font_name,
        font_size, padding_percent) loaded from a TOML.
        Note: dimensions take precedence over font_size.
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

    page_width_pt = 8.5 * 72
    page_height_pt = 11 * 72

    label_width_pt = width_in * 72
    label_height_pt = height_in * 72

    c = canvas.Canvas(buffer, pagesize=(page_width_pt, page_height_pt))

    label_x_offset = 18
    label_y_offset = page_height_pt - 18 - label_height_pt

    font_name = style.get("font_name", "Helvetica")
    padding_percent = style.get("padding_percent", 0.05)

    if rotate_text:
        effective_width = label_height_pt
        effective_height = label_width_pt
    else:
        effective_width = label_width_pt
        effective_height = label_height_pt

    padding_x = effective_width * padding_percent
    padding_y = effective_height * padding_percent

    available_width = effective_width - 2 * padding_x
    available_height = effective_height - 2 * padding_y

    lines = [f"{key}: {value}" for key, value in label_data.items()]

    if not lines:
        c.rect(
            label_x_offset,
            label_y_offset,
            label_width_pt,
            label_height_pt,
            stroke=1,
            fill=0,
        )
        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    min_font_size = 4
    max_font_size = 72
    optimal_font_size = min_font_size

    low, high = min_font_size, max_font_size

    while high - low > 0.05:
        test_font_size = (low + high) / 2

        max_text_width = max(
            c.stringWidth(line, font_name, test_font_size) for line in lines
        )

        line_height = test_font_size
        total_text_height = len(lines) * line_height

        fits_width = max_text_width <= available_width
        fits_height = total_text_height <= available_height

        if fits_width and fits_height:
            optimal_font_size = test_font_size
            low = test_font_size
        else:
            high = test_font_size

    font_size = max(optimal_font_size, min_font_size)

    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.rect(
        label_x_offset,
        label_y_offset,
        label_width_pt,
        label_height_pt,
        stroke=1,
        fill=0,
    )

    c.setFont(font_name, font_size)
    c.setFillColorRGB(0, 0, 0)

    if rotate_text:
        c.saveState()
        c.translate(
            label_x_offset + label_width_pt / 2,
            label_y_offset + label_height_pt / 2,
        )
        c.rotate(90)
        text_start_x = -effective_width / 2 + padding_x
        text_start_y = effective_height / 2 - padding_y - font_size
    else:
        text_start_x = label_x_offset + padding_x
        text_start_y = label_y_offset + label_height_pt - padding_y - font_size

    y_position = text_start_y
    for line in lines:
        if rotate_text:
            bounds_check = y_position >= -effective_height / 2 + padding_y
        else:
            bounds_check = y_position >= label_y_offset + padding_y

        if bounds_check:
            c.drawString(text_start_x, y_position, line)
            y_position -= font_size

    if rotate_text:
        c.restoreState()

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


def get_dimensions_config() -> tuple[float, float, bool]:
    """
    Render sidebar UI to get label dimensions and rotation option.

    Returns
    -------
    tuple[float, float, bool]
        Width, height of the label in inches, and whether to rotate text.
    """
    st.sidebar.subheader("Label Dimensions")
    width_in = st.sidebar.number_input(
        "Width (inches)", min_value=0.1, max_value=8.0, value=1.0, step=0.05
    )
    height_in = st.sidebar.number_input(
        "Height (inches)", min_value=0.1, max_value=10.0, value=2.0, step=0.05
    )
    rotate_text = False
    if height_in > width_in:
        rotate_text = st.sidebar.checkbox(
            "Rotate text to fit better", value=False
        )
    return width_in, height_in, rotate_text


def display_preview_and_download(
    label_config: dict,
    style_config: dict,
    width_in: float,
    height_in: float,
    rotate_text: bool,
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
    width_in : float
        Width of the label in inches.
    height_in : float
        Height of the label in inches.
    """
    st.title("Specimen(s) Label Maker")
    if label_config:
        st.subheader("Preview")
        for k, v in label_config.items():
            st.markdown(f"**{k}:** {v}")
        pdf_bytes = generate_label_pdf(
            label_config,
            style_config,
            round(width_in, 2),
            round(height_in, 2),
            rotate_text,
        )
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
    width_in, height_in, rotate_text = get_dimensions_config()
    display_preview_and_download(
        label_cfg, style_cfg, width_in, height_in, rotate_text
    )

    duration = time.time() - start
    logger.info(f"Session duration: {duration:.2f}s")


if __name__ == "__main__":
    main()
