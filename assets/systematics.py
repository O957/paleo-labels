# @attrs.define
# class SystematicsLabel(Label):
#     """
#     A label class for individual or group systematics,
#     containing taxonomic details.
#     """

#     # domain Level
#     domain: str = "Domain: "
#     domain_author: str = ""
#     subdomain: str = "Subdomain: "
#     subdomain_author: str = ""

#     # kingdom Level
#     kingdom: str = "Kingdom: "
#     kingdom_author: str = ""
#     subkingdom: str = "Subkingdom: "
#     subkingdom_author: str = ""
#     infrakingdom: str = "Infrakingdom: "
#     infrakingdom_author: str = ""
#     superphylum: str = "Superphylum: "
#     superphylum_author: str = ""

#     # phylum (or division) Level
#     phylum: str = "Phylum: "
#     phylum_author: str = ""
#     subphylum: str = "Subphylum: "
#     subphylum_author: str = ""
#     infraphylum: str = "Infraphylum: "
#     infraphylum_author: str = ""
#     microphylum: str = "Microphylum: "
#     microphylum_author: str = ""
#     superclass: str = "Superclass: "
#     superclass_author: str = ""

#     # class Level
#     class_level: str = "Class: "
#     class_author: str = ""
#     subclass: str = "Subclass: "
#     subclass_author: str = ""
#     infraclass: str = "Infraclass: "
#     infraclass_author: str = ""
#     parvclass: str = "Parvclass: "
#     parvclass_author: str = ""
#     superorder: str = "Superorder: "
#     superorder_author: str = ""

#     # order Level
#     order: str = "Order: "
#     order_author: str = ""
#     suborder: str = "Suborder: "
#     suborder_author: str = ""
#     infraorder: str = "Infraorder: "
#     infraorder_author: str = ""
#     parvorder: str = "Parvorder: "
#     parvorder_author: str = ""
#     superfamily: str = "Superfamily: "
#     superfamily_author: str = ""

#     # family Level
#     family: str = "Family: "
#     family_author: str = ""
#     subfamily: str = "Subfamily: "
#     subfamily_author: str = ""
#     infrafamily: str = "Infrafamily: "
#     infrafamily_author: str = ""
#     supertribe: str = "Supertribe: "
#     supertribe_author: str = ""

#     # tribe Level
#     tribe: str = "Tribe: "
#     tribe_author: str = ""
#     subtribe: str = "Subtribe: "
#     subtribe_author: str = ""

#     # genus Level
#     genus: str = "Genus: "
#     genus_author: str = ""
#     subgenus: str = "Subgenus: "
#     subgenus_author: str = ""
#     section: str = "Section: "
#     section_author: str = ""
#     subsection: str = "Subsection: "
#     subsection_author: str = ""
#     series: str = "Series: "
#     series_author: str = ""
#     subseries: str = "Subseries: "
#     subseries_author: str = ""

#     # species Level
#     species: str = "Species: "
#     species_author: str = ""
#     subspecies: str = "Subspecies: "
#     subspecies_author: str = ""
#     variety: str = "Variety: "
#     variety_author: str = ""
#     subvariety: str = "Subvariety: "
#     subvariety_author: str = ""
#     form: str = "Form: "
#     form_author: str = ""
#     subform: str = "Subform: "
#     subform_author: str = ""


# def __attrs_post_init__(self):

#         # DIMENSION HANDLING

#         # ensure only one dimension unit is specified (either inches or centimeters)
#         if self.dimensions_in_centimeters and self.dimensions_in_inches:
#             raise ValueError(
#                 "You cannot specify both dimensions_in_inches and dimensions_in_centimeters. Please provide only one."
#             )
#         # handle case when dimensions are specified in centimeters
#         if self.dimensions_in_centimeters:
#             # set dimensions in centimeters
#             self.dimensions_unit = "centimeters"
#             self.dimensions_as_centimeters = self.dimensions
#             # convert to inches and pixels using the helper methods
#             self.dimensions_as_inches = self._convert_values_to_inches(
#                 values=self.dimensions,
#                 unit=self.dimensions_unit,
#             )
#             self.dimensions_as_pixels = self._convert_values_to_pixels(
#                 values=self.dimensions_as_inches,
#                 unit="inches",
#             )
#         # handle the case when dimensions are specified in inches
#         elif self.dimensions_in_inches:
#             # set dimensions in inches
#             self.dimensions_unit = "inches"
#             self.dimensions_as_inches = self.dimensions
#             # convert to centimeters and pixels using the helper methods
#             self.dimensions_as_centimeters = (
#                 self._convert_values_to_centimeters(
#                     values=self.dimensions,
#                     unit=self.dimensions_unit,
#                 )
#             )
#             self.dimensions_as_pixels = self._convert_values_to_pixels(
#                 values=self.dimensions,
#                 unit=self.dimensions_unit,
#             )
#         # raise an error if neither dimensions_in_centimeters nor dimensions_in_inches is specified
#         elif not (self.dimensions_in_centimeters or self.dimensions_in_inches):
#             raise ValueError(
#                 "You must specify either dimensions_in_centimeters or dimensions_in_inches."
#             )

