"""
Paleo-Labels: A Python package for writing and formatting
labels for geological, paleontological, and biological
specimens and related items, such localities and
expeditions.
"""

import json
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

import requests
import streamlit as st
import tomli
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# initialize storage paths
LABELS_DIR = Path.home() / ".paleo_labels" / "labels"
LABELS_DIR.mkdir(parents=True, exist_ok=True)

# style configuration paths
STYLE_DIR = Path(__file__).parent.parent / "templates"

# phase 1: unified measurement system - everything in points (1/72 inch)
POINTS_PER_INCH = 72
INCHES_TO_CM = 2.54
CM_TO_INCHES = 1 / INCHES_TO_CM
POINTS_PER_CM = POINTS_PER_INCH * CM_TO_INCHES


# measurement conversion functions
def inches_to_points(inches: float) -> float:
    """Convert inches to points (1/72 inch).

    Parameters
    ----------
    inches : float
        Value in inches to convert.

    Returns
    -------
    float
        Value converted to points.
    """
    return inches * POINTS_PER_INCH


def cm_to_points(cm: float) -> float:
    """Convert centimeters to points.

    Parameters
    ----------
    cm : float
        Value in centimeters to convert.

    Returns
    -------
    float
        Value converted to points.
    """
    return cm * POINTS_PER_CM


def points_to_inches(points: float) -> float:
    """Convert points to inches.

    Parameters
    ----------
    points : float
        Value in points to convert.

    Returns
    -------
    float
        Value converted to inches.
    """
    return points / POINTS_PER_INCH


def points_to_cm(points: float) -> float:
    """Convert points to centimeters.

    Parameters
    ----------
    points : float
        Value in points to convert.

    Returns
    -------
    float
        Value converted to centimeters.
    """
    return points / POINTS_PER_CM


def points_to_pixels(points: float, dpi: float = 96) -> float:
    """Convert points to pixels for HTML preview.

    Parameters
    ----------
    points : float
        Value in points to convert.
    dpi : float
        Dots per inch for conversion (default 96).

    Returns
    -------
    float
        Value converted to pixels.
    """
    return points * dpi / POINTS_PER_INCH


# default dimensions in points
DEFAULT_WIDTH_POINTS = inches_to_points(2.625)
DEFAULT_HEIGHT_POINTS = inches_to_points(1.0)
DEFAULT_FONT_SIZE_POINTS = 10
DEFAULT_PADDING_POINTS = 3.6  # 0.05 inches in points
DEFAULT_LINE_HEIGHT_RATIO = 1.2


def get_font_name(
    base_font: str, is_bold: bool = False, is_italic: bool = False
) -> str:
    """Get the correct font name based on style parameters.

    Parameters
    ----------
    base_font : str
        Base font name (e.g., 'Helvetica', 'Times-Roman', 'Courier').
    is_bold : bool
        Whether the font should be bold (default False).
    is_italic : bool
        Whether the font should be italic (default False).

    Returns
    -------
    str
        Font name with appropriate style variant.
    """
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


def _get_hardcoded_defaults() -> dict:
    """Return hardcoded default style configuration.

    Parameters
    ----------
    None

    Returns
    -------
    dict
        Dictionary containing default style configuration values.
    """
    return {
        "font_name": "Courier",
        "font_size": 10,
        "key_color_r": 0,
        "key_color_g": 0,
        "key_color_b": 0,
        "value_color_r": 0,
        "value_color_g": 0,
        "value_color_b": 0,
        "padding_percent": 0.05,
        "border_thickness": 1.5,
        "label_spacing": 0.125,
        "width_inches": 3.25,
        "height_inches": 2.25,
        "bold_keys": True,
        "bold_values": False,
        "italic_keys": False,
        "italic_values": False,
        "show_keys": True,
        "show_values": True,
    }


def _convert_font_name_to_reportlab(font_name: str) -> str:
    """Convert font name to ReportLab format.

    Parameters
    ----------
    font_name : str
        Font name to convert.

    Returns
    -------
    str
        Font name in ReportLab format.
    """
    if "Times" in font_name:
        return "Times-Roman"
    elif "Helvetica" in font_name or "Arial" in font_name:
        return "Helvetica"
    elif "Courier" in font_name:
        return "Courier"
    else:
        return "Courier"


def _process_toml_typography(style_config: dict, toml_data: dict) -> None:
    """Process typography section from TOML data.

    Parameters
    ----------
    style_config : dict
        Style configuration dictionary to update.
    toml_data : dict
        TOML data containing typography information.

    Returns
    -------
    None
    """
    if "typography" in toml_data:
        style_config.update(toml_data["typography"])
        font_name = toml_data["typography"].get("font_name", "Times New Roman")
        style_config["font_name"] = _convert_font_name_to_reportlab(font_name)


def _process_toml_colors(style_config: dict, toml_data: dict) -> None:
    """Process colors section from TOML data, normalizing to 0-1 range.

    Parameters
    ----------
    style_config : dict
        Style configuration dictionary to update.
    toml_data : dict
        TOML data containing color information.

    Returns
    -------
    None
    """
    if "colors" in toml_data:
        colors = toml_data["colors"]
        color_keys = [
            "key_color_r",
            "key_color_g",
            "key_color_b",
            "value_color_r",
            "value_color_g",
            "value_color_b",
        ]
        for color_key in color_keys:
            if color_key in colors:
                value = colors[color_key]
                style_config[color_key] = value / 255.0 if value > 1 else value


def load_default_style() -> dict:
    """Load default style from default_style.toml file.

    Parameters
    ----------
    None

    Returns
    -------
    dict
        Style configuration dictionary loaded from TOML file.
    """
    default_style_path = STYLE_DIR / "default_style.toml"

    if not default_style_path.exists():
        return _get_hardcoded_defaults()

    try:
        with open(default_style_path, "rb") as f:
            toml_data = tomli.load(f)

        style_config = {}

        # process each section
        if "dimensions" in toml_data:
            style_config.update(toml_data["dimensions"])

        _process_toml_typography(style_config, toml_data)
        _process_toml_colors(style_config, toml_data)

        if "style" in toml_data:
            style_config.update(toml_data["style"])

        return style_config

    except Exception as e:
        print(f"Error loading default style: {e}")
        return _get_hardcoded_defaults()


def get_hardcoded_defaults() -> dict:
    """Get default values - now loads from TOML file.

    Parameters
    ----------
    None

    Returns
    -------
    dict
        Default style configuration values.
    """
    return load_default_style()


def apply_style_defaults(style_config: dict) -> dict:
    """Apply default values to style configuration and handle font styling.

    Parameters
    ----------
    style_config : dict
        Style configuration dictionary to process.

    Returns
    -------
    dict
        Processed style configuration with defaults applied.
    """
    defaults = load_default_style()
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


def calculate_underline_length(
    key_part: str, available_width_points: float, font_size_points: float
) -> int:
    """Calculate number of underscores that fit within available width.

    Parameters
    ----------
    key_part : str
        The key text before the underline.
    available_width_points : float
        Available width in points.
    font_size_points : float
        Font size in points.

    Returns
    -------
    int
        Number of underscore characters to use.
    """
    # character width estimate in points
    # (more accurate for points-based system)
    char_width_points = font_size_points * 0.6

    # calculate how many characters can fit in available width
    max_chars_in_width = round(available_width_points / char_width_points)

    # calculate target position (95% of available character space)
    target_char_position = round(max_chars_in_width * 0.95)

    # calculate underlines needed to reach target position
    key_and_colon_length = len(key_part + ": ")
    underscore_count = max(1, target_char_position - key_and_colon_length)

    # ensure we don't exceed the maximum width
    max_underscores = max_chars_in_width - key_and_colon_length
    return min(underscore_count, max_underscores, 100)


