import dash_mantine_components as dmc

# Risk indicator colors
COLORS = {
    "positive": "green",
    "negative": "red",
    "warning": "yellow",
    "info": "blue",
    "muted": "dimmed",
}

# Mantine theme configuration
theme = dmc.DEFAULT_THEME.copy()
theme.update({
    "primaryColor": "blue",
    "fontFamily": "'Inter', sans-serif",
    "defaultRadius": "sm",
})


def get_color(value: float, threshold: float = 0) -> str:
    """Return color based on value (positive=green, negative=red)."""
    return COLORS["positive"] if value >= threshold else COLORS["negative"]
