import dash_mantine_components as dmc
from dash import html


def metric_card(label: str, value: str, color: str = "blue") -> dmc.Card:
    """Create a single metric card."""
    return dmc.Card(
        children=[
            dmc.Text(label, size="sm", c="dimmed"),
            dmc.Title(value, order=4, c=color),
        ],
        withBorder=True,
        padding="md",
        radius="sm",
        style={"textAlign": "center"},
    )


def portfolio_card(portfolio: dict, risk: dict | None) -> dmc.Card:
    """Create a portfolio summary card with risk metrics."""
    risk_color = "green" if risk and risk.get("var_95", 0) < 15 else "yellow"

    metrics = []
    if risk:
        metrics = [
            ("VaR 95%", f"{risk['var_95']}%", risk_color),
            ("Volatility", f"{risk['volatility']}%", "blue"),
            ("Sharpe", f"{risk['sharpe']}", "blue"),
            ("Max DD", f"{risk['max_drawdown']}%", "red"),
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
                        dmc.Button("View Details", size="xs", variant="light"),
                        href=f"/portfolio/{portfolio['id']}",
                    ),
                ],
                gap="sm",
                mt="sm",
            ),
        ],
        withBorder=True,
        padding="md",
        radius="sm",
        h="100%",
    )
