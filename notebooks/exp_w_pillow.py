"""
Experimentation file for using
Python's PIL to generate boxes
with text.
"""

# %% LIBRARY IMPORTS

from PIL import Image, ImageDraw, ImageFont

import paleo_utils

# %% CREATE A SIMPLE IMAGE & DRAWER

# produce new image object
# see: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.new
new_img = Image.new(mode="RGB", size=(1000, 1000), color="white")

# create image draw object
# see: https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html
draw = ImageDraw.Draw(im=new_img)

# text to draw
text_to_add = """
Name: Crow Shark
Scientific Name: Squalicorax pristodontus
Collection: TPM Repository
Found By: The Author
"""

# example font
# see: https://pillow.readthedocs.io/en/stable/reference/ImageFont.html
# fnt = ImageFont.truetype(
#     "Pillow/Tests/fonts/FreeMono.ttf", 20)
try:
    fnt = ImageFont.truetype(
        font=paleo_utils.get_font_path("texgyreschola-regular.otf"),
        size=20,
    )
except IOError:
    fnt = ImageFont.load_default()

# adding text to image
draw.text(
    xy=(100, 100),
    text=text_to_add,
    fill="black",
    font=fnt,
)

# show image
new_img.show()

# %%
