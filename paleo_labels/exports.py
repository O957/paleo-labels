"""
Advanced export system for Phase 2.
Handles multi-label PDF sheets, batch exports, and print layouts.
"""

import io
from typing import Dict, List, Optional, Tuple

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

try:
    from .storage import LabelStorage
except ImportError:
    from storage import LabelStorage

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
        "col_spacing": 0.125
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
        "col_spacing": 0.25
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
        "col_spacing": 0.5
    }
}


def exports_ui():
    """
    Main UI for advanced export features.
    """
    st.header("Advanced Export")
    st.write("Export multiple labels to professional print layouts")
    
    if 'storage' not in st.session_state:
        st.error("Storage not initialized")
        return
    
    # Export tabs
    tab1, tab2, tab3 = st.tabs(["Multi-Label Sheet", "Batch Export", "Print Layouts"])
    
    with tab1:
        multi_label_sheet_ui()
    
    with tab2:
        batch_export_ui()
    
    with tab3:
        print_layouts_ui()


def multi_label_sheet_ui():
    """
    UI for creating multi-label PDF sheets.
    """
    st.subheader("Multi-Label PDF Sheet")
    st.write("Create professional label sheets with multiple labels")
    
    # Check for labels in multi-label session
    if 'multi_labels' not in st.session_state or not st.session_state.multi_labels:
        st.info("No labels found. Create labels in Batch Processing > Multi-Label Session first.")
        return
    
    labels = st.session_state.multi_labels
    st.write(f"**Available Labels: {len(labels)}**")
    
    # Template selection
    st.subheader("Sheet Layout")
    
    template_key = st.selectbox(
        "Layout Template:",
        list(AVERY_TEMPLATES.keys()),
        format_func=lambda x: AVERY_TEMPLATES[x]["name"]
    )
    
    template = AVERY_TEMPLATES[template_key]
    
    # Show template info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Labels per Sheet", template["labels_per_sheet"])
    with col2:
        st.metric("Rows × Columns", f"{template['rows']} × {template['cols']}")
    with col3:
        st.metric("Label Size", f"{template['label_width']}\" × {template['label_height']}\"")
    
    # Custom template editor
    if template_key == "custom":
        st.subheader("Custom Layout Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            template["rows"] = st.number_input("Rows:", value=template["rows"], min_value=1, max_value=20)
            template["cols"] = st.number_input("Columns:", value=template["cols"], min_value=1, max_value=10)
            template["label_width"] = st.number_input("Label Width (in):", value=template["label_width"], min_value=0.5, max_value=8.0, step=0.1)
            template["label_height"] = st.number_input("Label Height (in):", value=template["label_height"], min_value=0.5, max_value=10.0, step=0.1)
        
        with col2:
            template["top_margin"] = st.number_input("Top Margin (in):", value=template["top_margin"], min_value=0.0, max_value=2.0, step=0.1)
            template["left_margin"] = st.number_input("Left Margin (in):", value=template["left_margin"], min_value=0.0, max_value=2.0, step=0.1)
            template["row_spacing"] = st.number_input("Row Spacing (in):", value=template["row_spacing"], min_value=0.0, max_value=1.0, step=0.1)
            template["col_spacing"] = st.number_input("Column Spacing (in):", value=template["col_spacing"], min_value=0.0, max_value=1.0, step=0.1)
        
        template["labels_per_sheet"] = template["rows"] * template["cols"]
        st.write(f"**Total labels per sheet: {template['labels_per_sheet']}**")
    
    # Label selection
    st.subheader("Label Selection")
    
    selected_labels = st.multiselect(
        "Choose labels to include:",
        options=range(len(labels)),
        default=list(range(min(len(labels), template["labels_per_sheet"]))),
        format_func=lambda x: f"{labels[x]['name']} ({labels[x]['type']})"
    )
    
    if not selected_labels:
        st.warning("Please select at least one label.")
        return
    
    sheets_needed = (len(selected_labels) + template["labels_per_sheet"] - 1) // template["labels_per_sheet"]
    st.info(f"Will create {sheets_needed} sheet(s) for {len(selected_labels)} labels")
    
    # Generate sheet
    if st.button("🖨️ Generate Multi-Label Sheet", type="primary"):
        generate_multi_label_sheet(selected_labels, template, labels)


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
        ["Individual PDFs (ZIP)", "Single Combined PDF", "Label Data (JSON)"]
    )
    
    include_metadata = st.checkbox(
        "Include Metadata",
        value=True,
        help="Include creation dates, label types, etc."
    )
    
    if st.button("📦 Export All Labels", type="primary"):
        batch_export_action(saved_labels, export_format, include_metadata, storage)


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


