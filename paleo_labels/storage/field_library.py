"""Field value library for autocomplete using parquet for paleo-labels."""

from pathlib import Path

import polars as pl

STORAGE_DIR = Path.home() / ".paleo_labels"
FIELD_VALUES_PATH = STORAGE_DIR / "field_values.parquet"


def add_field_value(field_name: str, value: str) -> None:
    """Add a field value to the library.

    Parameters
    ----------
    field_name : str
        Name of the field.
    value : str
        Value to add.

    Returns
    -------
    None
    """
    if not value or not value.strip():
        return

    # load existing or create new
    if FIELD_VALUES_PATH.exists():
        df = pl.read_parquet(FIELD_VALUES_PATH)
    else:
        df = pl.DataFrame(
            {"field_name": [], "value": []},
            schema={"field_name": pl.String, "value": pl.String},
        )

    # check if this exact pair already exists
    existing = df.filter(
        (pl.col("field_name") == field_name)
        & (pl.col("value") == value.strip())
    )

    if len(existing) == 0:
        # add new entry
        new_row = pl.DataFrame(
            {
                "field_name": [field_name],
                "value": [value.strip()],
            }
        )
        df = pl.concat([df, new_row])
        df.write_parquet(FIELD_VALUES_PATH)


def get_field_suggestions(
    field_name: str, partial_value: str = ""
) -> list[str]:
    """Get autocomplete suggestions for a field.

    Parameters
    ----------
    field_name : str
        Name of the field to get suggestions for.
    partial_value : str
        Partial value for filtering suggestions.

    Returns
    -------
    list[str]
        List of suggested values.
    """
    if not FIELD_VALUES_PATH.exists():
        return []

    df = pl.read_parquet(FIELD_VALUES_PATH)

    # filter by field name
    filtered = df.filter(pl.col("field_name") == field_name)

    # filter by partial value if provided
    if partial_value:
        filtered = filtered.filter(
            pl.col("value")
            .str.to_lowercase()
            .str.contains(partial_value.lower())
        )

    # return unique values sorted
    values = filtered["value"].unique().sort().to_list()
    return values


def get_all_field_names() -> list[str]:
    """Get all unique field names in the library.

    Returns
    -------
    list[str]
        List of field names.
    """
    if not FIELD_VALUES_PATH.exists():
        return []

    df = pl.read_parquet(FIELD_VALUES_PATH)
    return df["field_name"].unique().sort().to_list()


def save_label_to_library(label_data: dict) -> None:
    """Save all field-value pairs from a label to the library.

    Parameters
    ----------
    label_data : dict
        Label data dictionary.

    Returns
    -------
    None
    """
    # skip blank labels
    if "__blank_label__" in label_data:
        return

    for field_name, value in label_data.items():
        add_field_value(field_name, value)
