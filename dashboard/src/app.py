import dash
from dash import Dash, dcc, callback, Output, Input, State, clientside_callback
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from src.theme import theme, PALETTE_DARK, PALETTE_LIGHT

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    assets_folder="assets",
)
server = app.server  # Expose Flask server for gunicorn

nav_links = [
    ("Home", "/"),
    ("Global Equity", "/portfolio/1"),
    ("Fixed Income", "/portfolio/2"),
    ("Multi-Asset", "/portfolio/3"),
    ("Stress Test", "/stress"),
]


def create_nav_links(scheme: str, pathname: str = "/"):
    """Create nav links with appropriate colors and active state."""
    palette = PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT

    def is_active(href: str) -> bool:
        if href == "/":
            return pathname == "/"
        return pathname.startswith(href)

    return [
        dmc.Anchor(
            label,
            href=href,
            c=palette["primary"] if is_active(href) else palette["text"],
            underline="never",
            fw=600 if is_active(href) else 400,
            style={
                "borderBottom": f"2px solid {palette['primary']}" if is_active(href) else "2px solid transparent",
                "paddingBottom": "4px",
            },
        )
        for label, href in nav_links
    ]


def create_drawer_links(scheme: str, pathname: str = "/"):
    """Create drawer nav links with active state."""
    palette = PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT

    def is_active(href: str) -> bool:
        if href == "/":
            return pathname == "/"
        return pathname.startswith(href)

    return [
        dmc.Anchor(
            label,
            href=href,
            c=palette["primary"] if is_active(href) else palette["text"],
            underline="never",
            size="lg",
            fw=600 if is_active(href) else 400,
            id={"type": "drawer-link", "index": i},
        )
        for i, (label, href) in enumerate(nav_links)
    ]


# Theme toggle button
theme_toggle = dmc.ActionIcon(
    id="theme-toggle",
    variant="subtle",
    size="lg",
    children=DashIconify(icon="radix-icons:sun", width=20, id="theme-icon"),
)

# Desktop navbar
desktop_nav = dmc.Group(
    id="desktop-nav",
    gap="lg",
    visibleFrom="sm",
)

# Mobile burger
mobile_burger = dmc.Burger(
    id="nav-burger",
    opened=False,
    hiddenFrom="sm",
    size="sm",
)

# Mobile drawer
mobile_drawer = dmc.Drawer(
    id="nav-drawer",
    title="Menu",
    padding="md",
    size="xs",
    zIndex=1000,
)

header = dmc.AppShellHeader(
    id="app-header",
    children=dmc.Group(
        [
            dmc.Title("CerberusRisk", order=3, id="app-title"),
            desktop_nav,
            dmc.Group([theme_toggle, mobile_burger], gap="xs"),
        ],
        justify="space-between",
        h="100%",
        px="md",
    ),
)

app.layout = dmc.MantineProvider(
    id="mantine-provider",
    theme=theme,
    forceColorScheme="dark",
    children=[
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="color-scheme-store", storage_type="local", data="dark"),
        mobile_drawer,
        dmc.AppShell(
            id="app-shell",
            children=[
                header,
                dmc.AppShellMain(
                    dmc.Container(
                        dash.page_container,
                        size="xl",
                        py="md",
                    ),
                    id="app-main",
                ),
            ],
            header={"height": 60},
            padding="md",
        ),
    ],
)


# Toggle color scheme
clientside_callback(
    """
    function(n_clicks, currentScheme) {
        if (n_clicks === undefined) {
            return window.dash_clientside.no_update;
        }
        return currentScheme === 'dark' ? 'light' : 'dark';
    }
    """,
    Output("color-scheme-store", "data"),
    Input("theme-toggle", "n_clicks"),
    State("color-scheme-store", "data"),
    prevent_initial_call=True,
)


# Update MantineProvider color scheme
clientside_callback(
    """
    function(scheme) {
        return scheme;
    }
    """,
    Output("mantine-provider", "forceColorScheme"),
    Input("color-scheme-store", "data"),
)


# Update theme icon
@callback(
    Output("theme-icon", "icon"),
    Input("color-scheme-store", "data"),
)
def update_theme_icon(scheme):
    return "radix-icons:moon" if scheme == "dark" else "radix-icons:sun"


# Update header styles with backdrop blur
@callback(
    Output("app-header", "style"),
    Output("app-title", "c"),
    Output("theme-toggle", "color"),
    Output("nav-burger", "color"),
    Input("color-scheme-store", "data"),
)
def update_header_styles(scheme):
    palette = PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT
    # Semi-transparent background with backdrop blur
    bg_color = "rgba(13, 13, 18, 0.9)" if scheme == "dark" else "rgba(250, 249, 251, 0.9)"
    header_style = {
        "backgroundColor": bg_color,
        "backdropFilter": "blur(12px)",
        "WebkitBackdropFilter": "blur(12px)",
        "borderColor": palette["border"],
    }
    return header_style, palette["primary"], palette["text"], palette["text"]


# Update app shell and main styles
@callback(
    Output("app-shell", "style"),
    Output("app-main", "style"),
    Input("color-scheme-store", "data"),
)
def update_shell_styles(scheme):
    palette = PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT
    return (
        {"backgroundColor": palette["background"]},
        {"backgroundColor": palette["background"]},
    )


# Update desktop nav with active state
@callback(
    Output("desktop-nav", "children"),
    Input("color-scheme-store", "data"),
    Input("url", "pathname"),
)
def update_desktop_nav(scheme, pathname):
    return create_nav_links(scheme, pathname or "/")


# Update mobile drawer with active state
@callback(
    Output("nav-drawer", "styles"),
    Output("nav-drawer", "children"),
    Input("color-scheme-store", "data"),
    Input("url", "pathname"),
)
def update_drawer(scheme, pathname):
    palette = PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT
    styles = {
        "content": {"backgroundColor": palette["surface"]},
        "header": {"backgroundColor": palette["surface"]},
    }
    children = dmc.Stack(
        create_drawer_links(scheme, pathname or "/"),
        gap="md",
    )
    return styles, children


# Toggle drawer on burger click
@callback(
    Output("nav-drawer", "opened"),
    Input("nav-burger", "opened"),
    Input("url", "pathname"),
    State("nav-drawer", "opened"),
)
def toggle_drawer(burger_opened, pathname, drawer_opened):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Close drawer when URL changes (link clicked)
    if trigger_id == "url" and drawer_opened:
        return False

    # Toggle based on burger
    if trigger_id == "nav-burger":
        return burger_opened

    return drawer_opened


if __name__ == "__main__":
    import os
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8050, debug=debug)
