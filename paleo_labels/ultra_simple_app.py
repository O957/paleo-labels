"""
Ultra-Simplified Paleo Labels App
Single interface following exact user specification for maximum simplicity.
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

# Initialize storage paths
LABELS_DIR = Path.home() / ".paleo_labels" / "labels"
LABELS_DIR.mkdir(parents=True, exist_ok=True)

# Style configuration paths
STYLE_DIR = Path(__file__).parent.parent / "label_templates"

# Phase 1: Unified measurement system - everything in points (1/72 inch)
POINTS_PER_INCH = 72
INCHES_TO_CM = 2.54
CM_TO_INCHES = 1 / INCHES_TO_CM
POINTS_PER_CM = POINTS_PER_INCH * CM_TO_INCHES


# Measurement conversion functions
def inches_to_points(inches: float) -> float:
    """Convert inches to points (1/72 inch)."""
    return inches * POINTS_PER_INCH


def cm_to_points(cm: float) -> float:
    """Convert centimeters to points."""
    return cm * POINTS_PER_CM


def points_to_inches(points: float) -> float:
    """Convert points to inches."""
    return points / POINTS_PER_INCH


def points_to_cm(points: float) -> float:
    """Convert points to centimeters."""
    return points / POINTS_PER_CM


def points_to_pixels(points: float, dpi: float = 96) -> float:
    """Convert points to pixels for HTML preview (default 96 DPI)."""
    return points * dpi / POINTS_PER_INCH


# Default dimensions in points
DEFAULT_WIDTH_POINTS = inches_to_points(2.625)
DEFAULT_HEIGHT_POINTS = inches_to_points(1.0)
DEFAULT_FONT_SIZE_POINTS = 10
DEFAULT_PADDING_POINTS = 3.6  # 0.05 inches in points
DEFAULT_LINE_HEIGHT_RATIO = 1.2


def get_font_name(
    base_font: str, is_bold: bool = False, is_italic: bool = False
) -> str:
    """Get the correct font name based on style parameters."""
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
    """Return hardcoded default style configuration."""
    return {
        "font_name": "Times-Roman",
        "font_size": 10,
        "key_color_r": 0,
        "key_color_g": 0,
        "key_color_b": 0,
        "value_color_r": 0,
        "value_color_g": 0,
        "value_color_b": 0,
        "padding_percent": 0.05,
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
    """Convert font name to ReportLab format."""
    if "Times" in font_name:
        return "Times-Roman"
    elif "Helvetica" in font_name or "Arial" in font_name:
        return "Helvetica"
    elif "Courier" in font_name:
        return "Courier"
    else:
        return "Times-Roman"


def _process_toml_typography(style_config: dict, toml_data: dict) -> None:
    """Process typography section from TOML data."""
    if "typography" in toml_data:
        style_config.update(toml_data["typography"])
        font_name = toml_data["typography"].get("font_name", "Times New Roman")
        style_config["font_name"] = _convert_font_name_to_reportlab(font_name)


def _process_toml_colors(style_config: dict, toml_data: dict) -> None:
    """Process colors section from TOML data, normalizing to 0-1 range."""
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
    """Load default style from default_style.toml file."""
    default_style_path = STYLE_DIR / "default_style.toml"

    if not default_style_path.exists():
        return _get_hardcoded_defaults()

    try:
        with open(default_style_path, "rb") as f:
            toml_data = tomli.load(f)

        style_config = {}

        # Process each section
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
    """Get default values - now loads from TOML file."""
    return load_default_style()


def apply_style_defaults(style_config: dict) -> dict:
    """Apply default values to style configuration and handle font styling."""
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
    """Calculate number of underscores that fit within available width (in points), aligned to same end position."""
    # Character width estimate in points (more accurate for points-based system)
    char_width_points = font_size_points * 0.6

    # Calculate how many characters can fit in available width
    max_chars_in_width = round(available_width_points / char_width_points)

    # Calculate target position (95% of available character space)
    target_char_position = round(max_chars_in_width * 0.95)

    # Calculate underlines needed to reach target position
    key_and_colon_length = len(key_part + ": ")
    underscore_count = max(1, target_char_position - key_and_colon_length)

    # Ensure we don't exceed the maximum width
    max_underscores = max_chars_in_width - key_and_colon_length
    return min(underscore_count, max_underscores, 100)


class LabelRenderer:
    """Phase 2: Dimension-first label renderer that works in points for both preview and PDF."""

    def __init__(
        self, width_inches: float, height_inches: float, style_config: dict
    ):
        self.width_points = inches_to_points(width_inches)
        self.height_points = inches_to_points(height_inches)
        self.style_config = style_config

        # Calculate padding in points
        self.padding_points = self.style_config.get(
            "padding_percent", 0.05
        ) * min(self.width_points, self.height_points)

        # Available text area in points
        self.text_width_points = self.width_points - (2 * self.padding_points)
        self.text_height_points = self.height_points - (
            2 * self.padding_points
        )

        # Font configuration
        self.font_size_points = self.style_config.get(
            "font_size", DEFAULT_FONT_SIZE_POINTS
        )
        print(
            f"DEBUG LabelRenderer: Received font_size={self.style_config.get('font_size')}, using font_size_points={self.font_size_points}"
        )
        self.line_height_points = (
            self.font_size_points * DEFAULT_LINE_HEIGHT_RATIO
        )

    def calculate_optimal_font_size(self, lines: list[str]) -> float:
        """Calculate optimal font size to fit all content within exact dimensions."""
        if not lines:
            return self.font_size_points

        # TEMPORARY: Disable auto-sizing to test if this is the issue
        # Just return the configured font size directly
        print(
            f"DEBUG: Using configured font size directly: {self.font_size_points}"
        )
        return self.font_size_points

        # ORIGINAL AUTO-SIZING CODE (commented out for debugging):
        # # Estimate character width (points)
        # base_char_width = self.font_size_points * 0.6
        #
        # # Find longest line
        # max_line_length = max(len(line) for line in lines)
        # estimated_line_width = max_line_length * base_char_width
        #
        # # Calculate scaling factors
        # width_scale = self.text_width_points / estimated_line_width if estimated_line_width > 0 else 1.0
        #
        # # Calculate height requirements
        # total_text_height = len(lines) * self.line_height_points
        # height_scale = self.text_height_points / total_text_height if total_text_height > 0 else 1.0
        #
        # print(f"DEBUG auto-sizing: text_width={self.text_width_points}, estimated_line_width={estimated_line_width}, width_scale={width_scale}")
        # print(f"DEBUG auto-sizing: text_height={self.text_height_points}, total_text_height={total_text_height}, height_scale={height_scale}")
        #
        # # Use the more restrictive scaling factor
        # # Allow font to grow up to 1.5x the configured size if there's space
        # max_scale = 1.5  # Allow up to 50% larger than configured
        # scale_factor = min(width_scale, height_scale, max_scale)
        #
        # result = max(self.font_size_points * scale_factor, 6.0)  # Minimum 6pt font
        # print(f"DEBUG calculate_optimal_font_size: configured={self.font_size_points}, scale_factor={scale_factor}, result={result}")
        # return result

    def process_label_data(self, label_data: dict) -> list[str]:
        """Process label data into lines with underlines for empty values."""
        lines = []

        # Handle colon alignment if enabled
        align_colons = self.style_config.get("align_colons", False)
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

        # Create lines with underlines for empty values
        for key, value in processed_entries.items():
            if not value or not value.strip():
                underline_count = calculate_underline_length(
                    key, self.text_width_points, self.font_size_points
                )
                underlines = "_" * underline_count
                lines.append(f"{key}: {underlines}")
            else:
                lines.append(f"{key}: {value}")

        return lines

    def render_to_html_preview(
        self, label_data: dict, preview_dpi: float = 96
    ) -> str:
        """Render label to HTML preview with exact dimensions."""
        lines = self.process_label_data(label_data)
        optimal_font_size = self.calculate_optimal_font_size(lines)

        # Convert points to pixels for HTML
        preview_width_px = points_to_pixels(self.width_points, preview_dpi)
        preview_height_px = points_to_pixels(self.height_points, preview_dpi)
        padding_px = points_to_pixels(self.padding_points, preview_dpi)
        font_size_px = points_to_pixels(optimal_font_size, preview_dpi)

        # Build HTML with precise dimensions
        lines_html = []
        for line in lines:
            if ": " in line:
                key_part, value_part = line.split(": ", 1)
                key_style = self._get_html_text_style("key", font_size_px)
                value_style = self._get_html_text_style("value", font_size_px)
                line_html = f'<span style="{key_style}">{key_part}: </span><span style="{value_style}">{value_part}</span>'
            else:
                key_style = self._get_html_text_style("key", font_size_px)
                line_html = f'<span style="{key_style}">{line}</span>'
            lines_html.append(line_html)

        # Calculate line height to match PDF
        line_height_px = points_to_pixels(
            optimal_font_size * DEFAULT_LINE_HEIGHT_RATIO, preview_dpi
        )

        # Position lines individually to match PDF positioning
        positioned_lines = []
        for i, line_html in enumerate(lines_html):
            top_position = i * line_height_px
            positioned_line = f'<div style="position: absolute; top: {top_position}px; left: 0; width: 100%; margin: 0; padding: 0; line-height: {line_height_px}px;">{line_html}</div>'
            positioned_lines.append(positioned_line)

        content_html = "".join(positioned_lines)
        text_align = (
            "center" if self.style_config.get("center_text", False) else "left"
        )

        outer_style = (
            f"border: 1px solid #cccccc; "
            f"width: {preview_width_px}px; height: {preview_height_px}px; "
            f"margin: 20px auto; background-color: white; "
            f"position: relative; box-sizing: border-box;"
        )

        inner_style = (
            f"position: absolute; top: {padding_px}px; left: {padding_px}px; "
            f"width: {preview_width_px - 2 * padding_px}px; "
            f"height: {preview_height_px - 2 * padding_px}px; "
            f"text-align: {text_align}; position: relative; "
            f"margin: 0; padding: 0; box-sizing: border-box;"
        )

        dimensions_info = f'Exact size: {points_to_inches(self.width_points):.3f}" × {points_to_inches(self.height_points):.3f}" ({points_to_cm(self.width_points):.2f}cm × {points_to_cm(self.height_points):.2f}cm)'

        return f'''<div style="{outer_style}">
    <div style="{inner_style}">{content_html}</div>
</div>
<p style="text-align: center; color: #666; font-size: 12px; margin-top: 10px;">{dimensions_info}</p>'''

    def _get_html_text_style(self, text_type: str, font_size_px: float) -> str:
        """Get HTML text styling for key or value text."""
        font_mapping = {
            "Helvetica": "Arial, sans-serif",
            "Times-Roman": "Times, serif",
            "Courier": "Courier New, monospace",
        }

        font_name = self.style_config.get("font_name", "Times-Roman")
        css_font = font_mapping.get(font_name, "Times, serif")

        if text_type == "key":
            color_r = int(self.style_config.get("key_color_r", 0.0) * 255)
            color_g = int(self.style_config.get("key_color_g", 0.0) * 255)
            color_b = int(self.style_config.get("key_color_b", 0.0) * 255)
            weight = (
                "bold"
                if self.style_config.get("bold_keys", True)
                else "normal"
            )
            style = (
                "italic"
                if self.style_config.get("italic_keys", False)
                else "normal"
            )
        else:  # value
            color_r = int(self.style_config.get("value_color_r", 0.0) * 255)
            color_g = int(self.style_config.get("value_color_g", 0.0) * 255)
            color_b = int(self.style_config.get("value_color_b", 0.0) * 255)
            weight = (
                "bold"
                if self.style_config.get("bold_values", False)
                else "normal"
            )
            style = (
                "italic"
                if self.style_config.get("italic_values", False)
                else "normal"
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
        self, canvas_obj, label_data: dict, x_offset: float, y_offset: float
    ):
        """Render label to PDF canvas at specified position (in points)."""
        lines = self.process_label_data(label_data)
        optimal_font_size = self.calculate_optimal_font_size(lines)

        # Draw border
        canvas_obj.setStrokeColor(colors.black)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.rect(
            x_offset, y_offset, self.width_points, self.height_points
        )

        # Get fonts
        base_font = self.style_config.get("font_name", "Times-Roman")
        key_font = get_font_name(
            base_font,
            self.style_config.get("bold_keys", True),
            self.style_config.get("italic_keys", False),
        )
        value_font = get_font_name(
            base_font,
            self.style_config.get("bold_values", False),
            self.style_config.get("italic_values", False),
        )

        # Get colors
        key_color = (
            self.style_config.get("key_color_r", 0.0),
            self.style_config.get("key_color_g", 0.0),
            self.style_config.get("key_color_b", 0.0),
        )
        value_color = (
            self.style_config.get("value_color_r", 0.0),
            self.style_config.get("value_color_g", 0.0),
            self.style_config.get("value_color_b", 0.0),
        )

        # Draw text
        text_y = (
            y_offset
            + self.height_points
            - self.padding_points
            - optimal_font_size
        )

        for line in lines:
            if text_y < y_offset + self.padding_points:
                break

            if ": " in line:
                key_part, value_part = line.split(": ", 1)

                # Calculate line width for centering
                key_text = f"{key_part}: "
                key_width = canvas_obj.stringWidth(
                    key_text, key_font, optimal_font_size
                )
                value_width = canvas_obj.stringWidth(
                    value_part, value_font, optimal_font_size
                )
                total_width = key_width + value_width

                # Set x position (centered or left-aligned)
                if self.style_config.get("center_text", False):
                    text_x = x_offset + (self.width_points - total_width) / 2
                else:
                    text_x = x_offset + self.padding_points

                # Draw key
                canvas_obj.setFont(key_font, optimal_font_size)
                canvas_obj.setFillColorRGB(*key_color)
                canvas_obj.drawString(text_x, text_y, key_text)

                # Draw value
                canvas_obj.setFont(value_font, optimal_font_size)
                canvas_obj.setFillColorRGB(*value_color)
                canvas_obj.drawString(text_x + key_width, text_y, value_part)
            else:
                # Single line (no colon)
                canvas_obj.setFont(key_font, optimal_font_size)
                canvas_obj.setFillColorRGB(*key_color)

                line_width = canvas_obj.stringWidth(
                    line, key_font, optimal_font_size
                )
                if self.style_config.get("center_text", False):
                    text_x = x_offset + (self.width_points - line_width) / 2
                else:
                    text_x = x_offset + self.padding_points

                canvas_obj.drawString(text_x, text_y, line)

            text_y -= optimal_font_size * DEFAULT_LINE_HEIGHT_RATIO


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def convert_key_name(underscore_key):
    """Convert underscore_key to 'Proper Key Name' format."""
    return underscore_key.replace("_", " ").title()


def load_label_types():
    """Load label types from TOML files in label_templates directory."""
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


def get_existing_labels():
    """Get list of existing saved labels."""
    labels = []
    for label_file in LABELS_DIR.glob("*.json"):
        try:
            with open(label_file) as f:
                data = json.load(f)
                labels.append({"name": label_file.stem, "data": data})
        except:
            continue
    return labels


def get_previous_values(key):
    """Get previous values used for a specific key."""
    values = set()
    for label in get_existing_labels():
        if key.lower() in [k.lower() for k in label["data"].keys()]:
            for k, v in label["data"].items():
                if k.lower() == key.lower() and v.strip():
                    values.add(v.strip())
    return sorted(list(values))


def get_pbdb_suggestions(partial_value):
    """Get PBDB suggestions for taxonomic fields."""
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
    except:
        pass
    return []


def get_scientific_name_suggestions(partial_value):
    """Get combined suggestions for Scientific Name from existing labels and PBDB."""
    suggestions = set()

    for label in get_existing_labels():
        for key, value in label["data"].items():
            if "scientific" in key.lower() and value.strip():
                if not partial_value or partial_value.lower() in value.lower():
                    suggestions.add(value.strip())

    if partial_value and len(partial_value) >= 2:
        pbdb_suggestions = get_pbdb_suggestions(partial_value)
        suggestions.update(pbdb_suggestions)

    return sorted(list(suggestions))


def _process_nested_dimensions(
    converted_style: dict, style_data: dict, default_style: dict
) -> None:
    """Process dimensions section from nested TOML format."""
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
    """Process typography section from nested TOML format."""
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
    """Process colors section from nested TOML format."""
    if "colors" in style_data:
        colors_data = style_data["colors"]

        # Process key colors
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

        # Process value colors
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
    """Process style section from nested TOML format."""
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
    """Process flat format TOML data."""
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
    """Normalize color component to 0-255 range."""
    return int(value * 255) if value <= 1 else int(value)


def _process_flat_colors(converted_style: dict, style_data: dict) -> None:
    """Process flat color format from TOML data."""
    # Process key colors
    if all(
        k in style_data for k in ["key_color_r", "key_color_g", "key_color_b"]
    ):
        key_r = _normalize_color_component(style_data["key_color_r"])
        key_g = _normalize_color_component(style_data["key_color_g"])
        key_b = _normalize_color_component(style_data["key_color_b"])
        converted_style["key_color"] = f"#{key_r:02x}{key_g:02x}{key_b:02x}"

    # Process value colors
    if all(
        k in style_data
        for k in ["value_color_r", "value_color_g", "value_color_b"]
    ):
        val_r = _normalize_color_component(style_data["value_color_r"])
        val_g = _normalize_color_component(style_data["value_color_g"])
        val_b = _normalize_color_component(style_data["value_color_b"])
        converted_style["value_color"] = f"#{val_r:02x}{val_g:02x}{val_b:02x}"


def _convert_style_data(style_data: dict, default_style: dict) -> dict:
    """Convert TOML style data to internal format."""
    converted_style = default_style.copy()

    # Process nested format sections
    _process_nested_dimensions(converted_style, style_data, default_style)
    _process_nested_typography(converted_style, style_data, default_style)
    _process_nested_colors(converted_style, style_data)
    _process_nested_style_options(converted_style, style_data, default_style)

    # Process flat format
    _process_flat_format(converted_style, style_data)
    _process_flat_colors(converted_style, style_data)

    return converted_style


def load_style_files():
    """Load available style files."""
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
    """Get available key options from existing labels."""
    all_keys = set()
    for label in get_existing_labels():
        all_keys.update(label["data"].keys())

    key_options = ["New", "Empty"] + sorted(list(all_keys))

    if current_key and current_key not in key_options:
        key_options.append(current_key)

    return key_options


def _render_key_input(index: int, current_key: str) -> str:
    """Render the key input widget."""
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
    """Render scientific name input with suggestions."""
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
    """Render standard value input with previous values."""
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
    """Check if a field is for scientific names."""
    return "scientific" in key.lower() and "name" in key.lower()


def render_key_value_input(index, current_key="", current_value=""):
    """Render a key-value input pair with smart suggestions."""
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


def hex_to_rgb_components(hex_color):
    """Convert hex color to separate r,g,b components (0-1 range) like original app.py expects."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return (r / 255.0, g / 255.0, b / 255.0)
    return (0.0, 0.0, 0.0)


