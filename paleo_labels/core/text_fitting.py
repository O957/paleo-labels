"""Text fitting and wrapping utilities for paleo-labels."""

from reportlab.pdfbase.pdfmetrics import stringWidth

DEFAULT_LINE_HEIGHT_RATIO = 1.2
MIN_FONT_SIZE = 6.0


def wrap_text_to_width(
    text: str,
    width_points: float,
    font_size: float,
    font_name: str = "Courier",
) -> list[str]:
    """Wrap text to fit within specified width.

    Parameters
    ----------
    text : str
        Text to wrap.
    width_points : float
        Available width in points.
    font_size : float
        Font size in points.
    font_name : str
        Font name for width calculations.

    Returns
    -------
    list[str]
        List of wrapped text lines.
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        test_width = stringWidth(test_line, font_name, font_size)

        if test_width <= width_points:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # word is too long, add it anyway
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else [""]


def fit_text_to_label(
    lines: list[str],
    available_width: float,
    available_height: float,
    initial_font_size: float,
    font_name: str,
    min_font_size: float = MIN_FONT_SIZE,
) -> tuple[list[str], float]:
    """Fit text within label boundaries by wrapping and scaling font.

    Parameters
    ----------
    lines : list[str]
        Initial text lines to fit.
    available_width : float
        Available width in points.
    available_height : float
        Available height in points.
    initial_font_size : float
        Starting font size in points.
    font_name : str
        Font name for width calculations.
    min_font_size : float
        Minimum readable font size (default 6.0pt).

    Returns
    -------
    tuple[list[str], float]
        Wrapped lines and final font size that fits.

    Algorithm
    ---------
    1. Start with initial_font_size
    2. Wrap all text to available_width
    3. Check if total height fits in available_height
    4. If no: reduce font_size by 0.5pt and repeat
    5. Continue until fits or min_font_size reached
    6. If min_font_size still doesn't fit: truncate content
    """
    font_size = initial_font_size

    while font_size >= min_font_size:
        # wrap all lines at current font size
        wrapped_lines = []
        for line in lines:
            wrapped_lines.extend(
                wrap_text_to_width(line, available_width, font_size, font_name)
            )

        # calculate total height needed
        line_height = font_size * DEFAULT_LINE_HEIGHT_RATIO
        total_height = len(wrapped_lines) * line_height

        # check if fits
        if total_height <= available_height:
            return wrapped_lines, font_size

        # reduce font size and try again
        font_size -= 0.5

    # minimum font size still doesn't fit - truncate with warning
    max_lines = int(
        available_height / (min_font_size * DEFAULT_LINE_HEIGHT_RATIO)
    )
    return wrapped_lines[:max_lines], min_font_size
