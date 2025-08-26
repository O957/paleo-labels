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

try:
    from .autocomplete import initialize_autocomplete_engine, render_autocomplete_text_input, render_smart_suggestions_panel, show_autocomplete_stats
    from .batch import generate_batch_labels_ui
    from .collection_manager import collections_ui
    from .database_queries import advanced_database_queries_ui
    from .exports import exports_ui
    from .paleobiology import PaleobiologyDatabase
    from .relationships import LabelRelationshipManager
    from .schemas import (
        LABEL_SCHEMAS,
        format_field_name,
        get_all_fields,
        get_optional_fields,
        get_required_fields,
        get_schema_for_label_type,
        normalize_field_name,
        validate_label_data,
    )
    from .storage import LabelStorage
    from .templates import templates_ui
except ImportError:
    from autocomplete import initialize_autocomplete_engine, render_autocomplete_text_input, render_smart_suggestions_panel, show_autocomplete_stats
    from batch import generate_batch_labels_ui
    from collection_manager import collections_ui
    from database_queries import advanced_database_queries_ui
    from exports import exports_ui
    from paleobiology import PaleobiologyDatabase
    from relationships import LabelRelationshipManager
    from schemas import (
        LABEL_SCHEMAS,
        format_field_name,
        get_all_fields,
        get_optional_fields,
        get_required_fields,
        get_schema_for_label_type,
        normalize_field_name,
        validate_label_data,
    )
    from storage import LabelStorage
    from templates import templates_ui

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

PREVIEW_SCALE = 100
PREVIEW_LINE_HEIGHT = 1.4
PREVIEW_FONT_SIZE = 12


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
        return get_hardcoded_defaults()


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
        "Helvetica-Narrow": {
            (False, False): "Helvetica-Narrow",
            (True, False): "Helvetica-Narrow-Bold",
            (False, True): "Helvetica-Narrow-Oblique",
            (True, True): "Helvetica-Narrow-BoldOblique",
        },
        "AvantGarde-Book": {
            (False, False): "AvantGarde-Book",
            (True, False): "AvantGarde-Demi",
            (False, True): "AvantGarde-BookOblique",
            (True, True): "AvantGarde-DemiOblique",
        },
        "AvantGarde-Demi": {
            (False, False): "AvantGarde-Demi",
            (True, False): "AvantGarde-Demi",
            (False, True): "AvantGarde-DemiOblique",
            (True, True): "AvantGarde-DemiOblique",
        },
        "Bookman-Light": {
            (False, False): "Bookman-Light",
            (True, False): "Bookman-Demi",
            (False, True): "Bookman-LightItalic",
            (True, True): "Bookman-DemiItalic",
        },
        "Bookman-Demi": {
            (False, False): "Bookman-Demi",
            (True, False): "Bookman-Demi",
            (False, True): "Bookman-DemiItalic",
            (True, True): "Bookman-DemiItalic",
        },
        "NewCenturySchlbk-Roman": {
            (False, False): "NewCenturySchlbk-Roman",
            (True, False): "NewCenturySchlbk-Bold",
            (False, True): "NewCenturySchlbk-Italic",
            (True, True): "NewCenturySchlbk-BoldItalic",
        },
        "Palatino-Roman": {
            (False, False): "Palatino-Roman",
            (True, False): "Palatino-Bold",
            (False, True): "Palatino-Italic",
            (True, True): "Palatino-BoldItalic",
        },
        "Symbol": {
            (False, False): "Symbol",
            (True, False): "Symbol",
            (False, True): "Symbol",
            (True, True): "Symbol",
        },
        "ZapfDingbats": {
            (False, False): "ZapfDingbats",
            (True, False): "ZapfDingbats",
            (False, True): "ZapfDingbats",
            (True, True): "ZapfDingbats",
        },
    }

    if base_font in font_variants:
        return font_variants[base_font][(is_bold, is_italic)]
    else:
        return base_font