def convert_to_original_style_format(style_config):
    """Convert our hex-based style to the RGB format the original app.py expects."""
    # Convert hex colors to RGB components
    key_r, key_g, key_b = hex_to_rgb_components(
        style_config.get("key_color", "#000000")
    )
    value_r, value_g, value_b = hex_to_rgb_components(
        style_config.get("value_color", "#000000")
    )

    return {
        "font_name": style_config.get("font_name", "Times-Roman"),
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


def create_pdf_from_labels(labels_data, style_config=None):
    """Create PDF from labels data using unified LabelRenderer for precise dimensions."""
    if style_config is None:
        style_config = load_default_style()

    # Get dimensions from style config
    width_inches = style_config.get("width_inches", 2.625)
    height_inches = style_config.get("height_inches", 1.0)

    # Create unified renderer with exact dimensions
    renderer = LabelRenderer(width_inches, height_inches, style_config)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Calculate layout in points for precise positioning
    margin_points = inches_to_points(0.1875)
    labels_per_row = 3
    labels_per_col = 10

    page_width_points = inches_to_points(8.5)  # US Letter width
    page_height_points = inches_to_points(11)  # US Letter height

    current_label = 0

    for label_data in labels_data:
        if (
            current_label > 0
            and current_label % (labels_per_row * labels_per_col) == 0
        ):
            c.showPage()

        row = (
            current_label % (labels_per_row * labels_per_col)
        ) // labels_per_row
        col = current_label % labels_per_row

        # Calculate exact position in points
        x = margin_points + col * renderer.width_points
        y = (
            page_height_points
            - margin_points
            - renderer.height_points
            - row * renderer.height_points
        )

        # Use unified renderer for precise dimensions
        renderer.render_to_pdf_canvas(c, label_data, x, y)

        current_label += 1

    c.save()
    return buffer.getvalue()


def main():
    st.set_page_config(page_title="Paleo Labels", page_icon="🏷️", layout="wide")
    st.title("🏷️ Paleo Labels")

    # Initialize session state
    if "current_labels" not in st.session_state:
        st.session_state.current_labels = []
    if "manual_entries" not in st.session_state:
        st.session_state.manual_entries = [{"key": "", "value": ""}]
    if "current_style" not in st.session_state:
        st.session_state.current_style = load_default_style()

    # Load label types
    if "loaded_label_types" not in st.session_state:
        st.session_state.loaded_label_types = load_label_types()

    # Fill With section
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
                    "No label types found. Please check the label_templates directory."
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

                    # Track processed files to prevent infinite loops
                    if "processed_files" not in st.session_state:
                        st.session_state.processed_files = set()
                    st.session_state.processed_files.add(uploaded_label.name)

                    st.success(
                        f"Loaded {len(st.session_state.manual_entries)} fields from TOML!"
                    )
                except Exception as e:
                    st.error(f"Error loading TOML: {e}")

    # Manual Entry section
    st.subheader("Manual Entry")

    # Render current entries
    for i, entry in enumerate(st.session_state.manual_entries):
        key, value = render_key_value_input(i, entry["key"], entry["value"])
        st.session_state.manual_entries[i] = {"key": key, "value": value}

    # Add/Remove entry buttons
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

    # Style Options section - COMPLETELY REWRITTEN to work like original app.py
    st.subheader("Style Options")

    # Get defaults from TOML
    defaults = load_default_style()

    # Style widgets with proper default values
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
            ["Times-Roman", "Helvetica", "Courier"],
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

    # Current label preview with styling
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

        style_config = st.session_state.current_style

        # Display current dimensions
        width_in = style_config.get("width_inches", 2.625)
        height_in = style_config.get("height_inches", 1.0)
        width_cm = width_in * INCHES_TO_CM
        height_cm = height_in * INCHES_TO_CM

        st.write(
            f'**Label Size**: {width_in:.3f}" × {height_in:.3f}" ({width_cm:.1f}cm × {height_cm:.1f}cm)'
        )

        # Build style config from current widget values (just like original app.py)
        # Get the dimensions from the style widgets above
        if st.session_state.get("style_units") == "Metric":
            width_in = (
                st.session_state.get("style_width_cm", 6.7) / INCHES_TO_CM
            )
            height_in = (
                st.session_state.get("style_height_cm", 2.5) / INCHES_TO_CM
            )
        else:
            width_in = st.session_state.get("style_width_in", 2.625)
            height_in = st.session_state.get("style_height_in", 1.0)

        # Get all style values from widgets
        key_color_hex = st.session_state.get("style_key_color", "#000000")
        value_color_hex = st.session_state.get("style_value_color", "#000000")
        key_r, key_g, key_b = hex_to_rgb(key_color_hex)
        value_r, value_g, value_b = hex_to_rgb(value_color_hex)

        # Build complete style config like original app.py
        font_size_value = st.session_state.get("style_font_size", 10)
        st.write(
            f"DEBUG: Font size from widget: {font_size_value} (type: {type(font_size_value)})"
        )

        style_config = {
            "font_name": st.session_state.get("style_font", "Times-Roman"),
            "font_size": font_size_value,
            "width_inches": width_in,
            "height_inches": height_in,
            "padding_percent": st.session_state.get("style_padding", 0.05),
            "key_color_r": key_r / 255.0,
            "key_color_g": key_g / 255.0,
            "key_color_b": key_b / 255.0,
            "value_color_r": value_r / 255.0,
            "value_color_g": value_g / 255.0,
            "value_color_b": value_b / 255.0,
            "bold_keys": st.session_state.get("style_bold_keys", True),
            "bold_values": st.session_state.get("style_bold_values", False),
            "italic_keys": st.session_state.get("style_italic_keys", False),
            "italic_values": st.session_state.get(
                "style_italic_values", False
            ),
            "center_text": st.session_state.get("style_center_text", False),
            "show_keys": st.session_state.get("style_show_keys", True),
            "show_values": True,
        }

        # Use unified renderer for precise preview with exact dimensions
        renderer = LabelRenderer(width_in, height_in, style_config)
        preview_html = renderer.render_to_html_preview(current_label)
        st.markdown(preview_html, unsafe_allow_html=True)

    # Download PDF section
    current_label = {
        entry["key"]: entry["value"]
        for entry in st.session_state.manual_entries
        if entry["key"] or entry["value"]
    }
    all_labels = st.session_state.current_labels.copy()
    if current_label:
        all_labels.append(current_label)

    if all_labels:
        # Use the same style config as preview
        if st.session_state.get("style_units") == "Metric":
            width_in = (
                st.session_state.get("style_width_cm", 6.7) / INCHES_TO_CM
            )
            height_in = (
                st.session_state.get("style_height_cm", 2.5) / INCHES_TO_CM
            )
        else:
            width_in = st.session_state.get("style_width_in", 2.625)
            height_in = st.session_state.get("style_height_in", 1.0)

        key_color_hex = st.session_state.get("style_key_color", "#000000")
        value_color_hex = st.session_state.get("style_value_color", "#000000")
        key_r, key_g, key_b = hex_to_rgb(key_color_hex)
        value_r, value_g, value_b = hex_to_rgb(value_color_hex)

        pdf_style_config = {
            "font_name": st.session_state.get("style_font", "Times-Roman"),
            "font_size": st.session_state.get("style_font_size", 10),
            "width_inches": width_in,
            "height_inches": height_in,
            "padding_percent": st.session_state.get("style_padding", 0.05),
            "key_color_r": key_r / 255.0,
            "key_color_g": key_g / 255.0,
            "key_color_b": key_b / 255.0,
            "value_color_r": value_r / 255.0,
            "value_color_g": value_g / 255.0,
            "value_color_b": value_b / 255.0,
            "bold_keys": st.session_state.get("style_bold_keys", True),
            "bold_values": st.session_state.get("style_bold_values", False),
            "italic_keys": st.session_state.get("style_italic_keys", False),
            "italic_values": st.session_state.get(
                "style_italic_values", False
            ),
            "center_text": st.session_state.get("style_center_text", False),
            "show_keys": st.session_state.get("style_show_keys", True),
            "show_values": True,
        }

        pdf_bytes = create_pdf_from_labels(all_labels, pdf_style_config)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 Download PDF",
            pdf_bytes,
            f"paleo_labels_{timestamp}.pdf",
            "application/pdf",
            type="primary",
        )

    # Save section
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

    # Make New Label
    st.subheader("Make New Label")

    if st.button("🔄 Reset Everything", type="secondary"):
        st.session_state.current_labels = []
        st.session_state.manual_entries = [{"key": "", "value": ""}]
        st.success("Session reset!")
        st.rerun()

    # Sidebar with session info
    with st.sidebar:
        st.subheader("📊 Session Info")
        st.metric("Labels in Session", len(st.session_state.current_labels))
        st.metric("Saved Labels", len(get_existing_labels()))

        if st.session_state.current_labels:
            st.subheader("Current Session Labels")
            for i, label in enumerate(st.session_state.current_labels):
                with st.expander(f"Label {i + 1}"):
                    for key, value in label.items():
                        st.write(f"**{key}**: {value}")


if __name__ == "__main__":
    main()
