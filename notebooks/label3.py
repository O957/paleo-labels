import os
import subprocess

import toml


class PaleontologyLabel:
    def __init__(self, config_path: str):
        self.config = toml.load(config_path)
        self.save_args = self.config["save_args"]
        self.body_style = self.config["body_style"]
        self.header_style = self.config["header_style"]
        self.footer_style = self.config["footer_style"]
        self.background = self.config["background"]
        self.spacing = self.config["spacing"]
        self.dimensions = self.config["dimensions"]

    def generate_label(self, label_data: dict):
        latex_template = """
        \documentclass[letterpaper]{article}
        \usepackage[utf8]{inputenc}
        \usepackage[table,xcdraw]{xcolor}
        \usepackage{geometry}
        \geometry{
            top=1in,
            bottom=1in,
            left=1in,
            right=1in
        }
        \pagestyle{empty}

        \begin{document}
        \noindent
        \fbox{\begin{minipage}[t][{height}in][t]{{width}in}
            \vspace{{-0.1in}}
            \noindent
        """

        if "header" in label_data:
            latex_template += f"""
            \textbf{\textcolor{{{header_title_color}}}{\Large Header:}}\\[{header_spacing}ex]
            \textcolor{{{header_content_color}}}{\texttt{Species: {species}, Formation: {formation}}}\\ \vspace{{{header_spacing}}}ex\\
            \textcolor{{{header_title_color}}}{\hrulefill}\\
            """.format(
                header_title_color=self.header_style["header_title_font_color"],
                header_content_color=self.header_style["header_content_font_color"],
                header_spacing=self.spacing["space_between_sections"],
                species=label_data["header"].get("species", ""),
                formation=label_data["header"].get("formation", "")
            )

        if "body" in label_data:
            latex_template += r"""
            \textbf{\textcolor{{{body_title_color}}}{\large Body:}}\\[{body_spacing}ex]
            \textcolor{{{body_content_color}}}{Date Collected: {date_collected},\\
                Collector: {collector},\\
                Locale: {locale}}\\
            \textcolor{{{body_title_color}}}{\hrulefill}\\
            """.format(
                body_title_color=self.body_style["body_title_font_color"],
                body_content_color=self.body_style["body_content_font_color"],
                body_spacing=self.spacing["space_between_sections"],
                date_collected=label_data["body"].get("date_collected", ""),
                collector=label_data["body"].get("collector", ""),
                locale=label_data["body"].get("locale", "")
            )

        if "footer" in label_data:
            latex_template += r"""
            \textbf{\textcolor{{{footer_title_color}}}{\large Footer:}}\\[{footer_spacing}ex]
            \textcolor{{{footer_content_color}}}{Repository: {repository},\\
                ID Number: {id_number}}\\
            """.format(
                footer_title_color=self.footer_style["footer_title_font_color"],
                footer_content_color=self.footer_style["footer_content_font_color"],
                footer_spacing=self.spacing["space_between_sections"],
                repository=label_data["footer"].get("repository", ""),
                id_number=label_data["footer"].get("id_number", "")
            )

        latex_template += """
        \end{minipage}}
        \end{document}
        """

        output_dir = self.save_args["save_path"]
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        tex_file_path = os.path.join(output_dir, "label.tex")
        with open(tex_file_path, "w") as tex_file:
            tex_file.write(latex_template)

        subprocess.run(["pdflatex", "-output-directory", output_dir, tex_file_path], check=True)

        if self.save_args["save_as_image"]:
            pdf_path = os.path.join(output_dir, "label.pdf")
            image_path = os.path.join(output_dir, f"label.{self.save_args['image_format']}")
            subprocess.run(["convert", "-density", str(self.dimensions["image_dots_per_inch"]), pdf_path, image_path], check=True)

if __name__ == "__main__":
    config_path = "example_config.toml"
    label_data = {
        "header": {
            "species": "Squalicorax pristodontus",
            "formation": "Basal Navesink",
        },
        "body": {
            "date_collected": "2024-08-29",
            "collector": "S233",
            "locale": "LCNACP01:08"
        },
        "footer": {
            "repository": "TM",
            "id_number": "3244",
        }
    }
    label_generator = PaleontologyLabel(config_path)
    label_generator.generate_label(label_data)



label = {
    "header": {
        "species": "Squalicorax pristodontus",
        "formation": "Basal Navesink",
    },
    "body": {
        "date_collected": "2024-08-29",
        "collector": "S233",
        "locale": "LCNACP01:08"
    },
    "footer": {
        "repository": "TM",
        "id_number": "3244",
    }
}
