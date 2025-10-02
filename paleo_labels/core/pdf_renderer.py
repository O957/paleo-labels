"""PDF rendering functionality for paleo-labels."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from paleo_labels.core.measurements import inches_to_points
from paleo_labels.core.styling import LabelStyle
from paleo_labels.core.text_fitting import (
    DEFAULT_LINE_HEIGHT_RATIO,
    fit_text_to_label,
)


def render_label_to_pdf(
    canvas_obj,
    label_data: dict,
    x_offset: float,
    y_offset: float,
    style: LabelStyle,
) -> None:
    """Render a single label to PDF canvas at specified position.

    Parameters
    ----------
    canvas_obj : reportlab.pdfgen.canvas.Canvas
        ReportLab canvas object.
    label_data : dict
        Dictionary of label field-value pairs or {"__blank_label__": text}.
    x_offset : float
        X position in points.
    y_offset : float
        Y position in points.
    style : LabelStyle
        Style configuration for the label.

    Returns
    -------
    None
    """
    # calculate dimensions
    width_points = inches_to_points(style.width_inches)
    height_points = inches_to_points(style.height_inches)
    padding_points = style.padding_percent * min(width_points, height_points)
    text_width = width_points - (2 * padding_points)
    text_height = height_points - (2 * padding_points)

    # draw border
    canvas_obj.setStrokeColor(colors.black)
    canvas_obj.setLineWidth(style.border_thickness)
    canvas_obj.rect(x_offset, y_offset, width_points, height_points)

    # handle blank text labels
    if "__blank_label__" in label_data:
        _render_blank_label(
            canvas_obj,
            label_data["__blank_label__"],
            x_offset,
            y_offset,
            width_points,
            height_points,
            padding_points,
            text_width,
            text_height,
            style,
        )
        return

    # handle fielded labels
    _render_fielded_label(
        canvas_obj,
        label_data,
        x_offset,
        y_offset,
        width_points,
        height_points,
        padding_points,
        text_width,
        text_height,
        style,
    )


def _render_blank_label(
    canvas_obj,
    text: str,
    x_offset: float,
    y_offset: float,
    width_points: float,
    height_points: float,
    padding_points: float,
    text_width: float,
    text_height: float,
    style: LabelStyle,
) -> None:
    """Render a blank text label."""
    value_style = style.default_value_style
    font_name = value_style.get_font_name()
    initial_font_size = value_style.font_size

    # fit text to label
    lines = [text]
    wrapped_lines, final_font_size = fit_text_to_label(
        lines, text_width, text_height, initial_font_size, font_name
    )

    # render lines
    canvas_obj.setFont(font_name, final_font_size)
    canvas_obj.setFillColorRGB(*value_style.get_color_rgb())

    text_y = y_offset + height_points - padding_points - final_font_size

    for line in wrapped_lines:
        if text_y < y_offset + padding_points:
            break

        line_width = canvas_obj.stringWidth(line, font_name, final_font_size)
        text_x = x_offset + (width_points - line_width) / 2  # centered

        canvas_obj.drawString(text_x, text_y, line)
        text_y -= final_font_size * DEFAULT_LINE_HEIGHT_RATIO


def _render_fielded_label(
    canvas_obj,
    label_data: dict,
    x_offset: float,
    y_offset: float,
    width_points: float,
    height_points: float,
    padding_points: float,
    text_width: float,
    text_height: float,
    style: LabelStyle,
) -> None:
    """Render a fielded label with key-value pairs."""
    # build lines with styling info
    lines_with_style = []

    for field_name, field_value in label_data.items():
        field_style_config = style.get_field_style(field_name)

        # skip empty fields if configured
        if not field_value and not field_style_config.show_if_empty:
            continue

        lines_with_style.append(
            {
                "field_name": field_name,
                "field_value": field_value if field_value else "",
                "field_style": field_style_config.field_style,
                "value_style": field_style_config.value_style,
                "separator": field_style_config.separator,
            }
        )

    if not lines_with_style:
        return

    # determine font size that fits all content
    # use the largest default font size as starting point
    max_field_size = max(
        ls["field_style"].font_size for ls in lines_with_style
    )
    max_value_size = max(
        ls["value_style"].font_size for ls in lines_with_style
    )
    initial_font_size = max(max_field_size, max_value_size)

    # create text lines for fitting calculation (using field font for width estimation)
    text_lines = []
    for ls in lines_with_style:
        line_text = f"{ls['field_name']}{ls['separator']}{ls['field_value']}"
        text_lines.append(line_text)

    # use first field's font for fitting calculation
    first_font = lines_with_style[0]["field_style"].get_font_name()
    _, final_font_size = fit_text_to_label(
        text_lines, text_width, text_height, initial_font_size, first_font
    )

    # scale all font sizes proportionally if needed
    scale_factor = (
        final_font_size / initial_font_size
        if final_font_size < initial_font_size
        else 1.0
    )

    # render lines
    text_y = y_offset + height_points - padding_points - final_font_size

    for ls in lines_with_style:
        if text_y < y_offset + padding_points:
            break

        field_name = ls["field_name"]
        field_value = ls["field_value"]
        separator = ls["separator"]

        # apply scaling
        field_font_size = ls["field_style"].font_size * scale_factor
        value_font_size = ls["value_style"].font_size * scale_factor

        field_font = ls["field_style"].get_font_name()
        value_font = ls["value_style"].get_font_name()

        # draw field name
        canvas_obj.setFont(field_font, field_font_size)
        canvas_obj.setFillColorRGB(*ls["field_style"].get_color_rgb())

        text_x = x_offset + padding_points
        field_text = f"{field_name}{separator}"
        canvas_obj.drawString(text_x, text_y, field_text)

        # draw value
        if field_value:
            field_width = canvas_obj.stringWidth(
                field_text, field_font, field_font_size
            )
            canvas_obj.setFont(value_font, value_font_size)
            canvas_obj.setFillColorRGB(*ls["value_style"].get_color_rgb())
            canvas_obj.drawString(text_x + field_width, text_y, field_value)

        text_y -= (
            max(field_font_size, value_font_size) * DEFAULT_LINE_HEIGHT_RATIO
        )


def create_pdf_from_labels(
    labels_data: list[dict], style: LabelStyle
) -> bytes:
    """Create PDF from labels data with optimal layout.

    Parameters
    ----------
    labels_data : list[dict]
        List of label data dictionaries.
    style : LabelStyle
        Style configuration to apply to all labels.

    Returns
    -------
    bytes
        PDF file content as bytes.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # calculate dimensions
    width_points = inches_to_points(style.width_inches)
    height_points = inches_to_points(style.height_inches)

    margin_points = inches_to_points(0.1875)
    page_width_points = inches_to_points(8.5)
    page_height_points = inches_to_points(11)

    label_spacing_points = inches_to_points(0.125)
    usable_width = page_width_points - (2 * margin_points)
    usable_height = page_height_points - (2 * margin_points)

    label_width_with_spacing = width_points + label_spacing_points
    label_height_with_spacing = height_points + label_spacing_points

    labels_per_row = int(usable_width // label_width_with_spacing)
    labels_per_col = int(usable_height // label_height_with_spacing)

    labels_per_row = min(labels_per_row, 3)
    labels_per_col = min(labels_per_col, 10)

    for current_label, label_data in enumerate(labels_data):
        if (
            current_label > 0
            and current_label % (labels_per_row * labels_per_col) == 0
        ):
            c.showPage()

        row = (
            current_label % (labels_per_row * labels_per_col)
        ) // labels_per_row
        col = current_label % labels_per_row

        x = margin_points + col * label_width_with_spacing
        y = (
            page_height_points
            - margin_points
            - height_points
            - row * label_height_with_spacing
        )

        render_label_to_pdf(c, label_data, x, y, style)

    c.save()
    return buffer.getvalue()
