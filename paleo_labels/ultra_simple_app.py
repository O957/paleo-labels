"""
Ultra-Simplified Paleo Labels App
Single interface following exact user specification for maximum simplicity.
"""

import streamlit as st
import json
import polars as pl
import requests
import tomli
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
import uuid

# Initialize storage paths
LABELS_DIR = Path.home() / ".paleo_labels" / "labels"
LABELS_DIR.mkdir(parents=True, exist_ok=True)

# Style configuration paths
STYLE_DIR = Path(__file__).parent.parent / "label_templates"

# Conversion constants
INCHES_TO_CM = 2.54
POINTS_PER_INCH = 72
PREVIEW_SCALE = 100

# Default style configuration using original app.py format
REFERENCE_FONT_SIZE = 10
DEFAULT_PADDING_PERCENT = 0.05
DEFAULT_WIDTH_IN = 2.625
DEFAULT_HEIGHT_IN = 1.0
PREVIEW_LINE_HEIGHT = 1.1

def get_font_name(base_font: str, is_bold: bool = False, is_italic: bool = False) -> str:
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

def load_default_style() -> dict:
    """Load default style from default_style.toml file."""
    default_style_path = STYLE_DIR / "default_style.toml"
    
    if default_style_path.exists():
        try:
            with open(default_style_path, "rb") as f:
                toml_data = tomli.load(f)
            
            # Flatten the TOML structure into the format expected by the style system
            style_config = {}
            
            # Dimensions
            if "dimensions" in toml_data:
                style_config.update(toml_data["dimensions"])
            
            # Typography
            if "typography" in toml_data:
                style_config.update(toml_data["typography"])
                # Convert font name to ReportLab format
                font_name = toml_data["typography"].get("font_name", "Times New Roman")
                if "Times" in font_name:
                    style_config["font_name"] = "Times-Roman"
                elif "Helvetica" in font_name or "Arial" in font_name:
                    style_config["font_name"] = "Helvetica"
                elif "Courier" in font_name:
                    style_config["font_name"] = "Courier"
                else:
                    style_config["font_name"] = "Times-Roman"
            
            # Colors (normalize to 0-1 range)
            if "colors" in toml_data:
                colors = toml_data["colors"]
                for color_key in ["key_color_r", "key_color_g", "key_color_b", "value_color_r", "value_color_g", "value_color_b"]:
                    if color_key in colors:
                        # If value is > 1, assume it's 0-255 range and convert to 0-1
                        value = colors[color_key]
                        style_config[color_key] = value / 255.0 if value > 1 else value
            
            # Style options
            if "style" in toml_data:
                style_config.update(toml_data["style"])
            
            return style_config
            
        except Exception as e:
            print(f"Error loading default style: {e}")
    
    # Fallback to hardcoded defaults if file doesn't exist or can't be loaded
    return {
        "font_name": "Times-Roman",
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
    processed["value_font"] = get_font_name(base_font, bold_values, italic_values)
    
    return processed

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
        "center_text": style_config.get("center_text", False),
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

    # Add center text support
    text_align = "center" if style_props.get("center_text", False) else "left"
    
    inner_div_style = (
        f"position: absolute; top: {padding_y}px; left: {padding_x}px; "
        f"width: {effective_width - 2 * padding_x}px; "
        f"height: {effective_height - 2 * padding_y}px; "
        f"font-family: {style_props['css_font']}; "
        f"font-size: {style_props['font_size'] * (PREVIEW_SCALE / POINTS_PER_INCH)}px; "
        f"line-height: {PREVIEW_LINE_HEIGHT}; "
        f"text-align: {text_align};"
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

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def convert_key_name(underscore_key):
    """Convert underscore_key to 'Proper Key Name' format."""
    return underscore_key.replace('_', ' ').title()

def load_label_types():
    """Load label types from TOML files in label_templates directory."""
    label_types = {}
    
    if STYLE_DIR.exists():
        for toml_file in STYLE_DIR.glob("*.toml"):
            if any(style_word in toml_file.name.lower() for style_word in ['style', 'default']):
                continue
                
            try:
                with open(toml_file, 'rb') as f:
                    toml_data = tomli.load(f)
                
                if 'label_type' in toml_data and 'fields' in toml_data:
                    label_type_name = toml_data['label_type']['name']
                    field_keys = list(toml_data['fields'].keys())
                    proper_field_names = [convert_key_name(key) for key in field_keys]
                    
                    label_types[label_type_name] = {
                        'fields': proper_field_names,
                        'raw_keys': field_keys,
                        'description': toml_data['label_type'].get('description', '')
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
            with open(label_file, 'r') as f:
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
                return [record["nam"] for record in data["records"] if "nam" in record]
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

def load_style_files():
    """Load available style files."""
    default_style = load_default_style()
    styles = {"Default Style": default_style}
    
    if STYLE_DIR.exists():
        for style_file in STYLE_DIR.glob("*.toml"):
            if 'style' not in style_file.name.lower():
                continue
                
            try:
                with open(style_file, 'rb') as f:
                    style_data = tomli.load(f)
                
                converted_style = default_style.copy()
                
                # Handle different TOML formats
                if 'dimensions' in style_data:
                    converted_style.update({
                        "width_inches": style_data['dimensions'].get('width_inches', default_style['width_inches']),
                        "height_inches": style_data['dimensions'].get('height_inches', default_style['height_inches']),
                        "padding_percent": style_data['dimensions'].get('padding_percent', default_style['padding_percent']),
                    })
                
                if 'typography' in style_data:
                    converted_style.update({
                        "font_name": style_data['typography'].get('font_name', default_style['font_name']),
                        "font_size": style_data['typography'].get('font_size', default_style['font_size']),
                    })
                
                if 'colors' in style_data:
                    colors_data = style_data['colors']
                    if all(k in colors_data for k in ['key_color_r', 'key_color_g', 'key_color_b']):
                        key_r = int(colors_data['key_color_r'])
                        key_g = int(colors_data['key_color_g'])
                        key_b = int(colors_data['key_color_b'])
                        converted_style['key_color'] = f"#{key_r:02x}{key_g:02x}{key_b:02x}"
                    
                    if all(k in colors_data for k in ['value_color_r', 'value_color_g', 'value_color_b']):
                        val_r = int(colors_data['value_color_r'])
                        val_g = int(colors_data['value_color_g']) 
                        val_b = int(colors_data['value_color_b'])
                        converted_style['value_color'] = f"#{val_r:02x}{val_g:02x}{val_b:02x}"
                
                if 'style' in style_data:
                    converted_style.update({
                        "bold_keys": style_data['style'].get('bold_keys', default_style['bold_keys']),
                        "bold_values": style_data['style'].get('bold_values', default_style['bold_values']),
                        "italic_keys": style_data['style'].get('italic_keys', default_style['italic_keys']),
                        "italic_values": style_data['style'].get('italic_values', default_style['italic_values']),
                        "show_keys": style_data['style'].get('show_keys', default_style['show_keys']),
                        "show_values": style_data['style'].get('show_values', default_style['show_values']),
                    })
                
                # Handle flat format
                for key in ['font_name', 'font_size', 'width_inches', 'height_inches', 'padding_percent',
                           'bold_keys', 'bold_values', 'italic_keys', 'italic_values', 'center_text', 'show_border']:
                    if key in style_data:
                        converted_style[key] = style_data[key]
                
                # Handle flat color format
                if all(k in style_data for k in ['key_color_r', 'key_color_g', 'key_color_b']):
                    key_r = int(style_data['key_color_r'] * 255) if style_data['key_color_r'] <= 1 else int(style_data['key_color_r'])
                    key_g = int(style_data['key_color_g'] * 255) if style_data['key_color_g'] <= 1 else int(style_data['key_color_g'])
                    key_b = int(style_data['key_color_b'] * 255) if style_data['key_color_b'] <= 1 else int(style_data['key_color_b'])
                    converted_style['key_color'] = f"#{key_r:02x}{key_g:02x}{key_b:02x}"
                
                if all(k in style_data for k in ['value_color_r', 'value_color_g', 'value_color_b']):
                    val_r = int(style_data['value_color_r'] * 255) if style_data['value_color_r'] <= 1 else int(style_data['value_color_r'])
                    val_g = int(style_data['value_color_g'] * 255) if style_data['value_color_g'] <= 1 else int(style_data['value_color_g'])
                    val_b = int(style_data['value_color_b'] * 255) if style_data['value_color_b'] <= 1 else int(style_data['value_color_b'])
                    converted_style['value_color'] = f"#{val_r:02x}{val_g:02x}{val_b:02x}"
                
                styles[style_file.stem.replace('_', ' ').title()] = converted_style
                
            except Exception as e:
                print(f"Error loading style {style_file}: {e}")
                continue
    
    return styles

def render_key_value_input(index, current_key="", current_value=""):
    """Render a key-value input pair with smart suggestions."""
    col1, col2 = st.columns(2)
    
    with col1:
        all_keys = set()
        for label in get_existing_labels():
            all_keys.update(label["data"].keys())
        
        key_options = ["New", "Empty"] + sorted(list(all_keys))
        
        if current_key and current_key not in key_options:
            key_options.append(current_key)
        
        selected_key = st.selectbox(
            f"Field {index + 1}:",
            key_options,
            index=key_options.index(current_key) if current_key in key_options else 0,
            key=f"key_select_{index}"
        )
        
        if selected_key == "New":
            actual_key = st.text_input("Enter new field:", value=current_key if current_key != "New" else "", key=f"key_new_{index}")
        elif selected_key == "Empty":
            actual_key = ""
        else:
            actual_key = selected_key
    
    with col2:
        if actual_key:
            value_label = f"Value {index + 1}"
            if actual_key:
                value_label += f" ({actual_key})"
            
            if "scientific" in actual_key.lower() and "name" in actual_key.lower():
                typed_value = st.text_input(
                    value_label + ":",
                    value=current_value,
                    key=f"value_text_{index}",
                    help="Type to search existing labels and paleobiology database"
                )
                
                if typed_value and len(typed_value) >= 2:
                    suggestions = get_scientific_name_suggestions(typed_value)
                    if suggestions:
                        st.write("**Suggestions:**")
                        for i, suggestion in enumerate(suggestions[:5]):
                            if st.button(f"🔍 {suggestion}", key=f"suggestion_{index}_{i}"):
                                st.session_state.manual_entries[index]["value"] = suggestion
                                st.rerun()
                
                actual_value = typed_value
            
            else:
                value_options = ["New", "Empty"]
                prev_values = get_previous_values(actual_key)
                value_options.extend(prev_values)
                
                if current_value and current_value not in value_options:
                    value_options.append(current_value)
                
                selected_value = st.selectbox(
                    value_label + ":",
                    value_options,
                    index=value_options.index(current_value) if current_value in value_options else 0,
                    key=f"value_select_{index}"
                )
                
                if selected_value == "New":
                    actual_value = st.text_input("Enter new value:", value=current_value if current_value != "New" else "", key=f"value_new_{index}")
                elif selected_value == "Empty":
                    actual_value = ""
                else:
                    actual_value = selected_value
        else:
            actual_value = ""
    
    return actual_key, actual_value

def hex_to_rgb_components(hex_color):
    """Convert hex color to separate r,g,b components (0-1 range) like original app.py expects."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (r/255.0, g/255.0, b/255.0)
    return (0.0, 0.0, 0.0)

def convert_to_original_style_format(style_config):
    """Convert our hex-based style to the RGB format the original app.py expects."""
    # Convert hex colors to RGB components
    key_r, key_g, key_b = hex_to_rgb_components(style_config.get('key_color', '#000000'))
    value_r, value_g, value_b = hex_to_rgb_components(style_config.get('value_color', '#000000'))
    
    return {
        'font_name': style_config.get('font_name', 'Times-Roman'),
        'font_size': style_config.get('font_size', 10),
        'width_inches': style_config.get('width_inches', 2.625),
        'height_inches': style_config.get('height_inches', 1.0),
        'padding_percent': style_config.get('padding_percent', 0.05),
        'bold_keys': style_config.get('bold_keys', True),
        'bold_values': style_config.get('bold_values', False),
        'italic_keys': style_config.get('italic_keys', False),
        'italic_values': style_config.get('italic_values', False),
        'show_keys': style_config.get('show_keys', True),
        'show_values': style_config.get('show_values', True),
        'center_text': style_config.get('center_text', False),
        'show_border': style_config.get('show_border', True),
        'key_color_r': key_r,
        'key_color_g': key_g,
        'key_color_b': key_b,
        'value_color_r': value_r,
        'value_color_g': value_g,
        'value_color_b': value_b,
    }

def extract_style_properties(style_config):
    """Extract and convert style properties from config - copied from original app.py."""
    font_mapping = {
        "Helvetica": "Arial, sans-serif",
        "Times-Roman": "Times, serif", 
        "Courier": "Courier New, monospace",
    }

    font_name = style_config.get("font_name", "Times-Roman")
    css_font = font_mapping.get(font_name, "Times, serif")

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
        "font_size": style_config.get("font_size", 10),
        "padding_percent": style_config.get("padding_percent", 0.05),
        "show_keys": style_config.get("show_keys", True),
        "show_values": style_config.get("show_values", True),
        "key_color": key_color,
        "value_color": value_color,
        "key_weight": "bold" if style_config.get("bold_keys", False) else "normal",
        "value_weight": "bold" if style_config.get("bold_values", False) else "normal",
        "key_style": "italic" if style_config.get("italic_keys", False) else "normal",
        "value_style": "italic" if style_config.get("italic_values", False) else "normal",
    }

def create_pdf_from_labels(labels_data, style_config=None):
    """Create PDF from labels data using original app.py style system."""
    if style_config is None:
        style_config = load_default_style()
    
    # Process style exactly like preview - use extract_style_properties directly
    style_props = extract_style_properties(style_config)
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    label_width = style_config.get('width_inches', 2.625) * inch
    label_height = style_config.get('height_inches', 1.0) * inch
    margin_left = 0.1875 * inch
    margin_top = 0.5 * inch
    labels_per_row = 3
    labels_per_col = 10
    
    current_label = 0
    
    for label_data in labels_data:
        if current_label > 0 and current_label % (labels_per_row * labels_per_col) == 0:
            c.showPage()
        
        row = (current_label % (labels_per_row * labels_per_col)) // labels_per_row
        col = current_label % labels_per_row
        
        x = margin_left + col * label_width
        y = letter[1] - margin_top - label_height - row * label_height
        
        # Draw border
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(x, y, label_width, label_height)
        
        # Calculate padding
        padding_x = label_width * style_props['padding_percent']
        padding_y = label_height * style_props['padding_percent']
        
        # Create lines exactly like preview
        lines = []
        for key, value in label_data.items():
            if not key and not value:
                continue
            if key:
                lines.append(f"{key}: {value if value else ''}")
            else:
                lines.append(value)
        
        # Draw text using style_props like preview
        font_size = style_props['font_size']
        line_height = font_size * 1.2
        text_y = y + label_height - padding_y - font_size
        
        # Get the key and value fonts directly from style_config
        base_font = style_config.get('font_name', 'Times-Roman')
        key_font = get_font_name(base_font, style_config.get('bold_keys', True), style_config.get('italic_keys', False))
        value_font = get_font_name(base_font, style_config.get('bold_values', False), style_config.get('italic_values', False))
        
        # Get RGB colors from style_config
        key_r = style_config.get('key_color_r', 0.0)
        key_g = style_config.get('key_color_g', 0.0) 
        key_b = style_config.get('key_color_b', 0.0)
        value_r = style_config.get('value_color_r', 0.0)
        value_g = style_config.get('value_color_g', 0.0)
        value_b = style_config.get('value_color_b', 0.0)
        
        for line in lines:
            if text_y < y + padding_y:  # Don't overflow label
                break
                
            if ": " in line and (style_props['show_keys'] or style_props['show_values']):
                key_part, value_part = line.split(": ", 1)
                
                # Calculate line width for centering
                line_width = 0
                key_text = f"{key_part}: " if style_props['show_keys'] else ""
                value_text = (value_part if value_part else "__________") if style_props['show_values'] else ""
                
                if style_props['show_keys']:
                    line_width += c.stringWidth(key_text, key_font, font_size)
                if style_props['show_values']:
                    line_width += c.stringWidth(value_text, value_font, font_size)
                
                # Set starting x position (centered or left-aligned)
                if style_config.get('center_text', False):
                    current_x = x + (label_width - line_width) / 2
                else:
                    current_x = x + padding_x
                
                if style_props['show_keys']:
                    c.setFont(key_font, font_size)
                    c.setFillColorRGB(key_r, key_g, key_b)
                    c.drawString(current_x, text_y, key_text)
                    current_x += c.stringWidth(key_text, key_font, font_size)
                
                if style_props['show_values']:
                    c.setFont(value_font, font_size)
                    c.setFillColorRGB(value_r, value_g, value_b)
                    c.drawString(current_x, text_y, value_text)
            else:
                c.setFont(key_font, font_size)
                c.setFillColorRGB(key_r, key_g, key_b)
                
                # Center single lines too
                if style_config.get('center_text', False):
                    line_width = c.stringWidth(line, key_font, font_size)
                    text_x = x + (label_width - line_width) / 2
                else:
                    text_x = x + padding_x
                    
                c.drawString(text_x, text_y, line)
            
            text_y -= line_height
        
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
        fill_option = st.selectbox("Fill with:", ["None", "Label Type", "Existing Label", "Upload Label TOML"])
        
        if fill_option == "Label Type":
            available_types = list(st.session_state.loaded_label_types.keys())
            if available_types:
                selected_type = st.selectbox("Select Label Type:", available_types)
                
                if selected_type:
                    description = st.session_state.loaded_label_types[selected_type].get('description', '')
                    if description:
                        st.write(f"*{description}*")
                
                if st.button("Load Label Type Fields"):
                    field_names = st.session_state.loaded_label_types[selected_type]['fields']
                    st.session_state.manual_entries = [{"key": key, "value": ""} for key in field_names]
                    st.rerun()
            else:
                st.info("No label types found. Please check the label_templates directory.")
        
        elif fill_option == "Existing Label":
            existing_labels = get_existing_labels()
            if existing_labels:
                label_names = [label["name"] for label in existing_labels]
                selected_label = st.selectbox("Select Existing Label:", label_names)
                if st.button("Load Existing Label"):
                    selected_data = next(label["data"] for label in existing_labels if label["name"] == selected_label)
                    st.session_state.manual_entries = [{"key": k, "value": v} for k, v in selected_data.items()]
                    st.rerun()
            else:
                st.info("No existing labels found")
        
        elif fill_option == "Upload Label TOML":
            uploaded_label = st.file_uploader("Upload Label TOML:", type=['toml'], key="upload_label_toml")
            if uploaded_label and uploaded_label.name not in st.session_state.get('processed_files', set()):
                try:
                    label_content = uploaded_label.read().decode('utf-8')
                    label_data = tomli.loads(label_content)
                    
                    if 'fields' in label_data:
                        entries = []
                        for key, value in label_data['fields'].items():
                            proper_key = convert_key_name(key)
                            entries.append({"key": proper_key, "value": str(value) if value else ""})
                        st.session_state.manual_entries = entries
                    else:
                        entries = []
                        for key, value in label_data.items():
                            if not key.startswith('_') and key not in ['label_type']:
                                entries.append({"key": key, "value": str(value) if value else ""})
                        st.session_state.manual_entries = entries
                    
                    # Track processed files to prevent infinite loops
                    if 'processed_files' not in st.session_state:
                        st.session_state.processed_files = set()
                    st.session_state.processed_files.add(uploaded_label.name)
                    
                    st.success(f"Loaded {len(st.session_state.manual_entries)} fields from TOML!")
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
        if len(st.session_state.manual_entries) > 1 and st.button("➖ Remove Last Field", key="remove_field_btn"):
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
            min_value=0.5, max_value=8.0, 
            value=defaults.get("width_inches", 2.625), 
            step=0.05, key="style_width_in"
        )
        height_inches = st.number_input(
            "Height (in):", 
            min_value=0.5, max_value=6.0, 
            value=defaults.get("height_inches", 1.0), 
            step=0.05, key="style_height_in"
        )
    
    with col2:
        st.write("**Typography**")
        font_name = st.selectbox(
            "Font:", ["Times-Roman", "Helvetica", "Courier"], 
            index=0,
            key="style_font"
        )
        font_size = st.slider(
            "Font Size:", 6, 20, 
            value=int(defaults.get("font_size", 10)), 
            key="style_font_size"
        )
    
    with col3:
        st.write("**Colors**")
        key_color = st.color_picker("Field Color:", value="#000000", key="style_key_color")
        value_color = st.color_picker("Value Color:", value="#000000", key="style_value_color")
    
    with col4:
        st.write("**Formatting**")
        bold_keys = st.checkbox("Bold Fields", value=True, key="style_bold_keys")
        bold_values = st.checkbox("Bold Values", value=False, key="style_bold_values")
        italic_keys = st.checkbox("Italic Fields", value=False, key="style_italic_keys")
        italic_values = st.checkbox("Italic Values", value=False, key="style_italic_values")
        center_text = st.checkbox("Center Text", value=False, key="style_center_text")
        padding_percent = st.slider("Padding %:", 0.01, 0.2, value=0.05, step=0.01, key="style_padding")
    
    
    # Current label preview with styling
    if any(entry["key"] or entry["value"] for entry in st.session_state.manual_entries):
        st.subheader("Current Label Preview")
        current_label = {entry["key"]: entry["value"] for entry in st.session_state.manual_entries if entry["key"] or entry["value"]}
        
        style_config = st.session_state.current_style
        
        # Display current dimensions
        width_in = style_config.get("width_inches", 2.625)
        height_in = style_config.get("height_inches", 1.0)
        width_cm = width_in * INCHES_TO_CM
        height_cm = height_in * INCHES_TO_CM
        
        st.write(f"**Label Size**: {width_in:.3f}\" × {height_in:.3f}\" ({width_cm:.1f}cm × {height_cm:.1f}cm)")
        
        # Calculate preview dimensions using proper scaling
        preview_width = int(width_in * PREVIEW_SCALE)
        preview_height = int(height_in * PREVIEW_SCALE)
        border_width = max(1, int(PREVIEW_SCALE / POINTS_PER_INCH))
        padding_x = int(preview_width * style_config.get("padding_percent", 0.05))
        padding_y = int(preview_height * style_config.get("padding_percent", 0.05))
        
        text_align = "center" if style_config.get("center_text", False) else "left"
        
        preview_font_size = int(style_config.get("font_size", 10) * (PREVIEW_SCALE / POINTS_PER_INCH))
        
        # Map PDF font names to CSS font families
        font_name = style_config.get("font_name", "Times-Roman")
        if "Times" in font_name:
            css_font_family = "Times, 'Times New Roman', serif"
        elif "Helvetica" in font_name:
            css_font_family = "Helvetica, Arial, sans-serif"
        elif "Courier" in font_name:
            css_font_family = "'Courier New', Courier, monospace"
        else:
            css_font_family = "Times, 'Times New Roman', serif"
        
        # Build style config from current widget values (just like original app.py)
        # Get the dimensions from the style widgets above
        if st.session_state.get("style_units") == "Metric":
            width_in = st.session_state.get("style_width_cm", 6.7) / INCHES_TO_CM
            height_in = st.session_state.get("style_height_cm", 2.5) / INCHES_TO_CM
        else:
            width_in = st.session_state.get("style_width_in", 2.625)
            height_in = st.session_state.get("style_height_in", 1.0)
        
        # Get all style values from widgets
        key_color_hex = st.session_state.get("style_key_color", "#000000")
        value_color_hex = st.session_state.get("style_value_color", "#000000")
        key_r, key_g, key_b = hex_to_rgb(key_color_hex)
        value_r, value_g, value_b = hex_to_rgb(value_color_hex)
        
        # Build complete style config like original app.py
        style_config = {
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
            "italic_values": st.session_state.get("style_italic_values", False),
            "center_text": st.session_state.get("style_center_text", False),
            "show_keys": st.session_state.get("style_show_keys", True),
            "show_values": True,
        }
        
        # Use exact same process as original app.py
        lines = [f"{key}: {value}" for key, value in current_label.items()]
        style_props = extract_style_properties(style_config)
        preview_lines = create_preview_lines(lines, style_props)
        preview_html = build_preview_html(preview_lines, width_in, height_in, False, style_props)
        st.markdown(preview_html, unsafe_allow_html=True)
    
    # Download PDF section
    current_label = {entry["key"]: entry["value"] for entry in st.session_state.manual_entries if entry["key"] or entry["value"]}
    all_labels = st.session_state.current_labels.copy()
    if current_label:
        all_labels.append(current_label)
    
    if all_labels:
        # Use the same style config as preview
        if st.session_state.get("style_units") == "Metric":
            width_in = st.session_state.get("style_width_cm", 6.7) / INCHES_TO_CM
            height_in = st.session_state.get("style_height_cm", 2.5) / INCHES_TO_CM
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
            "italic_values": st.session_state.get("style_italic_values", False),
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
            type="primary"
        )
    
    # Save section
    st.subheader("Save")
    
    current_label = {entry["key"]: entry["value"] for entry in st.session_state.manual_entries if entry["key"]}
    
    if current_label:
        save_option = st.selectbox("Save option:", ["Save Label", "Copy & Save N Times"])
        
        if save_option == "Save Label":
            label_name = st.text_input("Label name:", value=f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            if st.button("💾 Save Label"):
                label_file = LABELS_DIR / f"{label_name}.json"
                with open(label_file, 'w') as f:
                    json.dump(current_label, f, indent=2)
                
                st.session_state.current_labels.append(current_label)
                st.session_state.manual_entries = [{"key": "", "value": ""}]
                
                st.success(f"Label '{label_name}' saved!")
                st.rerun()
        
        elif save_option == "Copy & Save N Times":
            num_copies = st.number_input("Number of copies:", min_value=1, max_value=100, value=5)
            base_name = st.text_input("Base name:", value=f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            if st.button("💾 Copy & Save"):
                saved_labels = []
                
                for i in range(num_copies):
                    label_copy = current_label.copy()
                    label_name = f"{base_name}_{i+1:03d}"
                    
                    label_copy["Copy_ID"] = str(uuid.uuid4())[:8]
                    label_copy["Copy_Number"] = f"{i+1} of {num_copies}"
                    
                    label_file = LABELS_DIR / f"{label_name}.json"
                    with open(label_file, 'w') as f:
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
                with st.expander(f"Label {i+1}"):
                    for key, value in label.items():
                        st.write(f"**{key}**: {value}")

if __name__ == "__main__":
    main()