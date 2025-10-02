# Paleo-Labels Quick Start Guide

## Installation (One-Time Setup)

```bash
# install dependencies
pip install polars reportlab streamlit tomli

# verify installation
python3 verify_installation.py
```

Expected output: "✅ All checks passed!"

---

## Running the Application

### Option 1: Streamlit UI (Recommended)

```bash
streamlit run paleo_labels/ui/streamlit_app.py
```

Opens in browser at `http://localhost:8501`

### Option 2: Python Script

```python
from paleo_labels.core.styling import LabelStyle, TextStyle
from paleo_labels.core.pdf_renderer import create_pdf_from_labels

# create label
label = {
    "Specimen": "Enchodus petrosus",
    "Collector": "Smith, J.",
    "Date": "2024-01-15"
}

# generate PDF
style = LabelStyle()
pdf = create_pdf_from_labels([label], style)

with open("my_label.pdf", "wb") as f:
    f.write(pdf)
```

---

## Streamlit UI Modes

### Mode 1: Blank Text Label
**Use when:** Creating text-only labels (locality descriptions, notes)

1. Select "1. Blank Text Label" from dropdown
2. Enter your text in the text area
3. Click "Save Label" or "Add to PDF Queue"

**Example:** "Triassic Formation - Section B - Samples 45-67"

---

### Mode 2: Load Previous Label
**Use when:** Reusing or modifying saved labels

1. Select "2. Load Previous Label/Template"
2. Choose "Previous Labels"
3. Select label from dropdown
4. Click "Load" to edit or "Add to PDF Queue" to print

---

### Mode 3: Create Custom Label
**Use when:** Creating field-based labels (specimen data)

1. Select "3. Create Custom Label"
2. Enter field names and values
   - Type in dropdowns to get autocomplete suggestions
   - Click "Add Field" for more fields
3. Click "Save Label" or "Add to PDF Queue"

**Example fields:**
- Specimen: Enchodus petrosus
- Collector: Smith, J.
- Locality: Hell Creek Formation

---

### Mode 5: Custom Style Grid
**Use when:** Changing label appearance

1. Select "5. Custom Style Grid"
2. Adjust settings:
   - **Dimensions**: Width, height, border, padding
   - **Fonts**: Family, sizes, bold, italic
   - **Colors**: Field and value colors
   - **Separators**: ": ", " - ", etc.

Changes apply to all future labels.

---

## PDF Queue (Sidebar)

Located in sidebar, always visible.

**Workflow:**
1. Create labels in any mode
2. Click "Add to PDF Queue" for each label
3. Review queue in sidebar
4. Click "Generate PDF" when ready
5. Download multi-label PDF

**Queue operations:**
- Remove label: Click ✖ next to label
- Clear all: Click "Clear Queue"

---

## Common Tasks

### Task 1: Create One Simple Label

1. Mode 3: Create Custom Label
2. Add fields:
   - Specimen: _____
   - Locality: _____
3. Save or add to PDF queue
4. Generate PDF

**Time:** ~30 seconds

---

### Task 2: Create 10 Similar Labels

1. Mode 3: Create Custom Label
2. Create first label with common fields
3. Save it
4. Modify only specimen name
5. Save again (repeat 10 times)
6. Mode 2: Load each and add to PDF queue
7. Generate PDF

**Pro tip:** Field library autocomplete speeds this up!

---

### Task 3: Recreate Museum Label Format

1. Look at example in `assets/example_labels/`
2. Note dimensions, font, styling
3. Mode 5: Custom Style Grid
4. Set matching dimensions and fonts
5. Mode 3: Create label with fields
6. Generate PDF

See `reproduce_examples.py` for exact settings.

---

### Task 4: Make 50 Labels with Same Collector

1. Create first label with all fields
2. Save it (adds "Collector: Smith, J." to library)
3. For remaining 49 labels:
   - Start typing "Smi..." in Collector field
   - Autocomplete suggests "Smith, J."
   - Select it

**Autocomplete saves ~5 seconds per label = 4+ minutes total!**

---

## Styling Tips

### Professional Museum Label
```
Dimensions: 3.5" × 2.0"
Font: Times-Roman, 11pt
Field: Bold, black
Value: Regular, black
Border: 1.5pt
Separator: ": "
```

### Compact Field Label
```
Dimensions: 2.5" × 1.75"
Font: Courier, 9pt
Field: Bold, black
Value: Regular, black
Border: 0pt (none)
Separator: "" (none)
```

### Large Exhibition Label
```
Dimensions: 5.0" × 3.5"
Font: Helvetica, 14pt
Field: Bold, black
Value: Regular, black
Border: 2.0pt
Separator: ": "
```

---

## Keyboard Shortcuts

In Streamlit UI:
- `Tab` - Move between fields
- `Enter` - Submit current field
- `Ctrl+Enter` - Add field (in Mode 3)

---

## Storage Locations

Labels saved to: `~/.paleo_labels/labels/`
Field library: `~/.paleo_labels/field_values.parquet`

**Backup:** Copy `~/.paleo_labels/` directory

---

## Testing

### Quick Test
```bash
python3 test_refactor.py
```

Expected: "✅ All tests completed successfully!"

### Example Reproductions
```bash
python3 reproduce_examples.py
```

Generates 6 example label PDFs.

---

## Troubleshooting

### "Module not found: polars"
```bash
pip install polars
```

### "Streamlit not found"
```bash
pip install streamlit
```

### Labels saved but can't find them
Check: `~/.paleo_labels/labels/`

### Text overflowing label
System automatically scales down font. If still overflowing:
1. Reduce text amount
2. Increase label height
3. Check minimum font size (6pt default)

### Field suggestions not appearing
Need to save at least one label with that field first.

---

## Advanced Usage

See full documentation:
- `REFACTOR_README.md` - Complete usage guide
- `EXAMPLE_REPRODUCTIONS.md` - Real-world examples
- `FINAL_SUMMARY.md` - Feature reference

---

## Getting Help

1. Read `REFACTOR_README.md` for detailed examples
2. Check `reproduce_examples.py` for code samples
3. Review `EXAMPLE_REPRODUCTIONS.md` for styling patterns
4. Open issue on GitHub

---

## Quick Command Reference

```bash
# install
pip install polars reportlab streamlit tomli

# verify
python3 verify_installation.py

# test
python3 test_refactor.py

# run UI
streamlit run paleo_labels/ui/streamlit_app.py

# examples
python3 reproduce_examples.py
```

---

**Happy Labeling! 🏷️**
