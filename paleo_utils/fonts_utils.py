"""
Utilities to support the
use of some pre-packaged
fonts.
"""

from pathlib import Path

# the font directory "fonts" should be
# contained within the poetry package
FONT_DIR = Path(__file__).parent / "fonts"


def get_font_path(font_name: str) -> str:
    """
    Returns the full path of a font file by name.

    Parameters
    ----------
    font_name
        The name of the font file
        (e.g., "texgyreschola-bold.otf").

    Returns
    -------
    str
        Full path to the font file.
    """
    font_path = FONT_DIR / font_name
    if not font_path.exists():
        raise FileNotFoundError(f"Font {font_name} not found in {FONT_DIR}")
    return str(font_path)
