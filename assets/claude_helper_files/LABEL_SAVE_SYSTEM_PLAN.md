# Enhanced Label Save/Load System - Implementation Plan

## Current State Analysis

### What Exists:
- **Individual label saving**: Saves single labels as JSON files containing only field data
- **Basic loading**: Can load from existing saved labels and TOML templates
- **Session storage**: Labels stored temporarily in `st.session_state.current_labels`
- **File format**: Simple JSON with key-value pairs only

### What's Missing:
- **Style preservation**: Saved labels don't include font, border, spacing settings
- **Bulk operations**: No way to save/load entire sessions or label collections
- **Metadata**: No creation date, version info, or label descriptions
- **Export/Import**: No comprehensive backup/restore functionality

## Proposed Solution: Parquet-Based Label Storage

### Why Parquet?
- **Columnar efficiency**: Excellent compression for repetitive label data
- **Type safety**: Strong typing for all label properties and metadata
- **Performance**: Fast queries and filtering for large label collections
- **Polars integration**: Native support for your preferred data library
- **Scalability**: Handles thousands of labels efficiently
- **Metadata support**: Rich schema with nested data structures

### 1. Parquet File Formats

#### A. Individual Label File (`label_name.parquet`)
Single-row Parquet file containing one label with all metadata and styling:

```python
# Polars DataFrame Schema
import polars as pl

individual_schema = {
    # Metadata columns
    "label_id": pl.Utf8,
    "name": pl.Utf8,
    "description": pl.Utf8,
    "tags": pl.List(pl.Utf8),
    "created_at": pl.Datetime,
    "updated_at": pl.Datetime,
    "version": pl.Utf8,

    # Content columns
    "is_blank_label": pl.Boolean,
    "blank_text": pl.Utf8,  # null if not blank label
    "field_names": pl.List(pl.Utf8),  # ["Name", "Address", "City"]
    "field_values": pl.List(pl.Utf8), # ["John Smith", "123 Main St", "Springfield"]

    # Style columns
    "font_name": pl.Utf8,
    "font_size": pl.Float32,
    "border_thickness": pl.Float32,
    "label_spacing": pl.Float32,
    "width_inches": pl.Float32,
    "height_inches": pl.Float32,
    "padding_percent": pl.Float32,
    "key_color": pl.Utf8,      # "#000000"
    "value_color": pl.Utf8,    # "#000000"
    "bold_keys": pl.Boolean,
    "bold_values": pl.Boolean,
    "italic_keys": pl.Boolean,
    "italic_values": pl.Boolean,
    "center_text": pl.Boolean,
    "align_colons": pl.Boolean,
}
```

#### B. Label Collection File (`collection_name.parquet`)
Multi-row Parquet file where each row represents one label:

```python
# Example DataFrame content
df = pl.DataFrame({
    "label_id": ["label_001", "label_002", "label_003"],
    "collection_name": ["Customer Batch #123"] * 3,
    "collection_description": ["Weekly shipping labels"] * 3,
    "collection_tags": [["shipping", "batch-123"]] * 3,
    "created_at": ["2024-01-15T10:30:00Z"] * 3,
    "updated_at": ["2024-01-15T11:45:00Z"] * 3,

    "is_blank_label": [False, True, False],
    "blank_text": [None, "Special instructions here", None],
    "field_names": [
        ["Name", "Address", "City"],
        None,  # blank label has no fields
        ["Company", "Contact", "Phone"]
    ],
    "field_values": [
        ["John Smith", "123 Main St", "Springfield"],
        None,  # blank label has no field values
        ["Acme Corp", "Jane Doe", "555-0123"]
    ],

    # Style can be consistent across collection or vary per label
    "font_name": ["Courier", "Times-Roman", "Courier"],
    "font_size": [12.0, 10.0, 12.0],
    "border_thickness": [1.5] * 3,
    # ... other style properties
})
```

#### C. Master Label Database (`labels.parquet`)
Central database containing all labels for powerful querying:

```python
# Schema supports filtering and searching across all labels
master_schema = {
    **individual_schema,  # All individual label columns
    "collection_id": pl.Utf8,      # null for individual labels
    "collection_name": pl.Utf8,    # null for individual labels
    "source_file": pl.Utf8,        # original filename
    "file_type": pl.Utf8,          # "individual" or "collection"
}
```

### 2. New UI Components

#### A. Enhanced Save Dialog
```
┌─ Save Options ─────────────────────────┐
│ ○ Save Current Label                   │
│ ○ Save Entire Session                  │
│ ○ Save Selected Labels                 │
│                                        │
│ Name: [_____________________]          │
│ Description: [________________]        │
│ Tags: [_____________________]          │
│                                        │
│ ☑ Include current style settings      │
│ ☑ Create backup copy                  │
│                                        │
│ Format: ▼ .parquet (Individual)       │
│         ▼ .parquet (Collection)       │
│                                        │
│ [Cancel] [Save]                        │
└────────────────────────────────────────┘
```

