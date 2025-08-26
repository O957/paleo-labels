"""
Template management system for Phase 2.
Handles saving, loading, and managing label templates.
"""

import json
from datetime import datetime

import streamlit as st

try:
    from .schemas import LABEL_SCHEMAS, get_schema_for_label_type
    from .storage import LabelStorage
except ImportError:
    from schemas import LABEL_SCHEMAS
    from storage import LabelStorage


class TemplateManager:
    """Manage label templates for reuse."""

    def __init__(self, storage: LabelStorage):
        self.storage = storage
        self.templates_dir = storage.user_data_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)

    def save_template(self, name: str, template_data: dict) -> bool:
        """Save a template to disk."""
        try:
            template_file = self.templates_dir / f"{name}.json"

            template_record = {
                "name": name,
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "data": template_data,
            }

            with open(template_file, "w") as f:
                json.dump(template_record, f, indent=2)

            return True
        except Exception:
            return False

    def load_template(self, name: str) -> dict | None:
        """Load a template from disk."""
        try:
            template_file = self.templates_dir / f"{name}.json"
            if not template_file.exists():
                return None

            with open(template_file) as f:
                template_record = json.load(f)

            return template_record
        except Exception:
            return None

    def list_templates(self) -> list[str]:
        """List all available templates."""
        try:
            return [f.stem for f in self.templates_dir.glob("*.json")]
        except Exception:
            return []

    def delete_template(self, name: str) -> bool:
        """Delete a template."""
        try:
            template_file = self.templates_dir / f"{name}.json"
            if template_file.exists():
                template_file.unlink()
                return True
            return False
        except Exception:
            return False


def templates_ui():
    """
    Main UI for template management.
    """
    st.header("Template Management")
    st.write("Save and reuse label configurations")

    if "storage" not in st.session_state:
        st.error("Storage not initialized")
        return

    # Initialize template manager
    if "template_manager" not in st.session_state:
        st.session_state.template_manager = TemplateManager(
            st.session_state.storage
        )

    template_manager: TemplateManager = st.session_state.template_manager

    # Template tabs
    tab1, tab2, tab3 = st.tabs(
        ["Save Template", "Load Template", "Manage Templates"]
    )

    with tab1:
        save_template_ui(template_manager)

    with tab2:
        load_template_ui(template_manager)

    with tab3:
        manage_templates_ui(template_manager)


def save_template_ui(template_manager: TemplateManager):
    """UI for saving current label as a template."""
    st.subheader("Save Current Label as Template")

    # Check if there's a current label
    current_label_type = st.session_state.get("current_label_type", "General")

    # Get current manual entry data
    current_data = {}
    if hasattr(st.session_state, "num_rows"):
        for i in range(st.session_state.num_rows):
            key = st.session_state.get(f"key_{i}", "").strip()
            value = st.session_state.get(f"value_{i}", "").strip()
            if key:
                current_data[key] = value

    if not current_data:
        st.info(
            "No current label data to save. Create a label first in Single Label mode."
        )
        return

    st.write("**Current Label Preview:**")
    for key, value in current_data.items():
        st.write(f"• **{key}**: {value}")

    st.write(f"**Label Type**: {current_label_type}")

    # Template details
    template_name = st.text_input(
        "Template Name:",
        value=f"{current_label_type.lower()}_template",
        help="Choose a descriptive name for this template",
    )

    template_description = st.text_area(
        "Description (optional):", help="Describe when to use this template"
    )

    if st.button("💾 Save Template", type="primary"):
        if template_name:
            template_data = {
                "label_type": current_label_type,
                "label_data": current_data,
                "description": template_description,
                "field_count": len(current_data),
            }

            if template_manager.save_template(template_name, template_data):
                st.success(f"Template '{template_name}' saved successfully!")
            else:
                st.error("Error saving template")
        else:
            st.warning("Please enter a template name")