def get_hardcoded_defaults() -> dict:
    """
    Get hardcoded default values when no style file is available.
    """
    return {
        "font_name": "Helvetica",
        "font_size": REFERENCE_FONT_SIZE,
        "key_color_r": 0,
        "key_color_g": 0,
        "key_color_b": 0,
        "value_color_r": 0,
        "value_color_g": 0,
        "value_color_b": 0,
        "padding_percent": DEFAULT_PADDING_PERCENT,
        "width_inches": DEFAULT_WIDTH_IN,
        "height_inches": DEFAULT_HEIGHT_IN,
        "bold_keys": True,
        "bold_values": False,
        "italic_keys": False,
        "italic_values": False,
        "show_keys": True,
        "show_values": True,
    }


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
    defaults = get_hardcoded_defaults()
    processed = defaults.copy()

    if style_config:
        processed.update(style_config)

        for key in [
            "key_color_r",
            "key_color_g",
            "key_color_b",
            "value_color_r",
            "value_color_g",
            "value_color_b",
        ]:
            if key in processed and processed[key] > 1:
                processed[key] = processed[key] / 255.0

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

    # Use the user's selected font size instead of calculating optimal
    font_size = style.get("font_size", REFERENCE_FONT_SIZE)

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


def swap_rows(i: int, direction: int) -> None:
    """Swap row i with row i+direction."""
    target = i + direction
    if target >= 0 and target < st.session_state.num_rows:
        key_temp = st.session_state.get(f"key_{i}", "")
        value_temp = st.session_state.get(f"value_{i}", "")
        st.session_state[f"key_{i}"] = st.session_state.get(
            f"key_{target}", ""
        )
        st.session_state[f"value_{i}"] = st.session_state.get(
            f"value_{target}", ""
        )
        st.session_state[f"key_{target}"] = key_temp
        st.session_state[f"value_{target}"] = value_temp
        # Increment change counter to force UI updates
        st.session_state.manual_entry_version = (
            st.session_state.get("manual_entry_version", 0) + 1
        )


def render_row_controls(i: int) -> None:
    """Render up/down arrow controls for row i."""
    move_cols = st.columns(2)
    if move_cols[0].button("↑", key=f"up_{i}", help="Move up") and i > 0:
        swap_rows(i, -1)
    if (
        move_cols[1].button("↓", key=f"down_{i}", help="Move down")
        and i < st.session_state.num_rows - 1
    ):
        swap_rows(i, 1)


def render_manual_entry_row(i: int, label_type: str = "General") -> None:
    """Render a single manual entry row with field suggestions."""
    cols = st.columns([1, 4, 4])
    st.session_state.setdefault(f"key_{i}", "")
    st.session_state.setdefault(f"value_{i}", "")

    with cols[0]:
        render_row_controls(i)

    field_options = []
    if label_type != "General":
        schema = get_schema_for_label_type(label_type)
        required_fields = get_required_fields(label_type)
        optional_fields = get_optional_fields(label_type)

        field_options = required_fields + optional_fields
        for field, config in schema.items():
            field_options.extend(config.get("aliases", []))

    current_key = st.session_state[f"key_{i}"]

    version = st.session_state.get("manual_entry_version", 0)

    # Initialize auto-completion engine
    autocomplete_engine = initialize_autocomplete_engine()
    
    if field_options and current_key == "":
        k = cols[1].selectbox(
            f"Field {i + 1} Key",
            [""] + field_options,
            key=f"field_key_{i}_v{version}",
        )
    else:
        # Use auto-completion for key input
        if autocomplete_engine:
            with cols[1]:
                k = render_autocomplete_text_input(
                    f"Field {i + 1} Key",
                    value=current_key,
                    key=f"field_key_{i}_v{version}",
                    autocomplete_engine=autocomplete_engine,
                    field_type="key"
                )
        else:
            k = cols[1].text_input(
                f"Field {i + 1} Key",
                value=current_key,
                key=f"field_key_{i}_v{version}",
            )

    # Use auto-completion for value input
    if autocomplete_engine and k:
        with cols[2]:
            v = render_autocomplete_text_input(
                f"Field {i + 1} Value",
                value=st.session_state[f"value_{i}"],
                key=f"field_value_{i}_v{version}",
                autocomplete_engine=autocomplete_engine,
                field_type="value",
                related_key=k
            )
    else:
        v = cols[2].text_input(
            f"Field {i + 1} Value",
            value=st.session_state[f"value_{i}"],
            key=f"field_value_{i}_v{version}",
        )
    st.session_state[f"key_{i}"] = k
    st.session_state[f"value_{i}"] = v


def populate_manual_entry_from_upload(label_data: dict) -> None:
    """Populate manual entry session state with uploaded label data."""
    st.session_state.num_rows = len(label_data)

    for i, (key, value) in enumerate(label_data.items()):
        st.session_state[f"key_{i}"] = key
        st.session_state[f"value_{i}"] = (
            str(value) if value is not None else ""
        )

    st.session_state["manual_entry_initialized_General"] = True
    st.session_state["uploaded_data_populated"] = True

    for label_type in LABEL_SCHEMAS.keys():
        if (
            f"manual_entry_initialized_{label_type}" in st.session_state
            and label_type != "General"
        ):
            del st.session_state[f"manual_entry_initialized_{label_type}"]


