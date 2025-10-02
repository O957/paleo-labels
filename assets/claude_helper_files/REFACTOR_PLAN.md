# Paleo-Labels Refactor Plan

## Overview

This document outlines a major refactor to make paleo-labels simpler, more modular, and more efficient for creating specimen labels. The focus is on reducing repetitive data entry, enabling field reuse across sessions, and maintaining simplicity.

## Core Architecture Recommendations

### 1. Schema-Based Field System

Instead of hardcoding field names, use a flexible schema:

```python
# field schema
{
  "id": "specimen_id",
  "display_name": "Specimen",
  "type": "text",
  "reusable": true,  # can be reused across sessions
  "suggestions": true  # enable autocomplete from history
}
```

This allows users to define their own field vocabularies while maintaining common defaults.

### 2. Three-Tier Data Model

**Session State** (ephemeral):
- Current working labels
- Active field values

**User Library** (persistent, parquet):
- Reusable field values (collector names, localities, formations)
- Style templates
- Field schemas

**Label Collections** (persistent, parquet):
- Saved label batches with metadata
- Exportable/shareable

### 3. Simplified Preview Strategy

Given concerns about HTML preview complexity, **drop it entirely**. Instead:
- Show a **text-based preview** (formatted plaintext)
- Provide **instant PDF generation** (small preview PDF with 1-3 labels)
- Use ReportLab exclusively (already working well)

Current HTML rendering is 120+ lines and duplicates PDF logic. A text preview would be ~20 lines.

## Specific Solutions to Your Problems

### Problem: 50 Enchodus specimens, same collector/locality

**Solution: Bulk label creation with field groups**

```python
# unchanging fields (apply to all)
common_fields = {
  "Collector": "Smith",
  "Locality": "Hell Creek Formation"
}

# varying fields (one per specimen)
variable_fields = [
  {"Formation": "Hell Creek", "Date": "2024-01-15"},
  {"Formation": "Lance", "Date": "2024-01-16"},
  # ... 48 more
]

# generates 50 labels
generate_labels(common_fields, variable_fields)
```

### Problem: Reusing previous session values

**Solution: Parquet-based value library** (already in LABEL_SAVE_SYSTEM_PLAN.md)

Implement simple autocomplete from saved values:

```python
def get_field_suggestions(field_name: str) -> list[str]:
    """Get previous values for a field from parquet library.

    Parameters
    ----------
    field_name : str
        Name of the field to get suggestions for.

    Returns
    -------
    list[str]
        List of unique previous values for this field.
    """
    df = pl.read_parquet("~/.paleo_labels/field_values.parquet")
    return df.filter(pl.col("field") == field_name)["value"].unique().to_list()
```

### Problem: Different field name vocabularies

**Solution: Field aliases with canonical names**

```python
field_aliases = {
  "Specimen": ["Specimen", "Spec.", "Sample", "Item"],
  "Date Found": ["Date Found", "Collection Date", "Date", "Found"]
}
```

Users can use any alias, but internally map to canonical names. For public databases, require canonical names only.

### Problem: Images in labels

**Mark as future enhancement.** ReportLab supports images but it adds significant complexity. Start without it.

### Problem: Efficient PDF positioning

Already implemented! `create_pdf_from_labels()` (app.py:1768-1848) calculates optimal grid layout. Could enhance with:

```python
def calculate_optimal_layout(
    label_dims: tuple[float, float],
    page_dims: tuple[float, float],
    spacing: float
) -> tuple[int, int]:
    """Calculate optimal rows/cols to maximize labels per page.

    Parameters
    ----------
    label_dims : tuple[float, float]
        Width and height of label in inches.
    page_dims : tuple[float, float]
        Width and height of page in inches.
    spacing : float
        Spacing between labels in inches.

    Returns
    -------
    tuple[int, int]
        Number of columns and rows that fit on page.
    """
    # existing logic at lines 1810-1819
```

### Problem: Text overflow and fitting content

**Solution: Adaptive text fitting algorithm**

Current implementation has good foundations (app.py:512-570), but needs refinement:

