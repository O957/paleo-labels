# %%

import matplotlib.pyplot as plt
import svgwrite

# %%
fig, ax = plt.subplots(figsize=(8, 6))
ax.axis("off")
text = "This is copyable text in Matplotlib."
ax.text(0.1, 0.5, text, fontsize=24, family="Arial")
fig.savefig("output.svg", format="svg")
fig.savefig("output.pdf", format="pdf")
print("Matplotlib figure with copyable text saved!")


html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Copyable Text</title>
</head>
<body>
    <p style="font-family: Arial; font-size: 24px; color: black;">
        This is copyable text in an HTML file.
    </p>
</body>
</html>
"""
with open("output.html", "w") as file:
    file.write(html_content)
print("HTML with copyable text saved!")


dwg = svgwrite.Drawing("output.svg", size=("800px", "600px"))
dwg.add(
    dwg.text(
        "This is copyable text",
        insert=(50, 50),
        style="font-family: Arial; font-size: 24px; fill: black;",
    )
)
dwg.save()
print("SVG with copyable text saved!")

# %%
