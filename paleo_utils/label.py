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
        background_color: str,
        text_color: str,
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
        background_color: str,
        text_color: str,
        dimensions: tuple[int],
        dimension_type: str,
        image_save_type: str,
        general_description: str,
        scientific_name: str,
        specimen_author: str,
        chronostratigraphy: str,
        formation: str,
        locale: str,
        collector: str,
        date_of_discovery: str,
    ) -> None:

        super().__init__(
            save_path,
            save_format,
            font_path,
            font_size,
            watermark,
            background_color,
            text_color,
            dimensions,
            dimension_type,
            image_save_type,
        )