```python
def fit_text_to_label(
    lines: list[str],
    available_width: float,
    available_height: float,
    initial_font_size: float,
    font_name: str,
    min_font_size: float = 6.0
) -> tuple[list[str], float]:
    """Fit text within label boundaries by wrapping and scaling font.

    Parameters
    ----------
    lines : list[str]
        Initial text lines to fit.
    available_width : float
        Available width in points.
    available_height : float
        Available height in points.
    initial_font_size : float
        Starting font size in points.
    font_name : str
        Font name for width calculations.
    min_font_size : float
        Minimum readable font size (default 6.0pt).

    Returns
    -------
    tuple[list[str], float]
        Wrapped lines and final font size that fits.

    Algorithm
    ---------
    1. Start with initial_font_size
    2. Wrap all text to available_width
    3. Check if total height fits in available_height
    4. If no: reduce font_size by 0.5pt and repeat
    5. Continue until fits or min_font_size reached
    6. If min_font_size still doesn't fit: truncate content (with warning)
    """
    font_size = initial_font_size

    while font_size >= min_font_size:
        # wrap all lines at current font size
        wrapped_lines = []
        for line in lines:
            wrapped_lines.extend(
                wrap_text_to_width(line, available_width, font_size, font_name)
            )

        # calculate total height needed
        line_height = font_size * 1.2  # line height ratio
        total_height = len(wrapped_lines) * line_height

        # check if fits
        if total_height <= available_height:
            return wrapped_lines, font_size

        # reduce font size and try again
        font_size -= 0.5

    # minimum font size still doesn't fit - truncate with warning
    max_lines = int(available_height / (min_font_size * 1.2))
    return wrapped_lines[:max_lines], min_font_size
```

**Key requirements:**
1. **Never overflow boundaries** - text must stay within label dimensions
2. **Wrap first** - attempt to fit by wrapping long lines
3. **Scale down if needed** - reduce font size in 0.5pt increments
4. **Respect minimum** - never go below 6pt (readability threshold)
5. **Truncate as last resort** - with user warning if content is too large

## Recommended Implementation Plan

### Phase 1: Simplify Current System

1. Remove HTML preview entirely
2. Add text-based preview
3. Keep only PDF generation
4. **Refine text fitting algorithm** - ensure no overflow

**Benefits:**
- Removes ~200 lines of complex code
- Single source of truth for rendering (PDF only)
- Faster development iteration
- Guaranteed text containment within boundaries

### Phase 2: Field System Refactor

1. Create field schema TOML files
2. Add field aliasing
3. Implement autocomplete from history (parquet)

**Benefits:**
- Users can customize field vocabularies
- Automatic suggestions from past work
- Foundation for public databases

### Phase 3: Bulk Operations

1. Common/variable field separation
2. CSV import for bulk label creation
3. Session save/load (parquet collections)

**Benefits:**
- 50 Enchodus specimens with shared fields: write shared data once
- Import from spreadsheets
- Resume work across sessions

### Phase 4: Public Database Prep

1. Canonical field names only for exports
2. Collection metadata (creator, date, description)
3. Export to standardized format

**Benefits:**
- Enables sharing label collections
- Standardized format for interoperability
- Proper attribution and versioning

## Simplification Opportunities

### Remove/Simplify

- `render_to_html_preview()` (app.py:657-778) - 120 lines
- `_get_html_text_style()` (app.py:781-850) - 70 lines
- All HTML-related complexity

**Total removal: ~200 lines of complex code**

### Keep

- Excellent measurement system (app.py:36-116)
- PDF rendering (app.py:853-1001) - works well
- Style TOML loading (already clean)

### Add

- Simple text preview (~20 lines)
- Parquet field value storage
- Bulk creation UI

**Net reduction: ~180 lines**

## Architecture Sketch

```
paleo_labels/
├── core/
│   ├── field_schemas.py      # field definitions and aliases
│   ├── label_generator.py    # bulk label creation logic
│   └── pdf_renderer.py       # existing render functions (extracted)
├── storage/
│   ├── field_library.py      # parquet field value storage
│   └── collections.py        # parquet label collections
└── ui/
    ├── streamlit_app.py      # simplified UI
    └── cli.py                # command-line interface
```

**Modularity benefits:**
- Each component has single responsibility
- Easy to test in isolation
- CLI and Streamlit can share core logic
- Users can import core modules in their own scripts

## Data Storage Structure

```
~/.paleo_labels/
├── field_values.parquet      # reusable field values
├── collections/              # saved label collections
│   ├── enchodus_batch_001.parquet
│   └── expedition_2024.parquet
├── templates/                # style and field templates (existing TOML)
│   ├── default_style.toml
│   └── specimen_label.toml
└── schemas/                  # field schema definitions
    ├── paleontology.toml
    └── geology.toml
```

## Field Schema Format