#     @classmethod
#     def from_dict(cls, data: dict):
#         """
#         Instantiates a Label object from a
#         dictionary.
#         """
#         return cls(**data)

#     def _create_label_body(self):
#         """
#         Create the body of the Label using
#         PIL and the provided dimensions in
#         pixels, including background color.
#         """
#         # get label width and height in pixels
#         label_width, label_height = self.dimensions_as_pixels
#         # create the base image with background color
#         img = Image.new(
#             mode="RGB",
#             size=(
#                 int(label_width),
#                 int(label_height),
#             ),
#             color=self.background_color,
#         )
#         drawn_img = ImageDraw.Draw(img)
#         # add the border if specified
#         if self.border_style:
#             self._add_border(
#                 label_as_img=drawn_img,
#                 label_width=label_width,
#                 label_height=label_height,
#             )
#         # return generated image
#         return img

#     def _add_border(
#         self,
#         label_as_img,
#         label_width: float,
#         label_height: float,
#     ) -> float:
#         """
#         Add a border to the label using
#         the specified border style, color,
#         and size.
#         """
#         # convert border size and padding
#         # to pixels from whatever unit was
#         # used
#         border_size = self._convert_values_to_pixels(
#             [self.border_size],
#             unit=self.dimensions_unit,
#         )[0]
#         border_padding = self._convert_values_to_pixels(
#             [self.border_padding_from_edge],
#             unit=self.dimensions_unit,
#         )[0]
#         # border coordinates
#         border_left = border_padding
#         border_top = border_padding
#         border_right = label_width - border_padding
#         border_bottom = label_height - border_padding
#         if self.border_style == "solid":
#             # draw a solid border using
#             # rectangle
#             label_as_img.rectangle(
#                 [
#                     (border_left, border_top),
#                     (border_right, border_bottom),
#                 ],
#                 outline=self.border_color,
#                 width=int(border_size),
#             )
#         elif self.border_style == "dashed":
#             # draw a dashed border
#             dash_length = 10  # TODO: adjust length of each dash
#             for x in range(
#                 border_left,
#                 border_right,
#                 dash_length * 2,
#             ):
#                 label_as_img.line(
#                     [
#                         (x, border_top),
#                         (
#                             x + dash_length,
#                             border_top,
#                         ),
#                     ],
#                     fill=self.border_color,
#                     width=int(border_size),
#                 )
#                 label_as_img.line(
#                     [
#                         (x, border_bottom),
#                         (
#                             x + dash_length,
#                             border_bottom,
#                         ),
#                     ],
#                     fill=self.border_color,
#                     width=int(border_size),
#                 )
#             for y in range(
#                 border_top,
#                 border_bottom,
#                 dash_length * 2,
#             ):
#                 label_as_img.line(
#                     [
#                         (border_left, y),
#                         (
#                             border_left,
#                             y + dash_length,
#                         ),
#                     ],
#                     fill=self.border_color,
#                     width=int(border_size),
#                 )
#                 label_as_img.line(
#                     [
#                         (border_right, y),
#                         (
#                             border_right,
#                             y + dash_length,
#                         ),
#                     ],
#                     fill=self.border_color,
#                     width=int(border_size),
#                 )
#         elif self.border_style == "dotted":
#             # draw a dotted border using
#             # small circles
#             dot_radius = 2  # TODO adjust size of the dot
#             for x in range(
#                 border_left,
#                 border_right,
#                 2 * dot_radius,
#             ):
#                 label_as_img.ellipse(
#                     [
#                         x,
#                         border_top,
#                         x + dot_radius,
#                         border_top + dot_radius,
#                     ],
#                     fill=self.border_color,
#                 )
#                 label_as_img.ellipse(
#                     [
#                         x,
#                         border_bottom - dot_radius,
#                         x + dot_radius,
#                         border_bottom,
#                     ],
#                     fill=self.border_color,
#                 )
#             for y in range(
#                 border_top,
#                 border_bottom,
#                 2 * dot_radius,
#             ):
#                 label_as_img.ellipse(
#                     [
#                         border_left,
#                         y,
#                         border_left + dot_radius,
#                         y + dot_radius,
#                     ],
#                     fill=self.border_color,
#                 )
#                 label_as_img.ellipse(
#                     [
#                         border_right - dot_radius,
#                         y,
#                         border_right,
#                         y + dot_radius,
#                     ],
#                     fill=self.border_color,
#                 )
#         else:
#             raise ValueError(f"Unsupported border style: {self.border_style}")


