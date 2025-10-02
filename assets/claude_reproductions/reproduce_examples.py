"""Reproduce example labels found in assets/example_labels/."""

from paleo_labels.core.pdf_renderer import create_pdf_from_labels
from paleo_labels.core.styling import LabelStyle, TextStyle


def create_typewriter_label():
    """Reproduce typewriter-style label (Screenshot 17.42.51).

    Characteristics:
    - Monospace Courier font
    - Compact layout, small size
    - Left-aligned
    - No separators between fields
    """
    label_data = {
        "Eupachydiscus": "",
        "Up. Cretaceus": "",
        "Haalam Fm - Santonian": "",
        "Mt Tznhalem": "",
        "Coll. Tznhalem, Santonian TZl467": "",
        "2019 Cowichan,": "",
        "E40": "",
        "V.I": "",
    }

    style = LabelStyle(
        width_inches=2.5,
        height_inches=1.75,
        border_thickness=0.0,  # no visible border in original
        padding_percent=0.03,
    )

    # typewriter style - Courier, compact
    style.default_field_style = TextStyle(
        font_family="Courier",
        font_size=9.0,
        bold=False,
        italic=False,
        color="#000000",
    )

    style.default_value_style = TextStyle(
        font_family="Courier",
        font_size=9.0,
        bold=False,
        italic=False,
        color="#000000",
    )

    style.default_separator = ""  # no separator
    style.show_empty_fields = True

    return label_data, style


def create_ammonite_label():
    """Reproduce centered ammonite label (Screenshot 17.43.14).

    Characteristics:
    - Bold, underlined title
    - Centered text
    - Italic species name
    - Larger font for title
    """
    # need to create as blank label since it's centered text
    text = """Cleoniceras Ammonite
________________

C. besairei
112 – 99.5 million years old
Tulear, Madagascar"""

    label_data = {"__blank_label__": text}

    style = LabelStyle(
        width_inches=4.0,
        height_inches=2.0,
        border_thickness=0.0,
        padding_percent=0.08,
    )

    # centered, mixed styles - use default
    style.default_value_style = TextStyle(
        font_family="Times-Roman",
        font_size=14.0,
        bold=True,
        italic=False,
        color="#000000",
    )

    return label_data, style


def create_handwritten_form_label():
    """Reproduce handwritten-style label with underlines (Screenshot 17.43.08).

    Characteristics:
    - Fields with long underlines
    - Handwriting fills in blanks
    - Regular spacing
    """
    label_data = {
        "Name": "____________________________________",
        "Age": "____________________________________",
        "Formation": "____________________________________",
        "Locality": "____________________________________",
    }

    style = LabelStyle(
        width_inches=5.0,
        height_inches=2.0,
        border_thickness=2.0,
        padding_percent=0.05,
    )

    style.default_field_style = TextStyle(
        font_family="Times-Roman",
        font_size=11.0,
        bold=True,
        italic=False,
        color="#000000",
    )

    style.default_value_style = TextStyle(
        font_family="Times-Roman",
        font_size=11.0,
        bold=False,
        italic=False,
        color="#000000",
    )

    style.default_separator = ": "

    return label_data, style


def create_blank_form_label():
    """Reproduce blank form label (Screenshot 17.43.20).

    Characteristics:
    - Double border
    - Bold field names
    - Underlines for fill-in
    - Some fields on same line
    """
    label_data = {
        "Fossil ID#": "___________    Date__________",
        "Name": "_________________________________",
        "Location": "_________________________________",
        "Formation": "_________________________________",
        "Member": "_________________________________",
        "Age": "__________    Comments__________",
        "": "_________________________________",
    }

    style = LabelStyle(
        width_inches=5.5,
        height_inches=3.5,
        border_thickness=3.0,  # thick double border effect
        padding_percent=0.04,
    )

    style.default_field_style = TextStyle(
        font_family="Helvetica",
        font_size=12.0,
        bold=True,
        italic=False,
        color="#000000",
    )

    style.default_value_style = TextStyle(
        font_family="Helvetica",
        font_size=11.0,
        bold=False,
        italic=False,
        color="#000000",
    )

    style.default_separator = ""

    return label_data, style


