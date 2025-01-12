"""
Utilities to support the
use of some pre-packaged
fonts.
"""

import pathlib

import attrs

# the font directory "fonts" should be
# contained within the poetry package
FONT_DIR = pathlib.Path(__file__).parent / "fonts"


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


def validate_save_directory(
    instance: any,
    attribute: attrs.Attribute,
    value: str | pathlib.Path,
):
    """
    NOTE: Does not check if file already
    exists by the same name.
    """
    # convert str path to path
    if isinstance(value, str):
        value = pathlib.Path(value)
    # check if path exists, if not, err
    if not value.exists():
        raise ValueError(
            f"{attribute.name} must be a valid path; got '{value}', which does not exist."
        )


def combine_multiple_labels():
    """
    Combines multiple labels.
    """
    pass


def make_dual_label_sheet():
    """
    Aligns labels on front and back
    of article page so they are multi-
    sided.
    """
    pass
