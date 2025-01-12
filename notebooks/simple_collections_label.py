"""
A notebook walking through a simple
collections label procedure.
"""

# %% LIBRARIES USED

import json
from pathlib import Path

import attrs
from PIL import Image, ImageDraw, ImageFont

# %% EXAMPLE COLLECTIONS LABEL


@attrs.define
class CollectionsLabel:
    save_directory: str
    id_number: str
    collection: str
    collector: str
    location: str
    formation: str
    coordinates: tuple[float, float]
    date_found: str

    def to_json(self, filename: str):
        """Save label as a JSON file."""
        data = attrs.asdict(self)
        save_path = Path(self.save_directory) / f"{filename}.json"
        with open(save_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Saved JSON to {save_path}")

    def to_text(self, filename: str, template: str):
        """Save label as a TeX file using a specified template."""
        save_path = Path(self.save_directory) / f"{filename}.text"
        with open(save_path, "w") as f:
            f.write(template.format(self))
        print(f"Saved Text to {save_path}")

    def to_image(self, filename: str, template: str):
        """Save label as an image (placeholder implementation)."""

        save_path = Path(self.save_directory) / f"{filename}.png"

        width, height = 600, 400
        font_size = 20
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        text = template.format(self)
        draw.multiline_text((10, 10), text, fill="black", font=font, spacing=4)

        image.save(save_path)
        print(f"Saved image to {save_path}")


# %% USING THE COLLECTIONS LABEL


AMNH = """\
ID Number: {0.id_number}
Museum: {0.collection}
Collector: {0.collector}
Location: {0.location}
Formation: {0.formation}
Coordinates: {0.coordinates}
Date Found: {0.date_found}"""

formation = """\
Date Collected: {0.date_found}
     ID Number: {0.id_number}
     Formation: {0.formation}
    Collection: {0.collection}
     Collector: {0.collector}
      Locality: {0.location}
   Coordinates: {0.coordinates}"""

label = CollectionsLabel(
    save_directory="../assets/saved_images/",
    id_number="3244",
    collection="AMNH",
    collector="Dr. Montague",
    location="North America",
    formation="Navesink",
    coordinates=(40.7128, -74.0060),
    date_found="2024-01-01",
)

print(AMNH.format(label))
print(formation.format(label))

label.to_json("label_amnh")
label.to_text("label_amnh", AMNH)
label.to_image("label_amnh", AMNH)

# %%
