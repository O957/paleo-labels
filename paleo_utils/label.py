"""
Classes for creating paleontological labels.
There are collections labels and specimen (
individual or group) systematics labels.
"""

from abc import ABC


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
        label_dimensions: tuple[int],
        dimension_type: str = "metric",
    ) -> None:
        self.save_path = save_path
        self.save_format = save_format
        self.font_path = font_path
        self.font_size = font_size
        self.label_dimensions = label_dimensions
        self.dimension_type = dimension_type

    def load_label_font(self):
        pass

    def save_label(self):
        pass


class CollectionsLabel(Label):

    def __init__(
        self,
        save_path: str,
        save_format: str,
        font_path: str,
        font_size: int,
        label_dimensions: tuple[int],
        dimension_type: str,
        taxon_rank: str,
        scientific_name: str,
        author_citation: str,
        discovery_year: str,
    ) -> None:

        super().__init__(
            save_path,
            save_format,
            font_path,
            font_size,
            label_dimensions,
            dimension_type,
        )
