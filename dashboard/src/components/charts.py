import plotly.graph_objects as go
from src.theme import CATEGORICAL, SEQUENTIAL, DIVERGING


def _hex_to_luminance(hex_color: str) -> float:
    """Calculate relative luminance of a hex color."""
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    # sRGB to linear
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _get_text_colors(z: list, zmin: float, zmax: float, colorscale: list) -> list:
    """Generate contrasting text colors for each cell based on background luminance."""
    text_colors = []
    for row in z:
        row_colors = []
        for val in row:
            # Normalize value to 0-1 range
            if zmax == zmin:
                norm = 0.5
            else:
                norm = max(0, min(1, (val - zmin) / (zmax - zmin)))

            # Find the color at this position in the colorscale
            bg_color = colorscale[-1][1]  # default to last color
            for i in range(len(colorscale) - 1):
                if colorscale[i][0] <= norm <= colorscale[i + 1][0]:
                    bg_color = colorscale[i][1]  # use lower bound color
                    break

            # Choose white or dark text based on luminance
            luminance = _hex_to_luminance(bg_color)
            row_colors.append("#ffffff" if luminance < 0.4 else "#1e1b2e")
        text_colors.append(row_colors)
    return text_colors

# Chart colors (categorical)
CHART_COLORS = {
    "primary": "#a78bfa",
    "secondary": "#22d3ee",
    "positive": "#4ade80",
    "negative": "#fb7185",
    "warning": "#fbbf24",
    "info": "#60a5fa",
    "series": CATEGORICAL["primary"],
    "assetClasses": CATEGORICAL["assetClasses"],
}

# Sequential colorscales for Plotly
COLORSCALES = {
    "purpleIntensity": [[i / (len(SEQUENTIAL["purpleIntensity"]) - 1), c] for i, c in enumerate(SEQUENTIAL["purpleIntensity"])],
    "cyanIntensity": [[i / (len(SEQUENTIAL["cyanIntensity"]) - 1), c] for i, c in enumerate(SEQUENTIAL["cyanIntensity"])],
    "heat": [[i / (len(SEQUENTIAL["heat"]) - 1), c] for i, c in enumerate(SEQUENTIAL["heat"])],
    "cool": [[i / (len(SEQUENTIAL["cool"]) - 1), c] for i, c in enumerate(SEQUENTIAL["cool"])],
    "lossGain": [[i / (len(DIVERGING["lossGain"]) - 1), c] for i, c in enumerate(DIVERGING["lossGain"])],
    "performance": [[i / (len(DIVERGING["performance"]) - 1), c] for i, c in enumerate(DIVERGING["performance"])],
}

# Theme-specific settings
THEME_SETTINGS = {
    "dark": {
        "template": "plotly_dark",
        "font_color": "#ffffff",
        "font_secondary": "#c8c8d8",
        "grid_color": "rgba(45, 45, 58, 0.6)",
        "axis_color": "#6b6b78",
        "heatmap_mid": "#1a1a24",
        "tooltip_bg": "#1a1a24",
        "tooltip_border": "#3d3d4a",
        "benchmark": "#6b6b78",
    },
    "light": {
        "template": "plotly_white",
        "font_color": "#1e1b2e",
        "font_secondary": "#4a4760",
        "grid_color": "rgba(233, 229, 240, 0.8)",
        "axis_color": "#9898a8",
        "heatmap_mid": "#faf9fb",
        "tooltip_bg": "#ffffff",
        "tooltip_border": "#e9e5f0",
        "benchmark": "#9898a8",
    },
}


def empty_figure(height: int = 350, scheme: str = "dark") -> go.Figure:
    """Return an empty figure with no visible axes - use as placeholder."""
    settings = THEME_SETTINGS.get(scheme, THEME_SETTINGS["dark"])
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def chart_layout(height: int = 350, scheme: str = "dark", **kwargs) -> dict:
    """Common layout for charts with theme support."""
    settings = THEME_SETTINGS.get(scheme, THEME_SETTINGS["dark"])
    layout = {
        "template": settings["template"],
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": dict(l=40, r=40, t=20, b=40),
        "height": height,
        "font": {
            "family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            "color": settings["font_color"],
            "size": 12,
        },
        "xaxis": {
            "gridcolor": settings["grid_color"],
            "linecolor": settings["grid_color"],
            "tickfont": {"color": settings["font_secondary"], "size": 11},
            "title_font": {"color": settings["font_color"], "size": 12},
        },
        "yaxis": {
            "gridcolor": settings["grid_color"],
            "linecolor": settings["grid_color"],
            "tickfont": {"color": settings["font_secondary"], "size": 11},
            "title_font": {"color": settings["font_color"], "size": 12},
        },
        "legend": {
            "font": {"color": settings["font_secondary"], "size": 11},
            "bgcolor": "rgba(0,0,0,0)",
        },
        "hoverlabel": {
            "bgcolor": settings["tooltip_bg"],
            "bordercolor": settings["tooltip_border"],
            "font": {
                "family": "Inter, -apple-system, sans-serif",
                "color": settings["font_color"],
                "size": 12,
            },
        },
    }
    layout.update(kwargs)
    return layout


