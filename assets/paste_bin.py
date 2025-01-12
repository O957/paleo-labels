# TODO, SUPPORT MULTIPLE SECTIONS

# use_header: bool = attrs.field(
#     default=False,
#     validator=attrs.validators.instance_of(bool)
# )
# use_heading: bool = attrs.field(
#     default=False,
#     validator=attrs.validators.instance_of(
#         bool
#     ),
# )
# heading_font_size: int = attrs.field(
#     default=12,
#     validator=[
#         attrs.validators.instance_of(int),
#         attrs.validators.ge(4),
#         attrs.validators.le(20),
#     ],
# )

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

Attributes
----------
description:
    A short description of the specimen
    and or context surrounding the fossil.
    Defaults to None.

description_title
    The name of the description group
    on the label. Defaults to
    "Description: ".

domain
    The name of the domain of the specimen.
    The domain group defaults to "Domain: ".

domain_author
    The citation for the domain name.
    Defaults to "".

subdomain
    The name of the subdomain of the specimen.
    The subdomain group defaults to "Subdomain: ".

subdomain_author
    The citation for the subdomain name.
    Defaults to "".

kingdom
    The name of the kingdom of the specimen.
    The kingdom group defaults to "Kingdom: ".

kingdom_author
    The citation for the kingdom name.
    Defaults to "".

subkingdom
    The name of the subkingdom of the specimen.
    The subkingdom group defaults to "Subkingdom: ".

subkingdom_author
    The citation for the subkingdom name.
    Defaults to "".

infrakingdom
    The name of the infrakingdom of the specimen.
    The infrakingdom group defaults to "Infrakingdom: ".

infrakingdom_author
    The citation for the infrakingdom name.
    Defaults to "".

superphylum
    The name of the superphylum of the specimen.
    The superphylum group defaults to "Superphylum: ".

superphylum_author
    The citation for the superphylum name.
    Defaults to "".

phylum
    The name of the phylum (or division in botany) of the specimen.
    The phylum group defaults to "Phylum: ".

phylum_author
    The citation for the phylum name.
    Defaults to "".

subphylum
    The name of the subphylum of the specimen.
    The subphylum group defaults to "Subphylum: ".

subphylum_author
    The citation for the subphylum name.
    Defaults to "".

infraphylum
    The name of the infraphylum of the specimen.
    The infraphylum group defaults to "Infraphylum: ".

infraphylum_author
    The citation for the infraphylum name.
    Defaults to "".

microphylum
    The name of the microphylum of the specimen.
    The microphylum group defaults to "Microphylum: ".

microphylum_author
    The citation for the microphylum name.
    Defaults to "".

superclass
    The name of the superclass of the specimen.
    The superclass group defaults to "Superclass: ".

superclass_author
    The citation for the superclass name.
    Defaults to "".

class
    The name of the class of the specimen.
    The class group defaults to "Class: ".

class_author
    The citation for the class name.
    Defaults to "".

subclass
    The name of the subclass of the specimen.
    The subclass group defaults to "Subclass: ".

subclass_author
    The citation for the subclass name.
    Defaults to "".

infraclass
    The name of the infraclass of the specimen.
    The infraclass group defaults to "Infraclass: ".

infraclass_author
    The citation for the infraclass name.
    Defaults to "".

parvclass
    The name of the parvclass of the specimen.
    The parvclass group defaults to "Parvclass: ".

parvclass_author
    The citation for the parvclass name.
    Defaults to "".

superorder
    The name of the superorder of the specimen.
    The superorder group defaults to "Superorder: ".

superorder_author
    The citation for the superorder name.
    Defaults to "".

order
    The name of the order of the specimen.
    The order group defaults to "Order: ".

order_author
    The citation for the order name.
    Defaults to "".

suborder
    The name of the suborder of the specimen.
    The suborder group defaults to "Suborder: ".

suborder_author
    The citation for the suborder name.
    Defaults to "".

infraorder
    The name of the infraorder of the specimen.
    The infraorder group defaults to "Infraorder: ".

infraorder_author
    The citation for the infraorder name.
    Defaults to "".

parvorder
    The name of the parvorder of the specimen.
    The parvorder group defaults to "Parvorder: ".

parvorder_author
    The citation for the parvorder name.
    Defaults to "".

superfamily
    The name of the superfamily of the specimen.
    The superfamily group defaults to "Superfamily: ".

superfamily_author
    The citation for the superfamily name.
    Defaults to "".

family
    The name of the family of the specimen.
    The family group defaults to "Family: ".

family_author
    The citation for the family name.
    Defaults to "".

subfamily
    The name of the subfamily of the specimen.
    The subfamily group defaults to "Subfamily: ".

subfamily_author
    The citation for the subfamily name.
    Defaults to "".

infrafamily
    The name of the infrafamily of the specimen.
    The infrafamily group defaults to "Infrafamily: ".

infrafamily_author
    The citation for the infrafamily name.
    Defaults to "".

supertribe
    The name of the supertribe of the specimen.
    The supertribe group defaults to "Supertribe: ".

supertribe_author
    The citation for the supertribe name.
    Defaults to "".

tribe
    The name of the tribe of the specimen.
    The tribe group defaults to "Tribe: ".

tribe_author
    The citation for the tribe name.
    Defaults to "".

subtribe
    The name of the subtribe of the specimen.
    The subtribe group defaults to "Subtribe: ".

subtribe_author
    The citation for the subtribe name.
    Defaults to "".

genus
    The name of the genus of the specimen.
    The genus group defaults to "Genus: ".

genus_author
    The citation for the genus name.
    Defaults to "".

subgenus
    The name of the subgenus of the specimen.
    The subgenus group defaults to "Subgenus: ".

subgenus_author
    The citation for the subgenus name.
    Defaults to "".

section
    The name of the section within the genus.
    The section group defaults to "Section: ".

section_author
    The citation for the section name.
    Defaults to "".

subsection
    The name of the subsection within the genus.
    The subsection group defaults to "Subsection: ".

subsection_author
    The citation for the subsection name.
    Defaults to "".

series
    The name of the series within the genus.
    The series group defaults to "Series: ".

series_author
    The citation for the series name.
    Defaults to "".

subseries
    The name of the subseries within the genus.
    The subseries group defaults to "Subseries: ".

subseries_author
    The citation for the subseries name.
    Defaults to "".

species
    The scientific name of the species.
    The species group defaults to "Species: ".

species_author
    The citation for the species name.
    Defaults to "".

subspecies
    The name of the subspecies of the specimen.
    The subspecies group defaults to "Subspecies: ".

subspecies_author
    The citation for the subspecies name.
    Defaults to "".

variety
    The name of the variety of the specimen.
    The variety group defaults to "Variety: ".

variety_author
    The citation for the variety name.
    Defaults to "".

subvariety
    The name of the subvariety of the specimen.
    The subvariety group defaults to "Subvariety: ".

subvariety_author
    The citation for the subvariety name.
    Defaults to "".

form
    The name of the form of the specimen.
    The form group defaults to "Form: ".

form_author
    The citation for the form name.
    Defaults to "".

subform
    The name of the subform of the specimen.
    The subform group defaults to "Subform: ".

subform_author
    The citation for the subform name.
    Defaults to "".
"""
