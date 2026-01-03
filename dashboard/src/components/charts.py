import plotly.graph_objects as go


def dark_layout(height: int = 350, **kwargs) -> dict:
    """Common dark theme layout for charts."""
    layout = {
        "template": "plotly_dark",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": dict(l=40, r=40, t=20, b=40),
        "height": height,
    }
    layout.update(kwargs)
    return layout


def bar_chart(
    x: list,
    y: list,
    color: str = "#3498db",
    text: list | None = None,
    height: int = 350,
    **layout_kwargs,
) -> go.Figure:
    """Create a styled bar chart."""
    fig = go.Figure(
        data=[
            go.Bar(
                x=x,
                y=y,
                marker_color=color,
                text=text,
                textposition="outside" if text else None,
            )
        ]
    )
    fig.update_layout(**dark_layout(height=height, **layout_kwargs))
    return fig


def pie_chart(labels: list, values: list, height: int = 350) -> go.Figure:
    """Create a styled donut chart."""
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                textinfo="label+percent",
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        **dark_layout(
            height=height,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
    )
    return fig


def heatmap_chart(
    z: list,
    x: list,
    y: list,
    colorscale: str = "RdBu",
    height: int = 350,
) -> go.Figure:
    """Create a styled heatmap."""
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x,
            y=y,
            colorscale=colorscale,
            zmid=0,
            text=z,
            texttemplate="%{text:.2f}",
            textfont={"size": 10},
        )
    )
    fig.update_layout(
        **dark_layout(height=height, margin=dict(l=60, r=40, t=20, b=60))
    )
    return fig