def load_template_ui(template_manager: TemplateManager):
    """UI for loading templates."""
    st.subheader("Load Template")

    templates = template_manager.list_templates()

    if not templates:
        st.info("No templates found. Save some templates first!")
        return

    selected_template = st.selectbox(
        "Choose Template:", [""] + templates, help="Select a template to load"
    )

    if selected_template:
        template_record = template_manager.load_template(selected_template)

        if template_record:
            template_data = template_record["data"]

            st.write("**Template Preview:**")
            st.write(f"**Type**: {template_data.get('label_type', 'Unknown')}")
            st.write(f"**Fields**: {template_data.get('field_count', 0)}")

            if template_data.get("description"):
                st.write(f"**Description**: {template_data['description']}")

            st.write(
                f"**Created**: {template_record.get('created', 'Unknown')}"
            )

            # Show field preview
            label_data = template_data.get("label_data", {})
            if label_data:
                st.write("**Fields:**")
                for key, value in label_data.items():
                    st.write(f"• **{key}**: {value}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📥 Load Template", type="primary"):
                    load_template_action(template_data)

            with col2:
                if st.button("🗑️ Delete Template"):
                    if template_manager.delete_template(selected_template):
                        st.success(f"Template '{selected_template}' deleted!")
                        st.rerun()
                    else:
                        st.error("Error deleting template")


def manage_templates_ui(template_manager: TemplateManager):
    """UI for managing all templates."""
    st.subheader("Manage Templates")

    templates = template_manager.list_templates()

    if not templates:
        st.info("No templates found.")
        return

    st.write(f"**Found {len(templates)} templates:**")

    # Display all templates
    for template_name in templates:
        template_record = template_manager.load_template(template_name)

        if template_record:
            template_data = template_record["data"]

            with st.expander(f"📋 {template_name}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(
                        f"**Type**: {template_data.get('label_type', 'Unknown')}"
                    )
                    st.write(
                        f"**Fields**: {template_data.get('field_count', 0)}"
                    )
                    st.write(
                        f"**Created**: {template_record.get('created', 'Unknown')}"
                    )

                    if template_data.get("description"):
                        st.write(
                            f"**Description**: {template_data['description']}"
                        )

                with col2:
                    if st.button(
                        "🗑️ Delete", key=f"delete_template_{template_name}"
                    ):
                        if template_manager.delete_template(template_name):
                            st.success(f"Template '{template_name}' deleted!")
                            st.rerun()
                        else:
                            st.error("Error deleting template")

    # Bulk operations
    if len(templates) > 1:
        st.subheader("Bulk Operations")
        if st.button("🗑️ Delete All Templates", type="secondary"):
            deleted_count = 0
            for template_name in templates:
                if template_manager.delete_template(template_name):
                    deleted_count += 1

            st.success(f"Deleted {deleted_count} templates!")
            st.rerun()


def load_template_action(template_data: dict):
    """
    Load template data into the current session.
    """
    label_type = template_data.get("label_type", "General")
    label_data = template_data.get("label_data", {})

    if not label_data:
        st.warning("Template has no data to load")
        return

    # Set label type
    st.session_state.current_label_type = label_type

    # Clear existing manual entry initialization flags
    for existing_type in LABEL_SCHEMAS.keys():
        if f"manual_entry_initialized_{existing_type}" in st.session_state:
            del st.session_state[f"manual_entry_initialized_{existing_type}"]

    # Set up manual entry data
    st.session_state.num_rows = len(label_data)

    for i, (key, value) in enumerate(label_data.items()):
        st.session_state[f"key_{i}"] = key
        st.session_state[f"value_{i}"] = (
            str(value) if value is not None else ""
        )

    # Mark as initialized
    st.session_state[f"manual_entry_initialized_{label_type}"] = True

    # Clear upload flag if it exists
    if "uploaded_data_populated" in st.session_state:
        del st.session_state["uploaded_data_populated"]

    st.success("Template loaded! Switch to Single Label mode to see it.")
    st.info(
        "The template has been loaded into your manual entry. Go to Single Label mode to edit and use it."
    )


def create_template_from_current() -> dict | None:
    """
    Create a template from the current manual entry state.
    Returns template data or None if no valid data.
    """
    current_label_type = st.session_state.get("current_label_type", "General")

    # Get current manual entry data
    current_data = {}
    if hasattr(st.session_state, "num_rows"):
        for i in range(st.session_state.num_rows):
            key = st.session_state.get(f"key_{i}", "").strip()
            value = st.session_state.get(f"value_{i}", "").strip()
            if key:
                current_data[key] = value

    if not current_data:
        return None

    return {
        "label_type": current_label_type,
        "label_data": current_data,
        "field_count": len(current_data),
    }
