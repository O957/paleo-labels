from abc import ABC, abstractmethod

import attrs


@attrs.define
class Label(ABC):
    """
    Abstract base class for a Label.
    Each Label contains shared attributes like
    formatting, colors, and dimensions.
    """

    save_path: str
    font_path: str
    save_format: str = "image"
    font_size: int = 12
    watermark: str = ""
    watermark_opacity: float = 0.3
    watermark_position: str = "bottom-right"
    date_format: str = "YYYY-MM-DD"
    background_color: str = "white"
    text_color: str = "black"
    text_alignment: str = "center"
    margins: float = 10.0
    title_text: str = "Label Title"
    title_font: str = "arial.ttf"
    title_font_size: int = 16
    title_color: str = "blue"
    title_bold: bool = True
    title_alignment: str = "center"
    group_color: str = "black"
    groups_bold: bool = True
    groups_italicized: bool = False
    groups_small_caps: bool = False
    groups_underlined: bool = False
    groups_underline_color: str = "black"
    group_font_size: int = 12
    group_spacing: float = 5.0
    border_color: str = "black"
    border_width: float = 2.0
    border_style: str = "none"
    dimensions: tuple[int] = (400, 200)
    dimension_type: str = "pixel"
    image_save_type: str | None = None

    @abstractmethod
    def format_label_based_on_dimensions(self) -> str:
        """
        Abstract method for formatting the label content based on the type of label.
        """
        pass

    def save(self):
        """
        Save the label based on the specified format.
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
            raise ValueError(f"Unknown save format: {self.save_format}")

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


@attrs.define
class CollectionsLabel(Label):
    """
    A label class for paleontological collections,
    containing collection-specific details.
    """

    general_description: str = "COLLECTIONS LABEL"
    species_names: list[str] = attrs.Factory(list)
    species_authors: str = "Unknown"
    chronostratigraphy: str = "Unknown"
    formation: str = "Unknown Formation"
    locale: str = "Unknown Locale"
    collector: str = "Unknown Collector"
    date_of_discovery: str = "Unknown Date"

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


@attrs.define
class SystematicsLabel(Label):
    """
    A label class for individual or group systematics, containing taxonomic details.
    """

    general_description: str = "Fossil specimen."
    domain_name: str = "Eukarya"
    domain_author: str = "Linnaeus"
    kingdom_name: str = "Animalia"
    kingdom_author: str = "Linnaeus"
    phylum_name: str = "Chordata"
    phylum_author: str = "Linnaeus"
    class_name: str = "Mammalia"
    class_author: str = "Linnaeus"
    order_name: str = "Carnivora"
    order_author: str = "Bowdich"
    family_name: str = "Felidae"
    family_author: str = "Fischer"
    genus_name: str = "Panthera"
    genus_author: str = "Oken"
    species_name: str = "Panthera leo"
    specimen_author: str = "Linnaeus"

    def format_label_based_on_dimensions(self) -> str:
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
