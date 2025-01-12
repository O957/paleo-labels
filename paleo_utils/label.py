"""
Classes for creating labels for use in
paleontological collections. Labels have
headers, bodies, and footers. Labels can
have QR codes and watermarks.
"""

import pathlib
from typing import Iterable

import attrs
import matplotlib.pyplot as plt
import toml
from matplotlib.colors import CSS4_COLORS
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Rectangle

SUPPORTED_COLORS = list(CSS4_COLORS.keys())
SUPPORTED_STYLES = [
    "bold",
    "regular",
    "italics",
    "underlined",
    "small_caps",
]
SUPPORTED_FONTS = ["Iosevka", "TeX Gyra Schola", "Arial", "Times New Roman"]
SUPPORTED_POSITIONS = [
    "best",
    "upper-left",
    "upper-center",
    "upper-right",
    "middle-left",
    "middle-center",
    "middle-right",
    "lower-left",
    "lower-center",
    "lower-right",
]
SUPPORTED_ALIGNMENTS = ["center", "left", "right"]
SUPPORTED_BORDERS = ["dotted", "solid", "dashed"]
SUPPORTED_IMAGE_FORMATS = [
    ".jpg",
    ".png",
    ".heic",
]


def validate_save_directory(
    instance: any,
    attribute: attrs.Attribute,
    save_dir: str | pathlib.Path,
):
    # convert str path to path
    if isinstance(save_dir, str):
        save_dir = pathlib.Path(save_dir)
    # check if path exists, if not, err
    if not save_dir.exists():
        raise ValueError(
            f"{attribute.name} must be a valid path; got '{save_dir}', which does not exist."
        )


