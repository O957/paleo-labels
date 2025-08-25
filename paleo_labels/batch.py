"""
Batch label processing functionality for Phase 2.
Handles CSV import with Polars, multi-label session management, and batch loading.
"""

import io
import pathlib
from typing import Dict, List, Optional, Tuple

import streamlit as st

try:
    import polars as pl
except ImportError:
    pl = None

try:
    from .schemas import LABEL_SCHEMAS, get_schema_for_label_type, normalize_field_name
    from .storage import LabelStorage
except ImportError:
    from schemas import LABEL_SCHEMAS, get_schema_for_label_type, normalize_field_name
    from storage import LabelStorage


def process_csv_for_batch_labels(uploaded_file, label_type: str = "General") -> Tuple[List[Dict], List[str]]:
    """
    Process an uploaded CSV file into a list of label dictionaries using Polars.
    
    Returns:
        Tuple of (label_data_list, column_headers)
    """
    if pl is None:
        st.error("Polars is required for CSV processing")
        return [], []
    
    try:
        # Read CSV into Polars DataFrame
        df = pl.read_csv(uploaded_file)
        
        # Get column headers
        column_headers = df.columns
        
        # Convert each row to a dictionary
        label_data_list = []
        for row_data in df.iter_rows(named=True):
            # Filter out empty values and convert to strings
            label_data = {}
            for col, value in row_data.items():
                if value is not None and str(value).strip():
                    label_data[col] = str(value).strip()
            
            if label_data:  # Only add non-empty rows
                label_data_list.append(label_data)
        
        return label_data_list, column_headers
        
    except Exception as e:
        st.error(f"Error processing CSV: {str(e)}")
        return [], []


def create_field_mapping_ui(csv_columns: List[str], label_type: str) -> Dict[str, str]:
    """
    Create UI for mapping CSV columns to label schema fields.
    
    Returns:
        Dictionary mapping CSV columns to schema fields
    """
    st.subheader("Field Mapping")
    st.write("Map your CSV columns to label fields:")
    
    # Get schema fields for the selected label type
    if label_type != "General":
        schema = get_schema_for_label_type(label_type)
        schema_fields = list(schema.keys())
        
        # Add aliases to the options
        field_options = [""] + schema_fields
        for field, config in schema.items():
            field_options.extend(config.get("aliases", []))
    else:
        field_options = [""]
    
    # Create mapping UI
    field_mapping = {}
    
    cols = st.columns(2)
    cols[0].write("**CSV Column**")
    cols[1].write("**Maps To**")
    
    for csv_col in csv_columns:
        cols = st.columns(2)
        cols[0].write(csv_col)
        
        mapped_field = cols[1].selectbox(
            f"Map '{csv_col}' to:",
            field_options,
            key=f"map_{csv_col}",
            label_visibility="collapsed"
        )
        
        if mapped_field:
            # Normalize the field name if it's an alias
            if label_type != "General":
                normalized = normalize_field_name(label_type, mapped_field)
                field_mapping[csv_col] = normalized if normalized else mapped_field
            else:
                field_mapping[csv_col] = mapped_field
    
    return field_mapping


def apply_field_mapping(label_data_list: List[Dict], field_mapping: Dict[str, str]) -> List[Dict]:
    """
    Apply field mapping to transform CSV data into properly mapped label data.
    """
    mapped_data_list = []
    
    for label_data in label_data_list:
        mapped_data = {}
        
        for csv_col, value in label_data.items():
            # Use mapped field name if available, otherwise use original
            field_name = field_mapping.get(csv_col, csv_col)
            if field_name:  # Only include if mapped to something
                mapped_data[field_name] = value
        
        if mapped_data:
            mapped_data_list.append(mapped_data)
    
    return mapped_data_list


