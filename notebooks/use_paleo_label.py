# %% LIBRARIES USED

import paleo_utils

# %% USE LABEL

label_full = paleo_utils.Label(
    save_path="label_output",
    dimensions=(6, 4),
    background_color="lightyellow",
    border_style="solid",
    header=[{"Genus": "Examplicus"}, {"Species": "fossil"}],
    body=[
        {"ID Number": "3432"},
        {"Location": "North America"},
        {"Formation": "Navesink"},
    ],
)


# %%
