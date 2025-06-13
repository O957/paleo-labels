# This script contains the label-making app. The workflow
# consists of the user either (1) manually entering label
# and style content, (2) manually entering label content
# and loading a style template, or (3) loading a label and
# a style template a label. Multiple labels can be created
# in a single session.

import tkinter as tk


class PaleoLabelApp:
    def __init__(self, master):
        master.title("Paleo-Labels")

        # load toml style or label template file button
        self.btn_load_style = tk.Button(
            master, text="Upload Style TOML", command=self.load_style_file
        )
        self.btn_load_style.pack(fill="x", padx=10, pady=(10, 5))
        self.btn_load_label_template = tk.Button(
            master,
            text="Upload Label Template TOML",
            command=self.load_label_template_file,
        )
        self.btn_load_label_template.pack(fill="x", padx=10, pady=(10, 5))
