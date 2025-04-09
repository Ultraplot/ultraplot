# Generate square logo for website icon
import ultraplot as uplt, numpy as np
from matplotlib import patheffects as pe
from matplotlib.font_manager import FontProperties
from matplotlib import patches

font = FontProperties(fname="PermanentMarker-Regular.ttf")
fs = 33
sw = 3


# Set the figure with a polar projection
fig, ax = uplt.subplots()
n = 30
for idx, (color, rad) in enumerate(zip(np.linspace(0, 1, n), np.linspace(0, 0.5, n))):
    color = uplt.colormaps.get("viko")(color)
    circle = patches.Circle(
        (0.5, 0.5), radius=rad, facecolor=color, zorder=n - idx, alpha=(n - idx) / n
    )
    ax.add_artist(circle)


# Remove grid and labels
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
ax.set_frame_on(False)

# Overlay text
left = 0.575
middle = 0.52
ax.text(
    left,
    middle,
    "Ultra",
    fontsize=fs,
    fontproperties=font,
    va="center",
    ha="right",
    color="steelblue",
    path_effects=[
        pe.Stroke(linewidth=sw, foreground="white"),
        pe.Normal(),
    ],
    transform=ax.transAxes,
    zorder=n + 1,
)
ax.text(
    left,
    middle,
    "Plot",
    fontsize=fs,
    # fontproperties = font,
    va="center",
    ha="left",
    color="white",
    path_effects=[
        pe.Stroke(linewidth=sw, foreground="steelblue"),
        pe.Normal(),
    ],
    transform=ax.transAxes,
    zorder=n + 1,
)
fig.savefig("../docs/_static/logo_blank.svg")
