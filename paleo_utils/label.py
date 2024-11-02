"""
Classes for creating
paleontological labels.
"""

from abc import ABC

import attrs


@attrs.define
class Label(ABC):
    """
    Abstract base class for a Label.
    Each Label contains shared attributes like
    formatting, colors, and dimensions.

    Attributes
    ----------
    save_directory
        The location to save the
        generated label(s).

    save_as_image
        Whether to save the label
        as an image. Defaults to
        True.

    save_as_text
        Whether to save the label
        as plain text. Defaults to
        False.

    save_as_svg
        Whether to save the label
        as an svg. Defaults to
        False.

    save_as_latex
        Whether to save the label
        as latex. Defaults to
        False.

    font_path
        The path to the desired font.
        Can be the name of a pre-loaded
        font. Defaults to Time News Roman.

    font_size
        The initially desired size of the
        font to use. Defaults to 9. Will
        resize depending on the label
        dimensions. Overridden if
        group_font_size and text_font_size
        are provided. Validated to be
        between 4 and 20.

    group_font_size
        The initially desired size of the
        font for groups (e.g. Collector or
        Phylum). Defaults to 9. Validated
        to be between 4 and 20.

    text_font_size
        The initially desired size of the
        font for text. Defaults to 9.
        Validated to be between 4 and 20.

    date_format
        The format to list dates on
        labels. Defaults to IS08601
        formatting, i.e. YYYY-MM-DD

    watermark_text
        Text indicating the creator
        of the label. Defaults to
        empty string.

    watermark_font
        The font to use for the
        watermark text. Defaults to
        Time News Roman.

    watermark_font_style
        The font size to use for
        the watermark text. Defaults
        to 9. Validated to be between
        4 and 20.

    watermark_font_size
        The font style to use for
        the watermark text.

    watermark_color
        The color of the watermark
        text. Defaults to black.

    watermark_opacity
        The opacity of the watermark
        text. Defaults to 0.5. Validated
        to be between 0.0 and 1.0.

    watermark_image
        Image indicating the creator
        of the label. Negates watermark
        text, if selected.

    watermark_position
        The position of the watermark.
        Options include cross product
        of top, middle, bottom and left,
        center, right. Defaults to
        bottom-left.

    background_color
        The background color of the
        label. Defaults to white. Accepts
        color names or hexcodes.

    color
        The color to use for all the text.
        Remains except if groups_colors or
        text_colors is provided. Defaults to
        black.

    group_colors : dict[str, str] | str
        The colors to use for the different
        groups. If single color, that color
        is used for all groups. Defaults to
        black.

    text_colors : dict[str, str] | str
        The colors to use for the text across
        different groups. If single color,
        that color is used for all text. Defaults
        to black.

    group_styling : dict[str, str] | list[str]
        Styling to apply to groups. If single list
        is provided, the styling is applied to all
        groups. Options include underlining, bold,
        italicizing, and small-caps. Defaults to
        bold.

    text_styling : dict[str, str] | list[str]
        Styling to apply to text. If single list
        is provided, the styling is applied to all
        text across groups. Options include underlining,
        bold, italicizing, and small-caps. Defaults to
        None.

    text_alignment
        How to align the label text. Defaults to center.
        Options include center, right, or left.

    text_flush
        Whether to have all text corresponding to groups
        to be flushly aligned. Defaults to False. Only
        applies to left or right aligned text.

    dimensions
        The size of the image.

    dimensions_system
        Which system to use for the dimensions. Options
        include inches, centimeters, or pixels. Defaults
        to pixels.

    border_style
        The style of the border to use. Defaults to None.
        Options include solid, dashed, and dotted.

    border_color
        The color of the border, if used.
        Defaults to black. Accepts hexcodes
        or color names.

    border_size
        The thickness of the label border.

    hide_group_names
        Whether to hide group names.
        Defaults to False.

    qr_code
        Whether to convert and save the
        label as a QR code.

    qr_code_size
        The size of the QR code in pixels.

    qr_code_position
        The position of the QR code.
        Options include cross product
        of top, middle, bottom and left,
        center, right. Defaults to
        bottom-left. Cannot conflict with
        watermark, if selected.

    image_path
        Path to an image to have in the
        label above the label text.

    image_dimensions
        What percentage of the label's
        dimensions to make the image.

    image_dpi
        The quality of the image to
        retain.

    override_size_w_image
        Whether to scale the label text to
        accommodate the image or scale the
        label size instead.
    """

    save_directory: str
    save_as_image: bool = True
    save_as_text: bool = False
    save_as_svg: bool = False
    save_as_latex: bool = False

    font_path: str = "Times New Roman"
    font_size: int = attrs.field(
        default=9,
        validator=attrs.validators.in_([4, 20]),
    )
    group_font_size: int = attrs.field(
        default=9,
        validator=attrs.validators.in_([4, 20]),
    )
    text_font_size: int = attrs.field(
        default=9,
        validator=attrs.validators.in_([4, 20]),
    )

    date_format: str = "YYYY-MM-DD"

    watermark_text: str = ""
    watermark_font: str = "Times New Roman"
    watermark_font_style: str = "normal"
    watermark_font_size: int = attrs.field(
        default=9,
        validator=attrs.validators.in_([4, 20]),
    )
    watermark_color: str = "black"
    watermark_opacity: float = attrs.field(
        default=0.5,
        validator=attrs.validators.in_(0.0, 1.0),
    )
    watermark_image: str | None = None
    watermark_position: str = "bottom-left"

    background_color: str = "white"
    color: str = "black"

    group_colors: dict[str, str] | str = "black"
    text_colors: dict[str, str] | str = "black"

    group_styling: (
        dict[str, str] | list[str] | str
    ) = "bold"
    text_styling: dict[str, str] | list[str] = (
        attrs.Factory(list)
    )

    text_alignment: str = "center"
    text_flush: bool = False

    dimensions: tuple[int, int] = (400, 200)
    dimensions_system: str = "pixels"

    border_style: str = "none"
    border_color: str = "black"
    border_size: int = 1

    hide_group_names: bool = False

    qr_code: bool = False
    qr_code_size: int = 100
    qr_code_position: str = "bottom-left"

    image_path: str | None = None
    image_dimensions: float = 1.0
    image_dpi: float = 150
    override_size_w_image: bool = True

    def save(self):
        """
        Method to the save based on the specified
        formats. Each label is expected to start
        out as a Pillow image.
        """
        if self.save_format == "plain_text":
            self.save_as_plain_text()
        elif self.save_format == "latex":
            self.save_as_latex()
        elif self.save_format == "svg":
            self.save_as_svg()
        elif self.save_format == "image":
            self.save_as_image()
        else:
            raise ValueError(
                f"Unknown save format: {self.save_format}"
            )

    def save_as_plain_text(self):
        """Save label as plain text."""
        pass

    def save_as_latex(self):
        """Save label as LaTeX."""
        pass

    def save_as_svg(self):
        """Save label as SVG."""
        pass

    def save_as_image(self):
        """Save label as an image."""
        pass

    # def add_watermark(self):
    #     """Overlay watermark text onto the label."""
    #     pass

    # def validate_dimensions(self):
    #     """Ensure font size is appropriate for label dimensions."""
    #     if (
    #         self.font_size
    #         > min(self.dimensions) // 10
    #     ):
    #         self.font_size = (
    #             min(self.dimensions) // 10
    #         )

    # def preview_label(self):
    #     """Generate a preview of the label."""
    #     print(
    #         self.format_label_based_on_dimensions()
    #     )

    # def convert_to_qr_code(self, data):
    #     """Generate a QR code based on given data."""
    #     qr = qrcode.make(data)
    #     qr.save(f"{self.save_path}_qr.png")

    # def format_for_metadata(self):
    #     """Format label information as JSON metadata."""
    #     return json.dumps(
    #         attrs.asdict(self), indent=2
    #     )