# Keep backward compatibility
def dark_layout(height: int = 350, **kwargs) -> dict:
    """Deprecated: use chart_layout(scheme='dark') instead."""
    return chart_layout(height=height, scheme="dark", **kwargs)


def bar_chart(
    x: list,
    y: list,
    color: str | list | None = None,
    text: list | None = None,
    height: int = 350,
    scheme: str = "dark",
    **layout_kwargs,
) -> go.Figure:
    """Create a styled bar chart."""
    settings = THEME_SETTINGS.get(scheme, THEME_SETTINGS["dark"])
    fig = go.Figure(
        data=[
            go.Bar(
                x=x,
                y=y,
                marker_color=color or CHART_COLORS["primary"],
                marker_line_width=0,
                marker_cornerradius=6,
                text=text,
                textposition="outside" if text else None,
                textfont={"color": settings["font_color"], "size": 11},
            )
        ]
    )
    fig.update_layout(**chart_layout(height=height, scheme=scheme, **layout_kwargs))
    return fig


def pie_chart(labels: list, values: list, height: int = 350, scheme: str = "dark") -> go.Figure:
    """Create a styled donut chart."""
    settings = THEME_SETTINGS.get(scheme, THEME_SETTINGS["dark"])
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                textinfo="label+percent",
                textposition="outside",
                marker={
                    "colors": CHART_COLORS["series"],
                    "line": {"width": 0},
                },
                textfont={"color": settings["font_color"], "size": 11},
                pull=[0.02] * len(labels),  # Slight separation
            )
        ]
    )
    fig.update_layout(
        **chart_layout(
            height=height,
            scheme=scheme,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
    )
    return fig


def heatmap_chart(
    z: list,
    x: list,
    y: list,
    colorscale: str | list | None = None,
    height: int = 350,
    scheme: str = "dark",
    zmin: float | None = None,
    zmax: float | None = None,
    show_text: bool = True,
) -> go.Figure:
    """Create a styled heatmap with auto-contrasting text and cell gaps.

    colorscale options: 'purpleIntensity', 'cyanIntensity', 'heat', 'cool', 'lossGain', 'performance'
    """
    # Resolve colorscale name to actual scale
    if isinstance(colorscale, str) and colorscale in COLORSCALES:
        resolved_scale = COLORSCALES[colorscale]
    elif colorscale is None:
        resolved_scale = COLORSCALES["purpleIntensity"]
    else:
        resolved_scale = colorscale

    # Calculate z range for text color computation
    flat_z = [v for row in z for v in row]
    z_min = zmin if zmin is not None else min(flat_z)
    z_max = zmax if zmax is not None else max(flat_z)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x,
            y=y,
            colorscale=resolved_scale,
            zmin=zmin,
            zmax=zmax,
            xgap=3,
            ygap=3,
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Value: %{z:.2f}<extra></extra>",
            showscale=False,
        )
    )

    # Add text annotations with per-cell contrasting colors
    if show_text:
        text_colors = _get_text_colors(z, z_min, z_max, resolved_scale)
        annotations = []
        for i, row in enumerate(z):
            for j, val in enumerate(row):
                annotations.append(
                    dict(
                        x=x[j],
                        y=y[i],
                        text=f"{val:.2f}",
                        showarrow=False,
                        font=dict(size=10, color=text_colors[i][j]),
                    )
                )
        fig.update_layout(annotations=annotations)

    fig.update_layout(
        **chart_layout(height=height, scheme=scheme, margin=dict(l=60, r=40, t=20, b=60))
    )
    return fig


def correlation_heatmap(
    z: list,
    x: list,
    y: list,
    height: int = 350,
    scheme: str = "dark",
    show_text: bool = True,
) -> go.Figure:
    """Create a correlation matrix heatmap with diverging colors and cell gaps."""
    settings = THEME_SETTINGS.get(scheme, THEME_SETTINGS["dark"])

    # Diverging scale centered on 0
    diverging_scale = [
        [0.0, "#fb7185"],    # Negative correlation
        [0.5, settings["heatmap_mid"]],  # Zero correlation
        [1.0, "#22d3ee"],    # Positive correlation
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x,
            y=y,
            colorscale=diverging_scale,
            zmid=0,
            zmin=-1,
            zmax=1,
            xgap=3,
            ygap=3,
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>",
            showscale=False,
        )
    )

    # Add text annotations with per-cell contrasting colors
    if show_text:
        text_colors = _get_text_colors(z, -1, 1, diverging_scale)
        annotations = []
        for i, row_data in enumerate(z):
            for j, val in enumerate(row_data):
                annotations.append(
                    dict(
                        x=x[j],
                        y=y[i],
                        text=f"{val:.2f}",
                        showarrow=False,
                        font=dict(size=10, color=text_colors[i][j]),
                    )
                )
        fig.update_layout(annotations=annotations)

    fig.update_layout(
        **chart_layout(height=height, scheme=scheme, margin=dict(l=60, r=40, t=20, b=60))
    )
    return fig


