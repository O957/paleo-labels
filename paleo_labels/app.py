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


def load_label_style_from_file(style_file_path: str) -> dict:
    """
    Load label style configuration from a TOML file.

    Parameters
    ----------
    style_file_path : str
        Path to the style TOML file.

    Returns
    -------
    dict
        Parsed style configuration with defaults applied.
    """
    try:
        with open(style_file_path, encoding="utf-8") as f:
            style_config = toml.load(f)

        processed_style = apply_style_defaults(style_config)
        return processed_style
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        logging.warning(f"Could not load style file {style_file_path}: {e}")
        return apply_style_defaults({})


def get_font_name(base_font: str, is_bold: bool, is_italic: bool) -> str:
    """Get the appropriate ReportLab font name based on style flags."""
    font_variants = {
        "Helvetica": {
            (False, False): "Helvetica",
            (True, False): "Helvetica-Bold",
            (False, True): "Helvetica-Oblique",
            (True, True): "Helvetica-BoldOblique",
        },
        "Times-Roman": {
            (False, False): "Times-Roman",
            (True, False): "Times-Bold",
            (False, True): "Times-Italic",
            (True, True): "Times-BoldItalic",
        },
        "Courier": {
            (False, False): "Courier",
            (True, False): "Courier-Bold",
            (False, True): "Courier-Oblique",
            (True, True): "Courier-BoldOblique",
        },
    }

    if base_font in font_variants:
        return font_variants[base_font][(is_bold, is_italic)]
    else:
        return base_font


def apply_style_defaults(style_config: dict) -> dict:
    """
    Apply default values to style configuration and handle font styling.

    Parameters
    ----------
    style_config : dict
        Raw style configuration from TOML.

    Returns
    -------
    dict
        Style configuration with defaults and processed font settings.
    """
    processed = style_config.copy()

    processed.setdefault("font_name", "Helvetica")
    processed.setdefault("font_size", REFERENCE_FONT_SIZE)
    processed.setdefault("key_color_r", 0.0)
    processed.setdefault("key_color_g", 0.0)
    processed.setdefault("key_color_b", 0.0)
    processed.setdefault("value_color_r", 0.0)
    processed.setdefault("value_color_g", 0.0)
    processed.setdefault("value_color_b", 0.0)
    processed.setdefault("padding_percent", DEFAULT_PADDING_PERCENT)
    processed.setdefault("width_inches", DEFAULT_WIDTH_IN)
    processed.setdefault("height_inches", DEFAULT_HEIGHT_IN)
    processed.setdefault("bold_keys", False)
    processed.setdefault("bold_values", False)
    processed.setdefault("italic_keys", False)
    processed.setdefault("italic_values", False)
    processed.setdefault("show_keys", True)
    processed.setdefault("show_values", True)

    base_font = processed["font_name"]
    bold_keys = processed["bold_keys"]
    bold_values = processed["bold_values"]
    italic_keys = processed["italic_keys"]
    italic_values = processed["italic_values"]

    processed["key_font"] = get_font_name(base_font, bold_keys, italic_keys)
    processed["value_font"] = get_font_name(
        base_font, bold_values, italic_values
    )

    return processed


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
    key_font: str,
    value_font: str,
    available_width: float,
    available_height: float,
    show_keys: bool,
    show_values: bool,
) -> float:
    """
    Calculate the largest font size that fits all text
    within available space using direct mathematical scaling.
    Handles different fonts for keys and values, and visibility options.
    """
    if not lines:
        return 12

    reference_font_size = REFERENCE_FONT_SIZE
    max_line_width = 0

    for line in lines:
        if ": " in line:
            key_part, value_part = line.split(": ", 1)
            line_width = 0

            if show_keys:
                line_width += canvas_obj.stringWidth(
                    key_part + ": ", key_font, reference_font_size
                )

            if show_values:
                line_width += canvas_obj.stringWidth(
                    value_part, value_font, reference_font_size
                )
        else:
            line_width = canvas_obj.stringWidth(
                line, key_font, reference_font_size
            )

        max_line_width = max(max_line_width, line_width)

    total_text_height = len(lines) * reference_font_size

    width_scale = (
        available_width / max_line_width
        if max_line_width > 0
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
    key_font: str,
    value_font: str,
    font_size: float,
    label_x_offset: float,
    label_y_offset: float,
    label_width_pt: float,
    label_height_pt: float,
    effective_width: float,
    effective_height: float,
    padding_x: float,
    padding_y: float,
    key_color: tuple[float, float, float],
    value_color: tuple[float, float, float],
    show_keys: bool,
    show_values: bool,
) -> None:
    """
    Draw text rotated 90 degrees clockwise with separate
    key/value fonts and colors.
    """
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
            if ": " in line:
                key_part, value_part = line.split(": ", 1)
                x_pos = text_start_x

                if show_keys:
                    canvas_obj.setFont(key_font, font_size)
                    canvas_obj.setFillColorRGB(*key_color)
                    canvas_obj.drawString(x_pos, y_position, key_part + ": ")
                    x_pos += canvas_obj.stringWidth(
                        key_part + ": ", key_font, font_size
                    )

                if show_values:
                    canvas_obj.setFont(value_font, font_size)
                    canvas_obj.setFillColorRGB(*value_color)
                    canvas_obj.drawString(x_pos, y_position, value_part)
            else:
                canvas_obj.setFont(key_font, font_size)
                canvas_obj.setFillColorRGB(*key_color)
                canvas_obj.drawString(text_start_x, y_position, line)
            y_position -= font_size

    canvas_obj.restoreState()