```toml
# schemas/paleontology.toml

[field.specimen]
display_name = "Specimen"
aliases = ["Spec.", "Sample", "Item"]
type = "text"
reusable = true
suggestions = true

[field.scientific_name]
display_name = "Scientific Name"
aliases = ["Taxon", "Species"]
type = "text"
reusable = true
suggestions = true
pbdb_lookup = true  # enable PBDB autocomplete

[field.collector]
display_name = "Collector"
aliases = ["Collected By", "Collector"]
type = "text"
reusable = true
suggestions = true

[field.date_found]
display_name = "Date Found"
aliases = ["Collection Date", "Date", "Found"]
type = "date"
reusable = false
suggestions = true
```

## UI Workflow Specification

### Main Interface: Dropdown-Based Progressive Disclosure

The app uses a dropdown menu to prevent overwhelming users. Each option reveals only relevant controls.

**Label Creation Mode dropdown:**
1. Blank Text Label
2. Load Previous Label/Template
3. Create Custom Label
4. Upload Style Template
5. Custom Style Grid

Content area changes based on selected mode.

### Mode 1: Blank Text Label

User enters text that will be formatted within a bordered label.

**Interface elements:**
- Text area for freeform text entry
- Preview button
- Save Label button
- Add to PDF button

**Behavior:**
- Text wraps automatically within label dimensions
- Font size reduces incrementally (0.5pt steps) if content doesn't fit
- Minimum font size: 6pt (readability threshold)
- If still doesn't fit at 6pt: truncate with warning
- Cannot add custom fields (locked to text-only mode)
- Saves as label object (parquet) to user's labels folder
- Optional: Add to PDF queue for later printing

**Text Fitting Example:**
- Initial: 12pt font, text too tall
- Try: 11.5pt font, still too tall
- Try: 11.0pt font, still too tall
- Try: 10.5pt font, fits!
- Result: Use 10.5pt font

### Mode 2: Load Previous Label/Template

User selects from saved labels or predefined templates.

**Interface elements:**
- Source radio buttons: Previous Labels / Templates
- Dropdown of saved labels or templates
- Preview area showing label content
- Load button
- Edit Fields button
- Add to PDF button

**Behavior:**
- Loads label data into editable form
- Can switch to Mode 3 (Create Custom) to add/modify fields
- Saves updated label as new version or overwrites
- Add to PDF queue for printing

### Mode 3: Create Custom Label

User builds label field-by-field with autocomplete suggestions.

**Interface elements:**
- List of field pairs (field name dropdown, value dropdown)
- Each dropdown has autocomplete from history
- Add Field button
- Remove Last Field button
- Preview area
- Save Label button
- Add to PDF button

**Behavior:**
- Each field has autocomplete from history (parquet library)
- Text wraps and font scales down (0.5pt steps) to fit within label boundaries
- Minimum font size: 6pt for readability
- Works on newly created labels or loaded labels (from Mode 2)
- **Cannot** be used on blank text labels (Mode 1)
- Saves as label object to user's labels folder
- Add to PDF queue for printing

### Mode 4: Upload Style Template

User uploads a TOML style file to apply custom formatting.

**Interface elements:**
- File upload widget (Browse button or drag-and-drop area)
- Filename display showing loaded file
- Preview area showing parsed style settings
- Apply to Current button
- Save as Default button

**Behavior:**
- Parses TOML style configuration
- Applies to current label immediately
- Can save as new template for reuse

### Mode 5: Custom Style Grid

User configures styling through GUI controls with granular customization options.

**Label Dimensions:**
- Width (inches)
- Height (inches)
- Border thickness (points)
- Padding (percentage of smaller dimension)

**Global Typography:**
- Font family (Courier, Helvetica, Times-Roman)
- Default font size (points)

**Field (Group) Styling:**
- Font size (points, or "Auto" to match default)
- Color (hex picker)
- Bold (checkbox)
- Italic (checkbox)

**Value (Content) Styling:**
- Font size (points, or "Auto" to match default)
- Color (hex picker)
- Bold (checkbox)
- Italic (checkbox)

**Separator Options:**
- Separator character(s): ": ", " - ", " | ", or custom text
- Show empty fields (checkbox) - e.g., display "Species:" even with no value

**Per-Field Overrides (Optional):**
- Select specific field to customize
- Override any of the above settings for that field only
- Can customize field name, value, separator independently
- Can hide specific empty fields even if global setting shows them

**Behavior:**
- Global settings apply to all fields by default
- Per-field overrides allow customization of individual fields (field name style, value style, separator)
- Live preview updates as settings change
- Save as named template for future use
- Applies to all labels in current session

**Example Per-Field Override:**

