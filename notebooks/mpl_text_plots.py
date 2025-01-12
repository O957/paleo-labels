# %%

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# %%

# label dimensions in inches
label_dimensions = (6, 4)  # width, height

# create the label body
fig, ax = plt.subplots(figsize=label_dimensions)
ax.set_xlim(0, label_dimensions[0])
ax.set_ylim(0, label_dimensions[1])
ax.set_aspect("equal")
ax.axis("off")

# add background color
ax.add_patch(Rectangle((0, 0), *label_dimensions, color="lightblue"))

# add border
border_size = 0.1  # in inches
border_padding = 0.2  # in inches
left = border_padding
bottom = border_padding
right = label_dimensions[0] - border_padding
top = label_dimensions[1] - border_padding

ax.add_patch(
    Rectangle(
        (left, bottom),
        right - left,
        top - bottom,
        edgecolor="black",
        facecolor="none",
        linewidth=border_size * 72,
    )
)  # Convert inches to points

# add text boxes
texts = [
    {"text": "First Text Box", "font": "Arial", "size": 16, "style": "normal"},
    {
        "text": "Second Text Box",
        "font": "Times New Roman",
        "size": 14,
        "style": "italic",
    },
    {
        "text": "Third Text Box (SMALL CAPS)",
        "font": "Courier New",
        "size": 12,
        "style": "small-caps",
    },
]

# calculate vertical positions for the text boxes
box_height = (top - bottom) / len(texts)
for i, t in enumerate(texts):
    text_x = label_dimensions[0] / 2  # centered horizontally
    text_y = top - (i + 0.5) * box_height  # stagger vertically

    # adjust small caps style
    if t["style"] == "small-caps":
        t["text"] = t["text"].upper()

    # load font properties
    font_path = fm.findfont(fm.FontProperties(family=t["font"]))
    font = fm.FontProperties(fname=font_path, size=t["size"])

    # add text box
    ax.text(
        text_x,
        text_y,
        t["text"],
        ha="center",
        va="center",
        fontproperties=font,
        bbox=dict(
            boxstyle="round,pad=0.5", facecolor="white", edgecolor="black"
        ),
    )

# save or display the figure
plt.savefig("label_with_text_boxes.png", dpi=300)
plt.show()

# %%

fig, ax = plt.subplots(figsize=label_dimensions)
ax.set_xlim(0, label_dimensions[0])
ax.set_ylim(0, label_dimensions[1])
ax.set_aspect("equal")
ax.axis("off")
ax.add_patch(Rectangle((0, 0), *label_dimensions, color="lightyellow"))
border_size = 0.1  # in inches
border_padding = 0.2  # in inches
left = border_padding
bottom = border_padding
right = label_dimensions[0] - border_padding
top = label_dimensions[1] - border_padding
ax.add_patch(
    Rectangle(
        (left, bottom),
        right - left,
        top - bottom,
        edgecolor="black",
        facecolor="none",
        linewidth=border_size * 12,
    )
)

text_content = f"""\
ID Number:{" "*20}3244
Collection: AMNH
Collector: Dr. Montague
Location: North America
Formation: Navesink
Coordinates: (40.7128, -74.0060)
Date Found: 2024-01-01"""

font_path = fm.findfont(fm.FontProperties(family="Arial"))
font = fm.FontProperties(fname=font_path, size=14)

ax.text(
    label_dimensions[0] / 2,
    label_dimensions[1] / 2,
    text_content,
    ha="center",
    va="center",
    fontproperties=font,
    bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="black"),
)


output_file_svg = "aligned_text_box.svg"
plt.savefig(output_file_svg, format="svg")
print(f"Saved as SVG: {output_file_svg}")

plt.savefig("centered_text_box.png", dpi=300)
plt.show()
# %%
