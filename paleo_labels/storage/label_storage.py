"""Label storage using parquet format for paleo-labels."""

from datetime import datetime
from pathlib import Path

import polars as pl

from paleo_labels.core.styling import LabelStyle

# storage paths
STORAGE_DIR = Path.home() / ".paleo_labels"
LABELS_DIR = STORAGE_DIR / "labels"
LABELS_DIR.mkdir(parents=True, exist_ok=True)


def save_label(
    label_data: dict,
    label_id: str | None = None,
    style: LabelStyle | None = None,
    metadata: dict | None = None,
) -> Path:
    """Save a label to parquet file.

    Parameters
    ----------
    label_data : dict
        Label content (field-value pairs or {"__blank_label__": text}).
    label_id : str
        Unique label identifier (auto-generated if None).
    style : LabelStyle
        Style configuration for the label.
    metadata : dict
        Additional metadata (tags, description, etc.).

    Returns
    -------
    Path
        Path to saved label file.
    """
    if label_id is None:
        label_id = f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # determine label type
    if "__blank_label__" in label_data:
        label_type = "blank_text"
        content_json = label_data
    else:
        label_type = "fielded"
        content_json = label_data

    # serialize style to dict
    style_dict = {}
    if style:
        style_dict = {
            "width_inches": style.width_inches,
            "height_inches": style.height_inches,
            "border_thickness": style.border_thickness,
            "padding_percent": style.padding_percent,
            "default_separator": style.default_separator,
            "show_empty_fields": style.show_empty_fields,
        }

    # create dataframe with single row
    df = pl.DataFrame(
        {
            "label_id": [label_id],
            "created_at": [datetime.now()],
            "label_type": [label_type],
            "content": [str(content_json)],  # store as string
            "style": [str(style_dict)],
            "metadata": [str(metadata or {})],
        }
    )

    # save to parquet
    filepath = LABELS_DIR / f"{label_id}.parquet"
    df.write_parquet(filepath)

    return filepath


def load_label(label_id: str) -> dict:
    """Load a label from parquet file.

    Parameters
    ----------
    label_id : str
        Label identifier.

    Returns
    -------
    dict
        Dictionary with keys: label_data, style, metadata, created_at, label_type.
    """
    filepath = LABELS_DIR / f"{label_id}.parquet"

    if not filepath.exists():
        raise FileNotFoundError(f"Label not found: {label_id}")

    df = pl.read_parquet(filepath)
    row = df.row(0, named=True)

    # deserialize content
    import ast

    label_data = ast.literal_eval(row["content"])
    style_dict = ast.literal_eval(row["style"])
    metadata = ast.literal_eval(row["metadata"])

    return {
        "label_data": label_data,
        "style": style_dict,
        "metadata": metadata,
        "created_at": row["created_at"],
        "label_type": row["label_type"],
    }


def load_labels_from_folder(folder_path: Path) -> list[dict]:
    """Load all labels from a folder.

    Parameters
    ----------
    folder_path : Path
        Path to folder containing label parquet files.

    Returns
    -------
    list[dict]
        List of label dictionaries.
    """
    labels = []

    for parquet_file in folder_path.glob("*.parquet"):
        try:
            label_id = parquet_file.stem
            label = load_label(label_id)
            labels.append(label)
        except Exception:
            continue

    return labels


def list_saved_labels() -> list[str]:
    """List all saved label IDs.

    Returns
    -------
    list[str]
        List of label IDs.
    """
    return [f.stem for f in LABELS_DIR.glob("*.parquet")]


def delete_label(label_id: str) -> None:
    """Delete a saved label.

    Parameters
    ----------
    label_id : str
        Label identifier to delete.

    Returns
    -------
    None
    """
    filepath = LABELS_DIR / f"{label_id}.parquet"
    if filepath.exists():
        filepath.unlink()
