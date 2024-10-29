"""
Package initialization file for
Paleo-Utils. For usage details
and possibility of omission see
PEP 420:
https://peps.python.org/pep-0420/
"""

from .label import (
    CollectionsLabel,
    Label,
    SystematicsLabel,
)

__all__ = [
    "Label",
    "CollectionsLabel",
    "SystematicsLabel",
]
