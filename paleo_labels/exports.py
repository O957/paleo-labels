"""
Advanced export system for Phase 2.
Handles multi-label PDF sheets, batch exports, and print layouts.
"""

import io

import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

try:
    from .schemas import LABEL_SCHEMAS
    from .storage import LabelStorage
except ImportError:
    from schemas import LABEL_SCHEMAS
    from storage import LabelStorage

import tempfile
from datetime import datetime

# Import POINTS_PER_INCH constant directly to avoid circular import
POINTS_PER_INCH = 72


# Avery label sheet templates
AVERY_TEMPLATES = {
    "5160": {
        "name": "Avery 5160 (Address Labels)",
        "labels_per_sheet": 30,
        "rows": 10,
        "cols": 3,
        "label_width": 2.625,
        "label_height": 1.0,
        "top_margin": 0.5,
        "left_margin": 0.1875,
        "row_spacing": 0.0,
        "col_spacing": 0.125,
    },
    "5161": {
        "name": "Avery 5161 (Address Labels)",
        "labels_per_sheet": 20,
        "rows": 10,
        "cols": 2,
        "label_width": 4.0,
        "label_height": 1.0,
        "top_margin": 0.5,
        "left_margin": 0.25,
        "row_spacing": 0.0,
        "col_spacing": 0.25,
    },
    "5163": {
        "name": "Avery 5163 (Shipping Labels)",
        "labels_per_sheet": 10,
        "rows": 5,
        "cols": 2,
        "label_width": 4.0,
        "label_height": 2.0,
        "top_margin": 0.5,
        "left_margin": 0.25,
        "row_spacing": 0.0,
        "col_spacing": 0.25,
    },
    "museum_large": {
        "name": "Museum Large (3×4 inches)",
        "labels_per_sheet": 6,
        "rows": 2,
        "cols": 2,
        "label_width": 3.0,
        "label_height": 4.0,
        "top_margin": 0.5,
        "left_margin": 1.25,
        "row_spacing": 0.5,
        "col_spacing": 0.5,
    },
    "specimen_small": {
        "name": "Small Specimen Labels (2×1 inches)",
        "labels_per_sheet": 18,
        "rows": 6,
        "cols": 3,
        "label_width": 2.0,
        "label_height": 1.0,
        "top_margin": 1.0,
        "left_margin": 0.75,
        "row_spacing": 0.5,
        "col_spacing": 0.75,
    },
    "custom": {
        "name": "Custom Layout",
        "labels_per_sheet": 6,
        "rows": 2,
        "cols": 3,
        "label_width": 2.5,
        "label_height": 2.0,
        "top_margin": 1.0,
        "left_margin": 0.5,
        "row_spacing": 0.5,
        "col_spacing": 0.5,
    },
}


def exports_ui():
    """
    Main UI for advanced export features.
    """
    st.header("Advanced Export")
    st.write("Export multiple labels to professional print layouts")

    if "storage" not in st.session_state:
        st.error("Storage not initialized")
        return

    # Export tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Multi-Label Sheet",
            "Continuous Stream Export",
            "Batch Export",
            "Print Layouts",
        ]
    )

    with tab1:
        multi_label_sheet_ui()

    with tab2:
        continuous_stream_export_ui()

    with tab3:
        batch_export_ui()

    with tab4:
        print_layouts_ui()


