"""
Attributes
----------
save_path
    The location to save the
    generated label(s). Accepts str or
    pathlib.Path input.

save_as_image
    Whether to save the label
    as an image. Defaults to
    True.

image_format
    What file type to save the image
    as. Only applies if save_as_image is
    True. Only covers ".jpg", ".png", and
    ".heic". Defaults to ".jpg".

save_as_text
    Whether to save the label
    as plain text. Defaults to
    False.

save_as_svg
    Whether to save the label
    as an svg. Defaults to
    False.

save_as_latex
    Whether to save the label
    as latex. Defaults to
    False.

font_path
    The path to the desired font.
    Can be the name of a pre-loaded
    font. Defaults to Time News Roman.

font_size
    The initially desired size of the
    font to use. Defaults to 9. Will
    resize depending on the label
    dimensions. Overridden if
    group_font_size and text_font_size
    are provided. Validated to be
    between 4 and 20.

group_font_size
    The initially desired size of the
    font for groups (e.g. Collector or
    Phylum). Defaults to 9. Validated
    to be between 4 and 20.

text_font_size
    The initially desired size of the
    font for text. Defaults to 9.
    Validated to be between 4 and 20.

date_format
    The format to list dates on
    labels. Defaults to IS08601
    formatting, i.e. YYYY-MM-DD

watermark_text
    Text indicating the creator
    of the label. Defaults to
    empty string.

watermark_font
    The font to use for the
    watermark text. Defaults to
    Time News Roman.

watermark_font_style
    The font size to use for
    the watermark text. Defaults
    to 9. Validated to be between
    4 and 20.

watermark_font_size
    The font style to use for
    the watermark text.

watermark_color
    The color of the watermark
    text. Defaults to black.

watermark_opacity
    The opacity of the watermark
    text. Defaults to 0.5. Validated
    to be between 0.0 and 1.0.

watermark_image
    Image indicating the creator
    of the label. Negates watermark
    text, if selected.

watermark_position
    The position of the watermark.
    Options include cross product
    of top, middle, bottom and left,
    center, right. Defaults to
    bottom-left.

background_color
    The background color of the
    label. Defaults to white. Accepts
    color names or hexcodes.

color
    The color to use for all the text.
    Remains except if groups_colors or
    text_colors is provided. Defaults to
    black.

group_colors : dict[str, str] | str
    The colors to use for the different
    groups. If single color, that color
    is used for all groups. Defaults to
    black.

text_colors : dict[str, str] | str
    The colors to use for the text across
    different groups. If single color,
    that color is used for all text. Defaults
    to black.

group_styling : dict[str, str] | list[str]
    Styling to apply to groups. If single list
    is provided, the styling is applied to all
    groups. Options include underlining, bold,
    italicizing, and small-caps. Defaults to
    bold.

text_styling : dict[str, str] | list[str]
    Styling to apply to text. If single list
    is provided, the styling is applied to all
    text across groups. Options include underlining,
    bold, italicizing, and small-caps. Defaults to
    None.

text_alignment
    How to align the label text. Defaults to center.
    Options include center, right, or left.

text_flush
    Whether to have all text corresponding to groups
    to be flushly aligned. Defaults to False. Only
    applies to left or right aligned text.

dimensions
    The size of the image.

dimensions_system
    Which system to use for the dimensions. Options
    include inches, centimeters, or pixels. Defaults
    to pixels.

border_style
    The style of the border to use. Defaults to None.
    Options include solid, dashed, and dotted.

border_color
    The color of the border, if used.
    Defaults to black. Accepts hexcodes
    or color names.

border_size
    The thickness of the label border.

hide_group_names
    Whether to hide group names.
    Defaults to False.

qr_code
    Whether to convert and save the
    label as a QR code.

qr_code_size
    The size of the QR code in pixels.

qr_code_position
    The position of the QR code.
    Options include cross product
    of top, middle, bottom and left,
    center, right. Defaults to
    bottom-left. Cannot conflict with
    watermark, if selected.

image_path
    Path to an image to have in the
    label above the label text.

image_dimensions
    What percentage of the label's
    dimensions to make the image.

image_dpi
    The quality of the image to
    retain.

override_size_w_image
    Whether to scale the label text to
    accommodate the image or scale the
    label size instead.

to_hide
    A list of the attributes of the label
    to not display the group name for.
    Defaults to None.
"""

"""
A label for collections specimens, i.e.
labels involving more details than
fossil systematics. The kwargs parameter
used is the group title.


Attributes
----------
coordinates_separate
    Whether to have the coordinates listed
    as their own line.


Optional Keyword Arguments
--------------------------
collection
    The name of the collection housing
    the specimen.

id_number
    The ID number of the specimen in the
    housing collection.

collector
    The name of the collector, if this
    information is known.

species
    The scientific name of the species
    that the label is associated with.

species_author
    The author of the scientific name of
    the species that the label is
    associated with.

species_author_separate
    Whether to place the species author
    separate from the species.

common_name
    The common name of the species
    that the label is associated with.

location
    The geographical name of the location
    where the specimen was retrieved.

coordinates
    The coordinates of the geographical
    location where the specimen was retrieved.

date_found
    The date the specimen was found.

date_cataloged
    The date the specimen was cataloged.

formation
    The formation in which the specimen
    was found.

formation_author
    The author of the formation in which
    the specimen was found. Defaults to
    same placement.

chrono_age
    The chronostratigraphic age of the
    specimen.

chrono_age_author
    The author of the chronostratigraphic
    age of the specimen. Defaults to
    same placement.

size
    The size and weight of the specimen.

link
    A URL to the specimen online.
"""