#### B. Load/Import Dialog
```
┌─ Load Options ─────────────────────────┐
│ Source:                                │
│ ○ Saved Labels                         │
│ ○ Upload File                          │
│ ○ Recent Sessions                      │
│                                        │
│ [Browse Files...] or [Drop files here] │
│                                        │
│ Preview:                               │
│ ┌────────────────────────────────────┐ │
│ │ Name: Customer Batch #123          │ │
│ │ Type: Collection (25 labels)       │ │
│ │ Style: Courier, 1.5pt borders     │ │
│ │ Created: Jan 15, 2024              │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Import Options:                        │
│ ○ Replace current session             │
│ ○ Append to current session           │
│ ○ Load as new session                 │
│                                        │
│ ☑ Apply saved style settings          │
│ ☑ Preserve label order                │
│                                        │
│ [Cancel] [Load]                        │
└────────────────────────────────────────┘
```

### 3. Implementation Plan

#### Phase 1: Parquet Infrastructure
- [ ] Add Polars dependency to requirements
- [ ] Create label schema definitions and validation
- [ ] Implement Parquet read/write functions with proper typing
- [ ] Create individual label save functionality with full style preservation
- [ ] Implement backward compatibility with existing `.json` files

#### Phase 2: Collection Management with Parquet
- [ ] Implement collection Parquet format for multiple labels
- [ ] Add "Save Session" functionality using multi-row Parquet
- [ ] Create collection preview using Polars DataFrame operations
- [ ] Add selective label saving with efficient filtering
- [ ] Implement master database (`labels.parquet`) for cross-collection queries

#### Phase 3: Polars-Powered Loading System
- [ ] Parquet file detection and schema validation
- [ ] Fast filtering and searching using Polars expressions
- [ ] Style application options with DataFrame operations
- [ ] Import modes with efficient DataFrame concatenation
- [ ] Drag-and-drop with Parquet validation

#### Phase 4: Advanced Parquet Features
- [ ] Recent sessions tracking with efficient queries
- [ ] Label templates using filtered DataFrames
- [ ] Lightning-fast search across thousands of labels
- [ ] Export to multiple formats using Polars connectors (CSV, Excel, JSON)
- [ ] Advanced analytics (most used fields, style patterns, etc.)

### 4. File Organization

```
paleo-labels/
├── saved_labels/
│   ├── individual/          # Single-row .parquet files
│   ├── collections/         # Multi-row .parquet files
│   ├── templates/           # Template .parquet files
│   ├── labels.parquet       # Master database (all labels)
│   └── backups/            # Automatic backups
├── sessions/
│   ├── recent_sessions.parquet  # Recent session metadata
│   └── auto_save/          # Auto-saved session .parquet files
```

### 5. Code Implementation Examples

#### A. Save Individual Label to Parquet
```python
import polars as pl
from datetime import datetime

def save_label_to_parquet(label_data: dict, style_config: dict,
                         name: str, description: str = ""):
    """Save a single label to individual Parquet file."""

    # Extract field data
    if "__blank_label__" in label_data:
        is_blank = True
        blank_text = label_data["__blank_label__"]
        field_names = None
        field_values = None
    else:
        is_blank = False
        blank_text = None
        field_names = list(label_data.keys())
        field_values = list(label_data.values())

    # Create DataFrame
    df = pl.DataFrame({
        "label_id": [f"label_{datetime.now().strftime('%Y%m%d_%H%M%S')}"],
        "name": [name],
        "description": [description],
        "tags": [[]],  # Empty list for now
        "created_at": [datetime.now()],
        "updated_at": [datetime.now()],
        "version": ["1.0"],

        "is_blank_label": [is_blank],
        "blank_text": [blank_text],
        "field_names": [field_names],
        "field_values": [field_values],

        "font_name": [style_config.get("font_name", "Courier")],
        "font_size": [style_config.get("font_size", 12.0)],
        "border_thickness": [style_config.get("border_thickness", 1.5)],
        "label_spacing": [style_config.get("label_spacing", 0.125)],
        "width_inches": [style_config.get("width_inches", 2.625)],
        "height_inches": [style_config.get("height_inches", 1.0)],
        "padding_percent": [style_config.get("padding_percent", 0.05)],
        "key_color": [style_config.get("key_color", "#000000")],
        "value_color": [style_config.get("value_color", "#000000")],
        "bold_keys": [style_config.get("bold_keys", True)],
        "bold_values": [style_config.get("bold_values", False)],
        "italic_keys": [style_config.get("italic_keys", False)],
        "italic_values": [style_config.get("italic_values", False)],
        "center_text": [style_config.get("center_text", False)],
        "align_colons": [style_config.get("align_colons", False)],
    })

    # Save to Parquet
    filepath = LABELS_DIR / "individual" / f"{name}.parquet"
    df.write_parquet(filepath)

    # Update master database
    update_master_database(df)

    return filepath

#### B. Load and Filter Labels
```python
def load_labels_by_criteria(tags: list = None, font_name: str = None,
                           created_after: datetime = None):
    """Load labels using Polars filtering."""

    if not (LABELS_DIR / "labels.parquet").exists():
        return pl.DataFrame()

    df = pl.read_parquet(LABELS_DIR / "labels.parquet")

    # Apply filters using Polars expressions
    if tags:
        df = df.filter(pl.col("tags").list.contains(tags[0]))  # Contains any tag

    if font_name:
        df = df.filter(pl.col("font_name") == font_name)

    if created_after:
        df = df.filter(pl.col("created_at") > created_after)

    return df