@attrs.define
class CollectionsLabel(Label):
    """
    A label for collections specimens, i.e.
    labels involving more details than
    fossil systematics.

    Attributes
    ----------
    collection
        The name of the collection housing
        the specimen.

    collector
        The name of the collector, if this
        information is known.

    species
        The scientific name of the species
        that the label is associated with.

    species_author
        The author of the scientific name of
        the species that the label is
        associated with.

    common_name
        The common name of the species
        that the label is associated with.

    location
        The geographical name of the location
        where the specimen was retrieved.

    date
        When the fossil was discovered.
    formation
        Which formation the fossil came from.
    dimensions
        The size and weight of the specimen.
    repository
        Which repository the specimen is located in.
    id
        The repository ID of the specimen.
    age
        The chronostratigraphic age of the specimen.
    """

    general_description: str
    species_authors: str
    chronostratigraphy: str
    formation: str
    locale: str
    collector: str
    date_of_discovery: str
    species_names: list[str] = attrs.Factory(list)

    def format_label_based_on_dimensions(
        self,
    ) -> str:
        """
        Formats the label content for the collection details.
        """
        species_info = "\n".join(
            [
                f"{species} (Author: {self.species_authors})"
                for species in self.species_names
            ]
        )
        return (
            f"Description: {self.general_description}\n"
            f"Species: {species_info}\n"
            f"Chronostratigraphy: {self.chronostratigraphy}\n"
            f"Formation: {self.formation}\n"
            f"Locale: {self.locale}\n"
            f"Collector: {self.collector}\n"
            f"Date of Discovery: {self.date_of_discovery}"
        )

    # def summarize_species_info(self):
    #     """Summarize species information."""
    #     return f"{len(self.species_names)} species documented."

    # def generate_collection_overview(self):
    #     """Provide an overview statement for the collection."""
    #     return f"{self.general_description} - Found in {self.formation}, {self.locale}."