def multi_label_sheet_ui():
    """
    UI for creating multi-label PDF sheets.
    """
    st.subheader("Multi-Label PDF Sheet")
    st.write("Create professional label sheets with multiple labels")

    # Check for labels in multi-label session
    if (
        "multi_labels" not in st.session_state
        or not st.session_state.multi_labels
    ):
        st.info(
            "No labels found. Create labels in Batch Processing > Multi-Label Session first."
        )
        return

    labels = st.session_state.multi_labels
    st.write(f"**Available Labels: {len(labels)}**")

    # Template selection
    st.subheader("Sheet Layout")

    template_key = st.selectbox(
        "Layout Template:",
        list(AVERY_TEMPLATES.keys()),
        format_func=lambda x: AVERY_TEMPLATES[x]["name"],
    )

    template = AVERY_TEMPLATES[template_key]

    # Show template info with preview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Labels per Sheet", template["labels_per_sheet"])
    with col2:
        st.metric("Rows × Columns", f"{template['rows']} × {template['cols']}")
    with col3:
        st.metric(
            "Label Size",
            f'{template["label_width"]}" × {template["label_height"]}"',
        )
    with col4:
        sheets_needed = (
            len(labels) + template["labels_per_sheet"] - 1
        ) // template["labels_per_sheet"]
        st.metric("Est. Pages", sheets_needed)

    # Template preview
    if st.checkbox("Show Template Preview", help="Preview the label layout"):
        create_template_preview(template)

    # Custom template editor
    if template_key == "custom":
        st.subheader("Custom Layout Settings")

        col1, col2 = st.columns(2)
        with col1:
            template["rows"] = st.number_input(
                "Rows:", value=template["rows"], min_value=1, max_value=20
            )
            template["cols"] = st.number_input(
                "Columns:", value=template["cols"], min_value=1, max_value=10
            )
            template["label_width"] = st.number_input(
                "Label Width (in):",
                value=template["label_width"],
                min_value=0.5,
                max_value=8.0,
                step=0.1,
            )
            template["label_height"] = st.number_input(
                "Label Height (in):",
                value=template["label_height"],
                min_value=0.5,
                max_value=10.0,
                step=0.1,
            )

        with col2:
            template["top_margin"] = st.number_input(
                "Top Margin (in):",
                value=template["top_margin"],
                min_value=0.0,
                max_value=2.0,
                step=0.1,
            )
            template["left_margin"] = st.number_input(
                "Left Margin (in):",
                value=template["left_margin"],
                min_value=0.0,
                max_value=2.0,
                step=0.1,
            )
            template["row_spacing"] = st.number_input(
                "Row Spacing (in):",
                value=template["row_spacing"],
                min_value=0.0,
                max_value=1.0,
                step=0.1,
            )
            template["col_spacing"] = st.number_input(
                "Column Spacing (in):",
                value=template["col_spacing"],
                min_value=0.0,
                max_value=1.0,
                step=0.1,
            )

        template["labels_per_sheet"] = template["rows"] * template["cols"]
        st.write(f"**Total labels per sheet: {template['labels_per_sheet']}**")

    # Label selection
    st.subheader("Label Selection")

    selected_labels = st.multiselect(
        "Choose labels to include:",
        options=range(len(labels)),
        default=list(range(min(len(labels), template["labels_per_sheet"]))),
        format_func=lambda x: f"{labels[x]['name']} ({labels[x]['type']})",
    )

    if not selected_labels:
        st.warning("Please select at least one label.")
        return

    sheets_needed = (
        len(selected_labels) + template["labels_per_sheet"] - 1
    ) // template["labels_per_sheet"]
    st.info(
        f"📄 Will create {sheets_needed} sheet(s) for {len(selected_labels)} labels"
    )

    # Advanced options
    with st.expander("🔧 Advanced Options"):
        include_numbering = st.checkbox(
            "Include label numbering",
            value=True,
            help="Add small numbers to each label",
        )
        alternate_shading = st.checkbox(
            "Alternate background shading",
            value=True,
            help="Shade every other label for easier reading",
        )
        border_style = st.selectbox(
            "Border Style", ["Standard", "Thin", "Bold", "None"]
        )

        # Font size override
        font_override = st.checkbox(
            "Override font size",
            help="Manually set font size instead of auto-sizing",
        )
        if font_override:
            font_size = st.slider("Font Size", 4, 16, 8)
        else:
            font_size = None

        # Store advanced options in session state
        st.session_state.multi_label_options = {
            "include_numbering": include_numbering,
            "alternate_shading": alternate_shading,
            "border_style": border_style,
            "font_size": font_size,
        }

    # Generate sheet
    if st.button("🖨️ Generate Multi-Label Sheet", type="primary"):
        # Get advanced options
        advanced_options = st.session_state.get("multi_label_options", {})
        generate_multi_label_sheet(
            selected_labels, template, labels, advanced_options
        )


