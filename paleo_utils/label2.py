# %%

import json
import pathlib

import attrs
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# %%


@attrs.define(kw_only=True)
class Label:
    """
    Class for a Label with a header, body,
    and footer.
    """

    # REQUIRED SECTIONS
    body: list[dict[str, str]] = attrs.field(
        validator=attrs.validators.deep_iterable(
            member_validator=attrs.validators.instance_of(dict),
            iterable_validator=attrs.validators.instance_of(list),
        )
    )
    header: list[dict[str, str]] | None = None
    footer: list[dict[str, str]] | None = None

    # SAVING OPTIONS
    save_path: str | pathlib.Path = attrs.field()
    save_as_image: bool = attrs.field(default=True)
    image_format: str = attrs.field(default="png")
    save_as_text: bool = attrs.field(default=False)
    save_as_svg: bool = attrs.field(default=False)
    save_as_tex: bool = attrs.field(default=False)
    save_as_json: bool = attrs.field(default=False)

    # FONT OPTIONS
    body_font_path: str = "Times New Roman"
    body_title_font_size: int = 10
    body_content_font_size: int = 12
    body_title_font_styling: str = "bold"
    body_content_font_styling: str = "regular"
    body_title_font_color: str = "black"
    body_content_font_color: str = "darkblue"

    header_font_path: str = "Courier"
    header_title_font_size: int = 14
    header_content_font_size: int = 12
    header_title_font_styling: str = "bold"
    header_content_font_styling: str = "italic"
    header_title_font_color: str = "blue"
    header_content_font_color: str = "darkgreen"

    footer_font_path: str = "Arial"
    footer_title_font_size: int = 12
    footer_content_font_size: int = 10
    footer_title_font_styling: str = "bold"
    footer_content_font_styling: str = "regular"
    footer_title_font_color: str = "purple"
    footer_content_font_color: str = "black"

    # BACKGROUND COLORS
    label_background_color: str = "white"
    header_background_color: str = "white"
    body_background_color: str = "white"
    footer_background_color: str = "white"

    # SPACING
    body_spaces_between_lines: int = 0
    header_spaces_between_lines: int = 0
    footer_spaces_between_lines: int = 0
    space_between_sections: int = 0

    # DIMENSIONS
    dimensions: tuple[float, float] = (4.0, 4.0)
    image_dots_per_inch: int = 150

    def _convert_to_string(self, section: list[dict[str, str]] | None) -> str:
        """
        Converts a section (header, body, footer) into a string.
        """
        if not section:
            return ""
        return "\n".join(
            f"{group}: {content}"
            for group in section
            for group, content in group.items()
        )

    def render(self):
        """
        Renders the label as a Matplotlib plot.
        """
        fig, ax = plt.subplots(figsize=self.dimensions)
        ax.set_xlim(0, self.dimensions[0])
        ax.set_ylim(0, self.dimensions[1])
        ax.set_aspect("equal")
        ax.axis("off")

        # add background
        ax.add_patch(
            Rectangle(
                (0, 0), *self.dimensions, color=self.label_background_color
            )
        )

        # calculate section heights
        section_height = self.dimensions[1] / 3
        width = self.dimensions[0]

        # render header
        if self.header:
            header_text = self._convert_to_string(self.header)
            ax.text(
                width / 2,
                2 * section_height,
                header_text,
                ha="center",
                va="center",
                fontsize=self.header_content_font_size,
                color=self.header_content_font_color,
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor=self.header_background_color,
                    edgecolor="black",
                ),
            )

        # render body
        body_text = self._convert_to_string(self.body)
        ax.text(
            width / 2,
            section_height,
            body_text,
            ha="center",
            va="center",
            fontsize=self.body_content_font_size,
            color=self.body_content_font_color,
            bbox=dict(
                boxstyle="round,pad=0.5",
                facecolor=self.body_background_color,
                edgecolor="black",
            ),
        )

        # render footer
        if self.footer:
            footer_text = self._convert_to_string(self.footer)
            ax.text(
                width / 2,
                0,
                footer_text,
                ha="center",
                va="center",
                fontsize=self.footer_content_font_size,
                color=self.footer_content_font_color,
                bbox=dict(
                    boxstyle="round,pad=0.5",
                    facecolor=self.footer_background_color,
                    edgecolor="black",
                ),
            )

        plt.show()

    def save(self):
        """
        Saves the label in the specified formats.
        """
        if self.save_as_image:
            plt.savefig(self.save_path, format=self.image_format)
        if self.save_as_text:
            with open(f"{self.save_path}.txt", "w") as f:
                f.write(self._convert_to_string(self.body))
        if self.save_as_svg:
            plt.savefig(f"{self.save_path}.svg")
        if self.save_as_json:
            with open(f"{self.save_path}.json", "w") as f:
                json.dump(
                    {
                        "header": self.header,
                        "body": self.body,
                        "footer": self.footer,
                    },
                    f,
                    indent=4,
                )


# %%

header = [{"Title": "Fossil Specimen"}, {"Subtitle": "Jurassic Period"}]
body = [
    {"ID": "3244"},
    {"Location": "North America"},
    {"Formation": "Navesink"},
]
footer = [{"Collector": "Dr. Montague"}, {"Date Found": "2024-01-01"}]

label = Label(
    header=header,
    body=body,
    footer=footer,
    save_path="label_output.png",
    dimensions=(6, 4),
    label_background_color="lightgray",
    header_background_color="lightblue",
    body_background_color="white",
    footer_background_color="lightyellow",
)

label.render()
# label.save()

# %%