For field "Scientific Name":
- Field text: "Scientific Name"
- Field font size: 9pt
- Field color: #1a1a1a
- Field bold: Yes
- Field italic: Yes
- Value font size: 11pt
- Value color: #004400
- Value bold: No
- Value italic: Yes
- Separator: ": "
- Show if empty: No

## Label Objects and PDF Workflow

### Label Object Storage

Each label is saved as a parquet file in the user's labels folder:

```
~/.paleo_labels/labels/
├── enchodus_001.parquet        # single label object
├── enchodus_002.parquet
└── expedition_2024_015.parquet
```

**Label Object Schema:**
```python
{
  "label_id": str,
  "created_at": datetime,
  "label_type": str,  # "blank_text", "fielded", "template"
  "content": dict,    # field-value pairs or text
  "style": dict,      # applied style configuration
  "metadata": dict    # tags, description, etc.
}
```

### PDF Generation Workflow

**PDF Queue Interface:**
- List of queued labels with Remove buttons
- Total label count display
- Optimize layout checkbox (maximize labels per page)
- Include label metadata checkbox
- Clear Queue button
- Generate PDF button

### Upload Labels for PDF

Users can upload previously saved label objects.

**Interface elements:**
- Upload mode radio buttons: Individual Label / Folder of Labels
- File/folder browser widget (or drag-and-drop area)
- List of loaded labels with counts
- Add to Queue button
- Generate PDF Now button

**Behavior:**
- Individual parquet files or entire folders can be uploaded
- Labels are validated and added to PDF queue
- Can mix different label types in same PDF
- Optimal layout calculated based on label dimensions

## Complete User Flow Examples

### Example 1: Quick Blank Label

1. Select "Blank Text Label" from dropdown
2. Enter: "Triassic Formation - Section B - Samples 45-67"
3. Click "Save Label" → saved to `~/.paleo_labels/labels/`
4. Click "Add to PDF" → added to PDF queue
5. Click "Generate PDF" → downloads PDF

### Example 2: Creating 50 Similar Labels

1. Select "Create Custom Label"
2. Add common fields:
   - Collector: Smith, J. (autocomplete from history)
   - Locality: Hell Creek Formation (autocomplete)
3. Add varying field:
   - Specimen: [empty for now]
4. Click "Save Label" 50 times, changing only Specimen field
   - Or: future feature - bulk creation with CSV import

### Example 3: Printing Saved Labels

1. Select "Load Previous Label/Template"
2. Choose "Previous Labels" source
3. Multi-select enchodus_001 through enchodus_050
4. Click "Add to PDF"
5. PDF queue now has 50 labels
6. Click "Generate PDF"
7. Download optimally-laid-out PDF (e.g., 3×10 grid per page)

### Example 4: Using Uploaded Label Folder

1. Select "Upload Labels for PDF" (new mode/button)
2. Choose folder: `~/Desktop/field_season_2024/`
3. App loads all .parquet label objects
4. Preview shows 150 labels loaded
5. Click "Generate PDF Now"
6. Downloads multi-page PDF with optimal layout

## Text Preview Example

Instead of complex HTML rendering, use simple formatted text:

**Label Preview (3.25" × 2.25"):**

Specimen: Enchodus petrosus
Collector: Smith, J.
Locality: Hell Creek Fm.
Date Found: 2024-01-15
Formation: Hell Creek

Font: Courier, 10pt
Border: 1.5pt

Simple, clear, and ~20 lines of code vs. 200 lines for HTML.

## Migration Path

### For Existing Users

1. **Automatic migration** of existing JSON labels to parquet
2. **Backward compatibility** - continue reading old JSON files
3. **Opt-in** for new features (bulk creation, field library)

### For New Users

1. Start with simplified interface
2. Build field library as they work
3. Access bulk features when needed

## Success Criteria

A successful refactor achieves:

1. **Simplicity**: Core operations require fewer clicks/inputs
2. **Efficiency**: 50 similar labels → write shared data once
3. **Reusability**: Previous values easily accessible
4. **Modularity**: Can use as library, CLI, or Streamlit app
5. **Performance**: Parquet enables fast queries on thousands of labels
6. **Maintainability**: Less code, clearer responsibilities

## Open Questions

1. **Field vocabulary**: Start with paleontology-specific schemas or generic?
2. **CSV format**: What columns for bulk import?
3. **Public database**: SQLite, Parquet, or both?
4. **CLI priority**: Build CLI alongside Streamlit or after?

## Next Steps

1. Review this plan
2. Decide on Phase 1 scope
3. Create feature branch for refactor
4. Begin with preview simplification (quick win)
5. Implement parquet field storage
6. Build bulk creation UI