def continuous_stream_export_ui():
    """
    UI for continuous stream PDF export from labels directory.
    """
    st.subheader("Continuous Stream PDF Export")
    st.write(
        "Export multiple labels from your labels directory onto optimized PDF pages"
    )

    storage: LabelStorage = st.session_state.storage
    saved_labels = storage.list_labels()

    if not saved_labels:
        st.info("No saved labels found in labels directory.")
        return

    st.write(f"**Found {len(saved_labels)} saved labels in directory**")

    # Label selection with search and filtering
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input(
            "🔍 Search labels:", placeholder="Filter by name or content..."
        )
    with col2:
        label_type_filter = st.selectbox(
            "Filter by type:", ["All Types"] + list(LABEL_SCHEMAS.keys())
        )

    # Load and filter labels
    filtered_labels = load_and_filter_labels(
        storage, saved_labels, search_term, label_type_filter
    )

    if not filtered_labels:
        st.warning("No labels match your filters.")
        return

    st.write(f"**{len(filtered_labels)} labels match your filters**")

    # Label selection interface
    selection_method = st.radio(
        "Selection Method:",
        ["Select All", "Choose Specific Labels", "Random Sample"],
        horizontal=True,
    )

    selected_label_data = []

    if selection_method == "Select All":
        selected_label_data = filtered_labels
        st.info(f"✅ All {len(filtered_labels)} filtered labels selected")

    elif selection_method == "Choose Specific Labels":
        label_options = []
        for i, (name, data) in enumerate(filtered_labels):
            preview = ", ".join(
                [f"{k}: {v}" for k, v in list(data.items())[:2]]
            )
            if len(preview) > 50:
                preview = preview[:47] + "..."
            label_options.append(f"{name} - {preview}")

        selected_indices = st.multiselect(
            "Choose labels:",
            options=range(len(filtered_labels)),
            default=list(
                range(min(20, len(filtered_labels)))
            ),  # Default first 20
            format_func=lambda x: label_options[x],
        )
        selected_label_data = [filtered_labels[i] for i in selected_indices]

    elif selection_method == "Random Sample":
        sample_size = st.slider(
            "Sample size:",
            min_value=1,
            max_value=len(filtered_labels),
            value=min(50, len(filtered_labels)),
        )
        import random

        random.seed(42)  # For reproducible results
        selected_label_data = random.sample(filtered_labels, sample_size)
        st.info(
            f"🎲 Random sample of {len(selected_label_data)} labels selected"
        )

    if not selected_label_data:
        st.warning("Please select at least one label.")
        return

    # Page layout optimization options
    st.subheader("📐 Page Layout Optimization")

    col1, col2 = st.columns(2)
    with col1:
        optimization_mode = st.selectbox(
            "Optimization Mode:",
            ["Auto-fit (Recommended)", "Fixed Template", "Custom Layout"],
        )

    with col2:
        max_labels_per_page = st.slider(
            "Max Labels per Page:",
            min_value=1,
            max_value=50,
            value=20,
            help="Upper limit for labels per page",
        )

    # Template selection for fixed template mode
    template = None
    if optimization_mode == "Fixed Template":
        template_key = st.selectbox(
            "Choose Template:",
            list(AVERY_TEMPLATES.keys()),
            format_func=lambda x: AVERY_TEMPLATES[x]["name"],
        )
        template = AVERY_TEMPLATES[template_key]

    # Style options
    with st.expander("🎨 Styling Options"):
        col1, col2 = st.columns(2)

        with col1:
            # Style file selection
            use_custom_style = st.checkbox(
                "Use custom style file", value=False
            )
            style_file = None

            if use_custom_style:
                uploaded_style = st.file_uploader(
                    "Upload Style File (.toml):",
                    type=["toml"],
                    help="Upload a style TOML file to apply to all labels",
                )
                if uploaded_style:
                    style_file = uploaded_style

            font_size_mode = st.selectbox("Font Size:", ["Auto-size", "Fixed"])
            if font_size_mode == "Fixed":
                fixed_font_size = st.slider("Font Size:", 4, 16, 8)
            else:
                fixed_font_size = None

        with col2:
            include_borders = st.checkbox("Include borders", value=True)
            include_numbering = st.checkbox("Number labels", value=True)
            alternate_shading = st.checkbox("Alternate shading", value=False)
            compact_layout = st.checkbox(
                "Compact layout",
                value=False,
                help="Reduce spacing between labels",
            )

    # Generate continuous PDF
    if st.button("🖨️ Generate Continuous Stream PDF", type="primary"):
        style_options = {
            "font_size": fixed_font_size,
            "include_borders": include_borders,
            "include_numbering": include_numbering,
            "alternate_shading": alternate_shading,
            "compact_layout": compact_layout,
            "style_file": style_file,
        }

        generate_continuous_stream_pdf(
            selected_label_data,
            optimization_mode,
            max_labels_per_page,
            template,
            style_options,
        )


def batch_export_ui():
    """
    UI for batch exporting saved labels.
    """
    st.subheader("Batch Export")
    st.write("Export all saved labels as individual PDFs")

    storage: LabelStorage = st.session_state.storage
    saved_labels = storage.list_labels()

    if not saved_labels:
        st.info("No saved labels found.")
        return

    st.write(f"**Found {len(saved_labels)} saved labels**")

    # Export options
    export_format = st.selectbox(
        "Export Format:",
        ["Individual PDFs (ZIP)", "Single Combined PDF", "Label Data (JSON)"],
    )

    include_metadata = st.checkbox(
        "Include Metadata",
        value=True,
        help="Include creation dates, label types, etc.",
    )

    if st.button("📦 Export All Labels", type="primary"):
        batch_export_action(
            saved_labels, export_format, include_metadata, storage
        )