def generate_batch_labels_ui():
    """
    Main UI for batch label operations:
    1. Multi-label session (create multiple labels in one session)
    2. Load all labels from folder
    3. CSV import for batch creation
    """
    st.header("Batch Operations")
    
    # Batch operation tabs
    tab1, tab2, tab3 = st.tabs(["Multi-Label Session", "Load All Labels", "CSV Import"])
    
    with tab1:
        multi_label_session_ui()
    
    with tab2:
        load_all_labels_ui()
    
    with tab3:
        csv_import_ui()


def multi_label_session_ui():
    """
    UI for creating multiple labels in a single session.
    """
    st.subheader("Multi-Label Session")
    st.write("Create multiple labels quickly in a single session")
    
    # Initialize session state
    if 'multi_labels' not in st.session_state:
        st.session_state.multi_labels = []
    
    # Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Add New Label"):
            new_label = {
                'id': len(st.session_state.multi_labels),
                'type': 'General',
                'data': {},
                'name': f"Label {len(st.session_state.multi_labels) + 1}"
            }
            st.session_state.multi_labels.append(new_label)
    
    with col2:
        if st.button("🗑️ Clear All") and st.session_state.multi_labels:
            st.session_state.multi_labels = []
            st.rerun()
    
    with col3:
        if st.button("💾 Save All Labels") and st.session_state.multi_labels:
            save_all_multi_labels()
    
    # Display current labels
    if st.session_state.multi_labels:
        st.write(f"**Current Labels: {len(st.session_state.multi_labels)}**")
        
        for i, label in enumerate(st.session_state.multi_labels):
            with st.expander(f"📄 {label['name']}", expanded=i == len(st.session_state.multi_labels) - 1):
                render_multi_label_editor(i, label)
    else:
        st.info("No labels in session. Click 'Add New Label' to start.")


def render_multi_label_editor(index: int, label: Dict):
    """
    Render an individual label editor in the multi-label session.
    """
    # Label controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        new_name = st.text_input(
            "Label Name:",
            value=label['name'],
            key=f"multi_label_name_{index}"
        )
        st.session_state.multi_labels[index]['name'] = new_name
    
    with col2:
        new_type = st.selectbox(
            "Label Type:",
            list(LABEL_SCHEMAS.keys()),
            index=list(LABEL_SCHEMAS.keys()).index(label['type']),
            key=f"multi_label_type_{index}"
        )
        st.session_state.multi_labels[index]['type'] = new_type
    
    with col3:
        if st.button("🗑️", key=f"delete_multi_label_{index}", help="Delete this label"):
            st.session_state.multi_labels.pop(index)
            st.rerun()
    
    # Simple key-value editor
    st.write("**Label Data:**")
    
    # Add field button
    if st.button(f"➕ Add Field", key=f"add_field_{index}"):
        label['data'][f'field_{len(label["data"]) + 1}'] = ''
    
    # Edit existing fields
    fields_to_delete = []
    for field_key, field_value in label['data'].items():
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            new_key = st.text_input(
                "Key:",
                value=field_key,
                key=f"multi_key_{index}_{field_key}",
                label_visibility="collapsed"
            )
        
        with col2:
            new_value = st.text_input(
                "Value:",
                value=field_value,
                key=f"multi_value_{index}_{field_key}",
                label_visibility="collapsed"
            )
        
        with col3:
            if st.button("❌", key=f"del_field_{index}_{field_key}", help="Delete field"):
                fields_to_delete.append(field_key)
        
        # Update the data if key or value changed
        if new_key != field_key:
            # Key changed - remove old, add new
            label['data'].pop(field_key)
            label['data'][new_key] = new_value
        else:
            label['data'][field_key] = new_value
    
    # Delete marked fields
    for field_key in fields_to_delete:
        if field_key in label['data']:
            label['data'].pop(field_key)
    
    st.session_state.multi_labels[index] = label