def normalize_key(key: str) -> str:
    """Normalize a key by making it lowercase and joining with underscores."""
    return key.lower().replace(" ", "_").replace("-", "_")


def match_uploaded_keys_to_schema(
    uploaded_data: dict, label_type: str, filter_non_matching: bool = False
) -> dict:
    """Match uploaded keys to schema fields and their aliases."""
    if label_type == "General":
        return uploaded_data

    schema = get_schema_for_label_type(label_type)
    matched_data = {}

    # Create a mapping from normalized keys to schema fields
    key_mapping = {}
    for field_name, field_config in schema.items():
        # Add the main field name
        key_mapping[normalize_key(field_name)] = field_name
        # Add all aliases
        for alias in field_config.get("aliases", []):
            key_mapping[normalize_key(alias)] = field_name

    # Match uploaded keys
    for uploaded_key, value in uploaded_data.items():
        normalized_uploaded = normalize_key(uploaded_key)
        if normalized_uploaded in key_mapping:
            matched_field = key_mapping[normalized_uploaded]
            matched_data[matched_field] = value
        elif not filter_non_matching:
            # Keep unmatched keys as-is (only if not filtering)
            matched_data[uploaded_key] = value

    return matched_data


def populate_manual_entry_from_schema_match(
    label_data: dict, label_type: str
) -> None:
    """Populate manual entry with schema-matched data when label type changes."""
    # Filter out non-compliant rows when changing to a specific label type
    matched_data = match_uploaded_keys_to_schema(
        label_data, label_type, filter_non_matching=(label_type != "General")
    )

    # Clear out any existing rows beyond what we need
    if hasattr(st.session_state, "num_rows"):
        for i in range(len(matched_data), st.session_state.num_rows):
            if f"key_{i}" in st.session_state:
                del st.session_state[f"key_{i}"]
            if f"value_{i}" in st.session_state:
                del st.session_state[f"value_{i}"]

    st.session_state.num_rows = len(matched_data)

    for i, (key, value) in enumerate(matched_data.items()):
        st.session_state[f"key_{i}"] = key
        st.session_state[f"value_{i}"] = (
            str(value) if value is not None else ""
        )

    st.session_state[f"manual_entry_initialized_{label_type}"] = True


def get_label_source_config() -> tuple[dict, dict]:
    """Handle label source file uploads."""
    source = st.selectbox(
        "Upload Type",
        ["Upload Label File", "Upload Label Folder"],
        key="label_source_dropdown",
    )

    label_config: dict = {}
    combo_style_config: dict = {}

    if source == "Upload Label File":
        uploaded = st.file_uploader(
            "Upload Label TOML", type=["toml"], key="label_file"
        )
        if uploaded:
            label_config = load_toml(uploaded)
            if label_config:
                st.session_state.current_label_type = "General"
                populate_manual_entry_from_upload(label_config)
    else:
        st.info("Folder upload functionality coming soon!")

    uploaded_style = st.file_uploader(
        "Upload Label Style TOML", type=["toml"], key="style_file"
    )
    if uploaded_style:
        combo_style_config = load_toml(uploaded_style)

    return label_config, combo_style_config