#### C. Save Session Collection
```python
def save_session_collection(session_labels: list, collection_name: str,
                           description: str = ""):
    """Save entire session as multi-row Parquet collection."""

    rows = []
    current_style = _build_style_config()  # Get current style

    for i, label_data in enumerate(session_labels):
        # Similar to individual save but append to rows list
        row_data = {
            "label_id": f"{collection_name}_label_{i+1:03d}",
            "collection_name": collection_name,
            "collection_description": description,
            # ... all other fields
        }
        rows.append(row_data)

    df = pl.DataFrame(rows)

    # Save collection
    filepath = LABELS_DIR / "collections" / f"{collection_name}.parquet"
    df.write_parquet(filepath)

    # Update master database
    update_master_database(df)

    return filepath
```

### 6. Benefits of Parquet-Based System

#### For Users:
- **Full fidelity**: Saved labels look exactly the same when reloaded
- **Lightning-fast search**: Find labels across thousands of entries instantly
- **Powerful filtering**: Search by date, style, content, tags, etc.
- **Efficient storage**: Excellent compression, even for large label collections
- **Analytics**: Discover patterns in your label usage
- **Future-proof**: Industry-standard format with broad tool support

#### For Development:
- **Type safety**: Strong schema validation prevents data corruption
- **Performance**: Columnar format optimized for analytical queries
- **Scalability**: Handles massive label collections efficiently
- **Polars integration**: Leverages your preferred data library
- **Extensible**: Easy to add new columns without breaking existing data
- **Debuggable**: Can inspect Parquet files with any data tool

### 7. Migration Strategy

1. **JSON to Parquet conversion**: Automated migration of existing `.json` files
2. **Schema evolution**: Graceful handling of new columns as features are added
3. **Backward compatibility**: Read old JSON files and convert on-the-fly
4. **Incremental migration**: Convert files as they're accessed, not all at once

```python
def migrate_json_to_parquet(json_file_path: Path) -> Path:
    """Convert legacy JSON label to new Parquet format."""
    with open(json_file_path) as f:
        old_data = json.load(f)

    # Convert to new schema with default style values
    new_data = {
        "label_id": [json_file_path.stem],
        "name": [json_file_path.stem],
        "description": ["Migrated from JSON"],
        "field_names": [list(old_data.keys())],
        "field_values": [list(old_data.values())],
        "font_name": ["Courier"],  # Use current defaults
        "border_thickness": [1.5],
        # ... other default style values
    }

    df = pl.DataFrame(new_data)
    parquet_path = json_file_path.with_suffix('.parquet')
    df.write_parquet(parquet_path)

    return parquet_path
```

### 8. UI Integration Points

- **Style Options**: "Save Current Style as Template" button
- **Session Management**: "Save Session", "Load Session", "Recent Sessions"
- **Label Preview**: "Save this Label" button with metadata dialog
- **Search Interface**: Real-time filtering across all saved labels
- **Analytics Dashboard**: Label usage statistics and patterns
- **Import/Export**: Support for Parquet, CSV, Excel, JSON formats

### 9. Advanced Query Examples

```python
# Find all shipping labels created this month with Courier font
recent_shipping = (
    pl.read_parquet("saved_labels/labels.parquet")
    .filter(
        (pl.col("tags").list.contains("shipping")) &
        (pl.col("font_name") == "Courier") &
        (pl.col("created_at") > datetime.now() - timedelta(days=30))
    )
)

# Get most commonly used field names across all labels
field_usage = (
    pl.read_parquet("saved_labels/labels.parquet")
    .select(pl.col("field_names").list.explode())
    .group_by("field_names")
    .count()
    .sort("count", descending=True)
)

# Find labels with similar styling
courier_labels = (
    pl.read_parquet("saved_labels/labels.parquet")
    .filter(
        (pl.col("font_name") == "Courier") &
        (pl.col("border_thickness") >= 1.5) &
        (pl.col("center_text") == True)
    )
)
```

This Parquet-based system transforms label storage from simple file management into a powerful, searchable database while maintaining the simplicity and efficiency you want for your labeling workflow.