# def _create_label_body(self):
#         """
#         Create the body of the Label using
#         matplotlib and the provided dimensions
#         in inches or centimeters,
#         including background color.
#         """
#         fig, ax = plt.subplots(figsize=self.dimensions_as_inches)
#         ax.set_xlim(0, self.dimensions_as_inches[0])
#         ax.set_ylim(0, self.dimensions_as_inches[1])
#         ax.set_aspect("equal")
#         ax.axis("off")
#         # add background color
#         ax.add_patch(
#             Rectangle((0, 0),
#             *self.dimensions_as_inches,
#             color=self.background_color))
#         # add border if specified
#         if self.border_style:
#             self._add_border(ax)
#         return fig, ax

#     def _add_border(self, ax):
#         """
#         Add a border to the label using
#         the specified border style, color,
#         and size.
#         """
#         border_size = self._convert_values_to_inches([self.border_size], unit=self.dimensions_unit)[0]
#         border_padding = self._convert_values_to_inches([self.border_padding_from_edge], unit=self.dimensions_unit)[0]

#         left = border_padding
#         bottom = border_padding
#         right = self.dimensions_as_inches[0] - border_padding
#         top = self.dimensions_as_inches[1] - border_padding

#         if self.border_style == "solid":
#             ax.add_patch(Rectangle((left, bottom), right - left, top - bottom,
#                                    edgecolor=self.border_color, facecolor="none", linewidth=border_size))
#         elif self.border_style == "dashed":
#             ax.add_patch(Rectangle((left, bottom), right - left, top - bottom,
#                                    edgecolor=self.border_color, facecolor="none",
#                                    linewidth=border_size, linestyle=(0, (5, 5))))
#         elif self.border_style == "dotted":
#             ax.add_patch(Rectangle((left, bottom), right - left, top - bottom,
#                                    edgecolor=self.border_color, facecolor="none",
#                                    linewidth=border_size, linestyle=(0, (1, 3))))
#         else:
#             raise ValueError(f"Unsupported border style: {self.border_style}")

# OPTIONS FOR WATERMARKS

#     watermark: str = attrs.field(
#         default="",
#         validator=attrs.validators.instance_of(str),
#     )
#     watermark_font_path: str = attrs.field(
#         default="TeX Gyra Schola",
#         validator=[
#             attrs.validators.instance_of(str),
#             attrs.validators.in_(SUPPORTED_FONTS),
#         ],
#     )
#     watermark_font_style: str = attrs.field(
#         default="regular",
#         validator=[
#             attrs.validators.instance_of(str),
#             attrs.validators.in_(SUPPORTED_STYLES),
#         ],
#     )
#     watermark_font_size: int = attrs.field(
#         default=9,
#         validator=[
#             attrs.validators.instance_of(int),
#             attrs.validators.ge(4),
#             attrs.validators.le(20),
#         ],
#     )
#     watermark_color: str = attrs.field(
#         default="black",
#         validator=attrs.validators.instance_of(str),
#     )
#     watermark_opacity: float = attrs.field(
#         default=0.5,
#         validator=[
#             attrs.validators.ge(0.0),
#             attrs.validators.le(1.0),
#         ],
#     )
#     watermark_image: str | None = attrs.field(
#         default=None,
#         validator=attrs.validators.optional(attrs.validators.instance_of(str)),
#     )
#     watermark_position: str = attrs.field(
#         default="best",
#         validator=[
#             attrs.validators.instance_of(str),
#             attrs.validators.in_(SUPPORTED_POSITIONS),
#         ],
#     )