def create_collection_label():
    """Reproduce collection label (Screenshot 17.43.25).

    Characteristics:
    - Italic header line
    - Mixed field layout
    - Some fields split with divider
    """
    label_data = {
        "From the Collection of": "___________________",
        "Name": "",
        "": "                     | Catalogue Number",
        "Age": "",
        "Formation": "",
        "Locality": "",
        "Description": "",
        "Date collected": "          | Collector",
    }

    style = LabelStyle(
        width_inches=5.0,
        height_inches=3.5,
        border_thickness=1.5,
        padding_percent=0.05,
    )

    # first line should be italic
    style.default_field_style = TextStyle(
        font_family="Times-Roman",
        font_size=11.0,
        bold=True,
        italic=False,
        color="#000000",
    )

    style.default_value_style = TextStyle(
        font_family="Times-Roman",
        font_size=10.0,
        bold=False,
        italic=False,
        color="#000000",
    )

    # make first field italic
    from paleo_labels.core.styling import FieldStyle

    style.field_overrides["From the Collection of"] = FieldStyle(
        field_style=TextStyle(
            font_family="Times-Roman",
            font_size=12.0,
            bold=False,
            italic=True,
            color="#000000",
        ),
        value_style=TextStyle(
            font_family="Times-Roman",
            font_size=10.0,
            bold=False,
            italic=False,
            color="#000000",
        ),
        separator=" ",
        show_if_empty=True,
    )

    style.default_separator = ""

    return label_data, style


def create_german_label():
    """Reproduce dense German label (Screenshot 17.42.59).

    Characteristics:
    - Very compact
    - Bold field names (Nr., Beschreibung, etc.)
    - Dense text, small font
    - No underlines
    """
    label_data = {
        "Nr.": "AN1316",
        "Beschreibung": "Scheelit in Orthogneis",
        "Lokalität": "Abraummaterial Scheelitbergbau",
        "": "Felbertal Westfeld, Mittersill, Salzburg",
        "Aquirierung": "Eigenfund, 13.9.2002",
        "Maße": "10x5 cm, 197 g",
        "Bem.": "Selbe Probe wie AN138, 139",
        "": "Kunstharz-Imprägnation auffällig",
        "Hergestellt am": "16.1.2008",
    }

    style = LabelStyle(
        width_inches=3.5,
        height_inches=2.0,
        border_thickness=2.0,
        padding_percent=0.03,
    )

    style.default_field_style = TextStyle(
        font_family="Helvetica",
        font_size=9.0,
        bold=True,
        italic=False,
        color="#000000",
    )

    style.default_value_style = TextStyle(
        font_family="Helvetica",
        font_size=9.0,
        bold=False,
        italic=False,
        color="#000000",
    )

    style.default_separator = ": "

    return label_data, style


def main():
    """Generate all reproductions."""
    print("Reproducing example labels...")

    reproductions = [
        ("1_typewriter_label", create_typewriter_label()),
        ("2_ammonite_label", create_ammonite_label()),
        ("3_handwritten_form", create_handwritten_form_label()),
        ("4_blank_form", create_blank_form_label()),
        ("5_collection_label", create_collection_label()),
        ("6_german_label", create_german_label()),
    ]

    for name, (label_data, style) in reproductions:
        print(f"\nCreating {name}...")
        pdf_bytes = create_pdf_from_labels([label_data], style)

        output_path = f"reproduced_{name}.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"  ✓ Saved to {output_path}")
        print(f'    Size: {style.width_inches}" × {style.height_inches}"')
        print(f"    Border: {style.border_thickness}pt")
        print(
            f"    Font: {style.default_field_style.font_family}, {style.default_field_style.font_size}pt"
        )

    # create combined PDF with all labels
    print("\nCreating combined PDF with all labels...")
    all_labels = []
    all_styles = []

    for name, (label_data, style) in reproductions:
        all_labels.append(label_data)
        all_styles.append(style)

    # use first style for combined (will need enhancement for multiple styles)
    combined_pdf = create_pdf_from_labels(all_labels, all_styles[0])

    with open("reproduced_all_examples.pdf", "wb") as f:
        f.write(combined_pdf)

    print("  ✓ Saved to reproduced_all_examples.pdf")
    print("\n✅ All reproductions complete!")
    print(
        "\nNote: Some labels use features like underlined text or double borders"
    )
    print("that may require manual adjustment for exact reproduction.")


if __name__ == "__main__":
    main()
