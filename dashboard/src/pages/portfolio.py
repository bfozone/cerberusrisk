import dash
from dash import html, dcc
import dash_mantine_components as dmc

from src.api import (
    get_portfolio,
    get_portfolio_value,
    get_portfolio_risk,
    get_risk_contributions,
    get_correlation,
)
from src.components import metric_card, data_table, bar_chart, pie_chart, heatmap_chart

dash.register_page(__name__, path_template="/portfolio/<portfolio_id>", name="Portfolio")


def layout(portfolio_id=None):
    if not portfolio_id:
        return dmc.Text("Portfolio not found")

    portfolio_id = int(portfolio_id)
    portfolio = get_portfolio(portfolio_id)

    if not portfolio:
        return dmc.Text("Portfolio not found")

    value_data = get_portfolio_value(portfolio_id)
    risk = get_portfolio_risk(portfolio_id)
    contributions = get_risk_contributions(portfolio_id)
    correlation = get_correlation(portfolio_id)

    # Positions table
    positions = value_data["positions"] if value_data else portfolio["positions"]
    headers = ["Ticker", "Name", "Weight", "Price", "Change"]
    rows = []
    row_colors = []

    for pos in positions:
        price = pos.get("price", "—")
        change = pos.get("change_pct")
        change_color = None
        change_str = "—"
        if change is not None:
            change_color = "green" if change >= 0 else "red"
            change_str = f"{change:+.2f}%"

        rows.append([
            pos["ticker"],
            pos["name"],
            f"{pos['weight']*100:.1f}%",
            f"${price}" if isinstance(price, (int, float)) else price,
            change_str,
        ])
        row_colors.append([None, None, None, None, change_color])

    positions_table = data_table(headers, rows, row_colors)

    # Allocation pie chart
    labels = [p["ticker"] for p in portfolio["positions"]]
    values = [p["weight"] for p in portfolio["positions"]]
    pie_fig = pie_chart(labels, values)

    # Risk metrics cards
    risk_cards = []
    if risk:
        metrics = [
            ("VaR 95%", f"{risk['var_95']}%", "yellow"),
            ("VaR 99%", f"{risk['var_99']}%", "red"),
            ("CVaR 95%", f"{risk['cvar_95']}%", "yellow"),
            ("Volatility", f"{risk['volatility']}%", "blue"),
            ("Sharpe", f"{risk['sharpe']}", "green" if risk["sharpe"] > 0.5 else "gray"),
            ("Max DD", f"{risk['max_drawdown']}%", "red"),
        ]
        for name, value, color in metrics:
            risk_cards.append(dmc.GridCol(metric_card(name, value, color), span={"base": 4, "sm": 2}))

    # Risk contributions chart
    contrib_fig = None
    if contributions:
        tickers = [c["ticker"] for c in contributions]
        pct_contrib = [c["pct_contribution"] for c in contributions]
        contrib_fig = bar_chart(
            tickers,
            pct_contrib,
            color="#e74c3c",
            text=[f"{v:.1f}%" for v in pct_contrib],
            yaxis_title="% Contribution to VaR",
            showlegend=False,
        )

    # Correlation heatmap
    corr_fig = None
    if correlation and correlation["matrix"]:
        corr_fig = heatmap_chart(
            correlation["matrix"],
            correlation["tickers"],
            correlation["tickers"],
        )

    return dmc.Stack(
        [
            dmc.Title(portfolio["name"], order=2),
            dmc.Text(portfolio["description"], c="dimmed"),

            # Risk metrics
            dmc.Title("Risk Metrics", order=5, mt="md"),
            dmc.Grid(risk_cards, gutter="xs") if risk_cards else dmc.Text("Loading..."),

            dmc.Divider(my="md"),

            # Holdings and allocation
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Stack([dmc.Title("Holdings", order=5), positions_table], gap="sm"),
                        span={"base": 12, "md": 7},
                    ),
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Title("Allocation", order=5),
                            dcc.Graph(figure=pie_fig, config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 5},
                    ),
                ],
                gutter="md",
            ),

            dmc.Divider(my="md"),

            # Risk analysis
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Title("Risk Contribution", order=5),
                            dcc.Graph(figure=contrib_fig, config={"displayModeBar": False})
                            if contrib_fig else dmc.Text("Loading..."),
                        ], gap="sm"),
                        span={"base": 12, "md": 6},
                    ),
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Title("Correlation Matrix", order=5),
                            dcc.Graph(figure=corr_fig, config={"displayModeBar": False})
                            if corr_fig else dmc.Text("Loading..."),
                        ], gap="sm"),
                        span={"base": 12, "md": 6},
                    ),
                ],
                gutter="md",
            ),
        ],
        gap="sm",
    )
