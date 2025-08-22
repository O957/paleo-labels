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

POINTS_PER_INCH = 72
US_LETTER_WIDTH_IN = 8.5
US_LETTER_HEIGHT_IN = 11
PAGE_MARGIN_IN = 0.25
PAGE_MARGIN_PT = PAGE_MARGIN_IN * POINTS_PER_INCH

MIN_FONT_SIZE = 4
MAX_FONT_SIZE = 72
REFERENCE_FONT_SIZE = 12
DEFAULT_PADDING_PERCENT = 0.05

DIMENSION_MIN_IN = 0.1
DIMENSION_STEP_IN = 0.05
MAX_WIDTH_IN = 8.0
MAX_HEIGHT_IN = 10.0
DEFAULT_WIDTH_IN = 3.25
DEFAULT_HEIGHT_IN = 2.25

DIMENSION_MIN_CM = 0.3
DIMENSION_STEP_CM = 0.1
MAX_WIDTH_CM = 20.3
MAX_HEIGHT_CM = 25.4
DEFAULT_WIDTH_CM = 8.3
DEFAULT_HEIGHT_CM = 5.7

CM_TO_INCHES = 0.393701
INCHES_TO_CM = 2.54

DIMENSION_DECIMAL_PLACES = 2
BORDER_GRAY_VALUE = 0.8


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


def calculate_optimal_font_size(
    lines: list[str],
    canvas_obj: canvas.Canvas,
    font_name: str,
    available_width: float,
    available_height: float,
) -> float:
    """
    Calculate the largest font size that fits all text
    within available space using direct mathematical scaling.
    """
    if not lines:
        return 12

    reference_font_size = REFERENCE_FONT_SIZE

    max_text_width = max(
        canvas_obj.stringWidth(line, font_name, reference_font_size)
        for line in lines
    )
    total_text_height = len(lines) * reference_font_size

    width_scale = (
        available_width / max_text_width
        if max_text_width > 0
        else float("inf")
    )
    height_scale = (
        available_height / total_text_height
        if total_text_height > 0
        else float("inf")
    )

    optimal_scale = min(width_scale, height_scale)
    optimal_font_size = reference_font_size * optimal_scale

    return max(min(optimal_font_size, MAX_FONT_SIZE), MIN_FONT_SIZE)


def draw_rotated_text(
    canvas_obj: canvas.Canvas,
    lines: list[str],
    font_size: float,
    label_x_offset: float,
    label_y_offset: float,
    label_width_pt: float,
    label_height_pt: float,
    effective_width: float,
    effective_height: float,
    padding_x: float,
    padding_y: float,
) -> None:
    """Draw text rotated 90 degrees clockwise."""
    canvas_obj.saveState()
    canvas_obj.translate(
        label_x_offset + label_width_pt / 2,
        label_y_offset + label_height_pt / 2,
    )
    canvas_obj.rotate(90)
    text_start_x = -effective_width / 2 + padding_x
    text_start_y = effective_height / 2 - padding_y - font_size

    y_position = text_start_y
    for line in lines:
        if y_position >= -effective_height / 2 + padding_y:
            canvas_obj.drawString(text_start_x, y_position, line)
            y_position -= font_size

    canvas_obj.restoreState()


def draw_normal_text(
    canvas_obj: canvas.Canvas,
    lines: list[str],
    font_size: float,
    label_x_offset: float,
    label_y_offset: float,
    label_height_pt: float,
    padding_x: float,
    padding_y: float,
) -> None:
    """Draw text in normal orientation."""
    text_start_x = label_x_offset + padding_x
    text_start_y = label_y_offset + label_height_pt - padding_y - font_size

    y_position = text_start_y
    for line in lines:
        if y_position >= label_y_offset + padding_y:
            canvas_obj.drawString(text_start_x, y_position, line)
            y_position -= font_size


