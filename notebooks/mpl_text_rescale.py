# %%

import matplotlib.pyplot as plt

# %%


def rescale_text_to_fit(ax, text, x, y, width, height, **kwargs):
    from matplotlib.transforms import Bbox

    box = Bbox([[x, y], [x + width, y + height]])
    font_size = 10
    while True:
        t = ax.text(
            x, y, text, fontsize=font_size, va="top", ha="left", **kwargs
        )
        extent = t.get_window_extent(renderer=plt.gcf().canvas.get_renderer())
        if extent.width > box.width or extent.height > box.height:
            t.remove()
            font_size -= 1
            if font_size < 1:
                raise ValueError("Text cannot fit into the box.")
        else:
            break
    return t


# %%

fig, ax = plt.subplots(figsize=(6, 4))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")


ax.text(
    0.2,
    0.8,
    "Precise Placement",
    ha="left",
    va="top",
    bbox=dict(boxstyle="round", facecolor="lightgray", edgecolor="black"),
)


rescale_text_to_fit(
    ax,
    "Rescaled Text",
    0.2,
    0.5,
    0.5,
    0.1,
    bbox=dict(boxstyle="round", facecolor="lightblue"),
)


ax.text(0.5, 0.3, r"\underline{Underlined Text}", fontsize=12, ha="center")

ax.text(
    0.1,
    0.1,
    "Left-Flushed Text\nNext Line Left",
    ha="left",
    bbox=dict(boxstyle="round", facecolor="white"),
)

plt.show()

# %%
