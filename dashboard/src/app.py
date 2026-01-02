import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Global Equity", href="/portfolio/1")),
        dbc.NavItem(dbc.NavLink("Fixed Income", href="/portfolio/2")),
        dbc.NavItem(dbc.NavLink("Multi-Asset", href="/portfolio/3")),
        dbc.NavItem(dbc.NavLink("Stress Test", href="/stress")),
    ],
    brand="CerberusRisk",
    brand_href="/",
    color="primary",
    dark=True,
)

app.layout = dbc.Container(
    [
        navbar,
        html.Br(),
        dash.page_container,
    ],
    fluid=True,
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
