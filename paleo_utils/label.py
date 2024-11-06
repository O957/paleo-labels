"""
Classes for creating
paleontological labels.
"""

import pathlib

import attrs
from PIL import ImageColor

SUPPORTED_COLORS = list(
    ImageColor.colormap.keys()
)
SUPPORTED_STYLES = [
    "bold",
    "regular",
    "italics",
    "underlined",
    "small_caps",
]
SUPPORTED_FONTS = ["Iosevka", "TeX Gyra Schola"]
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


@attrs.define(kw_only=True)
class Label:
    """
    Abstract base class for a Label.
    Each Label contains shared attributes,
    such as dimensions or background color.
    """

    # OPTIONS FOR SAVING

    save_path: str | pathlib.Path = attrs.field(
        validator=[
            attrs.validators.instance_of(
                (str, pathlib.Path)
            ),
            validate_save_directory,
        ]
    )
    save_as_image: bool = attrs.field(
        default=True,
        validator=attrs.validators.instance_of(
            bool
        ),
    )
    image_format: str = attrs.field(
        default=".jpg",
        validator=[
            attrs.validators.in_(
                [".jpg", ".png", ".heic"]
            ),
            attrs.validators.instance_of(str),
        ],
    )
    save_as_text: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(
            bool
        ),
    )
    save_as_svg: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(
            bool
        ),
    )
    save_as_latex: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(
            bool
        ),
    )

    # OPTIONS FOR BODY FONT

    body_font_path: str = attrs.field(
        default="TeX Gyra Schola",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_FONTS),
        ],
    )
    group_title_font_size: int = attrs.field(
        default=9,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(20),
        ],
    )
    group_content_font_size: int = attrs.field(
        default=9,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(20),
        ],
    )
    use_heading: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(
            bool
        ),
    )
    heading_font_size: int = attrs.field(
        default=12,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(20),
        ],
    )

    # OPTIONS FOR WATERMARKS

    watermark: str = attrs.field(
        default="",
        validator=attrs.validators.instance_of(
            str
        ),
    )  # TODO: character limit, naughty word censoring
    watermark_font_path: str = attrs.field(
        default="TeX Gyra Schola",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(SUPPORTED_FONTS),
        ],
    )
    watermark_font_style: str = attrs.field(
        default="regular",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                SUPPORTED_STYLES
            ),
        ],
    )
    watermark_font_size: int = attrs.field(
        default=9,
        validator=[
            attrs.validators.instance_of(int),
            attrs.validators.ge(4),
            attrs.validators.le(20),
        ],
    )
    watermark_color: str = "black"
    watermark_opacity: float = attrs.field(
        default=0.5,
        validator=[
            attrs.validators.ge(0.0),
            attrs.validators.le(1.0),
        ],
    )
    watermark_image: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.and_(
                attrs.validators.instance_of(str),
                attrs.validators.ge(1),
            )
        ),
    )
    watermark_position: str = attrs.field(
        default="best",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                [SUPPORTED_POSITIONS]
            ),
        ],
    )

    # OPTIONS FOR COLORING OF COMPONENTS

    background_color: str = attrs.field(
        default="white",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                SUPPORTED_COLORS
            ),
        ],
    )
    group_title_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                SUPPORTED_COLORS
            ),
        ],
    )
    group_content_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                SUPPORTED_COLORS
            ),
        ],
    )

    # OPTIONS FOR TEXT COMPONENT STYLING

    group_title_styling: str = attrs.field(
        default="regular",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                SUPPORTED_STYLES
            ),
        ],
    )
    group_content_styling: str = attrs.field(
        default="regular",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                SUPPORTED_STYLES
            ),
        ],
    )
    group_titles_to_hide: list[str] | None = (
        attrs.field(
            default=None,
            validator=attrs.validators.optional(
                attrs.validators.deep_iterable(
                    member_validator=attrs.validators.instance_of(
                        str
                    ),
                    iterable_validator=attrs.validators.instance_of(
                        list
                    ),
                )
            ),
        )
    )

    # OPTIONS FOR TEXT ALIGNMENT

    text_alignment: str = attrs.field(
        default="center",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                SUPPORTED_ALIGNMENTS
            ),
        ],
    )
    text_flush: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(
            bool
        ),
    )

    # OPTIONS FOR IMAGE DIMENSIONS

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
                member_validator=attrs.validators.ge(
                    0.5
                )
                & attrs.validators.le(20.0),
                iterable_validator=attrs.validators.instance_of(
                    tuple
                ),
            ),
        ],
    )
    dimensions_in_inches: bool = attrs.field(
        default=True,
        validator=attrs.validators.instance_of(
            bool
        ),
    )
    dimensions_in_centimeters: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(
            bool
        ),
    )
    dimensions_as_inches: tuple[float, float] = (
        attrs.field(init=False)
    )
    dimensions_as_centimeters: tuple[
        float, float
    ] = attrs.field(init=False)
    dimensions_as_pixels: tuple[float, float] = (
        attrs.field(init=False)
    )

    # OPTIONS FOR BORDER

    border_style: str | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.and_(
                attrs.validators.instance_of(str),
                attrs.validators.ge(1),
                attrs.validators.in_(
                    SUPPORTED_BORDERS
                ),
            )
        ),
    )
    border_color: str = attrs.field(
        default="black",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                SUPPORTED_COLORS
            ),
        ],
    )
    border_size_in_inches: float = attrs.field(
        default=0.05,
        validator=[
            attrs.validators.ge(0.01),
            attrs.validators.le(0.50),
        ],  # TODO: raise error depending on border size
    )

    # OPTIONS FOR QR CODES

    qr_code: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(
            bool
        ),
    )
    qr_code_size_in_inches: float = attrs.field(
        default=0.75,
        validator=[
            attrs.validators.ge(0.25),
            attrs.validators.le(2.0),
        ],  # TODO: raise error depending on border size
    )
    qr_code_position: str = attrs.field(
        default="best",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                [SUPPORTED_POSITIONS]
            ),
        ],
    )
    qr_code_on_back: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(
            bool
        ),
    )

    def __attrs_post_init__(self):
        if (
            self.dimensions_in_centimeters
            and self.dimensions_in_inches
        ):
            raise ValueError(
                "You cannot specify both dimensions_in_inches and dimensions_in_centimeters. Please provide only one."
            )
        if self.dimensions_in_centimeters:
            self.dimensions_as_centimeters = (
                self.dimensions
            )
            self.dimensions_as_inches = (
                self.dimensions[0] / 2.54,
                self.dimensions[1] / 2.54,
            )
            self.dimensions_as_pixels: (
                self.dimensions_as_inches[0]
                * self.image_dots_per_inch,
                self.dimensions_as_inches[1]
                * self.image_dots_per_inch,
            )
        if self.dimensions_in_inches:
            self.dimensions_as_inches = (
                self.dimensions
            )
            self.dimensions_as_centimeters = (
                self.dimensions[0] * 2.54,
                self.dimensions[1] * 2.54,
            )
            self.dimensions_as_pixels: (
                self.dimensions[0]
                * self.image_dots_per_inch,
                self.dimensions[1]
                * self.image_dots_per_inch,
            )

    def create_label_body(self):
        """
        Create the body of the label using
        PIL.
        """
        pass

    def _add_text_content(self):
        """
        Internal method (not exposed to the
        user) for attaching label contents
        to the label.
        """
        pass

    def save(self):
        """
        Method to the save based on the specified
        formats. Each label is expected to start
        out as a Python string.
        """
        if self.save_as_text:
            self.save_as_plain_text()
        if self.save_as_latex:
            self.save_as_latex()
        if self.save_as_svg:
            self.save_as_svg()
        if self.save_as_image == "image":
            self.save_as_image()

    # def save_as_plain_text(self):
    #     """Saves label as plain text."""
    #     pass

    # def save_as_latex(self):
    #     """Saves label as LaTeX."""
    #     pass

    # def save_as_svg(self):
    #     """Saves label as SVG."""
    #     pass

    # def save_as_image(self):
    #     """Saves label as an image."""
    #     pass