def line_chart(
    x: list,
    y_series: dict,  # {"Series Name": [values], ...}
    height: int = 350,
    scheme: str = "dark",
    **layout_kwargs,
) -> go.Figure:
    """Create a multi-series line chart."""
    settings = THEME_SETTINGS.get(scheme, THEME_SETTINGS["dark"])
    colors = CHART_COLORS["series"]

    fig = go.Figure()

    for i, (name, y) in enumerate(y_series.items()):
        color = colors[i % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                name=name,
                mode="lines",
                line={"color": color, "width": 2},
                hovertemplate=f"<b>{name}</b><br>%{{x}}<br>Value: %{{y:.2f}}<extra></extra>",
            )
        )

    fig.update_layout(**chart_layout(height=height, scheme=scheme, **layout_kwargs))
    return fig


def area_chart(
    x: list,
    y: list,
    color: str | None = None,
    height: int = 350,
    scheme: str = "dark",
    **layout_kwargs,
) -> go.Figure:
    """Create a filled area chart."""
    settings = THEME_SETTINGS.get(scheme, THEME_SETTINGS["dark"])
    fill_color = color or CHART_COLORS["primary"]

    # Create gradient fill
    fill_rgba = fill_color.lstrip('#')
    r, g, b = tuple(int(fill_rgba[i:i+2], 16) for i in (0, 2, 4))

    fig = go.Figure(
        data=go.Scatter(
            x=x,
            y=y,
            fill="tozeroy",
            fillcolor=f"rgba({r},{g},{b},0.2)",
            line={"color": fill_color, "width": 2},
            hovertemplate="%{x}<br>Value: %{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(**chart_layout(height=height, scheme=scheme, **layout_kwargs))
    return fig


def histogram_chart(
    values: list,
    bins: int = 50,
    var_line: float | None = None,
    color: str | None = None,
    height: int = 350,
    scheme: str = "dark",
    **layout_kwargs,
) -> go.Figure:
    """Create a histogram with optional VaR vertical line."""
    fill_color = color or CHART_COLORS["primary"]

    fig = go.Figure(
        data=go.Histogram(
            x=values,
            nbinsx=bins,
            marker_color=fill_color,
            marker_line_width=0,
            opacity=0.8,
            hovertemplate="Return: %{x:.2f}%<br>Count: %{y}<extra></extra>",
        )
    )

    # Add VaR line if specified
    if var_line is not None:
        fig.add_vline(
            x=-var_line,
            line_dash="dash",
            line_color=CHART_COLORS["negative"],
            line_width=2,
            annotation_text=f"VaR: {var_line:.1f}%",
            annotation_position="top",
            annotation_font_color=CHART_COLORS["negative"],
        )

    fig.update_layout(**chart_layout(height=height, scheme=scheme, **layout_kwargs))
    return fig


def scatter_chart(
    x: list,
    y: list,
    trendline: bool = False,
    x_label: str = "X",
    y_label: str = "Y",
    height: int = 350,
    scheme: str = "dark",
    **layout_kwargs,
) -> go.Figure:
    """Create a scatter plot with optional regression trendline."""
    import numpy as np

    fig = go.Figure(
        data=go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(
                color=CHART_COLORS["primary"],
                size=6,
                opacity=0.6,
            ),
            hovertemplate=f"<b>{x_label}</b>: %{{x:.2f}}%<br><b>{y_label}</b>: %{{y:.2f}}%<extra></extra>",
        )
    )

    # Add trendline
    if trendline and len(x) > 1:
        x_arr = np.array(x)
        y_arr = np.array(y)
        z = np.polyfit(x_arr, y_arr, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(x_arr), max(x_arr), 100)

        fig.add_trace(
            go.Scatter(
                x=x_line.tolist(),
                y=p(x_line).tolist(),
                mode="lines",
                line=dict(color=CHART_COLORS["secondary"], width=2, dash="dash"),
                name="Trendline",
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        xaxis_title=x_label,
        yaxis_title=y_label,
        **chart_layout(height=height, scheme=scheme, **layout_kwargs),
    )
    return fig


def grouped_bar_chart(
    categories: list,
    groups: dict,  # {"Group Name": [values], ...}
    height: int = 350,
    scheme: str = "dark",
    **layout_kwargs,
) -> go.Figure:
    """Create a grouped bar chart for comparison."""
    colors = CHART_COLORS["series"]

    fig = go.Figure()

    for i, (name, values) in enumerate(groups.items()):
        color = colors[i % len(colors)]
        fig.add_trace(
            go.Bar(
                x=categories,
                y=values,
                name=name,
                marker_color=color,
                marker_line_width=0,
                marker_cornerradius=4,
            )
        )

    fig.update_layout(
        barmode="group",
        **chart_layout(height=height, scheme=scheme, **layout_kwargs),
    )
    return fig