def generate_label_pdf(
    label_data: dict,
    style: dict,
    width_in: float = 1.0,
    height_in: float = 2.0,
    rotate_text: bool = False,
) -> bytes:
    """
    Generate a printable PDF for a label with automatic
    font sizing."""
    buffer = BytesIO()

    page_width_pt = US_LETTER_WIDTH_IN * POINTS_PER_INCH
    page_height_pt = US_LETTER_HEIGHT_IN * POINTS_PER_INCH
    label_width_pt = width_in * POINTS_PER_INCH
    label_height_pt = height_in * POINTS_PER_INCH

    c = canvas.Canvas(buffer, pagesize=(page_width_pt, page_height_pt))

    label_x_offset = PAGE_MARGIN_PT
    label_y_offset = page_height_pt - PAGE_MARGIN_PT - label_height_pt
    font_name = style.get("font_name", "Helvetica")
    padding_percent = style.get("padding_percent", DEFAULT_PADDING_PERCENT)

    effective_width = label_height_pt if rotate_text else label_width_pt
    effective_height = label_width_pt if rotate_text else label_height_pt

    padding_x = effective_width * padding_percent
    padding_y = effective_height * padding_percent
    available_width = effective_width - 2 * padding_x
    available_height = effective_height - 2 * padding_y

    lines = [f"{key}: {value}" for key, value in label_data.items()]

    c.setStrokeColorRGB(
        BORDER_GRAY_VALUE, BORDER_GRAY_VALUE, BORDER_GRAY_VALUE
    )
    c.rect(
        label_x_offset,
        label_y_offset,
        label_width_pt,
        label_height_pt,
        stroke=1,
        fill=0,
    )

    if not lines:
        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    font_size = calculate_optimal_font_size(
        lines, c, font_name, available_width, available_height
    )

    c.setFont(font_name, font_size)
    c.setFillColorRGB(0, 0, 0)

    if rotate_text:
        draw_rotated_text(
            c,
            lines,
            font_size,
            label_x_offset,
            label_y_offset,
            label_width_pt,
            label_height_pt,
            effective_width,
            effective_height,
            padding_x,
            padding_y,
        )
    else:
        draw_normal_text(
            c,
            lines,
            font_size,
            label_x_offset,
            label_y_offset,
            label_height_pt,
            padding_x,
            padding_y,
        )

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
    Render sidebar UI to get label dimensions and rotation
    option.

    Returns
    -------
    tuple[float, float, bool]
        Width, height of the label in inches, and whether
        to rotate text.
    """
    st.sidebar.subheader("Label Dimensions")

    unit_system = st.sidebar.radio(
        "Units", ["Imperial (inches)", "Metric (cm)"], horizontal=True
    )

    is_metric = unit_system == "Metric (cm)"

    if is_metric:
        width_display = st.sidebar.number_input(
            "Width (cm)",
            min_value=DIMENSION_MIN_CM,
            max_value=MAX_WIDTH_CM,
            value=DEFAULT_WIDTH_CM,
            step=DIMENSION_STEP_CM,
        )
        height_display = st.sidebar.number_input(
            "Height (cm)",
            min_value=DIMENSION_MIN_CM,
            max_value=MAX_HEIGHT_CM,
            value=DEFAULT_HEIGHT_CM,
            step=DIMENSION_STEP_CM,
        )
        width_in = width_display * CM_TO_INCHES
        height_in = height_display * CM_TO_INCHES
    else:
        width_in = st.sidebar.number_input(
            "Width (inches)",
            min_value=DIMENSION_MIN_IN,
            max_value=MAX_WIDTH_IN,
            value=DEFAULT_WIDTH_IN,
            step=DIMENSION_STEP_IN,
        )
        height_in = st.sidebar.number_input(
            "Height (inches)",
            min_value=DIMENSION_MIN_IN,
            max_value=MAX_HEIGHT_IN,
            value=DEFAULT_HEIGHT_IN,
            step=DIMENSION_STEP_IN,
        )

    rotate_text = False
    if height_in > width_in:
        rotate_text = st.sidebar.checkbox(
            "Rotate Label (For Better Fit)", value=False
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
    st.title("Label Maker")
    if label_config:
        st.subheader("Preview")
        for k, v in label_config.items():
            st.markdown(f"**{k}:** {v}")
        pdf_bytes = generate_label_pdf(
            label_config,
            style_config,
            round(width_in, DIMENSION_DECIMAL_PLACES),
            round(height_in, DIMENSION_DECIMAL_PLACES),
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
            "Please provide label data via TOML upload "
            "or manual entry in "
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
