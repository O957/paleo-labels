"""Simple test script for refactored paleo-labels."""

from paleo_labels.core.pdf_renderer import create_pdf_from_labels
from paleo_labels.core.styling import LabelStyle, TextStyle
from paleo_labels.storage.field_library import (
    add_field_value,
    get_field_suggestions,
)
from paleo_labels.storage.label_storage import (
    list_saved_labels,
    load_label,
    save_label,
)

print("Testing paleo-labels refactor...")

# test 1: create a simple label
print("\n1. Creating a simple label...")
label_data = {
    "Specimen": "Enchodus petrosus",
    "Collector": "Smith, J.",
    "Date Found": "2024-01-15",
}

style = LabelStyle()
print(f'   Label dimensions: {style.width_inches}" × {style.height_inches}"')

# test 2: save label
print("\n2. Saving label to parquet...")
label_id = "test_label_001"
filepath = save_label(label_data, label_id, style)
print(f"   Saved to: {filepath}")

# test 3: load label
print("\n3. Loading label...")
loaded = load_label(label_id)
print(f"   Loaded: {loaded['label_data']}")

# test 4: field library
print("\n4. Testing field library...")
add_field_value("Collector", "Smith, J.")
add_field_value("Collector", "Jones, A.")
suggestions = get_field_suggestions("Collector")
print(f"   Collector suggestions: {suggestions}")

# test 5: create PDF
print("\n5. Creating PDF...")
labels = [
    {"Specimen": "Enchodus petrosus", "Collector": "Smith, J."},
    {"Specimen": "Xiphactinus audax", "Collector": "Jones, A."},
    {"__blank_label__": "This is a blank text label for testing purposes."},
]

pdf_bytes = create_pdf_from_labels(labels, style)
print(f"   PDF size: {len(pdf_bytes)} bytes")

with open("test_output.pdf", "wb") as f:
    f.write(pdf_bytes)
print("   Saved to: test_output.pdf")

# test 6: custom styling
print("\n6. Testing custom styling...")
custom_style = LabelStyle(
    width_inches=4.0,
    height_inches=3.0,
    border_thickness=2.0,
)
custom_style.default_field_style = TextStyle(
    font_family="Times-Roman",
    font_size=12.0,
    bold=True,
    italic=False,
    color="#0000FF",
)
custom_style.default_value_style = TextStyle(
    font_family="Times-Roman",
    font_size=10.0,
    bold=False,
    italic=True,
    color="#FF0000",
)

print(
    f'   Custom style: {custom_style.width_inches}" × {custom_style.height_inches}"'
)
print(
    f"   Field font: {custom_style.default_field_style.font_family}, {custom_style.default_field_style.font_size}pt"
)
print(
    f"   Value font: {custom_style.default_value_style.font_family}, {custom_style.default_value_style.font_size}pt"
)

# test 7: list saved labels
print("\n7. Listing saved labels...")
saved = list_saved_labels()
print(f"   Found {len(saved)} saved labels: {saved}")

print("\n✅ All tests completed successfully!")
