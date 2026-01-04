import dash
from dash import dcc, callback, Output, Input, no_update
import dash_mantine_components as dmc

from src.api import (
    get_portfolio,
    get_portfolio_value,
    get_portfolio_risk,
    get_risk_contributions,
    get_correlation,
)
from src.components import metric_card, data_table, bar_chart, pie_chart, heatmap_chart, empty_figure
from src.components.charts import CHART_COLORS

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

    # Risk metrics cards
    risk_cards = []
    if risk:
        metrics = [
            ("VaR 95%", f"{risk['var_95']}%", "orange"),
            ("VaR 99%", f"{risk['var_99']}%", "red"),
            ("CVaR 95%", f"{risk['cvar_95']}%", "orange"),
            ("Volatility", f"{risk['volatility']}%", "blue"),
            ("Sharpe", f"{risk['sharpe']}", "green" if risk["sharpe"] > 0.5 else "gray"),
            ("Max DD", f"{risk['max_drawdown']}%", "red"),
        ]
        for name, value, color in metrics:
            risk_cards.append(dmc.GridCol(metric_card(name, value, color), span={"base": 4, "sm": 2}))

    # Store portfolio_id for callbacks
    return dmc.Stack(
        [
            dcc.Store(id="portfolio-id-store", data=portfolio_id),
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
                            dcc.Graph(id="portfolio-pie-chart", figure=empty_figure(), config={"displayModeBar": False}),
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
                            dcc.Graph(id="portfolio-contrib-chart", figure=empty_figure(), config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 6},
                    ),
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Title("Correlation Matrix", order=5),
                            dcc.Graph(id="portfolio-corr-chart", figure=empty_figure(), config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 6},
                    ),
                ],
                gutter="md",
            ),
        ],
        gap="sm",
    )


@callback(
    Output("portfolio-pie-chart", "figure"),
    Input("color-scheme-store", "data"),
    Input("portfolio-id-store", "data"),
)
def update_pie_chart(scheme, portfolio_id):
    scheme = scheme or "dark"
    if not portfolio_id:
        return no_update

    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        return no_update

    labels = [p["ticker"] for p in portfolio["positions"]]
    values = [p["weight"] for p in portfolio["positions"]]
    return pie_chart(labels, values, scheme=scheme)


@callback(
    Output("portfolio-contrib-chart", "figure"),
    Input("color-scheme-store", "data"),
    Input("portfolio-id-store", "data"),
)
def update_contrib_chart(scheme, portfolio_id):
    scheme = scheme or "dark"
    if not portfolio_id:
        return no_update

    contributions = get_risk_contributions(portfolio_id)
    if not contributions:
        return no_update

    tickers = [c["ticker"] for c in contributions]
    pct_contrib = [c["pct_contribution"] for c in contributions]
    return bar_chart(
        tickers,
        pct_contrib,
        color=CHART_COLORS["negative"],
        text=[f"{v:.1f}%" for v in pct_contrib],
        yaxis_title="% Contribution to VaR",
        showlegend=False,
        scheme=scheme,
    )


@callback(
    Output("portfolio-corr-chart", "figure"),
    Input("color-scheme-store", "data"),
    Input("portfolio-id-store", "data"),
)
def update_corr_chart(scheme, portfolio_id):
    scheme = scheme or "dark"
    if not portfolio_id:
        return no_update

    correlation = get_correlation(portfolio_id)
    if not correlation or not correlation["matrix"]:
        return no_update

    return heatmap_chart(
        correlation["matrix"],
        correlation["tickers"],
        correlation["tickers"],
        scheme=scheme,
    )
