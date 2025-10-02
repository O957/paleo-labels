"""Verify paleo-labels installation and dependencies."""

import sys

print("Verifying paleo-labels installation...")
print(f"Python version: {sys.version}")
print()

# check imports
print("Checking dependencies...")

dependencies = [
    ("polars", "Parquet storage and data operations"),
    ("reportlab", "PDF generation"),
    ("streamlit", "Web UI"),
    ("tomli", "TOML configuration parsing"),
]

all_ok = True
for module_name, description in dependencies:
    try:
        __import__(module_name)
        print(f"  ✓ {module_name:15} - {description}")
    except ImportError as e:
        print(f"  ✗ {module_name:15} - MISSING: {description}")
        all_ok = False

print()

# check paleo_labels modules
print("Checking paleo-labels modules...")

modules = [
    ("paleo_labels.core.measurements", "Unit conversions"),
    ("paleo_labels.core.text_fitting", "Text wrapping and scaling"),
    ("paleo_labels.core.styling", "Styling system"),
    ("paleo_labels.core.pdf_renderer", "PDF rendering"),
    ("paleo_labels.storage.label_storage", "Label storage"),
    ("paleo_labels.storage.field_library", "Field autocomplete"),
    ("paleo_labels.ui.streamlit_app", "Streamlit UI"),
]

for module_name, description in modules:
    try:
        __import__(module_name)
        print(f"  ✓ {module_name:45} - {description}")
    except ImportError as e:
        print(f"  ✗ {module_name:45} - ERROR: {e}")
        all_ok = False

print()

# check storage directories
print("Checking storage directories...")
from pathlib import Path

storage_dir = Path.home() / ".paleo_labels"
labels_dir = storage_dir / "labels"

if labels_dir.exists():
    label_count = len(list(labels_dir.glob("*.parquet")))
    print(f"  ✓ Storage directory: {storage_dir}")
    print(f"  ✓ Labels directory: {labels_dir}")
    print(f"    Found {label_count} saved labels")
else:
    print(f"  ✓ Storage directory will be created on first use: {storage_dir}")

print()

if all_ok:
    print("✅ All checks passed! Installation is complete.")
    print()
    print("Quick start:")
    print("  1. Run test: python3 test_refactor.py")
    print("  2. Run UI: streamlit run paleo_labels/ui/streamlit_app.py")
else:
    print("❌ Some checks failed. Please install missing dependencies:")
    print("   pip install polars reportlab streamlit tomli")
