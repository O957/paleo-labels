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

# Default style configuration
DEFAULT_STYLE = {
    "font_name": "Times-Roman",
    "font_size": 10,
    "key_color": "#000000",
    "value_color": "#000000", 
    "width_inches": 2.625,
    "height_inches": 1.0,
    "padding_percent": 0.05,
    "bold_keys": True,
    "bold_values": False,
    "italic_keys": False,
    "italic_values": False,
    "show_keys": True,
    "show_values": True,
    "center_text": False,
    "show_border": True
}

# Label types will be loaded from TOML files
LABEL_TYPES = {}

def convert_key_name(underscore_key):
    """Convert underscore_key to 'Proper Key Name' format."""
    return underscore_key.replace('_', ' ').title()

def load_label_types():
    """Load label types from TOML files in label_templates directory."""
    label_types = {}
    
    if STYLE_DIR.exists():
        # Look for TOML files that define label types (not style files)
        for toml_file in STYLE_DIR.glob("*.toml"):
            # Skip style files
            if any(style_word in toml_file.name.lower() for style_word in ['style', 'default']):
                continue
                
            try:
                with open(toml_file, 'rb') as f:
                    toml_data = tomli.load(f)
                
                # Check if this is a label type file
                if 'label_type' in toml_data and 'fields' in toml_data:
                    label_type_name = toml_data['label_type']['name']
                    field_keys = list(toml_data['fields'].keys())
                    
                    # Convert underscore keys to proper names
                    proper_field_names = [convert_key_name(key) for key in field_keys]
                    
                    label_types[label_type_name] = {
                        'fields': proper_field_names,
                        'raw_keys': field_keys,  # Keep original keys for reference
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
    
    # Get from existing labels
    for label in get_existing_labels():
        for key, value in label["data"].items():
            if "scientific" in key.lower() and value.strip():
                if not partial_value or partial_value.lower() in value.lower():
                    suggestions.add(value.strip())
    
    # Get from PBDB
    if partial_value and len(partial_value) >= 2:
        pbdb_suggestions = get_pbdb_suggestions(partial_value)
        suggestions.update(pbdb_suggestions)
    
    return sorted(list(suggestions))

def load_style_files():
    """Load available style files (only files with 'style' in the name)."""
    styles = {"Default Style": DEFAULT_STYLE}
    
    if STYLE_DIR.exists():
        for style_file in STYLE_DIR.glob("*.toml"):
            # Only include files with 'style' in the name
            if 'style' not in style_file.name.lower():
                continue
                
            try:
                with open(style_file, 'rb') as f:
                    style_data = tomli.load(f)
                
                # Convert to consistent format
                converted_style = DEFAULT_STYLE.copy()
                
                # Handle different TOML formats
                if 'dimensions' in style_data:
                    converted_style.update({
                        "width_inches": style_data['dimensions'].get('width_inches', DEFAULT_STYLE['width_inches']),
                        "height_inches": style_data['dimensions'].get('height_inches', DEFAULT_STYLE['height_inches']),
                        "padding_percent": style_data['dimensions'].get('padding_percent', DEFAULT_STYLE['padding_percent']),
                    })
                
                if 'typography' in style_data:
                    converted_style.update({
                        "font_name": style_data['typography'].get('font_name', DEFAULT_STYLE['font_name']),
                        "font_size": style_data['typography'].get('font_size', DEFAULT_STYLE['font_size']),
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
                        "bold_keys": style_data['style'].get('bold_keys', DEFAULT_STYLE['bold_keys']),
                        "bold_values": style_data['style'].get('bold_values', DEFAULT_STYLE['bold_values']),
                        "italic_keys": style_data['style'].get('italic_keys', DEFAULT_STYLE['italic_keys']),
                        "italic_values": style_data['style'].get('italic_values', DEFAULT_STYLE['italic_values']),
                        "show_keys": style_data['style'].get('show_keys', DEFAULT_STYLE['show_keys']),
                        "show_values": style_data['style'].get('show_values', DEFAULT_STYLE['show_values']),
                    })
                
                # Handle flat format (like label_style_01.toml)
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
        # Key suggestions
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
            # Create label text with field name
            value_label = f"Value {index + 1}"
            if actual_key:
                value_label += f" ({actual_key})"
            
            # Special handling for Scientific Name
            if "scientific" in actual_key.lower() and "name" in actual_key.lower():
                # Use text input with dynamic suggestions for Scientific Name
                typed_value = st.text_input(
                    value_label + ":",
                    value=current_value,
                    key=f"value_text_{index}",
                    help="Type to search existing labels and paleobiology database"
                )
                
                # Show suggestions as user types
                if typed_value and len(typed_value) >= 2:
                    suggestions = get_scientific_name_suggestions(typed_value)
                    if suggestions:
                        st.write("**Suggestions:**")
                        # Show top 5 suggestions as buttons
                        for i, suggestion in enumerate(suggestions[:5]):
                            if st.button(f"🔍 {suggestion}", key=f"suggestion_{index}_{i}"):
                                st.session_state.manual_entries[index]["value"] = suggestion
                                st.rerun()
                
                actual_value = typed_value
            
            else:
                # Regular selectbox for other fields
                value_options = ["New", "Empty"]
                
                # Add previous values for this key
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

def create_pdf_from_labels(labels_data, style_config=None):
    """Create PDF from labels data with style configuration."""
    if style_config is None:
        style_config = DEFAULT_STYLE
        
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Use style dimensions
    label_width = style_config.get('width_inches', 2.625) * inch
    label_height = style_config.get('height_inches', 1.0) * inch
    margin_left = 0.1875 * inch
    margin_top = 0.5 * inch
    labels_per_row = 3
    labels_per_col = 10
    
    # Style settings
    font_name = style_config.get('font_name', 'Helvetica')
    font_size = style_config.get('font_size', 8)
    padding_percent = style_config.get('padding_percent', 0.05)
    padding = label_width * padding_percent
    
    # Process fonts like original app.py
    def get_font_name(base_font, is_bold, is_italic):
        """Get proper font name with bold/italic variants."""
        if is_bold and is_italic:
            if "Times" in base_font:
                return f"{base_font.split('-')[0]}-BoldItalic"
            else:
                return f"{base_font.split('-')[0]}-BoldOblique"
        elif is_bold:
            return f"{base_font.split('-')[0]}-Bold"
        elif is_italic:
            if "Times" in base_font:
                return f"{base_font.split('-')[0]}-Italic"
            else:
                return f"{base_font.split('-')[0]}-Oblique"
        return base_font
    
    key_font = get_font_name(font_name, style_config.get('bold_keys', True), style_config.get('italic_keys', False))
    value_font = get_font_name(font_name, style_config.get('bold_values', False), style_config.get('italic_values', False))
    show_keys = style_config.get('show_keys', True)
    show_values = style_config.get('show_values', True)
    
    # Colors - convert hex to RGB tuples like original app.py
    key_color_hex = style_config.get('key_color', '#000000')
    value_color_hex = style_config.get('value_color', '#000000')
    
    def hex_to_rgb_tuple(hex_color):
        """Convert hex color to RGB tuple (0-1 range)."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return (r/255.0, g/255.0, b/255.0)
        return (0.0, 0.0, 0.0)
    
    def hex_to_color(hex_color):
        """Convert hex color to reportlab Color object."""
        r, g, b = hex_to_rgb_tuple(hex_color)
        return colors.Color(r, g, b)
    
    key_color = hex_to_rgb_tuple(key_color_hex)
    value_color = hex_to_rgb_tuple(value_color_hex)
    key_color_obj = hex_to_color(key_color_hex)
    value_color_obj = hex_to_color(value_color_hex)
    
    current_label = 0
    
    for label_data in labels_data:
        if current_label > 0 and current_label % (labels_per_row * labels_per_col) == 0:
            c.showPage()
        
        row = (current_label % (labels_per_row * labels_per_col)) // labels_per_row
        col = current_label % labels_per_row
        
        x = margin_left + col * label_width
        y = letter[1] - margin_top - label_height - row * label_height
        
        # Draw border if enabled
        if style_config.get('show_border', True):
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.rect(x, y, label_width, label_height)
        
        # Draw label content with styling
        text_y = y + label_height - font_size - padding
        line_height = font_size + 2
        center_text = style_config.get('center_text', False)
        
        # Create lines from label data like original app.py
        lines = []
        for key, value in label_data.items():
            if not key and not value:
                continue
            if not key and value:
                lines.append(value)
            elif key:
                lines.append(f"{key}: {value if value else ''}")
        
        for line in lines:
            if text_y < y + padding:  # Don't overflow label
                break
            
            if ": " in line and (show_keys or show_values):
                key_part, value_part = line.split(": ", 1)
                parts_to_draw = []
                
                if show_keys:
                    key_text = f"{key_part}: "
                    parts_to_draw.append((key_text, key_font, key_color_obj))
                
                if show_values:
                    if not value_part or value_part.strip() == "":
                        # Calculate underline to padding border
                        available_width = label_width - 2 * padding
                        used_width = 0
                        for text, font, _ in parts_to_draw:
                            used_width += c.stringWidth(text, font, font_size)
                        underline_width = available_width - used_width
                        char_width = c.stringWidth("_", value_font, font_size)
                        underline_chars = max(1, int(underline_width / char_width))
                        value_text = "_" * underline_chars
                    else:
                        value_text = value_part
                    parts_to_draw.append((value_text, value_font, value_color_obj))
                
                # Draw all parts
                if center_text:
                    total_width = sum(c.stringWidth(text, font, font_size) for text, font, _ in parts_to_draw)
                    text_x = x + (label_width - total_width) / 2
                else:
                    text_x = x + padding
                
                for text, font, color in parts_to_draw:
                    c.setFillColor(color)
                    c.setFont(font, font_size)
                    c.drawString(text_x, text_y, text)
                    text_x += c.stringWidth(text, font, font_size)
            else:
                # Single line (no colon or only showing keys/values)
                c.setFillColor(key_color_obj)
                c.setFont(key_font, font_size)
                
                if center_text:
                    text_width = c.stringWidth(line, key_font, font_size)
                    text_x = x + (label_width - text_width) / 2
                else:
                    text_x = x + padding
                    
                c.drawString(text_x, text_y, line)
            
            text_y -= line_height
                # Prepare key font with bold/italic
                key_font = font_name
                if style_config.get('bold_keys', True) and style_config.get('italic_keys', False):
                    if "Times" in font_name:
                        key_font += "-BoldItalic"
                    else:
                        key_font += "-BoldOblique"
                elif style_config.get('bold_keys', True):
                    key_font += "-Bold"
                elif style_config.get('italic_keys', False):
                    if "Times" in font_name:
                        key_font += "-Italic"
                    else:
                        key_font += "-Oblique"
                
                # Use available fonts - ReportLab supports these built-in fonts
                available_fonts = [
                    'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique', 'Helvetica-BoldOblique',
                    'Times-Roman', 'Times-Bold', 'Times-Italic', 'Times-BoldItalic',
                    'Courier', 'Courier-Bold', 'Courier-Oblique', 'Courier-BoldOblique'
                ]
                if key_font not in available_fonts:
                    # Fallback to base font
                    key_font = font_name
                
                c.setFillColor(key_color_obj)
                c.setFont(key_font, font_size)
                
                if style_config.get('show_values', True):
                    key_text = f"{key}: "
                    
                    # Prepare value font with bold/italic
                    value_font = font_name
                    if style_config.get('bold_values', False) and style_config.get('italic_values', False):
                        if "Times" in font_name:
                            value_font += "-BoldItalic"
                        else:
                            value_font += "-BoldOblique"
                    elif style_config.get('bold_values', False):
                        value_font += "-Bold"
                    elif style_config.get('italic_values', False):
                        if "Times" in font_name:
                            value_font += "-Italic"
                        else:
                            value_font += "-Oblique"
                    
                    # Use available fonts
                    if value_font not in available_fonts:
                        value_font = font_name
                    
                    if value:
                        value_text = value
                    else:
                        # Calculate underline length to padding border
                        available_width = label_width - 2 * padding
                        key_width = c.stringWidth(key_text, key_font, font_size)
                        underline_width = available_width - key_width
                        char_width = c.stringWidth("_", value_font, font_size)
                        underline_chars = max(1, int(underline_width / char_width))
                        value_text = "_" * underline_chars
                    full_text = key_text + value_text
                    
                    if center_text:
                        # Center the full text
                        text_width = c.stringWidth(full_text, key_font, font_size)  # Approximate
                        text_x = x + (label_width - text_width) / 2
                    else:
                        text_x = x + padding
                    
                    # Draw key part
                    c.drawString(text_x, text_y, key_text)
                    key_width = c.stringWidth(key_text, key_font, font_size)
                    
                    # Draw value part
                    c.setFillColor(value_color_obj)
                    c.setFont(value_font, font_size)
                    c.drawString(text_x + key_width, text_y, value_text)
                else:
                    # Just key with calculated underline
                    if value:
                        key_text = f"{key}: {value}"
                    else:
                        # Calculate underline length to padding border
                        available_width = label_width - 2 * padding
                        key_prefix = f"{key}: "
                        key_prefix_width = c.stringWidth(key_prefix, key_font, font_size)
                        underline_width = available_width - key_prefix_width
                        char_width = c.stringWidth("_", key_font, font_size)
                        underline_chars = max(1, int(underline_width / char_width))
                        key_text = key_prefix + "_" * underline_chars
                    
                    if center_text:
                        text_width = c.stringWidth(key_text, key_font, font_size)
                        text_x = x + (label_width - text_width) / 2
                    else:
                        text_x = x + padding
                        
                    c.drawString(text_x, text_y, key_text)
                    
            elif key and not style_config.get('show_keys', True) and style_config.get('show_values', True) and value:
                # Just value
                value_font = font_name
                if style_config.get('bold_values', False) and style_config.get('italic_values', False):
                    value_font += "-BoldOblique"
                elif style_config.get('bold_values', False):
                    value_font += "-Bold"
                elif style_config.get('italic_values', False):
                    value_font += "-Oblique"
                
                if value_font not in available_fonts:
                    value_font = font_name
                
                c.setFillColor(value_color_obj)
                c.setFont(value_font, font_size)
                
                if center_text:
                    text_width = c.stringWidth(value, value_font, font_size)
                    text_x = x + (label_width - text_width) / 2
                else:
                    text_x = x + padding
                    
                c.drawString(text_x, text_y, value)
            
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
    
    # Load label types from TOML files
    if "loaded_label_types" not in st.session_state:
        st.session_state.loaded_label_types = load_label_types()
        st.session_state.loaded_label_types_loaded = True
    
    # Fill With section
    st.subheader("Fill With")
    col1, col2 = st.columns(2)
    
    with col1:
        fill_option = st.selectbox("Fill with:", ["None", "Label Type", "Existing Label", "Upload Label TOML"])
        
        if fill_option == "Label Type":
            available_types = list(st.session_state.loaded_label_types.keys())
            if available_types:
                selected_type = st.selectbox("Select Label Type:", available_types)
                
                # Show description if available
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
                    
                    # Handle label type files with fields section
                    if 'fields' in label_data:
                        entries = []
                        for key, value in label_data['fields'].items():
                            proper_key = convert_key_name(key)
                            entries.append({"key": proper_key, "value": str(value) if value else ""})
                        st.session_state.manual_entries = entries
                    else:
                        # Handle direct key-value pairs
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
        # Update the entry in place
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
    
    # Style Options section
    st.subheader("Style Options")
    
    # Initialize style session state
    if "current_style" not in st.session_state:
        st.session_state.current_style = DEFAULT_STYLE.copy()
    
    # Ensure all required style keys are present
    for key, default_value in DEFAULT_STYLE.items():
        if key not in st.session_state.current_style:
            st.session_state.current_style[key] = default_value
    
    # Load available styles
    available_styles = load_style_files()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Style preset selector
        style_names = list(available_styles.keys())
        # Default to "Default Style"
        default_index = 0
        if "Default Style" in style_names:
            default_index = style_names.index("Default Style")
            
        selected_style = st.selectbox("Style Preset:", style_names, index=default_index, key="style_preset")
        
        if selected_style and available_styles[selected_style] != st.session_state.current_style:
            st.session_state.current_style = available_styles[selected_style].copy()
            st.rerun()
    
    with col2:
        # Custom style upload
        uploaded_style = st.file_uploader("Upload Custom Style:", type=['toml'], key="custom_style")
        if uploaded_style:
            try:
                style_content = uploaded_style.read().decode('utf-8')
                custom_style = tomli.loads(style_content)
                
                # Convert custom style to our format using same logic as load_style_files
                converted_style = DEFAULT_STYLE.copy()
                
                # Handle different TOML formats
                if 'dimensions' in custom_style:
                    converted_style.update({
                        "width_inches": custom_style['dimensions'].get('width_inches', DEFAULT_STYLE['width_inches']),
                        "height_inches": custom_style['dimensions'].get('height_inches', DEFAULT_STYLE['height_inches']),
                        "padding_percent": custom_style['dimensions'].get('padding_percent', DEFAULT_STYLE['padding_percent']),
                    })
                
                if 'typography' in custom_style:
                    converted_style.update({
                        "font_name": custom_style['typography'].get('font_name', DEFAULT_STYLE['font_name']),
                        "font_size": custom_style['typography'].get('font_size', DEFAULT_STYLE['font_size']),
                    })
                
                if 'colors' in custom_style:
                    colors_data = custom_style['colors']
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
                
                if 'style' in custom_style:
                    converted_style.update({
                        "bold_keys": custom_style['style'].get('bold_keys', DEFAULT_STYLE['bold_keys']),
                        "bold_values": custom_style['style'].get('bold_values', DEFAULT_STYLE['bold_values']),
                        "italic_keys": custom_style['style'].get('italic_keys', DEFAULT_STYLE['italic_keys']),
                        "italic_values": custom_style['style'].get('italic_values', DEFAULT_STYLE['italic_values']),
                        "show_keys": custom_style['style'].get('show_keys', DEFAULT_STYLE['show_keys']),
                        "show_values": custom_style['style'].get('show_values', DEFAULT_STYLE['show_values']),
                    })
                
                # Handle flat format
                for key in ['font_name', 'font_size', 'width_inches', 'height_inches', 'padding_percent',
                           'bold_keys', 'bold_values', 'italic_keys', 'italic_values', 'center_text', 'show_border']:
                    if key in custom_style:
                        converted_style[key] = custom_style[key]
                
                # Handle flat color format
                if all(k in custom_style for k in ['key_color_r', 'key_color_g', 'key_color_b']):
                    key_r = int(custom_style['key_color_r'] * 255) if custom_style['key_color_r'] <= 1 else int(custom_style['key_color_r'])
                    key_g = int(custom_style['key_color_g'] * 255) if custom_style['key_color_g'] <= 1 else int(custom_style['key_color_g'])
                    key_b = int(custom_style['key_color_b'] * 255) if custom_style['key_color_b'] <= 1 else int(custom_style['key_color_b'])
                    converted_style['key_color'] = f"#{key_r:02x}{key_g:02x}{key_b:02x}"
                
                if all(k in custom_style for k in ['value_color_r', 'value_color_g', 'value_color_b']):
                    val_r = int(custom_style['value_color_r'] * 255) if custom_style['value_color_r'] <= 1 else int(custom_style['value_color_r'])
                    val_g = int(custom_style['value_color_g'] * 255) if custom_style['value_color_g'] <= 1 else int(custom_style['value_color_g'])
                    val_b = int(custom_style['value_color_b'] * 255) if custom_style['value_color_b'] <= 1 else int(custom_style['value_color_b'])
                    converted_style['value_color'] = f"#{val_r:02x}{val_g:02x}{val_b:02x}"
                
                st.session_state.current_style = converted_style
                st.success("Custom style loaded!")
                st.rerun()  # Force rerun to update UI with new values
            except Exception as e:
                st.error(f"Error loading style: {e}")
    
    # Style customization options
    st.write("**Customize Style:**")
    
    # Unit system selector
    unit_system = st.radio(
        "Units:", ["Imperial (inches)", "Metric (cm)"], 
        horizontal=True, key="style_units"
    )
    is_metric = unit_system == "Metric (cm)"
    
    # Initialize unit system in session state if needed
    if "style_unit_system" not in st.session_state:
        st.session_state.style_unit_system = unit_system
    
    # Convert dimensions if unit system changed
    if st.session_state.style_unit_system != unit_system:
        if is_metric and st.session_state.style_unit_system == "Imperial (inches)":
            # Convert from inches to cm
            st.session_state.current_style["width_inches"] = st.session_state.current_style.get("width_inches", 2.625) / INCHES_TO_CM
            st.session_state.current_style["height_inches"] = st.session_state.current_style.get("height_inches", 1.0) / INCHES_TO_CM
        elif not is_metric and st.session_state.style_unit_system == "Metric (cm)":
            # Convert from cm to inches  
            st.session_state.current_style["width_inches"] = st.session_state.current_style.get("width_inches", 2.625) * INCHES_TO_CM
            st.session_state.current_style["height_inches"] = st.session_state.current_style.get("height_inches", 1.0) * INCHES_TO_CM
        st.session_state.style_unit_system = unit_system
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.write("**Dimensions**")
        if is_metric:
            # Metric inputs
            width_cm = st.session_state.current_style.get("width_inches", 2.625) * INCHES_TO_CM
            height_cm = st.session_state.current_style.get("height_inches", 1.0) * INCHES_TO_CM
            
            new_width_cm = st.number_input(
                "Width (cm):", min_value=1.0, max_value=20.0, value=width_cm, step=0.1, key="style_width_cm"
            )
            new_height_cm = st.number_input(
                "Height (cm):", min_value=1.0, max_value=15.0, value=height_cm, step=0.1, key="style_height_cm"
            )
            
            # Convert and store as inches internally
            width_inches = new_width_cm / INCHES_TO_CM
            height_inches = new_height_cm / INCHES_TO_CM
            st.session_state.current_style["width_inches"] = width_inches
            st.session_state.current_style["height_inches"] = height_inches
        else:
            # Imperial inputs
            width_in = st.session_state.current_style.get("width_inches", 2.625)
            height_in = st.session_state.current_style.get("height_inches", 1.0)
            
            width_inches = st.number_input(
                "Width (in):", min_value=0.5, max_value=8.0, value=width_in, step=0.05, key="style_width_in"
            )
            height_inches = st.number_input(
                "Height (in):", min_value=0.5, max_value=6.0, value=height_in, step=0.05, key="style_height_in"
            )
            st.session_state.current_style["width_inches"] = width_inches
            st.session_state.current_style["height_inches"] = height_inches
    
    with col2:
        st.write("**Typography**")
        font_options = ["Times-Roman", "Helvetica", "Courier"]
        current_font = st.session_state.current_style.get("font_name", "Times-Roman")
        if current_font not in font_options:
            current_font = "Times-Roman"
        font_name = st.selectbox(
            "Font:", font_options, 
            index=font_options.index(current_font),
            key="style_font"
        )
        font_size = st.slider(
            "Font Size:", 6, 20, st.session_state.current_style.get("font_size", 10), key="style_font_size"
        )
        
        # Update session state
        st.session_state.current_style["font_name"] = font_name
        st.session_state.current_style["font_size"] = font_size
    
    with col3:
        st.write("**Colors**")
        key_color = st.color_picker(
            "Field Color:", st.session_state.current_style.get("key_color", "#000000"), key="style_key_color"
        )
        value_color = st.color_picker(
            "Value Color:", st.session_state.current_style.get("value_color", "#000000"), key="style_value_color"
        )
        
        # Update session state
        st.session_state.current_style["key_color"] = key_color
        st.session_state.current_style["value_color"] = value_color
    
    with col4:
        st.write("**Formatting**")
        bold_keys = st.checkbox(
            "Bold Fields", st.session_state.current_style.get("bold_keys", True), key="style_bold_keys"
        )
        bold_values = st.checkbox(
            "Bold Values", st.session_state.current_style.get("bold_values", False), key="style_bold_values"
        )
        italic_keys = st.checkbox(
            "Italic Fields", st.session_state.current_style.get("italic_keys", False), key="style_italic_keys"
        )
        italic_values = st.checkbox(
            "Italic Values", st.session_state.current_style.get("italic_values", False), key="style_italic_values"
        )
        center_text = st.checkbox(
            "Center Text", st.session_state.current_style.get("center_text", False), key="style_center_text"
        )
        show_keys = st.checkbox(
            "Show Field Names", st.session_state.current_style.get("show_keys", True), key="style_show_keys"
        )
        padding_percent = st.slider(
            "Padding %:", 0.01, 0.2, st.session_state.current_style.get("padding_percent", 0.05), step=0.01, key="style_padding"
        )
        
        # Update session state
        st.session_state.current_style.update({
            "bold_keys": bold_keys,
            "bold_values": bold_values, 
            "italic_keys": italic_keys,
            "italic_values": italic_values,
            "center_text": center_text,
            "show_keys": show_keys,
            "padding_percent": padding_percent
        })
    
    # Current label preview with styling
    if any(entry["key"] or entry["value"] for entry in st.session_state.manual_entries):
        st.subheader("Current Label Preview")
        current_label = {entry["key"]: entry["value"] for entry in st.session_state.manual_entries if entry["key"] or entry["value"]}
        
        # Apply style to preview with accurate dimensions
        style_config = st.session_state.current_style
        
        # Display current dimensions
        width_in = style_config.get("width_inches", 2.625)
        height_in = style_config.get("height_inches", 1.0)
        width_cm = width_in * INCHES_TO_CM
        height_cm = height_in * INCHES_TO_CM
        
        st.write(f"**Label Size**: {width_in:.3f}\" × {height_in:.3f}\" ({width_cm:.1f}cm × {height_cm:.1f}cm)")
        
        # Calculate preview dimensions using proper scaling (matches app.py)
        preview_width = int(width_in * PREVIEW_SCALE)
        preview_height = int(height_in * PREVIEW_SCALE)
        border_width = max(1, int(PREVIEW_SCALE / POINTS_PER_INCH))
        padding_x = int(preview_width * style_config.get("padding_percent", 0.05))
        padding_y = int(preview_height * style_config.get("padding_percent", 0.05))
        
        # Determine text alignment
        text_align = "center" if style_config.get("center_text", False) else "left"
        
        # Calculate font size for preview (matches app.py scaling)
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
        
        # Convert boolean style properties to CSS strings (like original app.py)
        key_weight = "bold" if style_config.get("bold_keys", True) else "normal"
        value_weight = "bold" if style_config.get("bold_values", False) else "normal"
        key_style = "italic" if style_config.get("italic_keys", False) else "normal"
        value_style = "italic" if style_config.get("italic_values", False) else "normal"
        key_color = style_config.get("key_color", "#000000")
        value_color = style_config.get("value_color", "#000000")
        
        # Create formatted lines like original app.py
        lines = []
        for key, value in current_label.items():
            if not key and not value:
                continue
            if not key and value:
                lines.append(value)
            elif key:
                lines.append(f"{key}: {value if value else '_' * 10}")
        
        preview_html = f"<div style='border: {border_width}px solid #cccccc; width: {preview_width}px; height: {preview_height}px; margin: 20px auto; background: white; position: relative; overflow: hidden; box-sizing: border-box;'>"
        preview_html += f"<div style='position: absolute; top: {padding_y}px; left: {padding_x}px; width: {preview_width - 2*padding_x}px; height: {preview_height - 2*padding_y}px; text-align: {text_align};'>"
        
        for line in lines:
            if ": " in line and (style_config.get("show_keys", True) or style_config.get("show_values", True)):
                key_part, value_part = line.split(": ", 1)
                parts = []
                if style_config.get("show_keys", True):
                    key_span = f'<span style="color: {key_color}; font-weight: {key_weight}; font-style: {key_style}; font-size: {preview_font_size}px; font-family: {css_font_family};">{key_part}: </span>'
                    parts.append(key_span)
                if style_config.get("show_values", True):
                    value_span = f'<span style="color: {value_color}; font-weight: {value_weight}; font-style: {value_style}; font-size: {preview_font_size}px; font-family: {css_font_family};">{value_part}</span>'
                    parts.append(value_span)
                preview_html += f'<div style="margin: 2px 0; line-height: 1.4;">{"".join(parts)}</div>'
            else:
                # No colon or showing just value
                line_span = f'<span style="color: {key_color}; font-weight: {key_weight}; font-style: {key_style}; font-size: {preview_font_size}px; font-family: {css_font_family};">{line}</span>'
                preview_html += f'<div style="margin: 2px 0; line-height: 1.4;">{line_span}</div>'
                
        preview_html += "</div></div>"
        st.markdown(preview_html, unsafe_allow_html=True)
    
    # Download PDF section
    current_label = {entry["key"]: entry["value"] for entry in st.session_state.manual_entries if entry["key"] or entry["value"]}
    all_labels = st.session_state.current_labels.copy()
    if current_label:
        all_labels.append(current_label)
    
    if all_labels:
        pdf_bytes = create_pdf_from_labels(all_labels, st.session_state.current_style)
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
                # Save to file
                label_file = LABELS_DIR / f"{label_name}.json"
                with open(label_file, 'w') as f:
                    json.dump(current_label, f, indent=2)
                
                # Add to session
                st.session_state.current_labels.append(current_label)
                
                # Clear manual entry
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
                    
                    # Add unique ID
                    label_copy["Copy_ID"] = str(uuid.uuid4())[:8]
                    label_copy["Copy_Number"] = f"{i+1} of {num_copies}"
                    
                    # Save to file
                    label_file = LABELS_DIR / f"{label_name}.json"
                    with open(label_file, 'w') as f:
                        json.dump(label_copy, f, indent=2)
                    
                    saved_labels.append(label_copy)
                
                # Add all to session
                st.session_state.current_labels.extend(saved_labels)
                
                # Clear manual entry
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