def draw_normal_text(
    canvas_obj: canvas.Canvas,
    lines: list[str],
    key_font: str,
    value_font: str,
    font_size: float,
    label_x_offset: float,
    label_y_offset: float,
    label_height_pt: float,
    padding_x: float,
    padding_y: float,
    key_color: tuple[float, float, float],
    value_color: tuple[float, float, float],
    show_keys: bool,
    show_values: bool,
) -> None:
    """
    Draw text in normal orientation with separate
    key/value fonts and colors.
    """
    text_start_x = label_x_offset + padding_x
    text_start_y = label_y_offset + label_height_pt - padding_y - font_size

    y_position = text_start_y
    for line in lines:
        if y_position >= label_y_offset + padding_y:
            if ": " in line:
                key_part, value_part = line.split(": ", 1)
                x_pos = text_start_x

                if show_keys:
                    canvas_obj.setFont(key_font, font_size)
                    canvas_obj.setFillColorRGB(*key_color)
                    canvas_obj.drawString(x_pos, y_position, key_part + ": ")
                    x_pos += canvas_obj.stringWidth(
                        key_part + ": ", key_font, font_size
                    )

                if show_values:
                    canvas_obj.setFont(value_font, font_size)
                    canvas_obj.setFillColorRGB(*value_color)
                    canvas_obj.drawString(x_pos, y_position, value_part)
            else:
                canvas_obj.setFont(key_font, font_size)
                canvas_obj.setFillColorRGB(*key_color)
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

    key_font = style.get("key_font", font_name)
    value_font = style.get("value_font", font_name)
    show_keys = style.get("show_keys", True)
    show_values = style.get("show_values", True)

    font_size = calculate_optimal_font_size(
        lines,
        c,
        key_font,
        value_font,
        available_width,
        available_height,
        show_keys,
        show_values,
    )

    key_color = (
        style.get("key_color_r", 0.0),
        style.get("key_color_g", 0.0),
        style.get("key_color_b", 0.0),
    )
    value_color = (
        style.get("value_color_r", 0.0),
        style.get("value_color_g", 0.0),
        style.get("value_color_b", 0.0),
    )

    if rotate_text:
        draw_rotated_text(
            c,
            lines,
            key_font,
            value_font,
            font_size,
            label_x_offset,
            label_y_offset,
            label_width_pt,
            label_height_pt,
            effective_width,
            effective_height,
            padding_x,
            padding_y,
            key_color,
            value_color,
            show_keys,
            show_values,
        )
    else:
        draw_normal_text(
            c,
            lines,
            key_font,
            value_font,
            font_size,
            label_x_offset,
            label_y_offset,
            label_height_pt,
            padding_x,
            padding_y,
            key_color,
            value_color,
            show_keys,
            show_values,
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


def get_style_config_ui() -> dict:
    """
    Render sidebar UI for comprehensive label styling options.

    Returns
    -------
    dict
        Complete style configuration dictionary.
    """
    with st.sidebar.expander("Label Styling", expanded=False):
        st.subheader("Dimensions")

        unit_system = st.radio(
            "Units",
            ["Imperial (inches)", "Metric (cm)"],
            horizontal=True,
            key="style_units",
        )

        is_metric = unit_system == "Metric (cm)"

        if is_metric:
            width_display = st.number_input(
                "Width (cm)",
                min_value=DIMENSION_MIN_CM,
                max_value=MAX_WIDTH_CM,
                value=DEFAULT_WIDTH_CM,
                step=DIMENSION_STEP_CM,
                key="style_width_cm",
            )
            height_display = st.number_input(
                "Height (cm)",
                min_value=DIMENSION_MIN_CM,
                max_value=MAX_HEIGHT_CM,
                value=DEFAULT_HEIGHT_CM,
                step=DIMENSION_STEP_CM,
                key="style_height_cm",
            )
            width_in = width_display * CM_TO_INCHES
            height_in = height_display * CM_TO_INCHES
        else:
            width_in = st.number_input(
                "Width (inches)",
                min_value=DIMENSION_MIN_IN,
                max_value=MAX_WIDTH_IN,
                value=DEFAULT_WIDTH_IN,
                step=DIMENSION_STEP_IN,
                key="style_width_in",
            )
            height_in = st.number_input(
                "Height (inches)",
                min_value=DIMENSION_MIN_IN,
                max_value=MAX_HEIGHT_IN,
                value=DEFAULT_HEIGHT_IN,
                step=DIMENSION_STEP_IN,
                key="style_height_in",
            )

        st.subheader("Layout")
        padding_percent = (
            st.slider(
                "Padding %",
                min_value=0,
                max_value=20,
                value=5,
                step=1,
                key="style_padding",
            )
            / 100.0
        )

        rotate_text = False
        if height_in > width_in:
            rotate_text = st.checkbox(
                "Rotate Label (For Better Fit)",
                value=False,
                key="style_rotate",
            )

        st.subheader("Typography")
        font_name = st.selectbox(
            "Font Family",
            ["Helvetica", "Times-Roman", "Courier"],
            index=0,
            key="style_font",
        )

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Keys**")
            bold_keys = st.checkbox("Bold", value=False, key="style_bold_keys")
            italic_keys = st.checkbox(
                "Italic", value=False, key="style_italic_keys"
            )
            show_keys = st.checkbox("Show", value=True, key="style_show_keys")

        with col2:
            st.write("**Values**")
            bold_values = st.checkbox(
                "Bold", value=False, key="style_bold_values"
            )
            italic_values = st.checkbox(
                "Italic", value=False, key="style_italic_values"
            )
            show_values = st.checkbox(
                "Show", value=True, key="style_show_values"
            )

        st.subheader("Colors")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Key Color**")
            key_color = st.color_picker(
                "Key Color", value="#000000", key="style_key_color"
            )
        with col2:
            st.write("**Value Color**")
            value_color = st.color_picker(
                "Value Color", value="#000000", key="style_value_color"
            )

        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip("#")
            return tuple(
                int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)
            )

        key_color_rgb = hex_to_rgb(key_color)
        value_color_rgb = hex_to_rgb(value_color)

    style_config = {
        "font_name": font_name,
        "padding_percent": padding_percent,
        "width_inches": width_in,
        "height_inches": height_in,
        "bold_keys": bold_keys,
        "bold_values": bold_values,
        "italic_keys": italic_keys,
        "italic_values": italic_values,
        "show_keys": show_keys,
        "show_values": show_values,
        "key_color_r": key_color_rgb[0],
        "key_color_g": key_color_rgb[1],
        "key_color_b": key_color_rgb[2],
        "value_color_r": value_color_rgb[0],
        "value_color_g": value_color_rgb[1],
        "value_color_b": value_color_rgb[2],
    }

    processed_style = apply_style_defaults(style_config)
    return processed_style, width_in, height_in, rotate_text


def get_dimensions_config() -> tuple[float, float, bool]:
    """
    Render sidebar UI to get label dimensions and rotation
    option. Legacy function for backward compatibility.

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
    uploaded_style_cfg = get_style_config()

    ui_style_cfg, width_in, height_in, rotate_text = get_style_config_ui()

    style_file_path = "label_styles/label_style_01.toml"
    file_style_cfg = load_label_style_from_file(style_file_path)

    final_style = {**file_style_cfg, **ui_style_cfg}
    if uploaded_style_cfg:
        final_style = {**final_style, **uploaded_style_cfg}

    display_preview_and_download(
        label_cfg, final_style, width_in, height_in, rotate_text
    )

    duration = time.time() - start
    logger.info(f"Session duration: {duration:.2f}s")


if __name__ == "__main__":
    main()