def print_layouts_ui():
    """
    UI for custom print layouts.
    """
    st.subheader("Print Layouts")
    st.write("Create custom print layouts for specific use cases")

    st.info("Print layout customization coming in Phase 3!")

    # Preview of planned features
    st.write("**Planned Features:**")
    st.write("• Custom page sizes and orientations")
    st.write("• Variable label sizes on same sheet")
    st.write("• Print margins and bleed settings")
    st.write("• Professional print shop compatibility")


def generate_multi_label_sheet(
    selected_indices: List[int],
    template: Dict,
    all_labels: List[Dict],
    advanced_options: Dict = None,
):
    """
    Generate a multi-label PDF sheet with improved formatting.
    """
    selected_labels = [all_labels[i] for i in selected_indices]

    # Create PDF buffer
    buffer = io.BytesIO()
    page_width = 8.5 * POINTS_PER_INCH
    page_height = 11.0 * POINTS_PER_INCH

    c = canvas.Canvas(buffer, pagesize=letter)

    # Add title and metadata
    c.setFont("Helvetica-Bold", 14)
    c.drawString(
        30, page_height - 30, f"Label Sheet - {len(selected_labels)} Labels"
    )
    c.setFont("Helvetica", 10)
    c.drawString(
        30,
        page_height - 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    )

    # Draw page border
    c.setStrokeColor("lightgray")
    c.rect(20, 20, page_width - 40, page_height - 80, stroke=1, fill=0)

    labels_per_sheet = template["labels_per_sheet"]
    current_label_index = 0
    page_number = 1

    # Apply advanced options
    if advanced_options is None:
        advanced_options = {}

    # Default style configuration with advanced options
    style_config = {
        "font_size": advanced_options.get("font_size", 8),
        "border_enabled": advanced_options.get("border_style", "Standard")
        != "None",
        "padding": 0.05,
        "border_style": advanced_options.get("border_style", "Standard"),
        "include_numbering": advanced_options.get("include_numbering", True),
        "alternate_shading": advanced_options.get("alternate_shading", True),
    }

    with st.spinner("Generating multi-label sheet..."):
        progress_bar = st.progress(0)

        while current_label_index < len(selected_labels):
            # Add page header if not first page
            if page_number > 1:
                c.setFont("Helvetica", 8)
                c.drawString(
                    30, page_height - 30, f"Page {page_number} - Continued"
                )

            # Calculate content area (avoiding header/footer)
            content_start_y = page_height - 80
            content_height = page_height - 120

            # Draw labels on current page
            labels_on_this_page = 0
            for row in range(template["rows"]):
                for col in range(template["cols"]):
                    if (
                        current_label_index >= len(selected_labels)
                        or labels_on_this_page >= labels_per_sheet
                    ):
                        break

                    label = selected_labels[current_label_index]

                    # Calculate position within content area
                    x = (
                        template["left_margin"] * POINTS_PER_INCH
                        + col
                        * (template["label_width"] + template["col_spacing"])
                        * POINTS_PER_INCH
                    )
                    y = content_start_y - (
                        template["top_margin"] * POINTS_PER_INCH
                        + row
                        * (template["label_height"] + template["row_spacing"])
                        * POINTS_PER_INCH
                        + template["label_height"] * POINTS_PER_INCH
                    )

                    # Ensure we don't go outside the content area
                    if y < 40:  # Leave space for footer
                        break

                    # Calculate label dimensions
                    label_width_pts = template["label_width"] * POINTS_PER_INCH
                    label_height_pts = (
                        template["label_height"] * POINTS_PER_INCH
                    )

                    # Draw border based on style
                    border_style = style_config.get("border_style", "Standard")
                    if border_style != "None":
                        c.setStrokeColor("gray")
                        if border_style == "Thin":
                            c.setLineWidth(0.25)
                        elif border_style == "Bold":
                            c.setLineWidth(1.0)
                        else:  # Standard
                            c.setLineWidth(0.5)
                        c.rect(
                            x,
                            y,
                            label_width_pts,
                            label_height_pts,
                            stroke=1,
                            fill=0,
                        )

                    # Add alternating background shading
                    if (
                        style_config.get("alternate_shading", True)
                        and (current_label_index % 2) == 1
                    ):
                        c.setFillColor("#f8f8f8")
                        c.rect(
                            x + 1,
                            y + 1,
                            label_width_pts - 2,
                            label_height_pts - 2,
                            stroke=0,
                            fill=1,
                        )

                    # Draw label content with style
                    draw_label_content(
                        c,
                        label["data"],
                        x,
                        y,
                        label_width_pts,
                        label_height_pts,
                        style_config,
                    )

                    # Add label number in corner if enabled
                    if style_config.get("include_numbering", True):
                        c.setFont("Helvetica", 6)
                        c.setFillColor("gray")
                        c.drawString(
                            x + 2,
                            y + label_height_pts - 8,
                            f"#{current_label_index + 1}",
                        )

                    current_label_index += 1
                    labels_on_this_page += 1
                    progress_bar.progress(
                        current_label_index / len(selected_labels)
                    )

                if (
                    current_label_index >= len(selected_labels)
                    or labels_on_this_page >= labels_per_sheet
                ):
                    break

            # Add page footer
            c.setFont("Helvetica", 8)
            c.setFillColor("gray")
            c.drawString(
                30,
                30,
                f"Page {page_number} of {((len(selected_labels) - 1) // labels_per_sheet) + 1}",
            )
            c.drawString(
                page_width - 100,
                30,
                f"Labels: {current_label_index}/{len(selected_labels)}",
            )

            # Start new page if more labels
            if current_label_index < len(selected_labels):
                c.showPage()
                page_number += 1

    # Finalize PDF
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Enhanced download section
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="📄 Download Multi-Label Sheet",
            data=pdf_bytes,
            file_name=f"multi_label_sheet_{len(selected_labels)}_labels.pdf",
            mime="application/pdf",
            type="primary",
        )

    with col2:
        st.metric("PDF Pages", page_number)
        st.metric("Labels per Page", f"~{labels_per_sheet}")

    st.success(
        f"✅ Generated {page_number}-page PDF with {len(selected_labels)} properly formatted labels!"
    )

    # Show generation summary
    with st.expander("📊 Generation Summary"):
        st.write(f"**Template**: {template.get('name', 'Custom')}")
        st.write(
            f'**Label Size**: {template["label_width"]}" × {template["label_height"]}"'
        )
        st.write(
            f"**Layout**: {template['rows']} rows × {template['cols']} columns"
        )
        st.write(f"**Total Pages**: {page_number}")
        st.write(f"**Labels Generated**: {len(selected_labels)}")