@attrs.define(kw_only=True)
class CollectionsLabel(Label):
    """
    A label for collections specimens, i.e.
    labels involving more details than
    fossil systematics. The kwargs parameter
    used is the group title.
    """

    collection: str | None = attrs.field(
        default=None
    )
    id_number: str | None = attrs.field(
        default=None
    )
    collector: str | None = attrs.field(
        default=None
    )
    species: str | None = attrs.field(
        default=None
    )
    species_author: str | None = attrs.field(
        default=None
    )
    common_name: str | None = attrs.field(
        default=None
    )
    location: str | None = attrs.field(
        default=None
    )
    coordinates: tuple[float, float] | None = (
        attrs.field(default=None)
    )
    coordinates_separate: bool = attrs.field(
        default=False
    )
    date_found: str | None = attrs.field(
        default=None
    )
    date_cataloged: str | None = attrs.field(
        default=None
    )
    formation: str | None = attrs.field(
        default=None
    )
    formation_author: str | None = attrs.field(
        default=None
    )
    chrono_age: str | None = attrs.field(
        default=None
    )
    chrono_age_author: str | None = attrs.field(
        default=None
    )
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

    _ordered_kwargs: dict = attrs.field(
        init=False
    )

    def __init__(self, **kwargs):
        self._ordered_kwargs = {
            key: kwargs[key] for key in kwargs
        }

    def __attrs_post_init__(self):
        # update title_overrides with any user-provided overrides
        if self.title_overrides:
            # merge user-provided titles, overriding defaults
            for (
                key,
                value,
            ) in self.title_overrides.items():
                if key in self.default_titles:
                    self.default_titles[key] = (
                        value
                    )

    def _get_collections_attrs(self):
        label_attrs = {
            attr.name
            for attr in Label.__attrs_attrs__
        }
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
        collections_attrs = (
            self._get_collections_attrs()
        )
        # iterative over collections attrs
        for (
            key,
            value,
        ) in collections_attrs.items():
            # for all non-None collections attrs, proceed
            if (
                value is not None
                and not isinstance(value, dict)
            ):
                # edit title with spaces and capitalized
                title = self.default_titles.get(
                    key,
                    f"{key.replace('_', ' ').capitalize()}: ",
                )
                # add the group
                parts.append(f"{title}{value}")
        # consolidate to multiline label
        return "\n".join(parts)