@attrs.define(kw_only=True)
class Label:
    """
    Class for a Label. Each Label consists
    of a header, body, and footer section.
    Selected dimensions influence the section
    size. Sections can consist of images.
    All sections have "titles" and "content"
    text (e.g., in "Genus: Examplicus",
    Genus is the title and Examplicus is the
    content).
    """

    # REQUIRED INPUT

    body: list[dict[str, str]] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(dict),
            iterable_validator=attrs.validators.instance_of(list),
        )
    )
    header: list[dict[str, str]] | None = None
    footer: list[dict[str, str]] | None = None

    # OPTIONS FOR SAVING

    save_path: str | pathlib.Path = attrs.field(
        validator=[
            attrs.validators.instance_of((str, pathlib.Path)),
            validate_save_directory,
        ]
    )
    save_as_image: bool = attrs.field(
        default=True,
        validator=attrs.validators.instance_of(bool),
    )
    image_format: str = attrs.field(
        default="png",
        validator=[
            attrs.validators.in_(SUPPORTED_IMAGE_FORMATS),
            attrs.validators.instance_of(str),
        ],
    )
    save_as_text: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )
    save_as_svg: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )
    save_as_tex: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )
    save_as_json: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )

    # OPTIONS FOR BODY, HEADER, FOOTER FONT SIZE

    body_font_path: str = attrs.field(
        default="TeX Gyra Schola",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_FONTS),
        ],
    )
    body_title_font_size: int = attrs.field(
        default=10,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(20),
        ],
    )
    body_content_font_size: int = attrs.field(
        default=12,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(20),
        ],
    )

    body_title_font_styling: str = attrs.field(
        default="bold",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_STYLES),
        ],
    )
    body_content_font_styling: str = attrs.field(
        default="regular",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_STYLES),
        ],
    )
    body_title_font_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )
    body_content_font_color: str = attrs.field(
        default="darkblue",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )

    header_font_path: str = attrs.field(
        default="TeX Gyra Schola",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_FONTS),
        ],
    )
    header_title_font_size: int = attrs.field(
        default=14,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(30),
        ],
    )
    header_content_font_size: int = attrs.field(
        default=12,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(30),
        ],
    )

    header_title_font_styling: str = attrs.field(
        default="bold",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_STYLES),
        ],
    )
    header_content_font_styling: str = attrs.field(
        default="italic",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_STYLES),
        ],
    )
    header_title_font_color: str = attrs.field(
        default="blue",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )
    header_content_font_color: str = attrs.field(
        default="darkgreen",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )

    footer_font_path: str = attrs.field(
        default="TeX Gyra Schola",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_FONTS),
        ],
    )
    footer_title_font_size: int = attrs.field(
        default=12,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(30),
        ],
    )
    footer_content_font_size: int = attrs.field(
        default=10,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(30),
        ],
    )
    footer_title_font_styling: str = attrs.field(
        default="bold",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_STYLES),
        ],
    )
    footer_content_font_styling: str = attrs.field(
        default="regular",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_STYLES),
        ],
    )
    footer_title_font_color: str = attrs.field(
        default="purple",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )
    footer_content_font_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )

    # OPTIONS FOR HEADER, BODY, AND FOOTER BORDERS

    header_border_style: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.and_(
                attrs.validators.instance_of(str),
                attrs.validators.in_(SUPPORTED_BORDERS),
            )
        ),
    )
    header_border_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )
    header_border_size: float = attrs.field(
        default=0.05,
        validator=[
            attrs.validators.ge(0.01),
            attrs.validators.le(0.50),
        ],
    )

    body_border_style: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.and_(
                attrs.validators.instance_of(str),
                attrs.validators.in_(SUPPORTED_BORDERS),
            )
        ),
    )
    body_border_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )
    body_border_size: float = attrs.field(
        default=0.05,
        validator=[
            attrs.validators.ge(0.01),
            attrs.validators.le(0.50),
        ],
    )

    footer_border_style: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.and_(
                attrs.validators.instance_of(str),
                attrs.validators.in_(SUPPORTED_BORDERS),
            )
        ),
    )
    footer_border_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )
    footer_border_size: float = attrs.field(
        default=0.05,
        validator=[
            attrs.validators.ge(0.01),
            attrs.validators.le(0.50),
        ],
    )

    # BACKGROUND COLORS FOR BODY, HEADER, AND FOOTER

    label_background_color: str = attrs.field(
        default="white",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )

    header_background_color: str = attrs.field(
        default="white",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )

    body_background_color: str = attrs.field(
        default="white",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )

    footer_background_color: str = attrs.field(
        default="white",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )

    # TITLES TO HIDE FOR BODY, HEADER, AND FOOTER

    body_titles_to_hide: list[str] | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.deep_iterable(
                member_validator=attrs.validators.instance_of(str),
                iterable_validator=attrs.validators.instance_of(list),
            )
        ),
    )

    header_titles_to_hide: list[str] | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.deep_iterable(
                member_validator=attrs.validators.instance_of(str),
                iterable_validator=attrs.validators.instance_of(list),
            )
        ),
    )

    footer_titles_to_hide: list[str] | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.deep_iterable(
                member_validator=attrs.validators.instance_of(str),
                iterable_validator=attrs.validators.instance_of(list),
            )
        ),
    )

    # SPACING BETWEEN LINES FOR BODY, HEADER, AND FOOTER

    body_spaces_between_lines: int = attrs.field(
        default=0,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(2),
        ],
    )

    header_spaces_between_lines: int = attrs.field(
        default=0,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(2),
        ],
    )

    footer_spaces_between_lines: int = attrs.field(
        default=0,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(2),
        ],
    )

    # SPACES BETWEEN SECTIONS

    space_between_sections: int = attrs.field(
        default=0,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(0),
            attrs.validators.le(2),
        ],
    )

    # OPTIONS FOR TEXT ALIGNMENT

    text_alignment: str = attrs.field(
        default="center",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_ALIGNMENTS),
        ],
    )
    text_flush: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )

    # OPTIONS FOR LABEL DIMENSIONS

    image_dots_per_inch: int = attrs.field(
        default=150,
        validator=[
            attrs.validators.ge(50),
            attrs.validators.le(500),
        ],
    )
    dimensions: tuple[float, float] = attrs.field(
        default=(4.0, 4.0),
        validator=[
            attrs.validators.deep_iterable(
                member_validator=attrs.validators.and_(
                    attrs.validators.ge(0.5),
                    attrs.validators.le(20.0),
                ),
                iterable_validator=attrs.validators.instance_of(tuple),
            ),
        ],
    )
    dimensions_in_inches: bool = attrs.field(
        default=True,
        validator=attrs.validators.instance_of(bool),
    )
    dimensions_in_centimeters: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )
    dimensions_as_inches: tuple[float, float] = attrs.field(init=False)
    dimensions_as_centimeters: tuple[float, float] = attrs.field(init=False)
    dimensions_as_pixels: tuple[float, float] = attrs.field(init=False)
    dimensions_unit: str = attrs.field(init=False)

    # OPTIONS FOR BORDER

    border_style: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.and_(
                attrs.validators.instance_of(str),
                attrs.validators.in_(SUPPORTED_BORDERS),
            )
        ),
    )
    border_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_COLORS),
        ],
    )
    border_size: float = attrs.field(
        default=0.05,
        validator=[
            attrs.validators.ge(0.01),
            attrs.validators.le(0.50),
        ],  # TODO: raise error depending on border size
    )
    border_padding_from_edge: float = attrs.field(
        default=0.05,
        validator=[
            attrs.validators.ge(0.01),
            attrs.validators.le(0.50),
        ],
    )

    def _convert_values_to_pixels(
        self, values: Iterable[float], unit: str
    ) -> float:
        """
        Internal method to convert unit
        values to pixels.
        """
        if unit == "inches":
            return [value * self.image_dots_per_inch for value in values]
        elif unit == "centimeters":
            return [
                value * (self.image_dots_per_inch / 2.54) for value in values
            ]
        else:
            raise ValueError("Unit must be either 'inches' or 'centimeters'")

    def _convert_values_to_inches(
        self, values: Iterable[float], unit: str
    ) -> list[float]:
        """
        Internal method to convert unit
        values to inches.
        """
        if unit == "pixels":
            return [value / self.image_dots_per_inch for value in values]
        elif unit == "centimeters":
            return [value / 2.54 for value in values]
        else:
            raise ValueError("Unit must be either 'pixels' or 'centimeters'")

    def _convert_values_to_centimeters(
        self, values: Iterable[float], unit: str
    ) -> list[float]:
        """
        Internal method to convert unit
        values to centimeters.
        """
        if unit == "pixels":
            return [
                value / self.image_dots_per_inch * 2.54 for value in values
            ]
        elif unit == "inches":
            return [value * 2.54 for value in values]
        else:
            raise ValueError("Unit must be either 'pixels' or 'inches'")

    def __attrs_post_init__(self):

        if self.dimensions_in_centimeters and self.dimensions_in_inches:
            raise ValueError(
                "You cannot specify both dimensions_in_inches and dimensions_in_centimeters. Please provide only one."
            )
        if self.dimensions_in_centimeters:
            self.dimensions_unit = "centimeters"
            self.dimensions_as_centimeters = self.dimensions
            self.dimensions_as_inches = self._convert_values_to_inches(
                values=self.dimensions,
                unit=self.dimensions_unit,
            )
            self.dimensions_as_pixels = self._convert_values_to_pixels(
                values=self.dimensions_as_inches,
                unit="inches",
            )
        elif self.dimensions_in_inches:
            # set dimensions in inches
            self.dimensions_unit = "inches"
            self.dimensions_as_inches = self.dimensions
            # convert to centimeters and pixels using the helper methods
            self.dimensions_as_centimeters = (
                self._convert_values_to_centimeters(
                    values=self.dimensions,
                    unit=self.dimensions_unit,
                )
            )
            self.dimensions_as_pixels = self._convert_values_to_pixels(
                values=self.dimensions,
                unit=self.dimensions_unit,
            )
        elif not (self.dimensions_in_centimeters or self.dimensions_in_inches):
            raise ValueError(
                "You must specify either dimensions_in_centimeters or dimensions_in_inches."
            )

    @classmethod
    def from_dict(cls, data: dict):
        """
        Instantiates a Label object from a
        dictionary.
        """
        return cls(**data)

    @classmethod
    def from_toml(cls, file_path: str):
        """
        Load a Label configuration from a
        TOML file.
        """
        with open(file_path, "r") as f:
            data = toml.load(f)
        return cls(**data)

    def _create_section(self, ax, content, position, width, height):
        """
        Create a text box or an image for a
        given section (header, body, footer).
        """
        if isinstance(content, list):
            # render text
            text = "\n".join(
                [
                    f"{key}: {value}"
                    for group in content
                    for key, value in group.items()
                ]
            )
            ax.text(
                position[0] + width / 2,
                position[1] + height / 2,
                text,
                ha="center",
                va="center",
                fontsize=self.font_size,
                color=self.group_content_color,
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor="white",
                    edgecolor="black",
                ),
            )
        elif isinstance(content, str):
            # render image
            img = plt.imread(content)
            imagebox = OffsetImage(img, zoom=0.2)
            image_annot = AnnotationBbox(
                imagebox,
                (position[0] + width / 2, position[1] + height / 2),
                frameon=False,
            )
            ax.add_artist(image_annot)

    def render(self):
        """
        Render the label with header, body,
        footer, and images.
        """
        fig, ax = plt.subplots(figsize=self.dimensions)
        ax.set_xlim(0, self.dimensions[0])
        ax.set_ylim(0, self.dimensions[1])
        ax.set_aspect("equal")
        ax.axis("off")

        # background color
        ax.add_patch(
            Rectangle((0, 0), *self.dimensions, color=self.background_color)
        )

        # border
        if self.border_style:
            border_size = self.border_size
            ax.add_patch(
                Rectangle(
                    (
                        self.border_padding_from_edge,
                        self.border_padding_from_edge,
                    ),
                    self.dimensions[0] - 2 * self.border_padding_from_edge,
                    self.dimensions[1] - 2 * self.border_padding_from_edge,
                    edgecolor=self.border_color,
                    facecolor="none",
                    linewidth=border_size,
                )
            )

        # section dimensions
        section_height = self.dimensions[1] / 3
        width = self.dimensions[0]

        # render header
        if self.header or self.header_image:
            self._create_section(
                ax,
                self.header if self.header else self.header_image,
                position=(0, 2 * section_height),
                width=width,
                height=section_height,
            )

        # render body
        if self.body:
            self._create_section(
                ax,
                self.body,
                position=(0, section_height),
                width=width,
                height=section_height,
            )

        # render footer
        if self.footer or self.footer_image:
            self._create_section(
                ax,
                self.footer if self.footer else self.footer_image,
                position=(0, 0),
                width=width,
                height=section_height,
            )

        plt.show()

    def _save_as_plain_text(self):
        """Saves label as plain text."""
        pass

    def _save_as_svg(self):
        """Saves label as SVG."""
        pass

    def _save_as_json(self):
        """Saves label as SVG."""
        pass

    def _save_as_image(self):
        """Saves label as an image."""
        pass

    def save(self):
        """
        Method to the save based on the specified
        formats. Each label is expected to start
        out as a Python string.
        """
        if self.save_as_text:
            self._save_as_plain_text()
        if self.save_as_tex:
            self._save_as_tex()
        if self.save_as_svg:
            self._save_as_svg()
        if self.save_as_image == "image":
            self._save_as_image()

        # if self.save_as_image:
        #     self.label.save(self.save_path, self.image_format)

        # if self.save_as_text:
        #     with open(self.save_path, "w") as f:
        #         f.write(self.text)

    def _add_qr_code():
        pass

    def _add_watermark():
        pass


