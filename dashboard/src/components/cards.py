import dash_mantine_components as dmc
from dash import dcc

from src.components.charts import sparkline_chart, CHART_COLORS


def metric_card(label: str, value: str, color: str | None = None) -> dmc.Card:
    """Create a single metric card."""
    return dmc.Card(
        children=[
            dmc.Text(label, size="sm", c="dimmed"),
            dmc.Title(value, order=4, c=color or "blue"),
        ],
        withBorder=True,
        padding="md",
        style={"textAlign": "center"},
    )


def portfolio_card(portfolio: dict, risk: dict | None) -> dmc.Card:
    """Create a portfolio summary card with risk metrics."""
    # Handle new ComparativeRiskMetrics format: {"portfolio": {...}, "benchmark": {...}, "delta": {...}}
    port_risk = risk.get("portfolio") if risk else None
    var_value = port_risk.get("var_95", 0) if port_risk else 0
    risk_color = "green" if var_value < 15 else "orange"

    metrics = []
    if port_risk:
        metrics = [
            ("VaR 95%", f"{port_risk['var_95']}%", risk_color),
            ("Volatility", f"{port_risk['volatility']}%", "blue"),
            ("Sharpe", f"{port_risk['sharpe']}", "blue"),
            ("Max DD", f"{port_risk['max_drawdown']}%", "red"),
        ]

    metric_items = [
        dmc.GridCol(
            [
                dmc.Text(label, size="xs", c="dimmed"),
                dmc.Text(value, size="lg", fw=600, c=color),
            ],
            span=6,
        )
        for label, value, color in metrics
    ] if metrics else [dmc.Text("Loading...", c="dimmed")]

    return dmc.Card(
        children=[
            dmc.CardSection(
                dmc.Title(portfolio["name"], order=5, p="sm"),
                withBorder=True,
            ),
            dmc.Stack(
                [
                    dmc.Text(portfolio["description"], size="sm", c="dimmed"),
                    dmc.Divider(),
                    dmc.Grid(metric_items, gutter="xs"),
                    dmc.Divider(),
                    dmc.Anchor(
                        dmc.Button("View Analytics", size="xs", variant="light"),
                        href="/analytics",
                    ),
                ],
                gap="sm",
                mt="sm",
            ),
        ],
        withBorder=True,
        padding="md",
        h="100%",
    )


def portfolio_card_enhanced(
    portfolio: dict,
    risk: dict | None,
    performance: dict | None,
    drawdown_series: list | None,
    scheme: str = "dark",
) -> dmc.Card:
    """Create an enhanced portfolio card with sparkline and clickable analytics link.

    Args:
        portfolio: Portfolio dict with id, name, description
        risk: Risk metrics dict with nested "portfolio" key
        performance: Performance dict with period_returns
        drawdown_series: List of drawdown values for sparkline (0 = peak, negative = below)
        scheme: Color scheme ("dark" or "light")
    """
    port_risk = risk.get("portfolio") if risk else None
    var_value = port_risk.get("var_95", 0) if port_risk else 0
    risk_color = "green" if var_value < 15 else "orange" if var_value < 25 else "red"

    # Get YTD return if available
    ytd_return = None
    if performance and performance.get("period_returns"):
        ytd_return = performance["period_returns"].get("ytd")

    # Build sparkline
    sparkline = None
    if drawdown_series and len(drawdown_series) > 5:
        sparkline = dcc.Graph(
            figure=sparkline_chart(drawdown_series, height=60, scheme=scheme),
            config={"displayModeBar": False, "staticPlot": True},
            style={"height": "60px"},
        )

    # Build metric items (2x2 grid)
    metrics = []
    if port_risk:
        metrics = [
            ("VaR 95%", f"{port_risk['var_95']:.1f}%", risk_color),
            ("Volatility", f"{port_risk['volatility']:.1f}%", "blue"),
            ("Sharpe", f"{port_risk['sharpe']:.2f}", "violet"),
            ("Max DD", f"{port_risk['max_drawdown']:.1f}%", "red"),
        ]

    metric_items = [
        dmc.GridCol(
            [
                dmc.Text(label, size="xs", c="dimmed"),
                dmc.Text(value, size="sm", fw=600, c=color),
            ],
            span=6,
        )
        for label, value, color in metrics
    ] if metrics else []

    # YTD badge color
    ytd_color = "green" if ytd_return and ytd_return > 0 else "red" if ytd_return else "gray"
    ytd_text = f"{ytd_return:+.1f}% YTD" if ytd_return is not None else "N/A"

    return dmc.Card(
        children=[
            dmc.CardSection(
                dmc.Group(
                    [
                        dmc.Text(portfolio["name"], fw=600, size="sm"),
                        dmc.Badge(ytd_text, color=ytd_color, size="sm", variant="light"),
                    ],
                    justify="space-between",
                    p="sm",
                ),
                withBorder=True,
            ),
            dmc.Stack(
                [
                    # Sparkline section
                    sparkline if sparkline else dmc.Text("No data", size="xs", c="dimmed", ta="center"),
                    # Metrics grid
                    dmc.Grid(metric_items, gutter="xs") if metric_items else None,
                    # Link to analytics
                    dmc.Anchor(
                        dmc.Button(
                            "View Details",
                            size="xs",
                            variant="light",
                            fullWidth=True,
                        ),
                        href=f"/analytics?portfolio={portfolio['id']}",
                        style={"textDecoration": "none"},
                    ),
                ],
                gap="xs",
                mt="sm",
            ),
        ],
        withBorder=True,
        padding="sm",
        h="100%",
    )
