"""For making quick plots for exploratory analysis."""

MIN_ASPECT_RATIO = 1 / 15
MAX_ASPECT_RATIO = 1 / 3
MAX_ASPECT_POINTS = 10

INTERPOLATE_DRAWSTYLE = {
    "previous": "steps-post",
    "linear": None,
}

FONTS = [
    ".SF Compact Rounded",
    "Helvetica Neue",
    "Segoe UI",
    "Helvetica",
    "Arial",
    None,
]

PLOT_STYLE = {
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#FFFFFF",
    "axes.linewidth": 1,
    "axes.grid": True,
    "axes.axisbelow": True,
    "axes.labelcolor": "#222222",
    "xtick.labelsize": 13,
    "xtick.color": "#666666",
    "xtick.direction": "out",
    "xtick.major.size": 6,
    "xtick.minor.size": 4,
    "xtick.major.pad": 4,
    "ytick.labelsize": 13,
    "ytick.color": "#666666",
    "ytick.direction": "out",
    "ytick.major.size": 6,
    "ytick.minor.size": 4,
    "ytick.major.pad": 4,
    "grid.color": "#DDDDDD",
    "grid.linestyle": ":",
    "grid.linewidth": 1,
    "figure.subplot.left": 0.05,
    "figure.subplot.right": 0.95,
    "figure.subplot.bottom": 0.2,
    "figure.subplot.top": 0.95,
}


def plot(
    ts,
    interpolate="previous",
    figure_width=12,
    linewidth=1,
    marker="o",
    markersize=3,
    color="#222222",
    aspect_ratio=None,
    font=None,
):
    try:
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except ImportError as error:
        msg = "need to install matplotlib for `plot` function"
        raise ImportError(msg) from error

    if font is None:
        available_fonts = {f.name for f in font_manager.fontManager.ttflist}
        for font in FONTS:
            if font in available_fonts:
                break

    if aspect_ratio is None:
        try:
            n_unique_values = len(ts.distribution())
        except KeyError:
            n_unique_values = 0
        scaled = min(MAX_ASPECT_POINTS, max(2, n_unique_values) - 2)
        aspect_ratio = MIN_ASPECT_RATIO + (
            MAX_ASPECT_RATIO - MIN_ASPECT_RATIO
        ) * (scaled / MAX_ASPECT_POINTS)

    try:
        drawstyle = INTERPOLATE_DRAWSTYLE[interpolate]
    except KeyError as error:
        msg = (
            f"invalid value for interpolate='{interpolate}', "
            f"must be in {set(INTERPOLATE_DRAWSTYLE.keys())}"
        )
        raise ValueError(msg) from error

    with plt.style.context(PLOT_STYLE):
        figure, axes = plt.subplots(
            figsize=(figure_width, aspect_ratio * figure_width),
        )

        items = ts.items()
        if items:
            x, y = zip(*items)
        else:
            x, y = [], []

        axes.plot(
            x,
            y,
            linewidth=linewidth,
            drawstyle=drawstyle,
            marker=marker,
            markersize=markersize,
            color=color,
        )
        axes.set_aspect(aspect_ratio / axes.get_data_ratio())
        axes.xaxis.set_major_locator(plt.MaxNLocator(int(figure_width / 2)))
        if font:
            plt.xticks(fontname=font)
            plt.yticks(fontname=font)

    return figure, axes