def wrap_text_to_width(
    text: str,
    width_points: float,
    font_size: float,
    font_name: str = "Courier",
) -> list[str]:
    """Wrap text to fit within specified width.

    Parameters
    ----------
    text : str
        Text to wrap.
    width_points : float
        Available width in points.
    font_size : float
        Font size in points.
    font_name : str
        Font name for width calculations.

    Returns
    -------
    list[str]
        List of wrapped text lines.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        test_width = stringWidth(test_line, font_name, font_size)

        if test_width <= width_points:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # word is too long, add it anyway
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else [""]


def _get_label_dimensions(
    width_inches: float, height_inches: float, style_config: dict
) -> dict:
    """Calculate label dimensions and parameters.

    Parameters
    ----------
    width_inches : float
        Label width in inches.
    height_inches : float
        Label height in inches.
    style_config : dict
        Style configuration dictionary.

    Returns
    -------
    dict
        Dictionary with calculated dimensions.
    """
    width_points = inches_to_points(width_inches)
    height_points = inches_to_points(height_inches)

    # calculate padding in points
    padding_points = style_config.get("padding_percent", 0.05) * min(
        width_points, height_points
    )

    # available text area in points
    text_width_points = width_points - (2 * padding_points)
    text_height_points = height_points - (2 * padding_points)

    # font configuration
    font_size_points = style_config.get("font_size", DEFAULT_FONT_SIZE_POINTS)
    line_height_points = font_size_points * DEFAULT_LINE_HEIGHT_RATIO

    return {
        "width_points": width_points,
        "height_points": height_points,
        "padding_points": padding_points,
        "text_width_points": text_width_points,
        "text_height_points": text_height_points,
        "font_size_points": font_size_points,
        "line_height_points": line_height_points,
    }


def calculate_optimal_font_size(
    lines: list[str],
    font_size_points: float,
    width_points: float,
    height_points: float,
    font_name: str = "Courier",
) -> float:
    """Calculate optimal font size to fit content within dimensions.

    Parameters
    ----------
    lines : list[str]
        List of text lines to fit.
    font_size_points : float
        Default/maximum font size in points.
    width_points : float
        Available width in points.
    height_points : float
        Available height in points.
    font_name : str
        Font name for width calculations.

    Returns
    -------
    float
        Optimal font size in points.
    """
    if not lines:
        return font_size_points

    from reportlab.pdfbase.pdfmetrics import stringWidth

    # start with the default font size
    test_size = font_size_points
    min_size = 6.0  # minimum readable font size

    # find the maximum width needed among all lines
    max_line_width = 0
    for line in lines:
        line_width = stringWidth(line, font_name, test_size)
        max_line_width = max(max_line_width, line_width)

    # calculate size based on width constraint
    if max_line_width > width_points:
        test_size = (width_points / max_line_width) * test_size

    # calculate size based on height constraint
    line_height = test_size * DEFAULT_LINE_HEIGHT_RATIO
    total_height_needed = len(lines) * line_height

    if total_height_needed > height_points:
        test_size = (height_points / total_height_needed) * test_size

    # ensure minimum readable size
    test_size = max(test_size, min_size)

    # ensure we don't exceed the original font size
    return min(test_size, font_size_points)


def process_label_data(
    label_data: dict, style_config: dict, dimensions: dict
) -> list[str]:
    """Process label data into lines with underlines for empty values.

    Parameters
    ----------
    label_data : dict
        Dictionary of label key-value pairs.
    style_config : dict
        Style configuration dictionary.
    dimensions : dict
        Dictionary with label dimensions.

    Returns
    -------
    list[str]
        List of formatted label lines.
    """
    # check if this is a blank label
    if "__blank_label__" in label_data:
        text = label_data["__blank_label__"]
        font_name = style_config.get("font_name", "Courier")

        # first try with default font size
        initial_lines = wrap_text_to_width(
            text,
            dimensions["text_width_points"],
            dimensions["font_size_points"],
            font_name,
        )

        # calculate optimal font size for these lines
        optimal_size = calculate_optimal_font_size(
            initial_lines,
            dimensions["font_size_points"],
            dimensions["text_width_points"],
            dimensions["text_height_points"],
            font_name,
        )

        # rewrap with optimal font size if it changed
        if abs(optimal_size - dimensions["font_size_points"]) > 0.1:
            return wrap_text_to_width(
                text, dimensions["text_width_points"], optimal_size, font_name
            )
        return initial_lines

    lines = []

    # handle colon alignment if enabled
    align_colons = style_config.get("align_colons", False)
    processed_entries = {}

    if align_colons:
        max_field_length = (
            max(len(key) for key in label_data if key) if label_data else 0
        )
        for key, value in label_data.items():
            if key:
                spaces_needed = max_field_length - len(key)
                padded_key = key + (" " * spaces_needed)
                processed_entries[padded_key] = value
            else:
                processed_entries[key] = value
    else:
        processed_entries = label_data

    # create lines with underlines for empty values
    for key, value in processed_entries.items():
        if not value or not value.strip():
            underline_count = calculate_underline_length(
                key,
                dimensions["text_width_points"],
                dimensions["font_size_points"],
            )
            underlines = "_" * underline_count
            lines.append(f"{key}: {underlines}")
        else:
            lines.append(f"{key}: {value}")

    return lines


def render_to_html_preview(
    label_data: dict,
    width_inches: float,
    height_inches: float,
    style_config: dict,
    preview_dpi: float = 96,
) -> str:
    """Render label to HTML preview with exact dimensions.

    Parameters
    ----------
    label_data : dict
        Dictionary of label key-value pairs.
    width_inches : float
        Label width in inches.
    height_inches : float
        Label height in inches.
    style_config : dict
        Style configuration dictionary.
    preview_dpi : float
        DPI for preview rendering (default 96).

    Returns
    -------
    str
        HTML string for label preview.
    """
    dimensions = _get_label_dimensions(
        width_inches, height_inches, style_config
    )
    lines = process_label_data(label_data, style_config, dimensions)
    optimal_font_size = calculate_optimal_font_size(
        lines,
        dimensions["font_size_points"],
        dimensions["text_width_points"],
        dimensions["text_height_points"],
        style_config.get("font_name", "Courier"),
    )

    # convert points to pixels for html
    preview_width_px = points_to_pixels(
        dimensions["width_points"], preview_dpi
    )
    preview_height_px = points_to_pixels(
        dimensions["height_points"], preview_dpi
    )
    padding_px = points_to_pixels(dimensions["padding_points"], preview_dpi)
    font_size_px = points_to_pixels(optimal_font_size, preview_dpi)

    # build html with precise dimensions
    lines_html = []
    is_blank_label = "__blank_label__" in label_data

    for line in lines:
        if is_blank_label:
            # for blank labels, use value style for all text
            value_style = _get_html_text_style(
                "value", font_size_px, style_config
            )
            line_html = f'<span style="{value_style}">{line}</span>'
        elif ": " in line:
            key_part, value_part = line.split(": ", 1)
            key_style = _get_html_text_style("key", font_size_px, style_config)
            value_style = _get_html_text_style(
                "value", font_size_px, style_config
            )
            line_html = (
                f'<span style="{key_style}">{key_part}: </span>'
                f'<span style="{value_style}">{value_part}</span>'
            )
        else:
            key_style = _get_html_text_style("key", font_size_px, style_config)
            line_html = f'<span style="{key_style}">{line}</span>'
        lines_html.append(line_html)

    # calculate line height to match pdf
    line_height_px = points_to_pixels(
        optimal_font_size * DEFAULT_LINE_HEIGHT_RATIO, preview_dpi
    )

    # position lines individually to match pdf positioning
    positioned_lines = []
    for i, line_html in enumerate(lines_html):
        top_position = i * line_height_px
        positioned_line = (
            f'<div style="position: absolute; '
            f"top: {top_position}px; left: 0; width: 100%; "
            f"margin: 0; padding: 0; "
            f'line-height: {line_height_px}px;">'
            f"{line_html}</div>"
        )
        positioned_lines.append(positioned_line)

    content_html = "".join(positioned_lines)
    text_align = "center" if style_config.get("center_text", False) else "left"

    # convert border thickness from points to pixels for preview
    border_thickness_px = points_to_pixels(
        style_config.get("border_thickness", 1.5), preview_dpi
    )
    outer_style = (
        f"border: {border_thickness_px}px solid #cccccc; "
        f"width: {preview_width_px}px; height: {preview_height_px}px; "
        f"margin: 20px auto; background-color: white; "
        f"position: relative; box-sizing: border-box;"
    )

    inner_style = (
        f"position: absolute; "
        f"top: {padding_px}px; left: {padding_px}px; "
        f"width: {preview_width_px - 2 * padding_px}px; "
        f"height: {preview_height_px - 2 * padding_px}px; "
        f"text-align: {text_align}; position: relative; "
        f"margin: 0; padding: 0; box-sizing: border-box;"
    )

    width_in = points_to_inches(dimensions["width_points"])
    height_in = points_to_inches(dimensions["height_points"])
    width_cm = points_to_cm(dimensions["width_points"])
    height_cm = points_to_cm(dimensions["height_points"])
    dimensions_info = (
        f'Exact size: {width_in:.3f}" × {height_in:.3f}" '
        f"({width_cm:.2f}cm × {height_cm:.2f}cm)"
    )

    return f'''<div style="{outer_style}">
    <div style="{inner_style}">{content_html}</div>
</div>
<p style="text-align: center; color: #666; font-size: 12px; "
   "margin-top: 10px;">{dimensions_info}</p>'''


def _get_html_text_style(
    text_type: str, font_size_px: float, style_config: dict
) -> str:
    """Get HTML text styling for key or value text.

    Parameters
    ----------
    text_type : str
        Type of text ('key' or 'value').
    font_size_px : float
        Font size in pixels.
    style_config : dict
        Style configuration dictionary.

    Returns
    -------
    str
        CSS style string.
    """
    font_mapping = {
        "Helvetica": "Arial, sans-serif",
        "Times-Roman": "Times, serif",
        "Courier": "Courier New, monospace",
    }

    font_name = style_config.get("font_name", "Courier")
    css_font = font_mapping.get(font_name, "Times, serif")

    if text_type == "key":
        color_r = int(style_config.get("key_color_r", 0.0) * 255)
        color_g = int(style_config.get("key_color_g", 0.0) * 255)
        color_b = int(style_config.get("key_color_b", 0.0) * 255)
        weight = "bold" if style_config.get("bold_keys", True) else "normal"
        style = (
            "italic" if style_config.get("italic_keys", False) else "normal"
        )
    else:  # value
        color_r = int(style_config.get("value_color_r", 0.0) * 255)
        color_g = int(style_config.get("value_color_g", 0.0) * 255)
        color_b = int(style_config.get("value_color_b", 0.0) * 255)
        weight = "bold" if style_config.get("bold_values", False) else "normal"
        style = (
            "italic" if style_config.get("italic_values", False) else "normal"
        )

    color = f"rgb({color_r}, {color_g}, {color_b})"

    line_height_px = font_size_px * DEFAULT_LINE_HEIGHT_RATIO

    return (
        f"font-family: {css_font}; "
        f"font-size: {font_size_px}px; "
        f"line-height: {line_height_px}px; "
        f"color: {color}; "
        f"font-weight: {weight}; "
        f"font-style: {style}; "
        f"margin: 0; padding: 0; vertical-align: baseline;"
    )


def render_to_pdf_canvas(
    canvas_obj,
    label_data: dict,
    x_offset: float,
    y_offset: float,
    width_inches: float,
    height_inches: float,
    style_config: dict,
) -> None:
    """Render label to PDF canvas at specified position.

    Parameters
    ----------
    canvas_obj : reportlab.pdfgen.canvas.Canvas
        ReportLab canvas object.
    label_data : dict
        Dictionary of label key-value pairs.
    x_offset : float
        X position in points.
    y_offset : float
        Y position in points.
    width_inches : float
        Label width in inches.
    height_inches : float
        Label height in inches.
    style_config : dict
        Style configuration dictionary.

    Returns
    -------
    None
    """
    dimensions = _get_label_dimensions(
        width_inches, height_inches, style_config
    )
    lines = process_label_data(label_data, style_config, dimensions)
    optimal_font_size = calculate_optimal_font_size(
        lines,
        dimensions["font_size_points"],
        dimensions["text_width_points"],
        dimensions["text_height_points"],
        style_config.get("font_name", "Courier"),
    )

    # draw border
    canvas_obj.setStrokeColor(colors.black)
    border_thickness = style_config.get("border_thickness", 1.5)
    canvas_obj.setLineWidth(border_thickness)
    canvas_obj.rect(
        x_offset,
        y_offset,
        dimensions["width_points"],
        dimensions["height_points"],
    )

    # get fonts
    base_font = style_config.get("font_name", "Courier")
    key_font = get_font_name(
        base_font,
        style_config.get("bold_keys", True),
        style_config.get("italic_keys", False),
    )
    value_font = get_font_name(
        base_font,
        style_config.get("bold_values", False),
        style_config.get("italic_values", False),
    )

    # get colors
    key_color = (
        style_config.get("key_color_r", 0.0),
        style_config.get("key_color_g", 0.0),
        style_config.get("key_color_b", 0.0),
    )
    value_color = (
        style_config.get("value_color_r", 0.0),
        style_config.get("value_color_g", 0.0),
        style_config.get("value_color_b", 0.0),
    )

    # check if this is a blank label
    is_blank_label = "__blank_label__" in label_data

    # draw text
    text_y = (
        y_offset
        + dimensions["height_points"]
        - dimensions["padding_points"]
        - optimal_font_size
    )

    for line in lines:
        if text_y < y_offset + dimensions["padding_points"]:
            break

        if is_blank_label:
            # for blank labels, use value font and color for all text
            canvas_obj.setFont(value_font, optimal_font_size)
            canvas_obj.setFillColorRGB(*value_color)

            line_width = canvas_obj.stringWidth(
                line, value_font, optimal_font_size
            )
            if style_config.get("center_text", False):
                text_x = (
                    x_offset + (dimensions["width_points"] - line_width) / 2
                )
            else:
                text_x = x_offset + dimensions["padding_points"]

            canvas_obj.drawString(text_x, text_y, line)
        elif ": " in line:
            key_part, value_part = line.split(": ", 1)

            # calculate line width for centering
            key_text = f"{key_part}: "
            key_width = canvas_obj.stringWidth(
                key_text, key_font, optimal_font_size
            )
            value_width = canvas_obj.stringWidth(
                value_part, value_font, optimal_font_size
            )
            total_width = key_width + value_width

            # set x position (centered or left-aligned)
            if style_config.get("center_text", False):
                text_x = (
                    x_offset + (dimensions["width_points"] - total_width) / 2
                )
            else:
                text_x = x_offset + dimensions["padding_points"]

            # draw key
            canvas_obj.setFont(key_font, optimal_font_size)
            canvas_obj.setFillColorRGB(*key_color)
            canvas_obj.drawString(text_x, text_y, key_text)

            # draw value
            canvas_obj.setFont(value_font, optimal_font_size)
            canvas_obj.setFillColorRGB(*value_color)
            canvas_obj.drawString(text_x + key_width, text_y, value_part)
        else:
            # single line (no colon)
            canvas_obj.setFont(key_font, optimal_font_size)
            canvas_obj.setFillColorRGB(*key_color)

            line_width = canvas_obj.stringWidth(
                line, key_font, optimal_font_size
            )
            if style_config.get("center_text", False):
                text_x = (
                    x_offset + (dimensions["width_points"] - line_width) / 2
                )
            else:
                text_x = x_offset + dimensions["padding_points"]

            canvas_obj.drawString(text_x, text_y, line)

        text_y -= optimal_font_size * DEFAULT_LINE_HEIGHT_RATIO


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple.

    Parameters
    ----------
    hex_color : str
        Hex color string (e.g., '#FF0000').

    Returns
    -------
    tuple[int, int, int]
        RGB values as integers (0-255).
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def convert_key_name(underscore_key: str) -> str:
    """Convert underscore_key to 'Proper Key Name' format.

    Parameters
    ----------
    underscore_key : str
        Key with underscores (e.g., 'field_name').

    Returns
    -------
    str
        Formatted key with spaces and title case.
    """
    return underscore_key.replace("_", " ").title()


def load_label_types() -> dict:
    """Load label types from TOML files in templates directory.

    Parameters
    ----------
    None

    Returns
    -------
    dict
        Dictionary of label types with their fields and descriptions.
    """
    label_types = {}

    if STYLE_DIR.exists():
        for toml_file in STYLE_DIR.glob("*.toml"):
            if any(
                style_word in toml_file.name.lower()
                for style_word in ["style", "default"]
            ):
                continue

            try:
                with open(toml_file, "rb") as f:
                    toml_data = tomli.load(f)

                if "label_type" in toml_data and "fields" in toml_data:
                    label_type_name = toml_data["label_type"]["name"]
                    field_keys = list(toml_data["fields"].keys())
                    proper_field_names = [
                        convert_key_name(key) for key in field_keys
                    ]

                    label_types[label_type_name] = {
                        "fields": proper_field_names,
                        "raw_keys": field_keys,
                        "description": toml_data["label_type"].get(
                            "description", ""
                        ),
                    }

            except Exception as e:
                print(f"Error loading label type from {toml_file}: {e}")
                continue

    return label_types


def get_existing_labels() -> list[dict]:
    """Get list of existing saved labels.

    Parameters
    ----------
    None

    Returns
    -------
    list[dict]
        List of dictionaries containing label names and data.
    """
    labels = []
    for label_file in LABELS_DIR.glob("*.json"):
        try:
            with open(label_file) as f:
                data = json.load(f)
                labels.append({"name": label_file.stem, "data": data})
        except Exception as e:
            continue
    return labels


def get_previous_values(key: str) -> list[str]:
    """Get previous values used for a specific key.

    Parameters
    ----------
    key : str
        Field key to get previous values for.

    Returns
    -------
    list[str]
        Sorted list of unique previous values for the key.
    """
    values = set()
    for label in get_existing_labels():
        if key.lower() in [k.lower() for k in label["data"]]:
            for k, v in label["data"].items():
                if k.lower() == key.lower() and v.strip():
                    values.add(v.strip())
    return sorted(list(values))


def get_pbdb_suggestions(partial_value: str) -> list[str]:
    """Get PBDB suggestions for taxonomic fields.

    Parameters
    ----------
    partial_value : str
        Partial text to search for in PBDB.

    Returns
    -------
    list[str]
        List of suggested taxonomic names from PBDB.
    """
    if not partial_value or len(partial_value) < 2:
        return []

    try:
        url = "https://paleobiodb.org/data1.2/taxa/auto.json"
        params = {"taxon_name": partial_value, "limit": 10}
        response = requests.get(url, params=params, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if "records" in data:
                return [
                    record["nam"]
                    for record in data["records"]
                    if "nam" in record
                ]
    except Exception as e:
        pass
    return []


def get_scientific_name_suggestions(partial_value: str) -> list[str]:
    """
    Get combined suggestions for Scientific Name from
    existing labels and PBDB.

    Parameters
    ----------
    partial_value : str
        Partial scientific name to search for.

    Returns
    -------
    list[str]
        Sorted list of suggested scientific names.
    """
    suggestions = set()

    for label in get_existing_labels():
        for key, value in label["data"].items():
            if (
                "scientific" in key.lower()
                and value.strip()
                and (
                    not partial_value or partial_value.lower() in value.lower()
                )
            ):
                suggestions.add(value.strip())

    if partial_value and len(partial_value) >= 2:
        pbdb_suggestions = get_pbdb_suggestions(partial_value)
        suggestions.update(pbdb_suggestions)

    return sorted(list(suggestions))


def _process_nested_dimensions(
    converted_style: dict, style_data: dict, default_style: dict
) -> None:
    """Process dimensions section from nested TOML format.

    Parameters
    ----------
    converted_style : dict
        Style dictionary to update with dimensions.
    style_data : dict
        TOML data containing style information.
    default_style : dict
        Default style values to use as fallback.

    Returns
    -------
    None
    """
    if "dimensions" in style_data:
        converted_style.update(
            {
                "width_inches": style_data["dimensions"].get(
                    "width_inches", default_style["width_inches"]
                ),
                "height_inches": style_data["dimensions"].get(
                    "height_inches", default_style["height_inches"]
                ),
                "padding_percent": style_data["dimensions"].get(
                    "padding_percent", default_style["padding_percent"]
                ),
            }
        )


def _process_nested_typography(
    converted_style: dict, style_data: dict, default_style: dict
) -> None:
    """Process typography section from nested TOML format.

    Parameters
    ----------
    converted_style : dict
        Style dictionary to update with typography.
    style_data : dict
        TOML data containing style information.
    default_style : dict
        Default style values to use as fallback.

    Returns
    -------
    None
    """
    if "typography" in style_data:
        converted_style.update(
            {
                "font_name": style_data["typography"].get(
                    "font_name", default_style["font_name"]
                ),
                "font_size": style_data["typography"].get(
                    "font_size", default_style["font_size"]
                ),
            }
        )


def _process_nested_colors(converted_style: dict, style_data: dict) -> None:
    """Process colors section from nested TOML format.

    Parameters
    ----------
    converted_style : dict
        Style dictionary to update with colors.
    style_data : dict
        TOML data containing color information.

    Returns
    -------
    None
    """
    if "colors" in style_data:
        colors_data = style_data["colors"]

        # process key colors
        if all(
            k in colors_data
            for k in ["key_color_r", "key_color_g", "key_color_b"]
        ):
            key_r = int(colors_data["key_color_r"])
            key_g = int(colors_data["key_color_g"])
            key_b = int(colors_data["key_color_b"])
            converted_style["key_color"] = (
                f"#{key_r:02x}{key_g:02x}{key_b:02x}"
            )

        # process value colors
        if all(
            k in colors_data
            for k in ["value_color_r", "value_color_g", "value_color_b"]
        ):
            val_r = int(colors_data["value_color_r"])
            val_g = int(colors_data["value_color_g"])
            val_b = int(colors_data["value_color_b"])
            converted_style["value_color"] = (
                f"#{val_r:02x}{val_g:02x}{val_b:02x}"
            )


def _process_nested_style_options(
    converted_style: dict, style_data: dict, default_style: dict
) -> None:
    """Process style section from nested TOML format.

    Parameters
    ----------
    converted_style : dict
        Style dictionary to update with style options.
    style_data : dict
        TOML data containing style information.
    default_style : dict
        Default style values to use as fallback.

    Returns
    -------
    None
    """
    if "style" in style_data:
        converted_style.update(
            {
                "bold_keys": style_data["style"].get(
                    "bold_keys", default_style["bold_keys"]
                ),
                "bold_values": style_data["style"].get(
                    "bold_values", default_style["bold_values"]
                ),
                "italic_keys": style_data["style"].get(
                    "italic_keys", default_style["italic_keys"]
                ),
                "italic_values": style_data["style"].get(
                    "italic_values", default_style["italic_values"]
                ),
                "show_keys": style_data["style"].get(
                    "show_keys", default_style["show_keys"]
                ),
                "show_values": style_data["style"].get(
                    "show_values", default_style["show_values"]
                ),
            }
        )


def _process_flat_format(converted_style: dict, style_data: dict) -> None:
    """Process flat format TOML data.

    Parameters
    ----------
    converted_style : dict
        Style dictionary to update.
    style_data : dict
        TOML data in flat format.

    Returns
    -------
    None
    """
    flat_keys = [
        "font_name",
        "font_size",
        "width_inches",
        "height_inches",
        "padding_percent",
        "bold_keys",
        "bold_values",
        "italic_keys",
        "italic_values",
        "center_text",
        "show_border",
    ]
    for key in flat_keys:
        if key in style_data:
            converted_style[key] = style_data[key]


def _normalize_color_component(value: float) -> int:
    """Normalize color component to 0-255 range.

    Parameters
    ----------
    value : float
        Color component value (0-1 or 0-255).

    Returns
    -------
    int
        Normalized color value (0-255).
    """
    return int(value * 255) if value <= 1 else int(value)


def _process_flat_colors(converted_style: dict, style_data: dict) -> None:
    """Process flat color format from TOML data.

    Parameters
    ----------
    converted_style : dict
        Style dictionary to update with colors.
    style_data : dict
        TOML data containing color information.

    Returns
    -------
    None
    """
    # process key colors
    if all(
        k in style_data for k in ["key_color_r", "key_color_g", "key_color_b"]
    ):
        key_r = _normalize_color_component(style_data["key_color_r"])
        key_g = _normalize_color_component(style_data["key_color_g"])
        key_b = _normalize_color_component(style_data["key_color_b"])
        converted_style["key_color"] = f"#{key_r:02x}{key_g:02x}{key_b:02x}"

    # process value colors
    if all(
        k in style_data
        for k in ["value_color_r", "value_color_g", "value_color_b"]
    ):
        val_r = _normalize_color_component(style_data["value_color_r"])
        val_g = _normalize_color_component(style_data["value_color_g"])
        val_b = _normalize_color_component(style_data["value_color_b"])
        converted_style["value_color"] = f"#{val_r:02x}{val_g:02x}{val_b:02x}"


def _convert_style_data(style_data: dict, default_style: dict) -> dict:
    """Convert TOML style data to internal format.

    Parameters
    ----------
    style_data : dict
        Raw TOML style data.
    default_style : dict
        Default style values to use as fallback.

    Returns
    -------
    dict
        Converted style configuration.
    """
    converted_style = default_style.copy()

    # process nested format sections
    _process_nested_dimensions(converted_style, style_data, default_style)
    _process_nested_typography(converted_style, style_data, default_style)
    _process_nested_colors(converted_style, style_data)
    _process_nested_style_options(converted_style, style_data, default_style)

    # process flat format
    _process_flat_format(converted_style, style_data)
    _process_flat_colors(converted_style, style_data)

    return converted_style


def load_style_files() -> dict:
    """Load available style files.

    Returns
    -------
    dict
        Dictionary of available styles keyed by name.
    """
    default_style = load_default_style()
    styles = {"Default Style": default_style}

    if not STYLE_DIR.exists():
        return styles

    for style_file in STYLE_DIR.glob("*.toml"):
        if "style" not in style_file.name.lower():
            continue

        try:
            with open(style_file, "rb") as f:
                style_data = tomli.load(f)

            converted_style = _convert_style_data(style_data, default_style)
            styles[style_file.stem.replace("_", " ").title()] = converted_style

        except Exception as e:
            print(f"Error loading style {style_file}: {e}")
            continue

    return styles


def _get_key_options(current_key: str) -> list[str]:
    """Get available key options from existing labels.

    Parameters
    ----------
    current_key : str
        Current key value to include in options.

    Returns
    -------
    list[str]
        List of available key options.
    """
    all_keys = set()
    for label in get_existing_labels():
        all_keys.update(label["data"].keys())

    key_options = ["New", "Empty"] + sorted(list(all_keys))

    if current_key and current_key not in key_options:
        key_options.append(current_key)

    return key_options


def _render_key_input(index: int, current_key: str) -> str:
    """Render the key input widget.

    Parameters
    ----------
    index : int
        Index of the field in the form.
    current_key : str
        Current key value.

    Returns
    -------
    str
        Selected or entered key value.
    """
    key_options = _get_key_options(current_key)

    selected_key = st.selectbox(
        f"Field {index + 1}:",
        key_options,
        index=key_options.index(current_key)
        if current_key in key_options
        else 0,
        key=f"key_select_{index}",
    )

    if selected_key == "New":
        return st.text_input(
            "Enter new field:",
            value=current_key if current_key != "New" else "",
            key=f"key_new_{index}",
        )
    elif selected_key == "Empty":
        return ""
    else:
        return selected_key


def _render_scientific_name_input(
    index: int, value_label: str, current_value: str
) -> str:
    """Render scientific name input with suggestions.

    Parameters
    ----------
    index : int
        Index of the field in the form.
    value_label : str
        Label for the value input.
    current_value : str
        Current value.

    Returns
    -------
    str
        Selected or entered value.
    """
    typed_value = st.text_input(
        value_label + ":",
        value=current_value,
        key=f"value_text_{index}",
        help="Type to search existing labels and paleobiology database",
    )

    if typed_value and len(typed_value) >= 2:
        suggestions = get_scientific_name_suggestions(typed_value)
        if suggestions:
            st.write("**Suggestions:**")
            for i, suggestion in enumerate(suggestions[:5]):
                if st.button(
                    f"🔍 {suggestion}",
                    key=f"suggestion_{index}_{i}",
                ):
                    st.session_state.manual_entries[index]["value"] = (
                        suggestion
                    )
                    st.rerun()

    return typed_value


def _render_standard_value_input(
    index: int, actual_key: str, value_label: str, current_value: str
) -> str:
    """Render standard value input with previous values.

    Parameters
    ----------
    index : int
        Index of the field in the form.
    actual_key : str
        Key for getting previous values.
    value_label : str
        Label for the value input.
    current_value : str
        Current value.

    Returns
    -------
    str
        Selected or entered value.
    """
    value_options = ["New", "Empty"]
    prev_values = get_previous_values(actual_key)
    value_options.extend(prev_values)

    if current_value and current_value not in value_options:
        value_options.append(current_value)

    selected_value = st.selectbox(
        value_label + ":",
        value_options,
        index=value_options.index(current_value)
        if current_value in value_options
        else 0,
        key=f"value_select_{index}",
    )

    if selected_value == "New":
        return st.text_input(
            "Enter new value:",
            value=current_value if current_value != "New" else "",
            key=f"value_new_{index}",
        )
    elif selected_value == "Empty":
        return ""
    else:
        return selected_value


def _is_scientific_name_field(key: str) -> bool:
    """Check if a field is for scientific names.

    Parameters
    ----------
    key : str
        Field key to check.

    Returns
    -------
    bool
        True if field is for scientific names.
    """
    return "scientific" in key.lower() and "name" in key.lower()


def render_key_value_input(
    index: int, current_key: str = "", current_value: str = ""
) -> tuple[str, str]:
    """Render a key-value input pair with smart suggestions.

    Parameters
    ----------
    index : int
        Index of the field in the form.
    current_key : str
        Current key value (default "").
    current_value : str
        Current value (default "").

    Returns
    -------
    tuple[str, str]
        Tuple of (key, value) entered by user.
    """
    col1, col2 = st.columns(2)

    with col1:
        actual_key = _render_key_input(index, current_key)

    with col2:
        if actual_key:
            value_label = f"Value {index + 1} ({actual_key})"

            if _is_scientific_name_field(actual_key):
                actual_value = _render_scientific_name_input(
                    index, value_label, current_value
                )
            else:
                actual_value = _render_standard_value_input(
                    index, actual_key, value_label, current_value
                )
        else:
            actual_value = ""

    return actual_key, actual_value


def hex_to_rgb_components(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color to separate r,g,b components (0-1 range).

    Parameters
    ----------
    hex_color : str
        Hex color string (e.g., '#FF0000').

    Returns
    -------
    tuple[float, float, float]
        RGB values as floats (0-1 range).
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return (r / 255.0, g / 255.0, b / 255.0)
    return (0.0, 0.0, 0.0)


def convert_to_original_style_format(style_config: dict) -> dict:
    """Convert hex-based style to RGB format.

    Parameters
    ----------
    style_config : dict
        Style configuration with hex colors.

    Returns
    -------
    dict
        Style configuration with RGB color components.
    """
    # convert hex colors to rgb components
    key_r, key_g, key_b = hex_to_rgb_components(
        style_config.get("key_color", "#000000")
    )
    value_r, value_g, value_b = hex_to_rgb_components(
        style_config.get("value_color", "#000000")
    )

    return {
        "font_name": style_config.get("font_name", "Courier"),
        "font_size": style_config.get("font_size", 10),
        "width_inches": style_config.get("width_inches", 2.625),
        "height_inches": style_config.get("height_inches", 1.0),
        "padding_percent": style_config.get("padding_percent", 0.05),
        "bold_keys": style_config.get("bold_keys", True),
        "bold_values": style_config.get("bold_values", False),
        "italic_keys": style_config.get("italic_keys", False),
        "italic_values": style_config.get("italic_values", False),
        "show_keys": style_config.get("show_keys", True),
        "show_values": style_config.get("show_values", True),
        "center_text": style_config.get("center_text", False),
        "show_border": style_config.get("show_border", True),
        "key_color_r": key_r,
        "key_color_g": key_g,
        "key_color_b": key_b,
        "value_color_r": value_r,
        "value_color_g": value_g,
        "value_color_b": value_b,
    }


def create_pdf_from_labels(
    labels_data: list[dict], style_config: dict | None = None
) -> bytes:
    """Create PDF from labels data using label rendering functions.

    Parameters
    ----------
    labels_data : list[dict]
        List of label data dictionaries.
    style_config : dict
        Style configuration (default None, uses default style).

    Returns
    -------
    bytes
        PDF file content as bytes.
    """
    if style_config is None:
        style_config = load_default_style()

    # get dimensions from style config
    width_inches = style_config.get("width_inches", 2.625)
    height_inches = style_config.get("height_inches", 1.0)

    # get dimensions for layout calculations
    dimensions = _get_label_dimensions(
        width_inches, height_inches, style_config
    )

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # calculate layout in points for precise positioning
    margin_points = inches_to_points(0.1875)
    page_width_points = inches_to_points(8.5)  # US Letter width
    page_height_points = inches_to_points(11)  # US Letter height

    # calculate how many labels can actually fit based on size and spacing
    label_spacing_points = inches_to_points(
        style_config.get("label_spacing", 0.125)
    )
    usable_width = page_width_points - (2 * margin_points)
    usable_height = page_height_points - (2 * margin_points)

    # include spacing in calculations
    label_width_with_spacing = (
        dimensions["width_points"] + label_spacing_points
    )
    label_height_with_spacing = (
        dimensions["height_points"] + label_spacing_points
    )

    labels_per_row = int(usable_width // label_width_with_spacing)
    labels_per_col = int(usable_height // label_height_with_spacing)

    # ensure we don't exceed standard layout
    labels_per_row = min(labels_per_row, 3)
    labels_per_col = min(labels_per_col, 10)

    for current_label, label_data in enumerate(labels_data):
        if (
            current_label > 0
            and current_label % (labels_per_row * labels_per_col) == 0
        ):
            c.showPage()

        row = (
            current_label % (labels_per_row * labels_per_col)
        ) // labels_per_row
        col = current_label % labels_per_row

        # calculate exact position in points with spacing
        x = margin_points + col * label_width_with_spacing
        y = (
            page_height_points
            - margin_points
            - dimensions["height_points"]
            - row * label_height_with_spacing
        )

        # use rendering function for precise dimensions
        render_to_pdf_canvas(
            c, label_data, x, y, width_inches, height_inches, style_config
        )

    c.save()
    return buffer.getvalue()


def _initialize_session_state() -> None:
    """Initialize Streamlit session state variables.

    Returns
    -------
    None
    """
    if "current_labels" not in st.session_state:
        st.session_state.current_labels = []
    if "manual_entries" not in st.session_state:
        st.session_state.manual_entries = [{"key": "", "value": ""}]
    if "current_style" not in st.session_state:
        st.session_state.current_style = load_default_style()
    if "loaded_label_types" not in st.session_state:
        st.session_state.loaded_label_types = load_label_types()


def fill_with_ui() -> None:
    """Render the 'Fill With' section of the UI.

    Returns
    -------
    None
    """
    st.subheader("Fill With")
    col1, col2 = st.columns(2)

    with col1:
        fill_option = st.selectbox(
            "Fill with:",
            ["None", "Label Type", "Existing Label", "Upload Label TOML"],
        )

        if fill_option == "Label Type":
            available_types = list(st.session_state.loaded_label_types.keys())
            if available_types:
                selected_type = st.selectbox(
                    "Select Label Type:", available_types
                )

                if selected_type:
                    description = st.session_state.loaded_label_types[
                        selected_type
                    ].get("description", "")
                    if description:
                        st.write(f"*{description}*")

                if st.button("Load Label Type Fields"):
                    field_names = st.session_state.loaded_label_types[
                        selected_type
                    ]["fields"]
                    st.session_state.manual_entries = [
                        {"key": key, "value": ""} for key in field_names
                    ]
                    st.rerun()
            else:
                st.info(
                    "No label types found. Please check the "
                    "templates directory."
                )

        elif fill_option == "Existing Label":
            existing_labels = get_existing_labels()
            if existing_labels:
                label_names = [label["name"] for label in existing_labels]
                selected_label = st.selectbox(
                    "Select Existing Label:", label_names
                )
                if st.button("Load Existing Label"):
                    selected_data = next(
                        label["data"]
                        for label in existing_labels
                        if label["name"] == selected_label
                    )
                    st.session_state.manual_entries = [
                        {"key": k, "value": v}
                        for k, v in selected_data.items()
                    ]
                    st.rerun()
            else:
                st.info("No existing labels found")

        elif fill_option == "Upload Label TOML":
            uploaded_label = st.file_uploader(
                "Upload Label TOML:", type=["toml"], key="upload_label_toml"
            )
            if (
                uploaded_label
                and uploaded_label.name
                not in st.session_state.get("processed_files", set())
            ):
                try:
                    label_content = uploaded_label.read().decode("utf-8")
                    label_data = tomli.loads(label_content)

                    if "fields" in label_data:
                        entries = []
                        for key, value in label_data["fields"].items():
                            proper_key = convert_key_name(key)
                            entries.append(
                                {
                                    "key": proper_key,
                                    "value": str(value) if value else "",
                                }
                            )
                        st.session_state.manual_entries = entries
                    else:
                        entries = []
                        for key, value in label_data.items():
                            if not key.startswith("_") and key not in [
                                "label_type"
                            ]:
                                entries.append(
                                    {
                                        "key": key,
                                        "value": str(value) if value else "",
                                    }
                                )
                        st.session_state.manual_entries = entries

                    # track processed files to prevent infinite loops
                    if "processed_files" not in st.session_state:
                        st.session_state.processed_files = set()
                    st.session_state.processed_files.add(uploaded_label.name)

                    st.success(
                        f"Loaded {len(st.session_state.manual_entries)} "
                        "fields from TOML!"
                    )
                except Exception as e:
                    st.error(f"Error loading TOML: {e}")


def manual_entry_ui() -> None:
    """Render the manual entry section of the UI.

    Returns
    -------
    None
    """
    st.subheader("Manual Entry")

    # render current entries
    for i, entry in enumerate(st.session_state.manual_entries):
        key, value = render_key_value_input(i, entry["key"], entry["value"])
        st.session_state.manual_entries[i] = {"key": key, "value": value}

    # add/remove entry buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Field", key="add_field_btn"):
            st.session_state.manual_entries.append({"key": "", "value": ""})
            st.rerun()

    with col2:
        if len(st.session_state.manual_entries) > 1 and st.button(
            "➖ Remove Last Field", key="remove_field_btn"
        ):
            st.session_state.manual_entries.pop()
            st.rerun()


def blank_label_ui() -> None:
    """Render the blank label section of the UI.

    Returns
    -------
    None
    """
    st.subheader("Blank Text Label")
    st.markdown(
        "Create a blank label with custom text that wraps within the border."
    )

    # text area for entering custom text
    text = st.text_area(
        "Enter your text:",
        height=100,
        help="Enter text that will wrap automatically within the label border.",
        key="blank_text_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Blank Label", key="add_blank_label_btn"):
            if text and text.strip():
                # add blank label with special marker
                st.session_state.current_labels.append(
                    {"__blank_label__": text.strip()}
                )
                # clear the text area by deleting its key from session state
                if "blank_text_input" in st.session_state:
                    del st.session_state["blank_text_input"]
                st.success("Blank label added!")
                st.rerun()
            else:
                st.warning("Please enter some text for the label.")

    with col2:
        if st.button("🔄 Clear Text", key="clear_blank_text_btn"):
            # clear the text area by deleting its key from session state
            if "blank_text_input" in st.session_state:
                del st.session_state["blank_text_input"]
            st.rerun()


def style_options_ui() -> None:
    """Render the style options section of the UI.

    Returns
    -------
    None
    """
    st.subheader("Style Options")

    # get defaults from toml
    defaults = load_default_style()

    # style widgets with proper default values
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.write("**Dimensions**")
        width_inches = st.number_input(
            "Width (in):",
            min_value=0.5,
            max_value=8.0,
            value=defaults.get("width_inches", 2.625),
            step=0.05,
            key="style_width_in",
        )
        height_inches = st.number_input(
            "Height (in):",
            min_value=0.5,
            max_value=6.0,
            value=defaults.get("height_inches", 1.0),
            step=0.05,
            key="style_height_in",
        )

    with col2:
        st.write("**Typography**")
        font_name = st.selectbox(
            "Font:",
            ["Courier", "Helvetica", "Times-Roman"],
            index=0,
            key="style_font",
        )
        font_size = st.slider(
            "Font Size:",
            6,
            20,
            value=int(defaults.get("font_size", 10)),
            key="style_font_size",
        )

    with col3:
        st.write("**Colors**")
        key_color = st.color_picker(
            "Field Color:", value="#000000", key="style_key_color"
        )
        value_color = st.color_picker(
            "Value Color:", value="#000000", key="style_value_color"
        )

    with col4:
        st.write("**Formatting**")
        bold_keys = st.checkbox(
            "Bold Fields", value=True, key="style_bold_keys"
        )
        bold_values = st.checkbox(
            "Bold Values", value=False, key="style_bold_values"
        )
        italic_keys = st.checkbox(
            "Italic Fields", value=False, key="style_italic_keys"
        )
        italic_values = st.checkbox(
            "Italic Values", value=False, key="style_italic_values"
        )
        center_text = st.checkbox(
            "Center Text", value=False, key="style_center_text"
        )
        align_colons = st.checkbox(
            "Align Colons",
            value=False,
            key="align_colons",
            help="Add spaces to align all colons vertically",
        )
        padding_percent = st.slider(
            "Padding %:", 0.01, 0.2, value=0.05, step=0.01, key="style_padding"
        )
        border_thickness = st.slider(
            "Border Thickness:",
            0.25,
            3.0,
            value=1.5,
            step=0.25,
            key="style_border_thickness",
            help="Border thickness in points",
        )
        label_spacing = st.slider(
            "Label Spacing:",
            0.0,
            0.5,
            value=0.125,
            step=0.025,
            key="style_label_spacing",
            help="Space between labels in inches",
        )


def _build_style_config() -> dict:
    """Build style configuration from current widget values.

    Returns
    -------
    dict
        Complete style configuration dictionary.
    """
    # get dimensions from widgets
    if st.session_state.get("style_units") == "Metric":
        width_in = st.session_state.get("style_width_cm", 6.7) / INCHES_TO_CM
        height_in = st.session_state.get("style_height_cm", 2.5) / INCHES_TO_CM
    else:
        width_in = st.session_state.get("style_width_in", 2.625)
        height_in = st.session_state.get("style_height_in", 1.0)

    # get color values
    key_color_hex = st.session_state.get("style_key_color", "#000000")
    value_color_hex = st.session_state.get("style_value_color", "#000000")
    key_r, key_g, key_b = hex_to_rgb(key_color_hex)
    value_r, value_g, value_b = hex_to_rgb(value_color_hex)

    return {
        "font_name": st.session_state.get("style_font", "Courier"),
        "font_size": st.session_state.get("style_font_size", 10),
        "width_inches": width_in,
        "height_inches": height_in,
        "padding_percent": st.session_state.get("style_padding", 0.05),
        "border_thickness": st.session_state.get(
            "style_border_thickness", 1.5
        ),
        "label_spacing": st.session_state.get("style_label_spacing", 0.125),
        "key_color_r": key_r / 255.0,
        "key_color_g": key_g / 255.0,
        "key_color_b": key_b / 255.0,
        "value_color_r": value_r / 255.0,
        "value_color_g": value_g / 255.0,
        "value_color_b": value_b / 255.0,
        "bold_keys": st.session_state.get("style_bold_keys", True),
        "bold_values": st.session_state.get("style_bold_values", False),
        "italic_keys": st.session_state.get("style_italic_keys", False),
        "italic_values": st.session_state.get("style_italic_values", False),
        "center_text": st.session_state.get("style_center_text", False),
        "show_keys": st.session_state.get("style_show_keys", True),
        "show_values": True,
    }


def preview_ui() -> None:
    """Render the current label preview section.

    Returns
    -------
    None
    """
    # show preview for current manual entry
    if any(
        entry["key"] or entry["value"]
        for entry in st.session_state.manual_entries
    ):
        st.subheader("Current Label Preview")
        current_label = {
            entry["key"]: entry["value"]
            for entry in st.session_state.manual_entries
            if entry["key"] or entry["value"]
        }

        style_config = _build_style_config()

        # display current dimensions
        width_in = style_config.get("width_inches", 2.625)
        height_in = style_config.get("height_inches", 1.0)
        width_cm = width_in * INCHES_TO_CM
        height_cm = height_in * INCHES_TO_CM

        st.write(
            f'**Label Size**: {width_in:.3f}" × {height_in:.3f}" '
            f"({width_cm:.1f}cm × {height_cm:.1f}cm)"
        )

        # use rendering function for precise preview with exact dimensions
        preview_html = render_to_html_preview(
            current_label, width_in, height_in, style_config
        )
        st.markdown(preview_html, unsafe_allow_html=True)

    # show previews for session labels including blank labels
    if st.session_state.current_labels:
        st.subheader("Session Labels Preview")

        style_config = _build_style_config()
        width_in = style_config.get("width_inches", 2.625)
        height_in = style_config.get("height_inches", 1.0)

        # show up to 3 labels as preview
        for i, label in enumerate(st.session_state.current_labels[:3]):
            if "__blank_label__" in label:
                st.write(f"**Label {i + 1}** (Blank Text)")
            else:
                st.write(f"**Label {i + 1}**")

            preview_html = render_to_html_preview(
                label, width_in, height_in, style_config
            )
            st.markdown(preview_html, unsafe_allow_html=True)

        if len(st.session_state.current_labels) > 3:
            st.info(
                f"... and {len(st.session_state.current_labels) - 3} more labels in session"
            )


def download_pdf_ui() -> None:
    """Render the PDF download section.

    Returns
    -------
    None
    """
    current_label = {
        entry["key"]: entry["value"]
        for entry in st.session_state.manual_entries
        if entry["key"] or entry["value"]
    }
    all_labels = st.session_state.current_labels.copy()
    if current_label:
        all_labels.append(current_label)

    if all_labels:
        style_config = _build_style_config()
        pdf_bytes = create_pdf_from_labels(all_labels, style_config)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 Download PDF",
            pdf_bytes,
            f"paleo_labels_{timestamp}.pdf",
            "application/pdf",
            type="primary",
        )


def save_labels_ui() -> None:
    """Render the save labels section.

    Returns
    -------
    None
    """
    st.subheader("Save")

    current_label = {
        entry["key"]: entry["value"]
        for entry in st.session_state.manual_entries
        if entry["key"]
    }

    if current_label:
        save_option = st.selectbox(
            "Save option:", ["Save Label", "Copy & Save N Times"]
        )

        if save_option == "Save Label":
            label_name = st.text_input(
                "Label name:",
                value=f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )

            if st.button("💾 Save Label"):
                label_file = LABELS_DIR / f"{label_name}.json"
                with open(label_file, "w") as f:
                    json.dump(current_label, f, indent=2)

                st.session_state.current_labels.append(current_label)
                st.session_state.manual_entries = [{"key": "", "value": ""}]

                st.success(f"Label '{label_name}' saved!")
                st.rerun()

        elif save_option == "Copy & Save N Times":
            num_copies = st.number_input(
                "Number of copies:", min_value=1, max_value=100, value=5
            )
            base_name = st.text_input(
                "Base name:",
                value=f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )

            if st.button("💾 Copy & Save"):
                saved_labels = []

                for i in range(num_copies):
                    label_copy = current_label.copy()
                    label_name = f"{base_name}_{i + 1:03d}"

                    label_copy["Copy_ID"] = str(uuid.uuid4())[:8]
                    label_copy["Copy_Number"] = f"{i + 1} of {num_copies}"

                    label_file = LABELS_DIR / f"{label_name}.json"
                    with open(label_file, "w") as f:
                        json.dump(label_copy, f, indent=2)

                    saved_labels.append(label_copy)

                st.session_state.current_labels.extend(saved_labels)
                st.session_state.manual_entries = [{"key": "", "value": ""}]

                st.success(f"Saved {num_copies} label copies!")
                st.rerun()


def new_label_ui() -> None:
    """Render the new label section.

    Returns
    -------
    None
    """
    st.subheader("Make New Label")

    if st.button("🔄 Reset Everything", type="secondary"):
        st.session_state.current_labels = []
        st.session_state.manual_entries = [{"key": "", "value": ""}]
        st.success("Session reset!")
        st.rerun()


def sidebar_ui() -> None:
    """Render the sidebar with session information.

    Returns
    -------
    None
    """
    with st.sidebar:
        st.subheader("📊 Session Info")
        st.metric("Labels in Session", len(st.session_state.current_labels))
        st.metric("Saved Labels", len(get_existing_labels()))

        if st.session_state.current_labels:
            st.subheader("Current Session Labels")
            for i, label in enumerate(st.session_state.current_labels):
                if "__blank_label__" in label:
                    with st.expander(f"Label {i + 1} (Blank Text)"):
                        st.write(label["__blank_label__"])
                else:
                    with st.expander(f"Label {i + 1}"):
                        for key, value in label.items():
                            st.write(f"**{key}**: {value}")


def main() -> None:
    """Run the Paleo Labels Streamlit application.

    Returns
    -------
    None
    """
    st.set_page_config(page_title="Paleo Labels", page_icon="🏷️", layout="wide")
    st.title("🏷️ Paleo Labels")

    # initialize session state
    _initialize_session_state()

    # render UI sections
    fill_with_ui()
    manual_entry_ui()
    blank_label_ui()
    style_options_ui()

    preview_ui()

    download_pdf_ui()

    save_labels_ui()

    new_label_ui()

    sidebar_ui()


if __name__ == "__main__":
    main()
