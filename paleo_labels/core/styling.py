"""Styling system with per-field customization for paleo-labels."""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path

import tomli


@dataclass
class TextStyle:
    """Text styling configuration.

    Parameters
    ----------
    font_family : str
        Font family name.
    font_size : float
        Font size in points.
    color : str
        Color in hex format.
    bold : bool
        Whether text is bold.
    italic : bool
        Whether text is italic.
    """

    font_family: str = "Courier"
    font_size: float = 10.0
    color: str = "#000000"
    bold: bool = False
    italic: bool = False

    def get_font_name(self) -> str:
        """Get ReportLab font name with style variants.

        Returns
        -------
        str
            Font name with appropriate style suffix.
        """
        font_variants = {
            "Helvetica": {
                (False, False): "Helvetica",
                (True, False): "Helvetica-Bold",
                (False, True): "Helvetica-Oblique",
                (True, True): "Helvetica-BoldOblique",
            },
            "Times-Roman": {
                (False, False): "Times-Roman",
                (True, False): "Times-Bold",
                (False, True): "Times-Italic",
                (True, True): "Times-BoldItalic",
            },
            "Courier": {
                (False, False): "Courier",
                (True, False): "Courier-Bold",
                (False, True): "Courier-Oblique",
                (True, True): "Courier-BoldOblique",
            },
        }

        if self.font_family in font_variants:
            return font_variants[self.font_family][(self.bold, self.italic)]
        return self.font_family

    def get_color_rgb(self) -> tuple[float, float, float]:
        """Get RGB color values normalized to 0-1 range.

        Returns
        -------
        tuple[float, float, float]
            RGB values as floats between 0 and 1.
        """
        hex_color = self.color.lstrip("#")
        r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return (r / 255.0, g / 255.0, b / 255.0)


@dataclass
class FieldStyle:
    """Style configuration for a single field.

    Parameters
    ----------
    field_style : TextStyle
        Style for the field name/group.
    value_style : TextStyle
        Style for the field value/content.
    separator : str
        Separator between field and value.
    show_if_empty : bool
        Whether to show field when value is empty.
    """

    field_style: TextStyle = dataclass_field(default_factory=TextStyle)
    value_style: TextStyle = dataclass_field(default_factory=TextStyle)
    separator: str = ": "
    show_if_empty: bool = True


@dataclass
class LabelStyle:
    """Complete label styling configuration.

    Parameters
    ----------
    width_inches : float
        Label width in inches.
    height_inches : float
        Label height in inches.
    border_thickness : float
        Border thickness in points.
    padding_percent : float
        Padding as percentage of smaller dimension.
    default_field_style : TextStyle
        Default style for field names.
    default_value_style : TextStyle
        Default style for field values.
    default_separator : str
        Default separator between field and value.
    show_empty_fields : bool
        Global setting for showing empty fields.
    field_overrides : dict
        Per-field style overrides keyed by field name.
    """

    width_inches: float = 3.25
    height_inches: float = 2.25
    border_thickness: float = 1.5
    padding_percent: float = 0.05
    default_field_style: TextStyle = dataclass_field(
        default_factory=lambda: TextStyle(bold=True)
    )
    default_value_style: TextStyle = dataclass_field(default_factory=TextStyle)
    default_separator: str = ": "
    show_empty_fields: bool = True
    field_overrides: dict[str, FieldStyle] = dataclass_field(
        default_factory=dict
    )

    def get_field_style(self, field_name: str) -> FieldStyle:
        """Get style for a specific field, using overrides if available.

        Parameters
        ----------
        field_name : str
            Name of the field.

        Returns
        -------
        FieldStyle
            Style configuration for the field.
        """
        if field_name in self.field_overrides:
            return self.field_overrides[field_name]

        return FieldStyle(
            field_style=self.default_field_style,
            value_style=self.default_value_style,
            separator=self.default_separator,
            show_if_empty=self.show_empty_fields,
        )


def load_style_from_toml(toml_path: Path) -> LabelStyle:
    """Load label style from TOML file.

    Parameters
    ----------
    toml_path : Path
        Path to TOML style file.

    Returns
    -------
    LabelStyle
        Loaded style configuration.
    """
    with open(toml_path, "rb") as f:
        data = tomli.load(f)

    style = LabelStyle()

    # dimensions
    if "dimensions" in data:
        style.width_inches = data["dimensions"].get(
            "width_inches", style.width_inches
        )
        style.height_inches = data["dimensions"].get(
            "height_inches", style.height_inches
        )
        style.border_thickness = data["dimensions"].get(
            "border_thickness", style.border_thickness
        )
        style.padding_percent = data["dimensions"].get(
            "padding_percent", style.padding_percent
        )

    # default field style
    if "field_style" in data:
        fs = data["field_style"]
        style.default_field_style = TextStyle(
            font_family=fs.get("font_family", "Courier"),
            font_size=fs.get("font_size", 10.0),
            color=fs.get("color", "#000000"),
            bold=fs.get("bold", True),
            italic=fs.get("italic", False),
        )

    # default value style
    if "value_style" in data:
        vs = data["value_style"]
        style.default_value_style = TextStyle(
            font_family=vs.get("font_family", "Courier"),
            font_size=vs.get("font_size", 10.0),
            color=vs.get("color", "#000000"),
            bold=vs.get("bold", False),
            italic=vs.get("italic", False),
        )

    # separator
    style.default_separator = data.get("separator", ": ")
    style.show_empty_fields = data.get("show_empty_fields", True)

    # field overrides
    if "field_overrides" in data:
        for field_name, override_data in data["field_overrides"].items():
            field_style = TextStyle(**override_data.get("field_style", {}))
            value_style = TextStyle(**override_data.get("value_style", {}))
            separator = override_data.get("separator", style.default_separator)
            show_if_empty = override_data.get(
                "show_if_empty", style.show_empty_fields
            )

            style.field_overrides[field_name] = FieldStyle(
                field_style=field_style,
                value_style=value_style,
                separator=separator,
                show_if_empty=show_if_empty,
            )

    return style
