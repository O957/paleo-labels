"""Streamlit UI for paleo-labels with dropdown-based modes."""

from datetime import datetime

import streamlit as st

from paleo_labels.core.pdf_renderer import create_pdf_from_labels
from paleo_labels.core.styling import LabelStyle
from paleo_labels.storage.field_library import (
    get_all_field_names,
    get_field_suggestions,
    save_label_to_library,
)
from paleo_labels.storage.label_storage import (
    list_saved_labels,
    load_label,
    save_label,
)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "pdf_queue" not in st.session_state:
        st.session_state.pdf_queue = []
    if "current_style" not in st.session_state:
        st.session_state.current_style = LabelStyle()
    if "current_fields" not in st.session_state:
        st.session_state.current_fields = [{"name": "", "value": ""}]


def mode_blank_text_label():
    """Mode 1: Blank Text Label."""
    st.header("Blank Text Label")

    text = st.text_area(
        "Enter text:",
        height=150,
        help="Text will wrap automatically and font will scale to fit.",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Save Label", disabled=not text):
            label_data = {"__blank_label__": text}
            label_id = f"blank_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            save_label(label_data, label_id, st.session_state.current_style)
            st.success(f"Saved as {label_id}")

    with col2:
        if st.button("📄 Add to PDF Queue", disabled=not text):
            label_data = {"__blank_label__": text}
            st.session_state.pdf_queue.append(label_data)
            st.success(
                f"Added to queue ({len(st.session_state.pdf_queue)} labels)"
            )

    with col3:
        if st.button("🔍 Preview", disabled=not text):
            st.text("Preview:")
            st.text(f"Text: {text[:100]}...")
            st.text(
                f"Font: {st.session_state.current_style.default_value_style.font_family}"
            )
            st.text(
                f'Size: {st.session_state.current_style.width_inches}" × {st.session_state.current_style.height_inches}"'
            )


def mode_load_label():
    """Mode 2: Load Previous Label/Template."""
    st.header("Load Label")

    source = st.radio("Source:", ["Previous Labels", "Templates"])

    if source == "Previous Labels":
        saved_labels = list_saved_labels()

        if not saved_labels:
            st.info("No saved labels found.")
            return

        selected_label_id = st.selectbox("Select label:", saved_labels)

        if st.button("📂 Load"):
            loaded = load_label(selected_label_id)
            st.session_state.current_fields = []

            label_data = loaded["label_data"]

            if "__blank_label__" in label_data:
                st.info("This is a blank text label. Cannot edit fields.")
            else:
                for field_name, value in label_data.items():
                    st.session_state.current_fields.append(
                        {"name": field_name, "value": value}
                    )

            st.success(f"Loaded {selected_label_id}")
            st.rerun()

        if st.button("📄 Add to PDF Queue"):
            loaded = load_label(selected_label_id)
            st.session_state.pdf_queue.append(loaded["label_data"])
            st.success(
                f"Added to queue ({len(st.session_state.pdf_queue)} labels)"
            )


def mode_create_custom_label():
    """Mode 3: Create Custom Label."""
    st.header("Create Custom Label")

    # get all field names for suggestions
    all_field_names = get_all_field_names()

    # render fields
    for i, field_entry in enumerate(st.session_state.current_fields):
        col1, col2 = st.columns(2)

        with col1:
            # field name with suggestions
            field_name_options = [""] + all_field_names
            if (
                field_entry["name"]
                and field_entry["name"] not in field_name_options
            ):
                field_name_options.append(field_entry["name"])

            field_name = st.selectbox(
                f"Field {i + 1}:",
                options=field_name_options,
                index=field_name_options.index(field_entry["name"])
                if field_entry["name"] in field_name_options
                else 0,
                key=f"field_name_{i}",
            )

            # allow custom field name entry
            if field_name == "":
                field_name = st.text_input(
                    "Or enter custom field name:",
                    value=field_entry["name"]
                    if field_entry["name"] not in field_name_options
                    else "",
                    key=f"custom_field_{i}",
                )

            st.session_state.current_fields[i]["name"] = field_name

        with col2:
            if field_name:
                # value with autocomplete suggestions
                value_suggestions = get_field_suggestions(field_name)
                value_options = [""] + value_suggestions

                if (
                    field_entry["value"]
                    and field_entry["value"] not in value_options
                ):
                    value_options.append(field_entry["value"])

                value = st.selectbox(
                    f"Value {i + 1}:",
                    options=value_options,
                    index=value_options.index(field_entry["value"])
                    if field_entry["value"] in value_options
                    else 0,
                    key=f"field_value_{i}",
                )

                # allow custom value entry
                if value == "":
                    value = st.text_input(
                        "Or enter custom value:",
                        value=field_entry["value"]
                        if field_entry["value"] not in value_options
                        else "",
                        key=f"custom_value_{i}",
                    )

                st.session_state.current_fields[i]["value"] = value

    # add/remove field buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("➕ Add Field"):
            st.session_state.current_fields.append({"name": "", "value": ""})
            st.rerun()

    with col2:
        if len(st.session_state.current_fields) > 1:
            if st.button("➖ Remove Last Field"):
                st.session_state.current_fields.pop()
                st.rerun()

    # action buttons
    st.divider()
    col1, col2, col3 = st.columns(3)

    # build label data
    label_data = {
        field["name"]: field["value"]
        for field in st.session_state.current_fields
        if field["name"]
    }

    with col1:
        if st.button("💾 Save Label", disabled=not label_data):
            label_id = f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            save_label(label_data, label_id, st.session_state.current_style)
            save_label_to_library(label_data)
            st.success(f"Saved as {label_id}")

    with col2:
        if st.button("📄 Add to PDF Queue", disabled=not label_data):
            st.session_state.pdf_queue.append(label_data)
            st.success(
                f"Added to queue ({len(st.session_state.pdf_queue)} labels)"
            )

    with col3:
        if st.button("🔍 Preview", disabled=not label_data):
            st.text("Preview:")
            for field_name, value in label_data.items():
                st.text(f"{field_name}: {value}")


def mode_custom_style():
    """Mode 5: Custom Style Grid."""
    st.header("Custom Style")

    style = st.session_state.current_style

    # label dimensions
    st.subheader("Label Dimensions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        width = st.number_input(
            "Width (inches):",
            min_value=0.5,
            max_value=8.0,
            value=style.width_inches,
            step=0.05,
        )
        style.width_inches = width

    with col2:
        height = st.number_input(
            "Height (inches):",
            min_value=0.5,
            max_value=10.0,
            value=style.height_inches,
            step=0.05,
        )
        style.height_inches = height

    with col3:
        border = st.number_input(
            "Border (points):",
            min_value=0.0,
            max_value=5.0,
            value=style.border_thickness,
            step=0.25,
        )
        style.border_thickness = border

    with col4:
        padding = st.number_input(
            "Padding (%):",
            min_value=0.01,
            max_value=0.2,
            value=style.padding_percent,
            step=0.01,
        )
        style.padding_percent = padding

    # global typography
    st.subheader("Global Typography")
    col1, col2 = st.columns(2)

    with col1:
        font_family = st.selectbox(
            "Font Family:",
            ["Courier", "Helvetica", "Times-Roman"],
            index=["Courier", "Helvetica", "Times-Roman"].index(
                style.default_field_style.font_family
            ),
        )
        style.default_field_style.font_family = font_family
        style.default_value_style.font_family = font_family

    with col2:
        default_size = st.number_input(
            "Default Font Size (points):",
            min_value=6.0,
            max_value=24.0,
            value=style.default_field_style.font_size,
            step=0.5,
        )

    # field styling
    st.subheader("Field (Group) Styling")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        field_size = st.number_input(
            "Font Size:",
            min_value=6.0,
            max_value=24.0,
            value=style.default_field_style.font_size,
            step=0.5,
            key="field_size",
        )
        style.default_field_style.font_size = field_size

    with col2:
        field_color = st.color_picker(
            "Color:",
            value=style.default_field_style.color,
            key="field_color",
        )
        style.default_field_style.color = field_color

    with col3:
        field_bold = st.checkbox(
            "Bold",
            value=style.default_field_style.bold,
            key="field_bold",
        )
        style.default_field_style.bold = field_bold

    with col4:
        field_italic = st.checkbox(
            "Italic",
            value=style.default_field_style.italic,
            key="field_italic",
        )
        style.default_field_style.italic = field_italic

    # value styling
    st.subheader("Value (Content) Styling")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        value_size = st.number_input(
            "Font Size:",
            min_value=6.0,
            max_value=24.0,
            value=style.default_value_style.font_size,
            step=0.5,
            key="value_size",
        )
        style.default_value_style.font_size = value_size

    with col2:
        value_color = st.color_picker(
            "Color:",
            value=style.default_value_style.color,
            key="value_color",
        )
        style.default_value_style.color = value_color

    with col3:
        value_bold = st.checkbox(
            "Bold",
            value=style.default_value_style.bold,
            key="value_bold",
        )
        style.default_value_style.bold = value_bold

    with col4:
        value_italic = st.checkbox(
            "Italic",
            value=style.default_value_style.italic,
            key="value_italic",
        )
        style.default_value_style.italic = value_italic

    # separator options
    st.subheader("Separator Options")
    col1, col2 = st.columns(2)

    with col1:
        separator_option = st.selectbox(
            "Separator:",
            [": ", " - ", " | ", "Custom"],
        )

        if separator_option == "Custom":
            separator = st.text_input("Custom separator:", value=": ")
        else:
            separator = separator_option

        style.default_separator = separator

    with col2:
        show_empty = st.checkbox(
            "Show empty fields",
            value=style.show_empty_fields,
        )
        style.show_empty_fields = show_empty

    st.success("Style updated! Changes apply to new labels.")


def pdf_queue_section():
    """Render PDF queue and generation controls."""
    st.sidebar.header("📄 PDF Queue")

    if not st.session_state.pdf_queue:
        st.sidebar.info("Queue is empty")
        return

    st.sidebar.write(f"**{len(st.session_state.pdf_queue)} labels queued**")

    for i, label in enumerate(st.session_state.pdf_queue):
        if "__blank_label__" in label:
            label_preview = f"Blank: {label['__blank_label__'][:20]}..."
        else:
            label_preview = f"{list(label.keys())[0] if label else 'Empty'}"

        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.text(f"{i + 1}. {label_preview}")
        with col2:
            if st.button("✖", key=f"remove_{i}"):
                st.session_state.pdf_queue.pop(i)
                st.rerun()

    if st.sidebar.button("🗑️ Clear Queue"):
        st.session_state.pdf_queue = []
        st.rerun()

    if st.sidebar.button("📥 Generate PDF"):
        pdf_bytes = create_pdf_from_labels(
            st.session_state.pdf_queue,
            st.session_state.current_style,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.sidebar.download_button(
            "⬇️ Download PDF",
            pdf_bytes,
            f"paleo_labels_{timestamp}.pdf",
            "application/pdf",
        )


def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="Paleo Labels", page_icon="🏷️", layout="wide")
    st.title("🏷️ Paleo Labels")

    initialize_session_state()

    # mode selection
    mode = st.selectbox(
        "Label Creation Mode:",
        [
            "1. Blank Text Label",
            "2. Load Previous Label/Template",
            "3. Create Custom Label",
            "5. Custom Style Grid",
        ],
    )

    st.divider()

    # render selected mode
    if mode == "1. Blank Text Label":
        mode_blank_text_label()
    elif mode == "2. Load Previous Label/Template":
        mode_load_label()
    elif mode == "3. Create Custom Label":
        mode_create_custom_label()
    elif mode == "5. Custom Style Grid":
        mode_custom_style()

    # sidebar with PDF queue
    pdf_queue_section()


if __name__ == "__main__":
    main()