@attrs.define
class SystematicsLabel(Label):
    """
    A label class for individual or group systematics, containing taxonomic details.
    """

    general_description: str
    domain_name: str
    domain_author: str
    kingdom_name: str
    kingdom_author: str
    phylum_name: str
    phylum_author: str
    class_name: str
    class_author: str
    order_name: str
    order_author: str
    family_name: str
    family_author: str
    genus_name: str
    genus_author: str
    species_name: str
    specimen_author: str

    def format_label_based_on_dimensions(
        self,
    ) -> str:
        """
        Formats the label for systematics based on taxonomic details.
        """
        return (
            f"Description: {self.general_description}\n"
            f"Domain: {self.domain_name} (Author: {self.domain_author})\n"
            f"Kingdom: {self.kingdom_name} (Author: {self.kingdom_author})\n"
            f"Phylum: {self.phylum_name} (Author: {self.phylum_author})\n"
            f"Class: {self.class_name} (Author: {self.class_author})\n"
            f"Order: {self.order_name} (Author: {self.order_author})\n"
            f"Family: {self.family_name} (Author: {self.family_author})\n"
            f"Genus: {self.genus_name} (Author: {self.genus_author})\n"
            f"Species: {self.species_name} (Author: {self.specimen_author})"
        )

    def validate_taxonomy(self):
        """Ensure taxonomic fields are complete."""
        missing_fields = [
            field
            for field in [
                "domain_name",
                "kingdom_name",
                "phylum_name",
                "class_name",
                "order_name",
                "family_name",
                "genus_name",
                "species_name",
            ]
            if not getattr(self, field)
        ]
        if missing_fields:
            raise ValueError(
                f"Missing taxonomy fields: {', '.join(missing_fields)}"
            )
