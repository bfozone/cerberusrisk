import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

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
        return html.Div("Portfolio not found")

    portfolio_id = int(portfolio_id)
    portfolio = get_portfolio(portfolio_id)

    if not portfolio:
        return html.Div("Portfolio not found")

    value_data = get_portfolio_value(portfolio_id)
    risk = get_portfolio_risk(portfolio_id)
    contributions = get_risk_contributions(portfolio_id)
    correlation = get_correlation(portfolio_id)

    # Positions table
    positions = value_data["positions"] if value_data else portfolio["positions"]
    headers = ["Ticker", "Name", "Weight", "Price", "Change"]
    rows = []
    row_classes = []

    for pos in positions:
        price = pos.get("price", "—")
        change = pos.get("change_pct")
        change_class = ""
        change_str = "—"
        if change is not None:
            change_class = "text-success" if change >= 0 else "text-danger"
            change_str = f"{change:+.2f}%"

        rows.append([
            pos["ticker"],
            pos["name"],
            f"{pos['weight']*100:.1f}%",
            f"${price}" if isinstance(price, (int, float)) else price,
            change_str,
        ])
        row_classes.append(["", "", "", "", change_class])

    positions_table = data_table(headers, rows, row_classes)

    # Allocation pie chart
    labels = [p["ticker"] for p in portfolio["positions"]]
    values = [p["weight"] for p in portfolio["positions"]]
    pie_fig = pie_chart(labels, values)

    # Risk metrics cards
    risk_cards = []
    if risk:
        metrics = [
            ("VaR 95%", f"{risk['var_95']}%", "warning"),
            ("VaR 99%", f"{risk['var_99']}%", "danger"),
            ("CVaR 95%", f"{risk['cvar_95']}%", "warning"),
            ("Volatility", f"{risk['volatility']}%", "info"),
            ("Sharpe", f"{risk['sharpe']}", "success" if risk["sharpe"] > 0.5 else "secondary"),
            ("Max DD", f"{risk['max_drawdown']}%", "danger"),
        ]
        for name, value, color in metrics:
            risk_cards.append(metric_card(name, value, color))

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

    return html.Div(
        [
            html.H2(portfolio["name"], className="mb-2"),
            html.P(portfolio["description"], className="text-muted mb-4"),
            # Risk metrics
            html.H5("Risk Metrics", className="mb-3"),
            dbc.Row(risk_cards, className="mb-4") if risk_cards else html.P("Loading..."),
            html.Hr(),
            # Two columns: positions table and pie chart
            dbc.Row(
                [
                    dbc.Col([html.H5("Holdings", className="mb-3"), positions_table], md=7),
                    dbc.Col(
                        [
                            html.H5("Allocation", className="mb-3"),
                            dcc.Graph(
                                figure=pie_fig,
                                config={"displayModeBar": False},
                                style={"height": "350px"},
                            ),
                        ],
                        md=5,
                    ),
                ],
                className="mb-4",
            ),
            html.Hr(),
            # Risk analysis
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Risk Contribution", className="mb-3"),
                            dcc.Graph(
                                figure=contrib_fig,
                                config={"displayModeBar": False},
                                style={"height": "350px"},
                            ) if contrib_fig else html.P("Loading..."),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.H5("Correlation Matrix", className="mb-3"),
                            dcc.Graph(
                                figure=corr_fig,
                                config={"displayModeBar": False},
                                style={"height": "350px"},
                            ) if corr_fig else html.P("Loading..."),
                        ],
                        md=6,
                    ),
                ]
            ),
        ]
    )
