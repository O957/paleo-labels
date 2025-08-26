"""
Ultra-Simplified Paleo Labels App
Single interface following exact user specification for maximum simplicity.
"""

import streamlit as st
import json
import polars as pl
import requests
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from io import BytesIO
import uuid

# Initialize storage paths
LABELS_DIR = Path.home() / ".paleo_labels" / "labels"
LABELS_DIR.mkdir(parents=True, exist_ok=True)

# Label type schemas - simplified
LABEL_TYPES = {
    "Specimen": ["Specimen Number", "Scientific Name", "Locality", "Collection Date", "Collector"],
    "Locality": ["Locality", "Country", "State", "Formation", "Age", "Coordinates"], 
    "Taxonomy": ["Scientific Name", "Genus", "Species", "Family", "Order", "Class"],
    "Collection": ["Collection Name", "Institution", "Curator", "Date", "Project"],
}

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

def render_key_value_input(index, current_key="", current_value=""):
    """Render a key-value input pair with smart suggestions."""
    col1, col2 = st.columns(2)
    
    with col1:
        # Key suggestions
        all_keys = set()
        for label in get_existing_labels():
            all_keys.update(label["data"].keys())
        
        key_options = ["New"] + sorted(list(all_keys))
        
        if current_key and current_key not in key_options:
            key_options.append(current_key)
        
        selected_key = st.selectbox(
            f"Key {index + 1}:",
            key_options,
            index=key_options.index(current_key) if current_key in key_options else 0,
            key=f"key_select_{index}"
        )
        
        if selected_key == "New":
            actual_key = st.text_input("Enter new key:", value=current_key if current_key != "New" else "", key=f"key_new_{index}")
        else:
            actual_key = selected_key
    
    with col2:
        if actual_key:
            # Special handling for Scientific Name
            if "scientific" in actual_key.lower() and "name" in actual_key.lower():
                # Use text input with dynamic suggestions for Scientific Name
                typed_value = st.text_input(
                    f"Value {index + 1} (Scientific Name):",
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
                value_options = ["New"]
                
                # Add previous values for this key
                prev_values = get_previous_values(actual_key)
                value_options.extend(prev_values)
                
                if current_value and current_value not in value_options:
                    value_options.append(current_value)
                
                selected_value = st.selectbox(
                    f"Value {index + 1}:",
                    value_options,
                    index=value_options.index(current_value) if current_value in value_options else 0,
                    key=f"value_select_{index}"
                )
                
                if selected_value == "New":
                    actual_value = st.text_input("Enter new value:", value=current_value if current_value != "New" else "", key=f"value_new_{index}")
                else:
                    actual_value = selected_value
        else:
            actual_value = ""
    
    return actual_key, actual_value

def create_pdf_from_labels(labels_data):
    """Create PDF from labels data."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Simple layout - 3x10 labels per page (Avery 5160 style)
    label_width = 2.625 * inch
    label_height = 1 * inch
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
        
        # Draw label content
        c.setFont("Helvetica", 8)
        text_y = y + label_height - 12
        
        for key, value in label_data.items():
            if text_y < y + 4:  # Don't overflow label
                break
            text = f"{key}: {value}" if value else f"{key}: ___________"
            c.drawString(x + 4, text_y, text)
            text_y -= 10
        
        current_label += 1
    
    c.save()
    return buffer.getvalue()

def main():
    st.set_page_config(page_title="Paleo Labels - Ultra Simple", page_icon="🏷️", layout="wide")
    st.title("🏷️ Paleo Labels - Ultra Simple")
    
    # Initialize session state
    if "current_labels" not in st.session_state:
        st.session_state.current_labels = []
    if "manual_entries" not in st.session_state:
        st.session_state.manual_entries = [{"key": "", "value": ""}]
    
    # Fill With section
    st.subheader("Fill With")
    col1, col2 = st.columns(2)
    
    with col1:
        fill_option = st.selectbox("Fill with:", ["None", "Label Type", "Existing Label"])
        
        if fill_option == "Label Type":
            selected_type = st.selectbox("Select Label Type:", list(LABEL_TYPES.keys()))
            if st.button("Load Label Type Fields"):
                st.session_state.manual_entries = [{"key": key, "value": ""} for key in LABEL_TYPES[selected_type]]
                st.rerun()
        
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
    
    # Manual Entry section
    st.subheader("Manual Entry")
    
    # Render current entries
    updated_entries = []
    for i, entry in enumerate(st.session_state.manual_entries):
        key, value = render_key_value_input(i, entry["key"], entry["value"])
        if key or value:  # Only keep non-empty entries
            updated_entries.append({"key": key, "value": value})
    
    st.session_state.manual_entries = updated_entries
    
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
    
    # Current label preview
    if any(entry["key"] for entry in st.session_state.manual_entries):
        st.subheader("Current Label Preview")
        current_label = {entry["key"]: entry["value"] for entry in st.session_state.manual_entries if entry["key"]}
        for key, value in current_label.items():
            st.write(f"**{key}**: {value if value else '_____________'}")
    
    # Export PDF section
    st.subheader("Export PDF")
    
    total_labels = len(st.session_state.current_labels) + (1 if any(entry["key"] for entry in st.session_state.manual_entries) else 0)
    st.write(f"**Current labels in session**: {total_labels}")
    
    if total_labels > 0:
        if st.button("📄 Export PDF", type="primary"):
            # Combine current manual entry with saved session labels
            all_labels = st.session_state.current_labels.copy()
            current_label = {entry["key"]: entry["value"] for entry in st.session_state.manual_entries if entry["key"]}
            if current_label:
                all_labels.append(current_label)
            
            if all_labels:
                pdf_bytes = create_pdf_from_labels(all_labels)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    "📥 Download PDF",
                    pdf_bytes,
                    f"paleo_labels_{timestamp}.pdf",
                    "application/pdf"
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