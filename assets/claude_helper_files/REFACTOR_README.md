# Paleo-Labels Refactor

This refactor implements a simplified, modular architecture for paleo-labels.

## What Changed

### Architecture

**New modular structure:**
```
paleo_labels/
├── core/              # Core functionality
│   ├── measurements.py     # Unit conversions
│   ├── styling.py          # Granular styling system
│   ├── text_fitting.py     # Text wrapping and scaling
│   └── pdf_renderer.py     # PDF generation
├── storage/           # Data persistence
│   ├── label_storage.py    # Parquet-based label storage
│   └── field_library.py    # Field value autocomplete
└── ui/               # User interface
    └── streamlit_app.py    # New dropdown-based UI
```

### Key Features

1. **Parquet-based storage** - All labels saved as efficient parquet files
2. **Field value library** - Automatic autocomplete from previous entries
3. **Granular styling** - Per-field customization of fonts, colors, bold/italic
4. **Text fitting** - Automatic font scaling to fit content within boundaries
5. **PDF queue** - Batch labels before generating PDF
6. **Dropdown modes** - Clean UI with progressive disclosure

### Removed

- HTML preview (complex, duplicated PDF logic)
- ~200 lines of rendering code
- Scattered styling logic

### Added

- ~600 lines of well-organized, modular code
- Parquet storage for labels and field values
- Per-field style overrides
- Robust text fitting algorithm

## Running the Refactored App

### Quick Test

```bash
python3 test_refactor.py
```

This will:
1. Create and save a label
2. Test field library autocomplete
3. Generate a test PDF
4. Show custom styling

### Run Streamlit App

```bash
streamlit run paleo_labels/ui/streamlit_app.py
```

Or use the launcher:

```bash
python3 -m streamlit run paleo_labels/ui/streamlit_app.py
```

## Usage Examples

### Creating a Label Programmatically

```python
from paleo_labels.core.styling import LabelStyle, TextStyle
from paleo_labels.core.pdf_renderer import create_pdf_from_labels
from paleo_labels.storage.label_storage import save_label

# create label data
label_data = {
    "Specimen": "Enchodus petrosus",
    "Collector": "Smith, J.",
    "Locality": "Hell Creek Formation",
}

# customize style
style = LabelStyle(
    width_inches=4.0,
    height_inches=3.0,
)
style.default_field_style = TextStyle(
    font_family="Times-Roman",
    bold=True,
    color="#0000FF",
)

# save label
save_label(label_data, "my_label_001", style)

# generate PDF
pdf_bytes = create_pdf_from_labels([label_data], style)
with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Using Field Library

```python
from paleo_labels.storage.field_library import add_field_value, get_field_suggestions

# add values
add_field_value("Collector", "Smith, J.")
add_field_value("Collector", "Jones, A.")

# get suggestions
suggestions = get_field_suggestions("Collector")
# Returns: ['Jones, A.', 'Smith, J.']

# partial match
suggestions = get_field_suggestions("Collector", "Smi")
# Returns: ['Smith, J.']
```

### Per-Field Style Overrides

```python
from paleo_labels.core.styling import LabelStyle, TextStyle, FieldStyle

style = LabelStyle()

# override style for "Scientific Name" field
style.field_overrides["Scientific Name"] = FieldStyle(
    field_style=TextStyle(
        font_family="Times-Roman",
        font_size=9.0,
        bold=True,
        italic=True,
        color="#1a1a1a",
    ),
    value_style=TextStyle(
        font_family="Times-Roman",
        font_size=11.0,
        bold=False,
        italic=True,
        color="#004400",
    ),
    separator=" - ",
    show_if_empty=False,
)
```

## UI Modes

### Mode 1: Blank Text Label
- Enter freeform text
- Text auto-wraps and scales to fit
- Cannot add custom fields

### Mode 2: Load Previous Label/Template
- Browse saved labels
- Load into editor
- Can switch to Mode 3 to edit fields

### Mode 3: Create Custom Label
- Add fields one by one
- Autocomplete from field library
- Saves field values for future reuse

### Mode 5: Custom Style Grid
- Configure dimensions, fonts, colors
- Set field vs. value styling independently
- Choose separator characters
- Save as templates

## Data Storage

Labels are stored in `~/.paleo_labels/`:

```
~/.paleo_labels/
├── labels/                    # Individual label parquet files
│   ├── label_001.parquet
│   └── label_002.parquet
└── field_values.parquet       # Field value library for autocomplete
```

## Migration from Old Code

The old `app.py` is preserved. New code is in separate modules.

To migrate:
1. Old JSON labels will need conversion (not yet implemented)
2. Use new UI or programmatic API
3. Style configurations can be recreated in new system

## Next Steps

Future enhancements:
1. CSV import for bulk label creation
2. TOML style template upload
3. Label collections (multi-label parquet files)
4. JSON to parquet migration tool
5. Command-line interface

## Testing

Run the test suite:

```bash
python3 test_refactor.py
```

Expected output:
- Creates test labels
- Saves to parquet
- Generates PDF
- Tests field library
- Tests custom styling

Check `test_output.pdf` to verify PDF generation.
