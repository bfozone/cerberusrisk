import dash
from dash import Dash, html, callback, Output, Input, State
import dash_mantine_components as dmc

from src.theme import theme

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server  # Expose Flask server for gunicorn

nav_links = [
    ("Home", "/"),
    ("Global Equity", "/portfolio/1"),
    ("Fixed Income", "/portfolio/2"),
    ("Multi-Asset", "/portfolio/3"),
    ("Stress Test", "/stress"),
]

# Desktop navbar
desktop_nav = dmc.Group(
    [dmc.Anchor(label, href=href, c="white", underline="never") for label, href in nav_links],
    gap="lg",
    visibleFrom="sm",
)

# Mobile burger
mobile_burger = dmc.Burger(
    id="nav-burger",
    opened=False,
    hiddenFrom="sm",
    color="white",
    size="sm",
)

# Mobile drawer
mobile_drawer = dmc.Drawer(
    id="nav-drawer",
    title="Menu",
    padding="md",
    size="xs",
    children=dmc.Stack(
        [dmc.Anchor(label, href=href, c="white", underline="never", size="lg") for label, href in nav_links],
        gap="md",
    ),
)

header = dmc.AppShellHeader(
    dmc.Group(
        [
            dmc.Title("CerberusRisk", order=3, c="white"),
            desktop_nav,
            mobile_burger,
        ],
        justify="space-between",
        h="100%",
        px="md",
    )
)

app.layout = dmc.MantineProvider(
    theme=theme,
    forceColorScheme="dark",
    children=[
        mobile_drawer,
        dmc.AppShell(
            [
                header,
                dmc.AppShellMain(
                    dmc.Container(
                        dash.page_container,
                        size="xl",
                        py="md",
                    )
                ),
            ],
            header={"height": 60},
            padding="md",
        ),
    ],
)


@callback(
    Output("nav-drawer", "opened"),
    Input("nav-burger", "opened"),
    State("nav-drawer", "opened"),
)
def toggle_drawer(burger_opened, drawer_opened):
    return burger_opened


if __name__ == "__main__":
    import os
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8050, debug=debug)
