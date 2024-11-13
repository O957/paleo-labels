"""
Making A Label For Squalicorax Pristodontus

The following tutorial demonstrates how to
use Paleo Utils to make a label for a
specimen from the Late Cretaceous of
New Jersey that the author found.
"""

# NOTES: Two labels come to mind, i.e. collections and systematics labels (both are classes, subclassed as Labels). Systematics labels have Linnaen taxonomic considerations. Collections labels have elements such as Collector, Repository, Date Found, Locale, etc... Each Label has dimensions, font, a save path, and a font size. Each Label can be saved as an image, as SVG, as text, or as a PDF.

# NOTES: For labeling images, with Labels, the image can be divided into grids, with the grids being displayed out to the user. A utility can be finger print detection and erasing. A utility can be replacing the background with a color. For creating a chart (line or perpendicular diagram) the basis could be a measurement of the item, provided by the user, and the detection of the item of interest, then scaling of the chart. Another utility could be receiving a pair of images and making them symmetrically aligned. Another utility: convert coin in image to an line or perpendicular label marker.

# NOTES: For testing on FF, do not have users use it themselves, just have users provide you images.


# %%  LIBRARY IMPORTS


import paleo_utils

# %% CREATE LABEL WITH BORDER

label = paleo_utils.Label(
    save_path="../assets",
    border_style="dashed",
    border_color="black",
    border_size=0.2,
    border_padding_from_edge=0.5,
)
img = label._create_label_body()
img.show()


# %%

label_dictionary_defaults = {
    "save_path": None,
    "save_as_image": True,
    "image_format": ".jpg",
    "save_as_text": False,
    "save_as_svg": False,
    "save_as_latex": False,
    "body_font_path": "TeX Gyra Schola",
    "group_title_font_size": 9,
    "group_content_font_size": 9,
    "watermark": "",
    "watermark_font_path": "TeX Gyra Schola",
    "watermark_font_style": "regular",
    "watermark_font_size": 9,
    "watermark_color": "black",
    "watermark_opacity": 0.5,
    "watermark_image": None,
    "watermark_position": "best",
    "background_color": "white",
    "group_title_color": "black",
    "group_content_color": "black",
    "group_title_styling": "regular",
    "group_content_styling": "regular",
    "group_titles_to_hide": None,
    "spaces_between_group_lines": 0,
    "text_alignment": "center",
    "text_flush": False,
}