def generate_multi_label_sheet(selected_indices: List[int], template: Dict, all_labels: List[Dict]):
    """
    Generate a multi-label PDF sheet.
    """
    selected_labels = [all_labels[i] for i in selected_indices]
    
    # Create PDF buffer
    buffer = io.BytesIO()
    page_width = 8.5 * POINTS_PER_INCH
    page_height = 11.0 * POINTS_PER_INCH
    
    c = canvas.Canvas(buffer, pagesize=letter)
    
    labels_per_sheet = template["labels_per_sheet"]
    current_label_index = 0
    
    with st.spinner("Generating multi-label sheet..."):
        progress_bar = st.progress(0)
        
        while current_label_index < len(selected_labels):
            # Draw labels on current page
            for row in range(template["rows"]):
                for col in range(template["cols"]):
                    if current_label_index >= len(selected_labels):
                        break
                    
                    label = selected_labels[current_label_index]
                    
                    # Calculate position
                    x = template["left_margin"] * POINTS_PER_INCH + col * (template["label_width"] + template["col_spacing"]) * POINTS_PER_INCH
                    y = page_height - (template["top_margin"] * POINTS_PER_INCH + row * (template["label_height"] + template["row_spacing"]) * POINTS_PER_INCH + template["label_height"] * POINTS_PER_INCH)
                    
                    # Draw label border
                    c.setStrokeColor("gray")
                    c.rect(x, y, template["label_width"] * POINTS_PER_INCH, template["label_height"] * POINTS_PER_INCH, stroke=1, fill=0)
                    
                    # Draw label content
                    draw_label_content(c, label["data"], x, y, template["label_width"] * POINTS_PER_INCH, template["label_height"] * POINTS_PER_INCH)
                    
                    current_label_index += 1
                    progress_bar.progress(current_label_index / len(selected_labels))
            
            # Start new page if more labels
            if current_label_index < len(selected_labels):
                c.showPage()
    
    # Finalize PDF
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Download button
    st.download_button(
        label="📄 Download Multi-Label Sheet",
        data=pdf_bytes,
        file_name="multi_label_sheet.pdf",
        mime="application/pdf"
    )
    
    st.success(f"Generated multi-label sheet with {len(selected_labels)} labels!")


def draw_label_content(c: canvas.Canvas, label_data: Dict, x: float, y: float, width: float, height: float):
    """
    Draw label content within the given bounds.
    """
    if not label_data:
        return
    
    # Simple text layout
    font_size = 10
    line_height = font_size * 1.2
    margin = 4
    
    text_x = x + margin
    text_y = y + height - margin - font_size
    
    c.setFont("Helvetica", font_size)
    c.setFillColor("black")
    
    for key, value in label_data.items():
        if text_y < y + margin:  # Check if we have space
            break
        
        text = f"{key}: {value}"
        # Truncate if too long
        max_chars = int((width - 2 * margin) / (font_size * 0.6))
        if len(text) > max_chars:
            text = text[:max_chars-3] + "..."
        
        c.drawString(text_x, text_y, text)
        text_y -= line_height


def batch_export_action(label_names: List[str], export_format: str, include_metadata: bool, storage: LabelStorage):
    """
    Perform batch export of all saved labels.
    """
    st.info("Batch export functionality coming soon!")
    st.write(f"Would export {len(label_names)} labels in format: {export_format}")
    
    if include_metadata:
        st.write("Including metadata in export")
    
    # This would implement:
    # - ZIP file creation with individual PDFs
    # - Combined PDF with all labels
    # - JSON export with all data