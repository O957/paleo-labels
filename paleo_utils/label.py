"""
Classes for creating paleontological labels.
There are collections labels and specimen (
individual or group) systematics labels.
"""

from abc import ABC, abstractmethod


class Label(ABC):
    """
    Abstract base class for a Label.
    Each Label must contain
    the following information. All
    labels have the same save format
    options All labels
    """

    def __init__(
        self,
        save_path: str,
        save_format: str,
        font_path: str,
        font_size: int,
        watermark: str,
        watermark_opacity: float,
        watermark_position: float,
        date_format: str,
        background_color: str,
        text_color: str,
        text_alignment: str,
        margins: float,
        title_text,
        title_font,
        title_font_size,
        title_color,
        title_bold,
        title_alignment,
        group_color: str,
        groups_bold: bool,
        groups_italicized: bool,
        groups_small_caps: bool,
        groups_underlined: bool,
        groups_underline_color: str,
        group_font_size: str,
        group_spacing: float,
        border_color: float,
        border_width: float,
        border_style: float,
        dimensions: tuple[int],
        dimension_type: str = "metric",
        image_save_type: str | None = None,
    ) -> None:

        self.save_path = save_path
        self.save_format = save_format
        self.font_path = font_path
        self.font_size = font_size
        self.watermark = watermark
        self.background_color = background_color
        self.text_color = text_color
        self.dimensions = dimensions
        self.dimension_type = dimension_type
        self.image_save_type = image_save_type

    @abstractmethod
    def format_label_based_on_dimensions(self) -> str:
        """
        Abstract method for formatting of label
        dimensions based on the label type.
        """
        pass

    def save_as_plain_text(self):
        """
        Save label as plain text.
        """
        pass

    def save_as_latex(self):
        """
        Save label as plain text.
        """
        pass

    def save_as_svg(self):
        """
        Save label as svg.
        """
        pass

    def save_as_image(self):
        """
        Save label as an image.
        """
        pass

    def save(self):
        """
        Save the label.
        """
        pass


class CollectionsLabel(Label):

    def __init__(
        self,
        save_path: str,
        save_format: str,
        font_path: str,
        font_size: int,
        watermark: str,
        watermark_opacity: float,
        watermark_position: str,
        date_format: str,
        background_color: str,
        text_color: str,
        text_alignment: str,
        margins: float,
        title_text: str,
        title_font: str,
        title_font_size: int,
        title_color: str,
        title_bold: bool,
        title_alignment: str,
        group_color: str,
        groups_bold: bool,
        groups_italicized: bool,
        groups_small_caps: bool,
        groups_underlined: bool,
        groups_underline_color: str,
        group_font_size: int,
        group_spacing: float,
        border_color: str,
        border_width: float,
        border_style: str,
        dimensions,
        dimension_type,
        image_save_type,
        general_description,
        species_names: list[str],
        species_authors: str,
        chronostratigraphy: str,
        formation: str,
        locale: str,
        collector: str,
        date_of_discovery: str,
    ) -> None:

        # general label parameters
        super().__init__(
            save_path,
            save_format,
            font_path,
            font_size,
            watermark,
            watermark_opacity,
            watermark_position,
            date_format,
            background_color,
            text_color,
            text_alignment,
            margins,
            title_text,
            title_font,
            title_font_size,
            title_color,
            title_bold,
            title_alignment,
            group_color,
            groups_bold,
            groups_italicized,
            groups_small_caps,
            groups_underlined,
            groups_underline_color,
            group_font_size,
            group_spacing,
            border_color,
            border_width,
            border_style,
            dimensions,
            dimension_type,
            image_save_type,
        )

        # collections label parameters
        self.general_description = general_description
        self.species_names = species_names
        self.species_authors = species_authors
        self.chronostratigraphy = chronostratigraphy
        self.formation = formation
        self.locale = locale
        self.collector = collector
        self.date_of_discovery = date_of_discovery

    def format_label_based_on_dimensions(self) -> str:
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


class SystematicsLabel(Label):

    def __init__(
        self,
        save_path: str,
        save_format: str,
        font_path: str,
        font_size: int,
        watermark: str,
        watermark_opacity: float,
        watermark_position: str,
        date_format: str,
        background_color: str,
        text_color: str,
        text_alignment: str,
        margins: float,
        title_text: str,
        title_font: str,
        title_font_size: int,
        title_color: str,
        title_bold: bool,
        title_alignment: str,
        group_color: str,
        groups_bold: bool,
        groups_italicized: bool,
        groups_small_caps: bool,
        groups_underlined: bool,
        groups_underline_color: str,
        group_font_size: int,
        group_spacing: float,
        border_color: str,
        border_width: float,
        border_style: str,
        dimensions: tuple[int],
        dimension_type: str,
        image_save_type: str,
        general_description: str,
        domain_name: str,
        domain_author: str,
        kingdom_name: str,
        kingdom_author: str,
        phylum_name: str,
        phylum_author: str,
        class_name: str,
        class_author: str,
        order_name: str,
        order_author: str,
        family_name: str,
        family_author: str,
        genus_name: str,
        genus_author: str,
        species_name: str,
        specimen_author: str,
    ) -> None:

        # general label parameters
        super().__init__(
            save_path,
            save_format,
            font_path,
            font_size,
            watermark,
            watermark_opacity,
            watermark_position,
            date_format,
            background_color,
            text_color,
            text_alignment,
            margins,
            title_text,
            title_font,
            title_font_size,
            title_color,
            title_bold,
            title_alignment,
            group_color,
            groups_bold,
            groups_italicized,
            groups_small_caps,
            groups_underlined,
            groups_underline_color,
            group_font_size,
            group_spacing,
            border_color,
            border_width,
            border_style,
            dimensions,
            dimension_type,
            image_save_type,
        )

        # Linnaean systematics parameters
        self.general_description = general_description
        self.domain_name = domain_name
        self.domain_author = domain_author
        self.kingdom_name = kingdom_name
        self.kingdom_author = kingdom_author
        self.phylum_name = phylum_name
        self.phylum_author = phylum_author
        self.class_name = class_name
        self.class_author = class_author
        self.order_name = order_name
        self.order_author = order_author
        self.family_name = family_name
        self.family_author = family_author
        self.genus_name = genus_name
        self.genus_author = genus_author
        self.species_name = species_name
        self.specimen_author = specimen_author

    def format_label_based_on_dimensions(self) -> str:
        """
        Formats the label for systematics based on the taxonomic details.
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