def load_all_labels_ui():
    """
    UI for loading all saved labels from the folder.
    """
    st.subheader("Load All Labels")
    st.write("Load and manage all saved labels from your collection")
    
    if 'storage' not in st.session_state:
        st.error("Storage not initialized")
        return
    
    storage: LabelStorage = st.session_state.storage
    saved_labels = storage.list_labels()
    
    if not saved_labels:
        st.info("No saved labels found.")
        return
    
    st.write(f"**Found {len(saved_labels)} saved labels**")
    
    # Load all button
    if st.button("📂 Load All Labels", type="primary"):
        load_all_labels_action(saved_labels, storage)
    
    # Preview saved labels
    with st.expander("Preview Saved Labels", expanded=False):
        for label_name in saved_labels[:10]:  # Show first 10
            metadata = storage.get_metadata(label_name)
            label_type = metadata.get('label_type', 'Unknown') if metadata else 'Unknown'
            created = metadata.get('created', 'Unknown') if metadata else 'Unknown'
            st.write(f"• **{label_name}** ({label_type}) - {created}")
        
        if len(saved_labels) > 10:
            st.write(f"... and {len(saved_labels) - 10} more")


def csv_import_ui():
    """
    UI for importing labels from CSV files.
    """
    st.subheader("CSV Import")
    st.write("Import multiple labels from a CSV file")
    
    # CSV Upload
    uploaded_csv = st.file_uploader(
        "Upload CSV File",
        type=["csv"],
        help="Upload a CSV file where each row will become a separate label"
    )
    
    if uploaded_csv:
        # Process CSV
        label_data_list, csv_columns = process_csv_for_batch_labels(uploaded_csv)
        
        if not label_data_list:
            st.warning("No valid data found in CSV file.")
            return
        
        st.success(f"Loaded {len(label_data_list)} rows from CSV")
        
        # Preview first few rows using Polars display
        with st.expander("Preview Data", expanded=True):
            if pl is not None:
                preview_df = pl.DataFrame(label_data_list[:5])  # Show first 5 rows
                st.dataframe(preview_df.to_pandas())  # Convert to pandas for streamlit display
            if len(label_data_list) > 5:
                st.info(f"Showing first 5 of {len(label_data_list)} rows")
        
        # Label Type Selection
        st.subheader("Label Configuration")
        
        batch_label_type = st.selectbox(
            "Label Type for Batch",
            list(LABEL_SCHEMAS.keys()),
            key="batch_label_type"
        )
        
        # Field Mapping
        field_mapping = create_field_mapping_ui(csv_columns, batch_label_type)
        
        if field_mapping:
            # Apply mapping and preview
            mapped_data_list = apply_field_mapping(label_data_list, field_mapping)
            
            st.subheader("Mapped Data Preview")
            if mapped_data_list:
                if pl is not None:
                    preview_mapped_df = pl.DataFrame(mapped_data_list[:3])
                    st.dataframe(preview_mapped_df.to_pandas())
                
                st.success(f"Ready to generate {len(mapped_data_list)} labels")
                
                # Import to multi-label session
                if st.button("📥 Import to Multi-Label Session", type="primary"):
                    import_csv_to_multi_session(mapped_data_list, batch_label_type)


def generate_batch_labels_action(label_data_list: List[Dict], label_type: str):
    """
    Generate and save multiple labels from batch data.
    """
    if 'storage' not in st.session_state:
        st.error("Storage not initialized")
        return
    
    storage: LabelStorage = st.session_state.storage
    saved_labels = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, label_data in enumerate(label_data_list):
        # Update progress
        progress = (i + 1) / len(label_data_list)
        progress_bar.progress(progress)
        status_text.text(f"Generating label {i + 1} of {len(label_data_list)}")
        
        # Generate a descriptive name for the label
        label_name = generate_batch_label_name(label_data, i + 1)
        
        # Save label
        try:
            saved_name = storage.save_label(label_data, label_type, label_name)
            saved_labels.append(saved_name)
        except Exception as e:
            st.error(f"Error saving label {i + 1}: {str(e)}")
    
    # Complete
    progress_bar.progress(1.0)
    status_text.text("Batch generation complete!")
    
    st.success(f"Successfully generated {len(saved_labels)} labels!")
    
    # Show saved labels
    with st.expander("Generated Labels"):
        for label_name in saved_labels:
            st.write(f"• {label_name}")


