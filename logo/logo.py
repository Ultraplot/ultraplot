# %%
import ultraplot as plt, numpy as np

from matplotlib.font_manager import FontProperties
from matplotlib import patheffects as pe
from matplotlib.patches import Rectangle
from scipy.ndimage import gaussian_filter

font = FontProperties(fname="./PermanentMarker-Regular.ttf")


fs = 38
left = 0.575
sw = 3
fig, ax = plt.subplots(figsize=(3, 1.25))
ax.text(
    left,
    0.5,
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
)
ax.text(
    left,
    0.5,
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
)

shift = 0.033
import colorengine as ce

colors = np.linspace(0, 1, 4, 0)
# colors = plt.colormaps.get_cmap("viko")(colors)
colors = ce.vivid(colors)
for idx, color in enumerate(colors):
    s = idx * shift
    ax.axhline(0.275 - 2.3 * s, 0.59 + s, 0.9 - s, color=color, ls="-", lw=3)
ax.axis(False)
# fig.set_facecolor("lightgray")


# Create checkerboard pattern
n_squares_x, n_squares_y = 20, 8  # Adjust number of squares
square_size = 0.1  # Size of each square


fig_aspect = fig.get_figwidth() / fig.get_figheight()
square_size_y = 0.1  # Base square size in y direction
square_size_x = square_size_y / fig_aspect  # Adjust x size to maintain square shape

n_squares_x = (
    int(1.0 / square_size_x) + 1
)  # Calculate number of squares needed in x direction

# Create alpha mask with Gaussian fade
x = np.linspace(-2, 2, n_squares_x)
y = np.linspace(-2, 2, n_squares_y)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
alpha = np.exp(-(R**2) / 0.75)  # Adjust the 1.0 to control fade rate
alpha = gaussian_filter(alpha, sigma=0.5)  # Adjust sigma for smoothness

# Create colormap gradient
cmap = plt.colormaps.get_cmap("viko")  # Choose your colormap

for i in range(n_squares_x):
    for j in range(n_squares_y):
        if (i + j) % 2 == 0:  # Checkerboard pattern
            color = cmap(i / n_squares_x)  # Color varies along x-axis
            rect = Rectangle(
                (i * square_size_x - 0.3, j * square_size_y + 0.075),
                square_size_x,
                square_size_y,
                facecolor=color,
                alpha=alpha[j, i],
                transform=ax.transAxes,
            )
            ax.add_patch(rect)


fig.savefig(
    "UltraPlotLogo.svg",
    transparent=True,
    bbox_inches="tight",
)

fig.savefig(
    "UltraPlotLogo.png",
    transparent=True,
    bbox_inches="tight",
)
fig.show()


# %%
import ultraplot as plt, numpy as np

from matplotlib.font_manager import FontProperties
from matplotlib import patheffects as pe
from matplotlib.patches import Rectangle
from scipy.ndimage import gaussian_filter

font = FontProperties(fname="./PermanentMarker-Regular.ttf")


fs = 38
left = 0.5
sw = 3
fig, ax = plt.subplots(figsize=(2, 2))
ax.text(
    left,
    0.52,
    "Ultra",
    fontsize=fs,
    fontproperties=font,
    va="bottom",
    ha="center",
    color="steelblue",
    path_effects=[
        pe.Stroke(linewidth=sw, foreground="white"),
        pe.Normal(),
    ],
    transform=ax.transAxes,
)
ax.text(
    left,
    0.48,
    "Plot",
    fontsize=fs,
    # fontproperties = font,
    va="top",
    ha="center",
    color="white",
    path_effects=[
        pe.Stroke(linewidth=sw, foreground="steelblue"),
        pe.Normal(),
    ],
    transform=ax.transAxes,
)

shift = 0.033
import colorengine as ce

colors = np.linspace(0, 1, 4, 0)
# colors = plt.colormaps.get_cmap("viko")(colors)
ax.axis(False)
ax.axis("square")
# fig.set_facecolor("lightgray")


# Create checkerboard pattern
n_squares_x, n_squares_y = 20, 8  # Adjust number of squares
square_size = 0.1  # Size of each square


fig_aspect = fig.get_figwidth() / fig.get_figheight()
square_size_y = 0.1  # Base square size in y direction
square_size_x = square_size_y / fig_aspect  # Adjust x size to maintain square shape

n_squares_x = (
    int(1.0 / square_size_x) + 1
)  # Calculate number of squares needed in x direction

# Create alpha mask with Gaussian fade
x = np.linspace(-2, 2, n_squares_x)
y = np.linspace(-2, 2, n_squares_y)
X, Y = np.meshgrid(x, y)
R = np.sqrt(X**2 + Y**2)
alpha = np.exp(-(R**2) / 0.75)  # Adjust the 1.0 to control fade rate
alpha = gaussian_filter(alpha, sigma=0.5)  # Adjust sigma for smoothness

# Create colormap gradient
cmap = plt.colormaps.get_cmap("viko")  # Choose your colormap

for i in range(n_squares_x):
    for j in range(n_squares_y):
        if (i + j) % 2 == 0:  # Checkerboard pattern
            color = cmap(i / n_squares_x)  # Color varies along x-axis
            rect = Rectangle(
                (i * square_size_x, j * square_size_y + 0.075),
                square_size_x,
                square_size_y,
                facecolor=color,
                alpha=alpha[j, i],
                transform=ax.transAxes,
            )
            ax.add_patch(rect)


fig.savefig(
    "UltraPlotLogoSquare.png",
    transparent=True,
    bbox_inches="tight",
)
fig.show()
