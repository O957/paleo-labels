"""
Streamlit application for users to create labels for their
specimens or collections.
"""

import attrs


@attrs.define
class LabelGroup:
    label: str
    content: str
    pass


@attrs.define
class Label:
    type: str
    groups: list[LabelGroup]
    pass
