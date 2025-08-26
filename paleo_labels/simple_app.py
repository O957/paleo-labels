"""
Simplified Paleo Labels Application
Single unified interface for label creation with smart suggestions and batch functionality.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path

from smart_data import SmartDataEngine, initialize_smart_data
from export_engine import ExportEngine, initialize_export_engine
from simple_storage import SimpleStorage, initialize_simple_storage


def initialize_app():
    """Initialize the simplified application."""
    if "app_initialized" not in st.session_state:
        # Initialize core components
        st.session_state.storage = initialize_simple_storage()
        st.session_state.smart_data = initialize_smart_data(st.session_state.storage)
        st.session_state.export_engine = initialize_export_engine(st.session_state.storage)
        
        # Initialize session state for label creation
        if "label_fields" not in st.session_state:
            st.session_state.label_fields = {}
        if "label_copies" not in st.session_state:
            st.session_state.label_copies = []
        if "current_label_name" not in st.session_state:
            st.session_state.current_label_name = ""
            
        st.session_state.app_initialized = True


def render_dynamic_field_addition():
    """Render the dynamic field addition interface with smart suggestions."""
    st.subheader("🏷️ Create Your Label")
    
    # Current label fields
    if st.session_state.label_fields:
        st.write("**Current Fields:**")
        for key, value in st.session_state.label_fields.items():
            col1, col2, col3 = st.columns([3, 4, 1])
            
            with col1:
                st.write(f"**{key}**")
            with col2:
                st.write(value)
            with col3:
                if st.button("🗑️", key=f"delete_{key}", help=f"Delete {key}"):
                    del st.session_state.label_fields[key]
                    st.rerun()
    
    # Add new field section
    st.write("**Add New Field:**")
    col1, col2, col3 = st.columns([3, 4, 1])
    
    with col1:
        # Smart field key suggestions
        smart_data: SmartDataEngine = st.session_state.smart_data
        key_suggestions = smart_data.get_key_suggestions(
            current_fields=list(st.session_state.label_fields.keys())
        )
        
        if key_suggestions:
            with st.expander("💡 Suggested Fields"):
                for suggestion in key_suggestions[:5]:
                    if st.button(f"📝 {suggestion}", key=f"suggest_key_{suggestion}"):
                        st.session_state.new_field_key = suggestion
                        st.rerun()
        
        new_key = st.text_input("Field Name:", key="new_field_key", placeholder="e.g., Scientific Name")
    
    with col2:
        # Smart value suggestions based on key
        if new_key:
            value_suggestions = smart_data.get_value_suggestions(new_key)
            if value_suggestions:
                with st.expander("💡 Suggested Values"):
                    for suggestion in value_suggestions[:5]:
                        if st.button(f"📝 {suggestion}", key=f"suggest_value_{suggestion}"):
                            st.session_state.new_field_value = suggestion
                            st.rerun()
        
        new_value = st.text_input("Value:", key="new_field_value", placeholder="Enter value")
    
    with col3:
        if st.button("➕", help="Add field"):
            if new_key and new_key not in st.session_state.label_fields:
                st.session_state.label_fields[new_key] = new_value
                st.session_state.new_field_key = ""
                st.session_state.new_field_value = ""
                st.rerun()


def render_copy_n_times_interface():
    """Render the 'Copy N Times' functionality interface."""
    if not st.session_state.label_fields:
        st.info("Create some fields first before copying.")
        return
    
    st.subheader("🔄 Copy Label Multiple Times")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_copies = st.number_input("Number of copies:", min_value=1, max_value=100, value=5)
    
    with col2:
        copy_mode = st.selectbox(
            "Copy mode:",
            ["Blank all fields", "Blank selected fields", "Keep all values"]
        )
    
    # Field selection for partial blanking
    fields_to_blank = []
    if copy_mode == "Blank selected fields":
        st.write("**Select fields to blank out:**")
        for field_name in st.session_state.label_fields.keys():
            if st.checkbox(f"Blank '{field_name}'", key=f"blank_{field_name}"):
                fields_to_blank.append(field_name)
    
    if st.button("🔄 Create Copies", type="primary"):
        create_label_copies(num_copies, copy_mode, fields_to_blank)


def create_label_copies(num_copies: int, copy_mode: str, fields_to_blank: list):
    """Create N copies of the current label with specified blanking."""
    base_label = st.session_state.label_fields.copy()
    copies = []
    
    for i in range(num_copies):
        label_copy = base_label.copy()
        
        if copy_mode == "Blank all fields":
            label_copy = {key: "" for key in label_copy.keys()}
        elif copy_mode == "Blank selected fields":
            for field in fields_to_blank:
                if field in label_copy:
                    label_copy[field] = ""
        # Keep all values mode requires no changes
        
        # Add copy number for identification
        label_copy["Copy Number"] = f"{i + 1}"
        copies.append(label_copy)
    
    st.session_state.label_copies = copies
    st.success(f"Created {num_copies} label copies!")


def render_batch_editor():
    """Render interface for editing batch-created labels."""
    if not st.session_state.label_copies:
        return
    
    st.subheader(f"📝 Edit Label Copies ({len(st.session_state.label_copies)} labels)")
    
    # Select label to edit
    copy_numbers = [f"Copy {i+1}" for i in range(len(st.session_state.label_copies))]
    selected_copy = st.selectbox("Select copy to edit:", copy_numbers)
    
    if selected_copy:
        copy_index = int(selected_copy.split()[-1]) - 1
        current_copy = st.session_state.label_copies[copy_index]
        
        st.write(f"**Editing {selected_copy}:**")
        
        # Edit fields
        updated_fields = {}
        for key, value in current_copy.items():
            if key != "Copy Number":  # Don't edit copy number
                new_value = st.text_input(f"{key}:", value=value, key=f"edit_{copy_index}_{key}")
                updated_fields[key] = new_value
        
        updated_fields["Copy Number"] = current_copy["Copy Number"]
        
        if st.button("💾 Save Changes", key=f"save_{copy_index}"):
            st.session_state.label_copies[copy_index] = updated_fields
            st.success(f"{selected_copy} updated!")


def render_export_section():
    """Render the export interface."""
    st.subheader("📄 Export Labels")
    
    export_engine: ExportEngine = st.session_state.export_engine
    
    # Determine what to export
    export_options = []
    if st.session_state.label_fields:
        export_options.append("Current Label")
    if st.session_state.label_copies:
        export_options.append(f"All Copies ({len(st.session_state.label_copies)} labels)")
    
    if not export_options:
        st.info("Create a label first to enable export options.")
        return
    
    export_choice = st.selectbox("What to export:", export_options)
    
    # Export format options
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox("Format:", ["PDF", "Multi-label Sheet", "CSV"])
    
    with col2:
        if export_format in ["PDF", "Multi-label Sheet"]:
            label_template = st.selectbox(
                "Label Template:",
                ["Standard", "Avery 5160", "Avery 8160", "Custom"]
            )
    
    # Style options
    style_file = st.file_uploader("Style File (optional):", type=['toml'])
    
    if st.button("📤 Export", type="primary"):
        perform_export(export_choice, export_format, label_template, style_file, export_engine)


def perform_export(export_choice: str, export_format: str, label_template: str, style_file, export_engine: ExportEngine):
    """Perform the actual export operation."""
    try:
        # Prepare data
        if "Current Label" in export_choice:
            labels_data = [st.session_state.label_fields]
        else:
            labels_data = st.session_state.label_copies
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = st.session_state.current_label_name or "labels"
        filename = f"{base_name}_{timestamp}"
        
        # Process style file if provided
        style_data = None
        if style_file is not None:
            style_data = style_file.read().decode('utf-8')
        
        # Export based on format
        if export_format == "PDF":
            pdf_bytes = export_engine.create_single_label_pdf(
                labels_data[0], style_data, label_template
            )
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"{filename}.pdf",
                mime="application/pdf"
            )
        
        elif export_format == "Multi-label Sheet":
            pdf_bytes = export_engine.create_multi_label_sheet(
                labels_data, style_data, label_template
            )
            st.download_button(
                label="📥 Download Multi-Label Sheet",
                data=pdf_bytes,
                file_name=f"{filename}_sheet.pdf",
                mime="application/pdf"
            )
        
        elif export_format == "CSV":
            csv_data = export_engine.create_csv_export(labels_data)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{filename}.csv",
                mime="text/csv"
            )
        
        st.success("Export completed successfully!")
        
    except Exception as e:
        st.error(f"Export failed: {str(e)}")


def render_file_upload_section():
    """Render file upload and manipulation interface."""
    st.subheader("📁 Upload & Import")
    
    upload_type = st.selectbox(
        "Upload type:",
        ["CSV Data", "TOML Label", "Style File", "Template"]
    )
    
    uploaded_file = st.file_uploader(
        f"Upload {upload_type}:",
        type=['csv', 'toml'] if upload_type != "Style File" else ['toml']
    )
    
    if uploaded_file is not None:
        try:
            if upload_type == "CSV Data":
                handle_csv_upload(uploaded_file)
            elif upload_type == "TOML Label":
                handle_toml_label_upload(uploaded_file)
            elif upload_type == "Style File":
                handle_style_file_upload(uploaded_file)
            elif upload_type == "Template":
                handle_template_upload(uploaded_file)
        except Exception as e:
            st.error(f"Upload failed: {str(e)}")


def handle_csv_upload(uploaded_file):
    """Handle CSV file upload for batch label creation."""
    smart_data: SmartDataEngine = st.session_state.smart_data
    labels_data = smart_data.process_csv_data(uploaded_file.read())
    
    if labels_data:
        st.session_state.label_copies = labels_data
        st.success(f"Imported {len(labels_data)} labels from CSV!")
    else:
        st.error("Failed to process CSV file.")


def handle_toml_label_upload(uploaded_file):
    """Handle TOML label file upload."""
    import tomli
    
    content = uploaded_file.read().decode('utf-8')
    label_data = tomli.loads(content)
    
    if 'fields' in label_data:
        st.session_state.label_fields = label_data['fields']
        st.success("Label loaded successfully!")
    else:
        st.error("Invalid TOML label format.")


def handle_style_file_upload(uploaded_file):
    """Handle style file upload."""
    st.session_state.uploaded_style = uploaded_file.read().decode('utf-8')
    st.success("Style file uploaded! It will be used in exports.")


def handle_template_upload(uploaded_file):
    """Handle template file upload."""
    # This would integrate with the template system
    st.info("Template upload functionality would integrate with existing template system.")


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Paleo Labels - Simplified",
        page_icon="🏷️",
        layout="wide"
    )
    
    st.title("🏷️ Paleo Labels - Simplified")
    st.write("Create professional paleontological labels with smart suggestions")
    
    # Initialize app
    initialize_app()
    
    # Main interface tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏷️ Create Label",
        "🔄 Batch Labels", 
        "📄 Export",
        "📁 Import"
    ])
    
    with tab1:
        # Label name
        st.session_state.current_label_name = st.text_input(
            "Label Name (optional):",
            value=st.session_state.current_label_name,
            placeholder="Enter a name for this label"
        )
        
        render_dynamic_field_addition()
        
        if st.session_state.label_fields:
            st.divider()
            render_copy_n_times_interface()
    
    with tab2:
        render_batch_editor()
    
    with tab3:
        render_export_section()
    
    with tab4:
        render_file_upload_section()
    
    # Sidebar stats
    with st.sidebar:
        st.subheader("📊 Session Stats")
        st.metric("Current Fields", len(st.session_state.label_fields))
        st.metric("Label Copies", len(st.session_state.label_copies))
        
        if st.button("🗑️ Clear All"):
            st.session_state.label_fields = {}
            st.session_state.label_copies = []
            st.session_state.current_label_name = ""
            st.rerun()


if __name__ == "__main__":
    main()