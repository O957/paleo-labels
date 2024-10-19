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
    ) -> None:
        self.save_path = save_path
        self.save_format = save_format
        self.font_path = font_path
        self.font_size = font_size
