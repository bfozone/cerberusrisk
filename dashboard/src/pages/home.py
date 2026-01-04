import dash
from dash import dcc, callback, Output, Input
import dash_mantine_components as dmc
import plotly.graph_objects as go

from src.api import get_portfolios, get_portfolio_risk
from src.components import portfolio_card, empty_figure
from src.components.charts import CHART_COLORS, chart_layout

dash.register_page(__name__, path="/", name="Home")


def layout():
    portfolios = get_portfolios()

    cards = []
    for p in portfolios:
        risk = get_portfolio_risk(p["id"])
        cards.append(dmc.GridCol(portfolio_card(p, risk), span={"base": 12, "sm": 6, "md": 4}))

    return dmc.Stack(
        [
            dmc.Title("Portfolio Overview", order=2),
            dmc.Grid(cards, gutter="md"),
            dmc.Title("Risk Comparison", order=4, mt="lg"),
            dcc.Graph(id="home-risk-chart", figure=empty_figure(height=400), config={"displayModeBar": False}),
        ],
        gap="md",
    )


@callback(
    Output("home-risk-chart", "figure"),
    Input("color-scheme-store", "data"),
)
def update_risk_chart(scheme):
    scheme = scheme or "dark"
    portfolios = get_portfolios()

    fig = go.Figure()

    if portfolios:
        risk_data = []
        for p in portfolios:
            risk = get_portfolio_risk(p["id"])
            risk_data.append({"name": p["name"], "risk": risk})

        names = [r["name"] for r in risk_data]
        var_values = [r["risk"]["var_95"] if r["risk"] else 0 for r in risk_data]
        vol_values = [r["risk"]["volatility"] if r["risk"] else 0 for r in risk_data]

        fig.add_trace(go.Bar(
            name="VaR 95%",
            x=names,
            y=var_values,
            marker_color=CHART_COLORS["warning"],
            marker_cornerradius=6,
        ))
        fig.add_trace(go.Bar(
            name="Volatility",
            x=names,
            y=vol_values,
            marker_color=CHART_COLORS["primary"],
            marker_cornerradius=6,
        ))

        fig.update_layout(
            **chart_layout(
                height=400,
                scheme=scheme,
                barmode="group",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            ),
        )

    return fig
