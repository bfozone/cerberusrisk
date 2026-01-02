import dash
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from src.api import get_portfolios, get_portfolio_risk

dash.register_page(__name__, path="/", name="Home")


def create_portfolio_card(portfolio, risk):
    risk_color = "success" if risk and risk.get("var_95", 0) < 15 else "warning"

    return dbc.Card(
        [
            dbc.CardHeader(html.H5(portfolio["name"], className="mb-0")),
            dbc.CardBody(
                [
                    html.P(portfolio["description"], className="text-muted small"),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P("VaR 95%", className="text-muted mb-0 small"),
                                    html.H4(
                                        f"{risk['var_95']}%" if risk else "—",
                                        className=f"text-{risk_color}",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.P("Volatility", className="text-muted mb-0 small"),
                                    html.H4(
                                        f"{risk['volatility']}%" if risk else "—",
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P("Sharpe", className="text-muted mb-0 small"),
                                    html.H4(f"{risk['sharpe']}" if risk else "—"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.P("Max DD", className="text-muted mb-0 small"),
                                    html.H4(
                                        f"{risk['max_drawdown']}%" if risk else "—",
                                        className="text-danger",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mt-2",
                    ),
                    html.Hr(),
                    dbc.Button(
                        "View Details",
                        href=f"/portfolio/{portfolio['id']}",
                        color="primary",
                        size="sm",
                    ),
                ]
            ),
        ],
        className="h-100",
    )


def layout():
    portfolios = get_portfolios()

    cards = []
    risk_data = []

    for p in portfolios:
        risk = get_portfolio_risk(p["id"])
        risk_data.append({"name": p["name"], "risk": risk})
        cards.append(dbc.Col(create_portfolio_card(p, risk), md=4))

    # Comparison chart
    fig = go.Figure()

    if risk_data:
        names = [r["name"] for r in risk_data]
        var_values = [r["risk"]["var_95"] if r["risk"] else 0 for r in risk_data]
        vol_values = [r["risk"]["volatility"] if r["risk"] else 0 for r in risk_data]

        fig.add_trace(go.Bar(name="VaR 95%", x=names, y=var_values, marker_color="#f39c12"))
        fig.add_trace(go.Bar(name="Volatility", x=names, y=vol_values, marker_color="#3498db"))

        fig.update_layout(
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=40, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )

    return html.Div(
        [
            html.H2("Portfolio Overview", className="mb-4"),
            dbc.Row(cards, className="mb-4"),
            html.H4("Risk Comparison", className="mt-4 mb-3"),
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
        ]
    )