def get_manual_entry_config(label_type: str = "General") -> dict:
    """Handle manual entry of label data with schema validation."""

    include_blank_lines = st.checkbox(
        "Include Blank Lines",
        value=False,
        help="Include rows with empty values in the output",
        key="include_blank_lines",
    )

    if f"manual_entry_initialized_{label_type}" not in st.session_state:
        if not (
            label_type == "General"
            and st.session_state.get("uploaded_data_populated")
        ):
            if label_type != "General":
                all_fields = get_all_fields(label_type)
                st.session_state.num_rows = len(all_fields)

                for i, field in enumerate(all_fields):
                    st.session_state[f"key_{i}"] = field
                    st.session_state[f"value_{i}"] = ""
            else:
                if "num_rows" not in st.session_state:
                    st.session_state.num_rows = 1
                    st.session_state["key_0"] = ""
                    st.session_state["value_0"] = ""

        st.session_state[f"manual_entry_initialized_{label_type}"] = True

    if label_type != "General":
        required_fields = get_required_fields(label_type)

        if required_fields:
            st.write("**Required fields must be filled:**")
            for field in required_fields:
                st.write(f"• {format_field_name(field)}")

    row_cols = st.columns(2)
    if row_cols[0].button("Add Row"):
        if "uploaded_data_populated" in st.session_state:
            del st.session_state["uploaded_data_populated"]
        st.session_state.num_rows += 1
        st.session_state[f"key_{st.session_state.num_rows - 1}"] = ""
        st.session_state[f"value_{st.session_state.num_rows - 1}"] = ""
    if row_cols[1].button("Remove Row") and st.session_state.num_rows > 1:
        if "uploaded_data_populated" in st.session_state:
            del st.session_state["uploaded_data_populated"]

        # Remove the last row and clean up any potential gaps
        last_row_idx = st.session_state.num_rows - 1
        if f"key_{last_row_idx}" in st.session_state:
            del st.session_state[f"key_{last_row_idx}"]
        if f"value_{last_row_idx}" in st.session_state:
            del st.session_state[f"value_{last_row_idx}"]
        st.session_state.num_rows -= 1
        # Increment change counter to force UI updates
        st.session_state.manual_entry_version = (
            st.session_state.get("manual_entry_version", 0) + 1
        )

    for i in range(st.session_state.num_rows):
        render_manual_entry_row(i, label_type)

    # Smart suggestions panel
    autocomplete_engine = initialize_autocomplete_engine()
    if autocomplete_engine:
        # Collect current data for smart suggestions
        current_data = {}
        for i in range(st.session_state.num_rows):
            k = st.session_state.get(f"key_{i}", "").strip()
            v = st.session_state.get(f"value_{i}", "").strip()
            if k and v:
                current_data[k] = v
        
        if current_data:
            with st.expander("🔮 Smart Suggestions", expanded=False):
                render_smart_suggestions_panel(current_data, label_type, autocomplete_engine)

    manual_config: dict = {}
    for i in range(st.session_state.num_rows):
        k = st.session_state.get(f"key_{i}", "").strip()
        v = st.session_state.get(f"value_{i}", "").strip()

        if k and (v or include_blank_lines):
            normalized_key = normalize_field_name(label_type, k)
            if normalized_key:
                manual_config[normalized_key] = v
            else:
                manual_config[k] = v

    if label_type != "General":
        validation_errors = validate_label_data(label_type, manual_config)
        if validation_errors["missing_required"]:
            missing_formatted = [
                format_field_name(f)
                for f in validation_errors["missing_required"]
            ]
            st.error(
                f"Missing required fields: {', '.join(missing_formatted)}"
            )
        if validation_errors["unknown_fields"]:
            st.warning(
                f"Unknown fields (will be included): {', '.join(validation_errors['unknown_fields'])}"
            )

    return manual_config


def get_label_config() -> tuple[dict, dict]:
    """
    Render sidebar UI to obtain label data either from
    a TOML upload or manual entry.

    Returns
    -------
    tuple[dict, dict]
        Tuple of (label config, combo style config).
    """
    st.sidebar.title("Options")

    with st.sidebar.expander("Label Source", expanded=True):
        label_config, combo_style_config = get_label_source_config()

    with st.sidebar.expander("Label Type", expanded=True):
        default_index = 0
        if (
            hasattr(st.session_state, "current_label_type")
            and st.session_state.current_label_type
        ):
            try:
                default_index = list(LABEL_SCHEMAS.keys()).index(
                    st.session_state.current_label_type
                )
            except ValueError:
                default_index = 0

        label_type = st.selectbox(
            "Select Label Type",
            list(LABEL_SCHEMAS.keys()),
            index=default_index,
            key="label_type_selection",
        )

        if st.session_state.get("current_label_type") != label_type:
            # Check if we have uploaded data to re-populate with schema matching
            if label_config and "uploaded_data_populated" in st.session_state:
                populate_manual_entry_from_schema_match(
                    label_config, label_type
                )
            elif "uploaded_data_populated" in st.session_state:
                del st.session_state["uploaded_data_populated"]

        st.session_state.current_label_type = label_type

        if label_type != "General":
            schema = get_schema_for_label_type(label_type)
            required_fields = get_required_fields(label_type)
            optional_fields = get_optional_fields(label_type)

            if required_fields:
                st.write("**Required Fields:**")
                for field in required_fields:
                    st.write(f"• {format_field_name(field)}")
            if optional_fields:
                st.write("**Optional Fields:**")
                for field in optional_fields[:5]:
                    st.write(f"• {format_field_name(field)}")
                if len(optional_fields) > 5:
                    st.write(f"... and {len(optional_fields) - 5} more")

    with st.sidebar.expander("Manual Entry", expanded=False):
        current_label_type = st.session_state.get(
            "current_label_type", "General"
        )
        manual_config = get_manual_entry_config(current_label_type)
        if manual_config:
            label_config.update(manual_config)

    return label_config, combo_style_config


