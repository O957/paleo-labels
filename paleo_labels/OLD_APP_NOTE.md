# Note: app.py is the OLD implementation

The file `paleo_labels/app.py` contains the original monolithic implementation.

## New Implementation

The refactored code is organized in:
- `paleo_labels/core/` - Core functionality
- `paleo_labels/storage/` - Data persistence
- `paleo_labels/ui/` - User interface

## Running the New App

Use the new Streamlit UI:
```bash
streamlit run paleo_labels/ui/streamlit_app.py
```

Or programmatically:
```python
from paleo_labels.core.pdf_renderer import create_pdf_from_labels
from paleo_labels.core.styling import LabelStyle
# ... see REFACTOR_README.md for examples
```

## Why Keep the Old File?

- Backward compatibility reference
- Shows evolution of the codebase
- Can be removed once migration is complete

## Migration

The old app.py can be safely removed once you've verified the new implementation meets your needs. The new code provides all the same functionality plus:
- Better organization
- Parquet storage
- Field autocomplete
- Granular styling
- PDF queue

See `REFACTOR_SUMMARY.md` for details.