@attrs.define
class SystematicsLabel(Label):
    """
    A label class for individual or group systematics,
    containing taxonomic details.
    """

    # domain Level
    domain: str = "Domain: "
    domain_author: str = ""
    subdomain: str = "Subdomain: "
    subdomain_author: str = ""

    # kingdom Level
    kingdom: str = "Kingdom: "
    kingdom_author: str = ""
    subkingdom: str = "Subkingdom: "
    subkingdom_author: str = ""
    infrakingdom: str = "Infrakingdom: "
    infrakingdom_author: str = ""
    superphylum: str = "Superphylum: "
    superphylum_author: str = ""

    # phylum (or division) Level
    phylum: str = "Phylum: "
    phylum_author: str = ""
    subphylum: str = "Subphylum: "
    subphylum_author: str = ""
    infraphylum: str = "Infraphylum: "
    infraphylum_author: str = ""
    microphylum: str = "Microphylum: "
    microphylum_author: str = ""
    superclass: str = "Superclass: "
    superclass_author: str = ""

    # class Level
    class_level: str = "Class: "
    class_author: str = ""
    subclass: str = "Subclass: "
    subclass_author: str = ""
    infraclass: str = "Infraclass: "
    infraclass_author: str = ""
    parvclass: str = "Parvclass: "
    parvclass_author: str = ""
    superorder: str = "Superorder: "
    superorder_author: str = ""

    # order Level
    order: str = "Order: "
    order_author: str = ""
    suborder: str = "Suborder: "
    suborder_author: str = ""
    infraorder: str = "Infraorder: "
    infraorder_author: str = ""
    parvorder: str = "Parvorder: "
    parvorder_author: str = ""
    superfamily: str = "Superfamily: "
    superfamily_author: str = ""

    # family Level
    family: str = "Family: "
    family_author: str = ""
    subfamily: str = "Subfamily: "
    subfamily_author: str = ""
    infrafamily: str = "Infrafamily: "
    infrafamily_author: str = ""
    supertribe: str = "Supertribe: "
    supertribe_author: str = ""

    # tribe Level
    tribe: str = "Tribe: "
    tribe_author: str = ""
    subtribe: str = "Subtribe: "
    subtribe_author: str = ""

    # genus Level
    genus: str = "Genus: "
    genus_author: str = ""
    subgenus: str = "Subgenus: "
    subgenus_author: str = ""
    section: str = "Section: "
    section_author: str = ""
    subsection: str = "Subsection: "
    subsection_author: str = ""
    series: str = "Series: "
    series_author: str = ""
    subseries: str = "Subseries: "
    subseries_author: str = ""

    # species Level
    species: str = "Species: "
    species_author: str = ""
    subspecies: str = "Subspecies: "
    subspecies_author: str = ""
    variety: str = "Variety: "
    variety_author: str = ""
    subvariety: str = "Subvariety: "
    subvariety_author: str = ""
    form: str = "Form: "
    form_author: str = ""
    subform: str = "Subform: "
    subform_author: str = ""
