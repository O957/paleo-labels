"""
Classes for creating
paleontological labels.
"""

import pathlib
from abc import ABC

import attrs


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
class Label(ABC):
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
            attrs.validators.in_(
                ["TeX Gyra Schola", "Iosevka"]
            ),
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
            attrs.validators.in_(
                ["TeX Gyra Schola", "Iosevka"]
            ),
        ],
    )
    watermark_font_style: str = attrs.field(
        default="regular",
        validator=[
            attrs.validators.instance_of(str),
            attrs.validators.in_(
                [
                    "bold",
                    "regular",
                    "italics",
                    "underlined",
                ]
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
    watermark_image: str | None = None
    watermark_position: str = "bottom-left"

    # OPTIONS FOR COLORING OF COMPONENTS

    background_color: str = "white"
    color: str = "black"

    group_colors: dict[str, str] | str = "black"
    text_colors: dict[str, str] | str = "black"

    # OPTIONS FOR TEXT COMPONENT STYLING

    group_styling: (
        dict[str, str] | list[str] | str
    ) = "bold"
    text_styling: dict[str, str] | list[str] = (
        attrs.Factory(list)
    )

    hide_group_names: bool = False
    to_hide: list[str] | None = None

    # OPTIONS FOR TEXT ALIGNMENT

    text_alignment: str = "center"
    text_flush: bool = False

    # OPTIONS FOR NON-TEXT COMPONENT STYLING

    dimensions: tuple[int, int] = (400, 200)
    dimensions_system: str = "pixels"

    border_style: str = "none"
    border_color: str = "black"
    border_size: int = 1

    image_dimensions: float = attrs.field(
        default=1.0,
        validator=[
            attrs.validators.ge(0.25),
            attrs.validators.le(1.0),
        ],
    )
    image_dpi: float = attrs.field(
        default=150,
        validator=[
            attrs.validators.ge(50),
            attrs.validators.le(500),
        ],
    )
    override_size_w_image: bool = True

    # OPTIONS FOR QR CODES

    qr_code: bool = False
    qr_code_size: int = 100
    qr_code_position: str = "bottom-left"

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

    Attributes
    ----------
    description:
        A short description of the specimen
        and or context surrounding the fossil.
        Defaults to None.

    description_title
        The name of the description group
        on the label. Defaults to
        "Description: ".

    domain
        The name of the domain of the specimen.
        The domain group defaults to "Domain: ".

    domain_author
        The citation for the domain name.
        Defaults to "".

    subdomain
        The name of the subdomain of the specimen.
        The subdomain group defaults to "Subdomain: ".

    subdomain_author
        The citation for the subdomain name.
        Defaults to "".

    kingdom
        The name of the kingdom of the specimen.
        The kingdom group defaults to "Kingdom: ".

    kingdom_author
        The citation for the kingdom name.
        Defaults to "".

    subkingdom
        The name of the subkingdom of the specimen.
        The subkingdom group defaults to "Subkingdom: ".

    subkingdom_author
        The citation for the subkingdom name.
        Defaults to "".

    infrakingdom
        The name of the infrakingdom of the specimen.
        The infrakingdom group defaults to "Infrakingdom: ".

    infrakingdom_author
        The citation for the infrakingdom name.
        Defaults to "".

    superphylum
        The name of the superphylum of the specimen.
        The superphylum group defaults to "Superphylum: ".

    superphylum_author
        The citation for the superphylum name.
        Defaults to "".

    phylum
        The name of the phylum (or division in botany) of the specimen.
        The phylum group defaults to "Phylum: ".

    phylum_author
        The citation for the phylum name.
        Defaults to "".

    subphylum
        The name of the subphylum of the specimen.
        The subphylum group defaults to "Subphylum: ".

    subphylum_author
        The citation for the subphylum name.
        Defaults to "".

    infraphylum
        The name of the infraphylum of the specimen.
        The infraphylum group defaults to "Infraphylum: ".

    infraphylum_author
        The citation for the infraphylum name.
        Defaults to "".

    microphylum
        The name of the microphylum of the specimen.
        The microphylum group defaults to "Microphylum: ".

    microphylum_author
        The citation for the microphylum name.
        Defaults to "".

    superclass
        The name of the superclass of the specimen.
        The superclass group defaults to "Superclass: ".

    superclass_author
        The citation for the superclass name.
        Defaults to "".

    class
        The name of the class of the specimen.
        The class group defaults to "Class: ".

    class_author
        The citation for the class name.
        Defaults to "".

    subclass
        The name of the subclass of the specimen.
        The subclass group defaults to "Subclass: ".

    subclass_author
        The citation for the subclass name.
        Defaults to "".

    infraclass
        The name of the infraclass of the specimen.
        The infraclass group defaults to "Infraclass: ".

    infraclass_author
        The citation for the infraclass name.
        Defaults to "".

    parvclass
        The name of the parvclass of the specimen.
        The parvclass group defaults to "Parvclass: ".

    parvclass_author
        The citation for the parvclass name.
        Defaults to "".

    superorder
        The name of the superorder of the specimen.
        The superorder group defaults to "Superorder: ".

    superorder_author
        The citation for the superorder name.
        Defaults to "".

    order
        The name of the order of the specimen.
        The order group defaults to "Order: ".

    order_author
        The citation for the order name.
        Defaults to "".

    suborder
        The name of the suborder of the specimen.
        The suborder group defaults to "Suborder: ".

    suborder_author
        The citation for the suborder name.
        Defaults to "".

    infraorder
        The name of the infraorder of the specimen.
        The infraorder group defaults to "Infraorder: ".

    infraorder_author
        The citation for the infraorder name.
        Defaults to "".

    parvorder
        The name of the parvorder of the specimen.
        The parvorder group defaults to "Parvorder: ".

    parvorder_author
        The citation for the parvorder name.
        Defaults to "".

    superfamily
        The name of the superfamily of the specimen.
        The superfamily group defaults to "Superfamily: ".

    superfamily_author
        The citation for the superfamily name.
        Defaults to "".

    family
        The name of the family of the specimen.
        The family group defaults to "Family: ".

    family_author
        The citation for the family name.
        Defaults to "".

    subfamily
        The name of the subfamily of the specimen.
        The subfamily group defaults to "Subfamily: ".

    subfamily_author
        The citation for the subfamily name.
        Defaults to "".

    infrafamily
        The name of the infrafamily of the specimen.
        The infrafamily group defaults to "Infrafamily: ".

    infrafamily_author
        The citation for the infrafamily name.
        Defaults to "".

    supertribe
        The name of the supertribe of the specimen.
        The supertribe group defaults to "Supertribe: ".

    supertribe_author
        The citation for the supertribe name.
        Defaults to "".

    tribe
        The name of the tribe of the specimen.
        The tribe group defaults to "Tribe: ".

    tribe_author
        The citation for the tribe name.
        Defaults to "".

    subtribe
        The name of the subtribe of the specimen.
        The subtribe group defaults to "Subtribe: ".

    subtribe_author
        The citation for the subtribe name.
        Defaults to "".

    genus
        The name of the genus of the specimen.
        The genus group defaults to "Genus: ".

    genus_author
        The citation for the genus name.
        Defaults to "".

    subgenus
        The name of the subgenus of the specimen.
        The subgenus group defaults to "Subgenus: ".

    subgenus_author
        The citation for the subgenus name.
        Defaults to "".

    section
        The name of the section within the genus.
        The section group defaults to "Section: ".

    section_author
        The citation for the section name.
        Defaults to "".

    subsection
        The name of the subsection within the genus.
        The subsection group defaults to "Subsection: ".

    subsection_author
        The citation for the subsection name.
        Defaults to "".

    series
        The name of the series within the genus.
        The series group defaults to "Series: ".

    series_author
        The citation for the series name.
        Defaults to "".

    subseries
        The name of the subseries within the genus.
        The subseries group defaults to "Subseries: ".

    subseries_author
        The citation for the subseries name.
        Defaults to "".

    species
        The scientific name of the species.
        The species group defaults to "Species: ".

    species_author
        The citation for the species name.
        Defaults to "".

    subspecies
        The name of the subspecies of the specimen.
        The subspecies group defaults to "Subspecies: ".

    subspecies_author
        The citation for the subspecies name.
        Defaults to "".

    variety
        The name of the variety of the specimen.
        The variety group defaults to "Variety: ".

    variety_author
        The citation for the variety name.
        Defaults to "".

    subvariety
        The name of the subvariety of the specimen.
        The subvariety group defaults to "Subvariety: ".

    subvariety_author
        The citation for the subvariety name.
        Defaults to "".

    form
        The name of the form of the specimen.
        The form group defaults to "Form: ".

    form_author
        The citation for the form name.
        Defaults to "".

    subform
        The name of the subform of the specimen.
        The subform group defaults to "Subform: ".

    subform_author
        The citation for the subform name.
        Defaults to "".
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