@attrs.define(kw_only=True)
class CollectionsLabel(Label):
    """
    A label for collections specimens, i.e.
    labels involving more details than
    fossil systematics. The kwargs parameter
    used is the group title.
    """

    collection: str | None = attrs.field(default=None)
    id_number: str | None = attrs.field(default=None)
    collector: str | None = attrs.field(default=None)
    species: str | None = attrs.field(default=None)
    species_author: str | None = attrs.field(default=None)
    common_name: str | None = attrs.field(default=None)
    location: str | None = attrs.field(default=None)
    coordinates: tuple[float, float] | None = attrs.field(default=None)
    coordinates_separate: bool = attrs.field(default=False)
    date_found: str | None = attrs.field(default=None)
    date_cataloged: str | None = attrs.field(default=None)
    formation: str | None = attrs.field(default=None)
    formation_author: str | None = attrs.field(default=None)
    chrono_age: str | None = attrs.field(default=None)
    chrono_age_author: str | None = attrs.field(default=None)
    size: str | None = attrs.field(default=None)
    link: str | None = attrs.field(default=None)

    default_titles = {
        "collection": "Collection: ",
        "id_number": "ID Number: ",
        "collector": "Collector: ",
        "species": "Scientific Name: ",
        "species_author": "Species Author: ",
        "common_name": "Common Name: ",
        "location": "Location: ",
        "coordinates": "Coordinates: ",
        "date_found": "Date Found: ",
        "date_cataloged": "Date Cataloged: ",
        "formation": "Formation: ",
        "formation_author": "Formation Author: ",
        "chrono_age": "Age: ",
        "chrono_age_author": "Age Author: ",
        "size": "Size: ",
        "link": "Link: ",
    }

    title_overrides: dict[str, str] = attrs.field(
        factory=dict
    )  # empty by default

    _ordered_kwargs: dict = attrs.field(init=False)

    def __init__(self, **kwargs):
        self._ordered_kwargs = {key: kwargs[key] for key in kwargs}

    def __attrs_post_init__(self):
        # update title_overrides with any user-provided overrides
        if self.title_overrides:
            # merge user-provided titles, overriding defaults
            for (
                key,
                value,
            ) in self.title_overrides.items():
                if key in self.default_titles:
                    self.default_titles[key] = value

    def _get_collections_attrs(self):
        label_attrs = {attr.name for attr in Label.__attrs_attrs__}
        # collections_attrs = {
        #     attr.name: getattr(self, attr.name)
        #     for attr in self.__attrs_attrs__
        #     if attr.name not in label_attrs
        # }
        # print(self.__attrs_attrs__)
        collections_attrs = {
            key: value
            for key, value in self._ordered_kwargs.items()
            if key not in label_attrs
        }
        return collections_attrs

    def label(self):
        # empty list for parts of the final label
        parts = []
        # collections label exclusive attrs
        collections_attrs = self._get_collections_attrs()
        # iterative over collections attrs
        for (
            key,
            value,
        ) in collections_attrs.items():
            # for all non-None collections attrs, proceed
            if value is not None and not isinstance(value, dict):
                # edit title with spaces and capitalized
                title = self.default_titles.get(
                    key,
                    f"{key.replace('_', ' ').capitalize()}: ",
                )
                # add the group
                parts.append(f"{title}{value}")
        # consolidate to multiline label
        return "\n".join(parts)
