import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from src.api import get_portfolios, get_portfolio_risk
from src.components import portfolio_card, dark_layout

dash.register_page(__name__, path="/", name="Home")


def layout():
    portfolios = get_portfolios()

    cards = []
    risk_data = []

    for p in portfolios:
        risk = get_portfolio_risk(p["id"])
        risk_data.append({"name": p["name"], "risk": risk})
        cards.append(dbc.Col(portfolio_card(p, risk), md=4))

    # Comparison chart
    fig = go.Figure()

    if risk_data:
        names = [r["name"] for r in risk_data]
        var_values = [r["risk"]["var_95"] if r["risk"] else 0 for r in risk_data]
        vol_values = [r["risk"]["volatility"] if r["risk"] else 0 for r in risk_data]

        fig.add_trace(go.Bar(name="VaR 95%", x=names, y=var_values, marker_color="#f39c12"))
        fig.add_trace(go.Bar(name="Volatility", x=names, y=vol_values, marker_color="#3498db"))

        fig.update_layout(
            **dark_layout(height=400),
            barmode="group",
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