def get_style_config_ui(
    uploaded_style: dict | None = None,
) -> tuple[dict, float, float, bool]:
    """
    Render sidebar UI for comprehensive label styling options.

    Parameters
    ----------
    uploaded_style : dict, optional
        Uploaded style configuration to use as defaults.

    Returns
    -------
    tuple[dict, float, float, bool]
        Tuple containing style configuration dictionary, width in inches,
        height in inches, and rotation flag.
    """
    with st.sidebar.expander("Manual Label Styling", expanded=False):
        if uploaded_style is None:
            uploaded_style = {}

        st.subheader("Dimensions")

        default_width_in = uploaded_style.get("width_inches", DEFAULT_WIDTH_IN)
        default_height_in = uploaded_style.get(
            "height_inches", DEFAULT_HEIGHT_IN
        )

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
                value=default_width_in * INCHES_TO_CM,
                step=DIMENSION_STEP_CM,
                key="style_width_cm",
            )
            height_display = st.number_input(
                "Height (cm)",
                min_value=DIMENSION_MIN_CM,
                max_value=MAX_HEIGHT_CM,
                value=default_height_in * INCHES_TO_CM,
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
                value=default_width_in,
                step=DIMENSION_STEP_IN,
                key="style_width_in",
            )
            height_in = st.number_input(
                "Height (inches)",
                min_value=DIMENSION_MIN_IN,
                max_value=MAX_HEIGHT_IN,
                value=default_height_in,
                step=DIMENSION_STEP_IN,
                key="style_height_in",
            )

        st.subheader("Layout")
        default_padding = int(
            uploaded_style.get("padding_percent", DEFAULT_PADDING_PERCENT)
            * 100
        )
        padding_percent = (
            st.slider(
                "Padding %",
                min_value=0,
                max_value=20,
                value=default_padding,
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
        default_font = uploaded_style.get("font_name", "Helvetica")
        font_options = [
            "Helvetica",
            "Times-Roman",
            "Courier",
            "Symbol",
            "ZapfDingbats",
            "Helvetica-Narrow",
            "AvantGarde-Book",
            "AvantGarde-Demi",
            "Bookman-Light",
            "Bookman-Demi",
            "NewCenturySchlbk-Roman",
            "Palatino-Roman",
        ]
        font_index = (
            font_options.index(default_font)
            if default_font in font_options
            else 0
        )

        col1, col2 = st.columns(2)
        with col1:
            font_name = st.selectbox(
                "Font Family",
                font_options,
                index=font_index,
                key="style_font",
            )

        with col2:
            default_font_size = uploaded_style.get(
                "font_size", REFERENCE_FONT_SIZE
            )
            font_size = st.slider(
                "Font Size",
                min_value=MIN_FONT_SIZE,
                max_value=min(MAX_FONT_SIZE, int(default_font_size * 1.5)),
                value=int(default_font_size),
                step=1,
                key="style_font_size",
                help="Adjust font size - usually smaller for fitting more text",
            )

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Keys**")
            bold_keys = st.checkbox(
                "Bold",
                value=uploaded_style.get("bold_keys", False),
                key="style_bold_keys",
            )
            italic_keys = st.checkbox(
                "Italic",
                value=uploaded_style.get("italic_keys", False),
                key="style_italic_keys",
            )
            show_keys = st.checkbox(
                "Show",
                value=uploaded_style.get("show_keys", True),
                key="style_show_keys",
            )

        with col2:
            st.write("**Values**")
            bold_values = st.checkbox(
                "Bold",
                value=uploaded_style.get("bold_values", False),
                key="style_bold_values",
            )
            italic_values = st.checkbox(
                "Italic",
                value=uploaded_style.get("italic_values", False),
                key="style_italic_values",
            )
            show_values = st.checkbox(
                "Show",
                value=uploaded_style.get("show_values", True),
                key="style_show_values",
            )

        def rgb_to_hex(r, g, b):
            return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

        def normalize_color_value(val):
            """Normalize color value to 0-1 range whether it comes as 0-1 or 0-255."""
            if val > 1:
                return val / 255.0
            return val

        default_key_color = rgb_to_hex(
            normalize_color_value(uploaded_style.get("key_color_r", 0)),
            normalize_color_value(uploaded_style.get("key_color_g", 0)),
            normalize_color_value(uploaded_style.get("key_color_b", 0)),
        )
        default_value_color = rgb_to_hex(
            normalize_color_value(uploaded_style.get("value_color_r", 0)),
            normalize_color_value(uploaded_style.get("value_color_g", 0)),
            normalize_color_value(uploaded_style.get("value_color_b", 0)),
        )

        st.subheader("Colors")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Key Color**")
            key_color = st.color_picker(
                "Key Color", value=default_key_color, key="style_key_color"
            )
        with col2:
            st.write("**Value Color**")
            value_color = st.color_picker(
                "Value Color",
                value=default_value_color,
                key="style_value_color",
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
        "font_size": font_size,
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


def extract_style_properties(style_config: dict) -> dict:
    """Extract and convert style properties from config."""
    font_mapping = {
        "Helvetica": "Arial, sans-serif",
        "Times-Roman": "Times, serif",
        "Courier": "Courier New, monospace",
    }

    font_name = style_config.get("font_name", "Helvetica")
    css_font = font_mapping.get(font_name, "Arial, sans-serif")

    # Convert RGB colors to CSS
    key_r = int(style_config.get("key_color_r", 0.0) * 255)
    key_g = int(style_config.get("key_color_g", 0.0) * 255)
    key_b = int(style_config.get("key_color_b", 0.0) * 255)
    key_color = f"rgb({key_r}, {key_g}, {key_b})"

    value_r = int(style_config.get("value_color_r", 0.0) * 255)
    value_g = int(style_config.get("value_color_g", 0.0) * 255)
    value_b = int(style_config.get("value_color_b", 0.0) * 255)
    value_color = f"rgb({value_r}, {value_g}, {value_b})"

    return {
        "css_font": css_font,
        "font_size": style_config.get("font_size", REFERENCE_FONT_SIZE),
        "padding_percent": style_config.get(
            "padding_percent", DEFAULT_PADDING_PERCENT
        ),
        "show_keys": style_config.get("show_keys", True),
        "show_values": style_config.get("show_values", True),
        "key_color": key_color,
        "value_color": value_color,
        "key_weight": "bold"
        if style_config.get("bold_keys", False)
        else "normal",
        "value_weight": "bold"
        if style_config.get("bold_values", False)
        else "normal",
        "key_style": "italic"
        if style_config.get("italic_keys", False)
        else "normal",
        "value_style": "italic"
        if style_config.get("italic_values", False)
        else "normal",
    }


def create_preview_lines(lines: list[str], style_props: dict) -> list[str]:
    """Create HTML spans for preview lines."""
    preview_lines = []
    for line in lines:
        if ": " in line and (
            style_props["show_keys"] or style_props["show_values"]
        ):
            key_part, value_part = line.split(": ", 1)
            parts = []
            if style_props["show_keys"]:
                key_span = (
                    f'<span style="color: {style_props["key_color"]}; '
                    f"font-weight: {style_props['key_weight']}; "
                    f"font-style: {style_props['key_style']}; "
                    f"font-size: {style_props.get('font_size', 12) * (PREVIEW_SCALE / POINTS_PER_INCH)}px; "
                    f'white-space: nowrap;">{key_part}: </span>'
                )
                parts.append(key_span)
            if style_props["show_values"]:
                value_span = (
                    f'<span style="color: {style_props["value_color"]}; '
                    f"font-weight: {style_props['value_weight']}; "
                    f"font-style: {style_props['value_style']}; "
                    f"font-size: {style_props.get('font_size', 12) * (PREVIEW_SCALE / POINTS_PER_INCH)}px; "
                    f'white-space: nowrap;">{value_part}</span>'
                )
                parts.append(value_span)
            preview_lines.append("".join(parts))
        else:
            line_span = (
                f'<span style="color: {style_props["key_color"]}; '
                f"font-weight: {style_props['key_weight']}; "
                f"font-style: {style_props['key_style']}; "
                f"font-size: {style_props.get('font_size', 12) * (PREVIEW_SCALE / POINTS_PER_INCH)}px;"
                f'">{line}</span>'
            )
            preview_lines.append(line_span)
    return preview_lines


def build_preview_html(
    preview_lines: list[str],
    width_in: float,
    height_in: float,
    rotate_text: bool,
    style_props: dict,
) -> str:
    """Build the complete preview HTML."""
    preview_width = width_in * PREVIEW_SCALE
    preview_height = height_in * PREVIEW_SCALE
    border_width = max(1, int(PREVIEW_SCALE / POINTS_PER_INCH))

    effective_width = preview_height if rotate_text else preview_width
    effective_height = preview_width if rotate_text else preview_height
    padding_x = effective_width * style_props["padding_percent"]
    padding_y = effective_height * style_props["padding_percent"]

    if rotate_text:
        transform_style = "transform: rotate(90deg); transform-origin: center;"
        preview_width, preview_height = preview_height, preview_width
    else:
        transform_style = ""

    preview_content = "<br>".join(preview_lines)

    outer_div_style = (
        f"border: {border_width}px solid #cccccc; "
        f"width: {preview_width}px; height: {preview_height}px; "
        f"margin: 20px auto; background-color: white; "
        f"position: relative; overflow: hidden; box-sizing: border-box; "
        f"{transform_style}"
    )

    inner_div_style = (
        f"position: absolute; top: {padding_y}px; left: {padding_x}px; "
        f"width: {effective_width - 2 * padding_x}px; "
        f"height: {effective_height - 2 * padding_y}px; "
        f"font-family: {style_props['css_font']}; "
        f"font-size: {style_props['font_size'] * (PREVIEW_SCALE / POINTS_PER_INCH)}px; "
        f"line-height: {PREVIEW_LINE_HEIGHT};"
    )

    rotation_text = "(rotated)" if rotate_text else ""
    preview_info = (
        f'Preview (scaled): {width_in:.2f}" × {height_in:.2f}" {rotation_text}'
    )

    return f"""<div style="{outer_div_style}">
    <div style="{inner_div_style}">{preview_content}</div>
</div>
<p style="text-align: center; color: #666; font-size: 12px;
   margin-top: 10px;">{preview_info}</p>"""


def show_database_list(list_type: str) -> None:
    """Display scrollable lists of database content."""
    st.subheader(f"Database {list_type.title()}")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back to Preview", key="back_to_preview"):
            if "show_preview_list" in st.session_state:
                del st.session_state.show_preview_list
            st.rerun()

    with col2:
        st.write(f"Showing all {list_type} from paleobiology database:")

    paleodb = st.session_state.paleodb

    if list_type == "species":
        items = paleodb.get_species_list()
        st.write(f"Found {len(items):,} species")
    elif list_type == "genera":
        items = paleodb.get_genus_list()
        st.write(f"Found {len(items):,} genera")
    elif list_type == "families":
        items = paleodb.get_family_list()
        st.write(f"Found {len(items):,} families")
    elif list_type == "orders":
        items = paleodb.get_order_list()
        st.write(f"Found {len(items):,} orders")
    elif list_type == "classes":
        items = paleodb.get_class_list()
        st.write(f"Found {len(items):,} classes")
    elif list_type == "phyla":
        items = paleodb.get_phylum_list()
        st.write(f"Found {len(items):,} phyla")
    elif list_type == "localities":
        items = paleodb.get_locality_list()
        st.write(f"Found {len(items):,} localities")
    else:
        st.error(f"Unknown list type: {list_type}")
        return

    if items:
        search_term = st.text_input(
            f"Search {list_type}:", key=f"search_{list_type}"
        )

        if search_term:
            filtered_items = [
                item for item in items if search_term.lower() in item.lower()
            ]
            st.write(
                f"Showing {len(filtered_items):,} results for '{search_term}'"
            )
        else:
            filtered_items = items

        display_items = (
            filtered_items[:1000]
            if len(filtered_items) > 1000
            else filtered_items
        )
        if len(filtered_items) > 1000:
            st.warning(
                f"Showing first 1,000 of {len(filtered_items):,} results. Use search to narrow down."
            )

        st.text_area(
            f"{list_type.title()} List",
            "\n".join(display_items),
            height=400,
            key=f"{list_type}_list_display",
        )
    else:
        st.warning(f"No {list_type} found in database.")


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
    # Mode selector
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Label Maker")
    with col2:
        app_mode = st.selectbox(
            "Mode:",
            ["Single Label", "Batch Processing", "Templates", "Advanced Export", "Collections", "Database Queries"],
            key="app_mode_selector"
        )
    
    # Handle different modes
    if app_mode == "Batch Processing":
        generate_batch_labels_ui()
        return
    elif app_mode == "Templates":
        templates_ui()
        return
    elif app_mode == "Advanced Export":
        exports_ui()
        return
    elif app_mode == "Collections":
        collections_ui()
        return
    elif app_mode == "Database Queries":
        advanced_database_queries_ui()
        return
    
    # Original single label logic
    if st.session_state.get("show_preview_list"):
        show_database_list(st.session_state.show_preview_list)
    elif label_config:
        st.subheader("Preview")

        lines = [f"{key}: {value}" for key, value in label_config.items()]
        style_props = extract_style_properties(style_config)
        preview_lines = create_preview_lines(lines, style_props)
        preview_html = build_preview_html(
            preview_lines, width_in, height_in, rotate_text, style_props
        )

        st.markdown(preview_html, unsafe_allow_html=True)

        pdf_bytes = generate_label_pdf(
            label_config,
            style_config,
            round(width_in, DIMENSION_DECIMAL_PLACES),
            round(height_in, DIMENSION_DECIMAL_PLACES),
            rotate_text,
        )
        if not st.session_state.get("show_preview_list"):
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

    if "storage" not in st.session_state:
        st.session_state.storage = LabelStorage()

    if "paleodb" not in st.session_state:
        st.session_state.paleodb = PaleobiologyDatabase()

    if "relationships" not in st.session_state:
        st.session_state.relationships = LabelRelationshipManager(
            st.session_state.storage
        )

    label_cfg, combo_style_cfg = get_label_config()

    default_style_paths = [
        "label_styles/default_style.toml",
        "label_styles/label_style_01.toml",
    ]

    file_style_cfg = {}
    for path in default_style_paths:
        if pathlib.Path(path).exists():
            file_style_cfg = load_label_style_from_file(path)
            break

    merged_uploaded_style = {**file_style_cfg}
    if combo_style_cfg:
        merged_uploaded_style = {**merged_uploaded_style, **combo_style_cfg}

    ui_style_cfg, width_in, height_in, rotate_text = get_style_config_ui(
        merged_uploaded_style
    )

    final_style = {**file_style_cfg}
    if combo_style_cfg:
        final_style = {**final_style, **combo_style_cfg}
    final_style = {**final_style, **ui_style_cfg}

    # Auto-completion stats
    autocomplete_engine = initialize_autocomplete_engine()
    if autocomplete_engine:
        with st.sidebar.expander("🤖 Auto-Complete Stats", expanded=False):
            show_autocomplete_stats(autocomplete_engine)
    
    if st.session_state.paleodb.is_available():
        with st.sidebar.expander("Database Info", expanded=False):
            stats = st.session_state.paleodb.get_database_stats()
            if stats:
                if st.button(
                    f"Species: {stats.get('unique_species', 0):,}",
                    key="show_species",
                ):
                    st.session_state.show_preview_list = "species"
                if st.button(
                    f"Genera: {stats.get('unique_genera', 0):,}",
                    key="show_genera",
                ):
                    st.session_state.show_preview_list = "genera"
                if st.button(
                    f"Families: {stats.get('unique_families', 0):,}",
                    key="show_families",
                ):
                    st.session_state.show_preview_list = "families"
                if st.button(
                    f"Orders: {stats.get('unique_orders', 0):,}",
                    key="show_orders",
                ):
                    st.session_state.show_preview_list = "orders"
                if st.button(
                    f"Classes: {stats.get('unique_classes', 0):,}",
                    key="show_classes",
                ):
                    st.session_state.show_preview_list = "classes"
                if st.button(
                    f"Phyla: {stats.get('unique_phyla', 0):,}",
                    key="show_phyla",
                ):
                    st.session_state.show_preview_list = "phyla"
                if st.button(
                    f"Localities: {stats.get('unique_localities', 0):,}",
                    key="show_localities",
                ):
                    st.session_state.show_preview_list = "localities"

    display_preview_and_download(
        label_cfg, final_style, width_in, height_in, rotate_text
    )

    if label_cfg and st.session_state.get("current_label_type"):
        with st.sidebar.expander("Save Label", expanded=False):
            label_name = st.text_input(
                "Label Name (optional)", key="save_label_name"
            )
            if st.button("Save Current Label"):
                saved_name = st.session_state.storage.save_label(
                    label_cfg,
                    st.session_state.current_label_type,
                    label_name if label_name else None,
                )
                st.success(f"Label saved as: {saved_name}")

        with st.sidebar.expander("Archive", expanded=False):
            saved_labels = st.session_state.storage.list_labels()
            if saved_labels:
                selected_label = st.selectbox(
                    "Load Saved Label", [""] + saved_labels
                )
                if selected_label and st.button("Load Label"):
                    loaded_data = st.session_state.storage.load_label(
                        selected_label
                    )
                    if loaded_data:
                        st.rerun()

    duration = time.time() - start
    logger.info(f"Session duration: {duration:.2f}s")


if __name__ == "__main__":
    main()
