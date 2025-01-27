import os
import toml
import subprocess

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
        latex_template = rf"""
\documentclass[letterpaper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[table,xcdraw]{{xcolor}}
\usepackage{{geometry}}
\geometry{{
    top=1in,
    bottom=1in,
    left=1in,
    right=1in
}}
\pagestyle{{empty}}

\begin{{document}}
\noindent
\fbox{{\begin{{minipage}}[t][{3.5}in][t]{{{3.5}in}}
    \vspace{{-0.1in}}
    \noindent
        """
        if "header" in label_data:
            latex_template += rf"""
    \textbf{{\textcolor[HTML]{{{self.header_style['header_title_font_color']}}}{{\Large Header:}}}}\\[{self.spacing['space_between_sections']}ex]
    \textcolor[HTML]{{{self.header_style['header_content_font_color']}}}{{\texttt{{Species: {label_data['header'].get('species', '')}, Formation: {label_data['header'].get('formation', '')}}}}}\\
    \vspace{{{self.spacing['space_between_sections']}}}ex\\
    \textcolor[HTML]{{{self.header_style['header_title_font_color']}}}{{\hrulefill}}\\
            """
        if "body" in label_data:
            latex_template += rf"""
    \textbf{{\textcolor[HTML]{{{self.body_style['body_title_font_color']}}}{{\large Body:}}}}\\[{self.spacing['space_between_sections']}ex]
    \textcolor[HTML]{{{self.body_style['body_content_font_color']}}}{{Date Collected: {label_data['body'].get('date_collected', '')},\\
        Collector: {label_data['body'].get('collector', '')},\\
        Locale: {label_data['body'].get('locale', '')}}}\\
    \textcolor[HTML]{{{self.body_style['body_title_font_color']}}}{{\hrulefill}}\\
            """
        if "footer" in label_data:
            latex_template += rf"""
    \textbf{{\textcolor[HTML]{{{self.footer_style['footer_title_font_color']}}}{{\large Footer:}}}}\\[{self.spacing['space_between_sections']}ex]
    \textcolor[HTML]{{{self.footer_style['footer_content_font_color']}}}{{Repository: {label_data['footer'].get('repository', '')},\\
        ID Number: {label_data['footer'].get('id_number', '')}}}\\
            """

        latex_template += r"""
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
    config_path = "label_config.toml"
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
    # can leave space for image

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