def generate_batch_label_name(label_data: Dict, index: int) -> str:
    """
    Generate a descriptive name for a batch label.
    """
    # Try to use specimen number, scientific name, or other identifying fields
    identifying_fields = ['specimen_number', 'scientific_name', 'name', 'title', 'location']
    
    for field in identifying_fields:
        if field in label_data:
            return f"{label_data[field]}"
    
    # Fallback to batch index
    return f"batch_label_{index:03d}"


def save_batch_template(field_mapping: Dict[str, str], label_type: str):
    """
    Save field mapping as a reusable template.
    """
    template_name = st.text_input(
        "Template Name:",
        value=f"{label_type.lower()}_batch_template",
        key="template_name_input"
    )
    
    if template_name and st.button("Save Template", key="save_template_btn"):
        template_data = {
            'field_mapping': field_mapping,
            'label_type': label_type,
            'created': pd.Timestamp.now().isoformat()
        }
        
        # Save to user data directory
        if 'storage' in st.session_state:
            storage: LabelStorage = st.session_state.storage
            template_file = storage.user_data_dir / "templates" / f"{template_name}.json"
            template_file.parent.mkdir(exist_ok=True)
            
            import json
            with open(template_file, 'w') as f:
                json.dump(template_data, f, indent=2)
            
            st.success(f"Template '{template_name}' saved!")


def save_all_multi_labels():
    """
    Save all labels from the multi-label session.
    """
    if 'storage' not in st.session_state:
        st.error("Storage not initialized")
        return
    
    storage: LabelStorage = st.session_state.storage
    saved_count = 0
    
    for label in st.session_state.multi_labels:
        if label['data']:  # Only save non-empty labels
            try:
                storage.save_label(label['data'], label['type'], label['name'])
                saved_count += 1
            except Exception as e:
                st.error(f"Error saving {label['name']}: {str(e)}")
    
    if saved_count > 0:
        st.success(f"Saved {saved_count} labels!")
        # Clear session after saving
        st.session_state.multi_labels = []


def load_all_labels_action(label_names: List[str], storage: LabelStorage):
    """
    Load all saved labels into the multi-label session.
    """
    loaded_labels = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, label_name in enumerate(label_names):
        progress = (i + 1) / len(label_names)
        progress_bar.progress(progress)
        status_text.text(f"Loading {label_name}...")
        
        try:
            label_data = storage.load_label(label_name)
            metadata = storage.get_metadata(label_name)
            
            if label_data:
                loaded_label = {
                    'id': len(loaded_labels),
                    'type': metadata.get('label_type', 'General') if metadata else 'General',
                    'data': label_data,
                    'name': label_name
                }
                loaded_labels.append(loaded_label)
        
        except Exception as e:
            st.error(f"Error loading {label_name}: {str(e)}")
    
    # Update session state
    st.session_state.multi_labels = loaded_labels
    
    progress_bar.progress(1.0)
    status_text.text("Loading complete!")
    
    st.success(f"Loaded {len(loaded_labels)} labels into multi-label session!")
    st.info("Switch to the 'Multi-Label Session' tab to edit them.")


def import_csv_to_multi_session(label_data_list: List[Dict], label_type: str):
    """
    Import CSV data into the multi-label session.
    """
    imported_labels = []
    
    for i, label_data in enumerate(label_data_list):
        # Try to generate a meaningful name
        name = generate_batch_label_name(label_data, i + 1)
        
        imported_label = {
            'id': i,
            'type': label_type,
            'data': label_data,
            'name': name
        }
        imported_labels.append(imported_label)
    
    # Add to existing multi-labels or replace
    if 'multi_labels' not in st.session_state:
        st.session_state.multi_labels = []
    
    st.session_state.multi_labels.extend(imported_labels)
    
    st.success(f"Imported {len(imported_labels)} labels to multi-label session!")
    st.info("Switch to the 'Multi-Label Session' tab to edit and save them.")