def load_style_from_uploaded_file(uploaded_file):
    """Load style configuration from uploaded TOML file."""
    if uploaded_file is None:
        return None

    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".toml", delete=False
        ) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name

        # Import the style loading function locally to avoid circular imports
        try:
            from .app import load_label_style_from_file
        except ImportError:
            from app import load_label_style_from_file

        style_config = load_label_style_from_file(temp_path)

        # Clean up temp file
        import os

        os.unlink(temp_path)

        return style_config
    except Exception as e:
        st.warning(f"Could not load style file: {str(e)}")
        return None


def get_font_color_from_style(
    style_config: Dict, is_key: bool = True
) -> Tuple[float, float, float]:
    """Extract RGB color values from style config."""
    if is_key:
        r = style_config.get("key_color_r", 0.0)
        g = style_config.get("key_color_g", 0.0)
        b = style_config.get("key_color_b", 0.0)
    else:
        r = style_config.get("value_color_r", 0.0)
        g = style_config.get("value_color_g", 0.0)
        b = style_config.get("value_color_b", 0.0)

    return (r, g, b)


def draw_label_content_with_style(
    c: canvas.Canvas,
    label_data: Dict,
    x: float,
    y: float,
    width: float,
    height: float,
    style_config: Dict = None,
):
    """Draw label content with full style support."""
    if not label_data:
        return

    # Default values
    font_size = 8
    font_name = "Helvetica"
    show_keys = True
    show_values = True
    key_color = (0, 0, 0)  # Black
    value_color = (0, 0, 0)  # Black
    bold_keys = False
    bold_values = False

    # Apply style config if provided
    if style_config:
        font_size = style_config.get("font_size", 8)
        font_name = style_config.get("font_name", "Helvetica")
        show_keys = style_config.get("show_keys", True)
        show_values = style_config.get("show_values", True)
        bold_keys = style_config.get("bold_keys", False)
        bold_values = style_config.get("bold_values", False)
        key_color = get_font_color_from_style(style_config, is_key=True)
        value_color = get_font_color_from_style(style_config, is_key=False)

    # Auto-size font if needed
    num_lines = len(label_data)
    if num_lines > 8:
        font_size = max(6, font_size - 2)
    elif num_lines > 5:
        font_size = max(6, font_size - 1)

    # Calculate layout
    margin = 4
    line_height = font_size * 1.2
    text_x = x + margin
    text_y = y + height - margin - font_size
    max_chars = int((width - 2 * margin) / (font_size * 0.6))

    # Draw each field with styling
    for key, value in label_data.items():
        if text_y < y + margin:
            break

        # Draw key if enabled
        if show_keys:
            key_font = f"{font_name}-Bold" if bold_keys else font_name
            c.setFont(key_font, font_size)
            c.setFillColor(key_color[0], key_color[1], key_color[2])

            key_text = f"{key}: "
            if len(key_text) > max_chars // 2:
                key_text = key_text[: max_chars // 2 - 3] + "..."

            c.drawString(text_x, text_y, key_text)
            key_width = len(key_text) * font_size * 0.6
        else:
            key_width = 0

        # Draw value if enabled
        if show_values:
            value_font = f"{font_name}-Bold" if bold_values else font_name
            c.setFont(value_font, font_size)
            c.setFillColor(value_color[0], value_color[1], value_color[2])

            remaining_chars = (
                max_chars - len(key_text) if show_keys else max_chars
            )
            value_text = str(value)
            if len(value_text) > remaining_chars:
                value_text = value_text[: remaining_chars - 3] + "..."

            value_x = text_x + key_width if show_keys else text_x
            c.drawString(value_x, text_y, value_text)

        text_y -= line_height


def draw_label_content(
    c: canvas.Canvas,
    label_data: Dict,
    x: float,
    y: float,
    width: float,
    height: float,
    style_config: Dict = None,
):
    """
    Draw label content within the given bounds - simplified for performance.
    """
    if not label_data:
        return

    # Extract style properties or use defaults
    font_size = 8  # Smaller default for multi-label sheets
    if style_config:
        font_size = style_config.get("font_size", 8)

    # Ensure font_size is never None
    if font_size is None:
        font_size = 8

    # Simple auto-sizing if needed
    num_lines = len(label_data)
    if style_config is None or style_config.get("font_size") is None:
        # Quick font size adjustment based on number of fields
        if num_lines > 8:
            font_size = 6
        elif num_lines > 5:
            font_size = 7
        # Keep default 8 for <= 5 lines

    # Set font and color
    c.setFont("Helvetica", font_size)
    c.setFillColor("black")

    # Calculate layout
    margin = 4
    line_height = font_size * 1.2
    text_x = x + margin
    text_y = y + height - margin - font_size
    max_chars = int((width - 2 * margin) / (font_size * 0.6))

    # Draw each field (simplified)
    for key, value in label_data.items():
        if text_y < y + margin:  # Check if we have space
            break

        # Format and truncate if necessary
        text = f"{key}: {value}"
        if len(text) > max_chars:
            text = text[: max_chars - 3] + "..."

        c.drawString(text_x, text_y, text)
        text_y -= line_height


def create_template_preview(template: Dict):
    """
    Create a visual preview of the label template layout.
    """
    # Create a simple SVG preview
    page_width = 400  # SVG units
    page_height = 500  # SVG units

    # Scale factors
    scale_x = page_width / 8.5
    scale_y = page_height / 11.0

    svg_elements = [
        f'<svg width="{page_width}" height="{page_height}" style="border: 1px solid #ccc; background: white;">',
        f'<rect width="{page_width}" height="{page_height}" fill="white" stroke="#ddd"/>',
        f'<text x="10" y="20" font-family="Arial" font-size="12" fill="#333">Template Preview: {template["name"]}</text>',
    ]

    # Draw label rectangles
    for row in range(template["rows"]):
        for col in range(template["cols"]):
            x = (
                template["left_margin"] * scale_x
                + col
                * (template["label_width"] + template["col_spacing"])
                * scale_x
            )
            y = (
                30
                + template["top_margin"] * scale_y
                + row
                * (template["label_height"] + template["row_spacing"])
                * scale_y
            )
            width = template["label_width"] * scale_x
            height = template["label_height"] * scale_y

            label_num = row * template["cols"] + col + 1

            svg_elements.extend(
                [
                    f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="lightblue" stroke="navy" stroke-width="1" opacity="0.7"/>',
                    f'<text x="{x + width / 2}" y="{y + height / 2}" text-anchor="middle" font-family="Arial" font-size="10" fill="navy">#{label_num}</text>',
                ]
            )

    svg_elements.append("</svg>")
    svg_code = "\n".join(svg_elements)

    st.markdown(
        f'<div style="text-align: center;">{svg_code}</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Preview shows {template['labels_per_sheet']} labels arranged in {template['rows']} rows × {template['cols']} columns"
    )


def load_and_filter_labels(
    storage: LabelStorage,
    label_names: List[str],
    search_term: str,
    type_filter: str,
) -> List[Tuple[str, Dict]]:
    """
    Load and filter labels from storage based on search and type filters.
    """
    filtered_labels = []

    for label_name in label_names:
        try:
            label_data = storage.load_label(label_name)
            if not label_data:
                continue

            # Apply type filter
            if type_filter != "All Types":
                # Try to determine label type from data structure
                label_type = determine_label_type(label_data)
                if label_type != type_filter:
                    continue

            # Apply search filter
            if search_term:
                search_lower = search_term.lower()
                # Search in label name
                if search_lower in label_name.lower():
                    filtered_labels.append((label_name, label_data))
                    continue

                # Search in label data
                search_matches = False
                for key, value in label_data.items():
                    if (
                        search_lower in str(key).lower()
                        or search_lower in str(value).lower()
                    ):
                        search_matches = True
                        break

                if search_matches:
                    filtered_labels.append((label_name, label_data))
            else:
                filtered_labels.append((label_name, label_data))

        except Exception:
            continue

    return filtered_labels


def determine_label_type(label_data: Dict) -> str:
    """
    Determine the most likely label type based on the data fields.
    """
    data_keys = set(k.lower() for k in label_data.keys())
    best_match = "General"
    best_score = 0

    for label_type, schema in LABEL_SCHEMAS.items():
        if label_type == "General":
            continue

        schema_keys = set()
        for field_name, field_config in schema.items():
            schema_keys.add(field_name.lower())
            schema_keys.update(
                alias.lower() for alias in field_config.get("aliases", [])
            )

        # Calculate match score
        matches = len(data_keys.intersection(schema_keys))
        score = matches / len(schema_keys) if schema_keys else 0

        if score > best_score:
            best_score = score
            best_match = label_type

    return best_match


def calculate_optimal_layout(
    num_labels: int,
    max_per_page: int,
    page_width: float = 8.5,
    page_height: float = 11.0,
) -> Dict:
    """
    Calculate optimal label layout for given constraints.
    """
    # Available area (leaving margins)
    available_width = page_width - 1.0  # 0.5" margins on each side
    available_height = page_height - 1.5  # 0.75" margins top/bottom

    # Try different grid configurations
    best_layout = None
    best_labels_per_page = 0

    for rows in range(1, 21):  # Max 20 rows
        for cols in range(1, 11):  # Max 10 columns
            labels_per_page = rows * cols
            if labels_per_page > max_per_page:
                continue

            # Calculate label dimensions
            label_width = (
                available_width - (cols - 1) * 0.1
            ) / cols  # 0.1" spacing
            label_height = (
                available_height - (rows - 1) * 0.1
            ) / rows  # 0.1" spacing

            # Check minimum viable size
            if label_width < 1.0 or label_height < 0.5:
                continue

            # Prefer layouts that use more labels per page
            if labels_per_page > best_labels_per_page:
                best_labels_per_page = labels_per_page
                best_layout = {
                    "rows": rows,
                    "cols": cols,
                    "labels_per_sheet": labels_per_page,
                    "label_width": label_width,
                    "label_height": label_height,
                    "top_margin": 0.75,
                    "left_margin": 0.5,
                    "row_spacing": 0.1,
                    "col_spacing": 0.1,
                }

    if best_layout is None:
        # Fallback to simple single column layout
        best_layout = {
            "rows": min(10, num_labels),
            "cols": 1,
            "labels_per_sheet": min(10, num_labels),
            "label_width": available_width,
            "label_height": available_height / min(10, num_labels),
            "top_margin": 0.75,
            "left_margin": 0.5,
            "row_spacing": 0.1,
            "col_spacing": 0.1,
        }

    return best_layout


def generate_continuous_stream_pdf(
    label_data_list: List[Tuple[str, Dict]],
    optimization_mode: str,
    max_per_page: int,
    template: Dict,
    style_options: Dict,
):
    """
    Generate a continuous stream PDF with style support.
    """
    if not label_data_list:
        st.error("No labels to export")
        return

    # Load style configuration if provided
    style_config = None
    if style_options.get("style_file"):
        style_config = load_style_from_uploaded_file(
            style_options["style_file"]
        )
        if style_config:
            st.info("✅ Custom style file loaded successfully!")
        else:
            st.warning(
                "⚠️ Using default styling (style file could not be loaded)"
            )

    # Use a simple, reliable layout
    layout = {
        "rows": 4,
        "cols": 3,
        "labels_per_sheet": 12,
        "label_width": 2.5,
        "label_height": 2.0,
        "top_margin": 0.75,
        "left_margin": 0.5,
        "row_spacing": 0.25,
        "col_spacing": 0.25,
    }

    # Create PDF
    buffer = io.BytesIO()
    page_width = 8.5 * POINTS_PER_INCH
    page_height = 11.0 * POINTS_PER_INCH
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    labels_per_page = layout["labels_per_sheet"]
    total_pages = (
        len(label_data_list) + labels_per_page - 1
    ) // labels_per_page

    progress_bar = st.progress(0)
    st.write(
        f"Generating PDF with {len(label_data_list)} labels{' using custom styling' if style_config else ''}..."
    )

    current_index = 0
    for page_num in range(1, total_pages + 1):
        # Page header
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30, page_height - 30, f"Labels Page {page_num}")

        # Draw labels grid
        for row in range(layout["rows"]):
            for col in range(layout["cols"]):
                if current_index >= len(label_data_list):
                    break

                label_name, label_data = label_data_list[current_index]

                # Position
                x = (
                    layout["left_margin"] * POINTS_PER_INCH
                    + col
                    * (layout["label_width"] + layout["col_spacing"])
                    * POINTS_PER_INCH
                )
                y = (
                    page_height
                    - 60
                    - (
                        row
                        * (layout["label_height"] + layout["row_spacing"])
                        * POINTS_PER_INCH
                    )
                    - (layout["label_height"] * POINTS_PER_INCH)
                )

                label_w = layout["label_width"] * POINTS_PER_INCH
                label_h = layout["label_height"] * POINTS_PER_INCH

                # Draw border if enabled
                if style_options.get("include_borders", True):
                    c.setStrokeColor("gray")
                    c.setLineWidth(0.5)
                    c.rect(x, y, label_w, label_h, stroke=1, fill=0)

                # Alternating background shading
                if (
                    style_options.get("alternate_shading", False)
                    and (current_index % 2) == 1
                ):
                    c.setFillColor("#f8f8f8")
                    c.rect(
                        x + 1,
                        y + 1,
                        label_w - 2,
                        label_h - 2,
                        stroke=0,
                        fill=1,
                    )

                # Draw content with style support
                if style_config:
                    # Use styled rendering
                    draw_label_content_with_style(
                        c, label_data, x, y, label_w, label_h, style_config
                    )
                else:
                    # Use simple rendering
                    draw_label_content(
                        c, label_data, x, y, label_w, label_h, style_options
                    )

                # Add label numbering if enabled
                if style_options.get("include_numbering", True):
                    c.setFont("Helvetica", 6)
                    c.setFillColor("gray")
                    c.drawString(
                        x + 2, y + label_h - 8, f"#{current_index + 1}"
                    )

                current_index += 1

            if current_index >= len(label_data_list):
                break

        # Footer
        c.setFont("Helvetica", 8)
        c.setFillColor("gray")
        c.drawString(30, 20, f"Page {page_num} of {total_pages}")

        # Update progress
        progress_bar.progress(current_index / len(label_data_list))

        # Next page
        if current_index < len(label_data_list):
            c.showPage()

    # Finalize
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Download
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    style_suffix = "_styled" if style_config else ""
    filename = (
        f"labels_stream_{len(label_data_list)}{style_suffix}_{timestamp}.pdf"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="📄 Download Styled PDF Stream"
            if style_config
            else "📄 Download PDF Stream",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            type="primary",
        )

    with col2:
        st.metric("Total Pages", total_pages)
        if style_config:
            st.metric("Styling", "✅ Custom")
        else:
            st.metric("Styling", "Default")

    success_msg = (
        f"✅ Generated {total_pages} pages with {len(label_data_list)} labels"
    )
    if style_config:
        success_msg += " using custom styling"
    st.success(success_msg + "!")

    # Show style info if available
    if style_config:
        with st.expander("🎨 Applied Style Settings"):
            st.write(f"**Font**: {style_config.get('font_name', 'Helvetica')}")
            st.write(f"**Font Size**: {style_config.get('font_size', 8)}")
            st.write(f"**Show Keys**: {style_config.get('show_keys', True)}")
            st.write(
                f"**Show Values**: {style_config.get('show_values', True)}"
            )
            st.write(f"**Bold Keys**: {style_config.get('bold_keys', False)}")
            st.write(
                f"**Bold Values**: {style_config.get('bold_values', False)}"
            )


def batch_export_action(
    label_names: List[str],
    export_format: str,
    include_metadata: bool,
    storage: LabelStorage,
):
    """
    Perform batch export of all saved labels.
    """
    st.info("Batch export functionality coming soon!")
    st.write(
        f"Would export {len(label_names)} labels in format: {export_format}"
    )

    if include_metadata:
        st.write("Including metadata in export")

    # This would implement:
    # - ZIP file creation with individual PDFs
    # - Combined PDF with all labels
    # - JSON export with all data
