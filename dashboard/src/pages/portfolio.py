import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

from src.api import (
    get_portfolio,
    get_portfolio_value,
    get_portfolio_risk,
    get_risk_contributions,
    get_correlation,
)

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
    table_rows = []
    for pos in positions:
        price = pos.get("price", "—")
        change = pos.get("change_pct")
        change_class = ""
        change_str = "—"
        if change is not None:
            change_class = "text-success" if change >= 0 else "text-danger"
            change_str = f"{change:+.2f}%"

        table_rows.append(
            html.Tr(
                [
                    html.Td(pos["ticker"]),
                    html.Td(pos["name"]),
                    html.Td(f"{pos['weight']*100:.1f}%"),
                    html.Td(f"${price}" if isinstance(price, (int, float)) else price),
                    html.Td(change_str, className=change_class),
                ]
            )
        )

    positions_table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Ticker"),
                        html.Th("Name"),
                        html.Th("Weight"),
                        html.Th("Price"),
                        html.Th("Change"),
                    ]
                )
            ),
            html.Tbody(table_rows),
        ],
        bordered=True,
        hover=True,
        responsive=True,
        className="table-dark",
    )

    # Allocation pie chart
    labels = [p["ticker"] for p in portfolio["positions"]]
    values = [p["weight"] for p in portfolio["positions"]]

    pie_fig = go.Figure(
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
    pie_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        height=350,
    )

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
            risk_cards.append(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.P(name, className="text-muted mb-1 small"),
                                html.H4(value, className=f"text-{color} mb-0"),
                            ]
                        ),
                        className="text-center",
                    ),
                    md=2,
                )
            )

    # Risk contributions chart
    contrib_fig = go.Figure()
    if contributions:
        tickers = [c["ticker"] for c in contributions]
        pct_contrib = [c["pct_contribution"] for c in contributions]

        contrib_fig.add_trace(
            go.Bar(
                x=tickers,
                y=pct_contrib,
                marker_color="#e74c3c",
                text=[f"{v:.1f}%" for v in pct_contrib],
                textposition="outside",
            )
        )
        contrib_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=40, t=20, b=40),
            yaxis_title="% Contribution to VaR",
            showlegend=False,
            height=350,
        )

    # Correlation heatmap
    corr_fig = go.Figure()
    if correlation and correlation["matrix"]:
        corr_fig = go.Figure(
            data=go.Heatmap(
                z=correlation["matrix"],
                x=correlation["tickers"],
                y=correlation["tickers"],
                colorscale="RdBu",
                zmid=0,
                text=correlation["matrix"],
                texttemplate="%{text:.2f}",
                textfont={"size": 10},
            )
        )
        corr_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=60, r=40, t=20, b=60),
            height=350,
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
                    dbc.Col(
                        [
                            html.H5("Holdings", className="mb-3"),
                            positions_table,
                        ],
                        md=7,
                    ),
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
                            ),
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
                            ),
                        ],
                        md=6,
                    ),
                ]
            ),
        ]
    )