# # OPTIONS FOR QR CODES

#     qr_code: bool = attrs.field(
#         default=False,
#         validator=attrs.validators.instance_of(bool),
#     )
#     qr_code_size_in_inches: float = attrs.field(
#         default=0.75,
#         validator=[
#             attrs.validators.ge(0.25),
#             attrs.validators.le(2.0),
#         ],  # TODO: raise error depending on border size
#     )
#     qr_code_position: str = attrs.field(
#         default="best",
#         validator=[
#             attrs.validators.instance_of(str),
#             attrs.validators.in_(SUPPORTED_POSITIONS),
#         ],
#     )
#     qr_code_on_back: bool = attrs.field(
#         default=False,
#         validator=attrs.validators.instance_of(bool),
#     )


# @attrs.define(kw_only=True)
# class CollectionsLabel(Label):
#     """
#     A label for collections specimens, i.e.
#     labels involving more details than
#     fossil systematics. The kwargs parameter
#     used is the group title.
#     """

#     collection: str | None = attrs.field(default=None)
#     id_number: str | None = attrs.field(default=None)
#     collector: str | None = attrs.field(default=None)
#     species: str | None = attrs.field(default=None)
#     species_author: str | None = attrs.field(default=None)
#     common_name: str | None = attrs.field(default=None)
#     location: str | None = attrs.field(default=None)
#     coordinates: tuple[float, float] | None = attrs.field(default=None)
#     coordinates_separate: bool = attrs.field(default=False)
#     date_found: str | None = attrs.field(default=None)
#     date_cataloged: str | None = attrs.field(default=None)
#     formation: str | None = attrs.field(default=None)
#     formation_author: str | None = attrs.field(default=None)
#     chrono_age: str | None = attrs.field(default=None)
#     chrono_age_author: str | None = attrs.field(default=None)
#     size: str | None = attrs.field(default=None)
#     link: str | None = attrs.field(default=None)

#     default_titles = {
#         "collection": "Collection: ",
#         "id_number": "ID Number: ",
#         "collector": "Collector: ",
#         "species": "Scientific Name: ",
#         "species_author": "Species Author: ",
#         "common_name": "Common Name: ",
#         "location": "Location: ",
#         "coordinates": "Coordinates: ",
#         "date_found": "Date Found: ",
#         "date_cataloged": "Date Cataloged: ",
#         "formation": "Formation: ",
#         "formation_author": "Formation Author: ",
#         "chrono_age": "Age: ",
#         "chrono_age_author": "Age Author: ",
#         "size": "Size: ",
#         "link": "Link: ",
#     }

#     title_overrides: dict[str, str] = attrs.field(
#         factory=dict
#     )  # empty by default

#     _ordered_kwargs: dict = attrs.field(init=False)

#     def __init__(self, **kwargs):
#         self._ordered_kwargs = {key: kwargs[key] for key in kwargs}

#     def __attrs_post_init__(self):
#         # update title_overrides with any user-provided overrides
#         if self.title_overrides:
#             # merge user-provided titles, overriding defaults
#             for (
#                 key,
#                 value,
#             ) in self.title_overrides.items():
#                 if key in self.default_titles:
#                     self.default_titles[key] = value

#     def _get_collections_attrs(self):
#         label_attrs = {attr.name for attr in Label.__attrs_attrs__}
#         # collections_attrs = {
#         #     attr.name: getattr(self, attr.name)
#         #     for attr in self.__attrs_attrs__
#         #     if attr.name not in label_attrs
#         # }
#         # print(self.__attrs_attrs__)
#         collections_attrs = {
#             key: value
#             for key, value in self._ordered_kwargs.items()
#             if key not in label_attrs
#         }
#         return collections_attrs

#     def label(self):
#         # empty list for parts of the final label
#         parts = []
#         # collections label exclusive attrs
#         collections_attrs = self._get_collections_attrs()
#         # iterative over collections attrs
#         for (
#             key,
#             value,
#         ) in collections_attrs.items():
#             # for all non-None collections attrs, proceed
#             if value is not None and not isinstance(value, dict):
#                 # edit title with spaces and capitalized
#                 title = self.default_titles.get(
#                     key,
#                     f"{key.replace('_', ' ').capitalize()}: ",
#                 )
#                 # add the group
#                 parts.append(f"{title}{value}")
#         # consolidate to multiline label
#         return "\n".join(parts)
