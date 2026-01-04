import dash
from dash import Dash, dcc, callback, Output, Input, State, clientside_callback
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from src.theme import theme, PALETTE_DARK, PALETTE_LIGHT
from src.api import get_portfolios

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    assets_folder="assets",
)
server = app.server


def nav_link(label, href, icon, pathname):
    """Single reusable nav link component."""
    active = pathname == href if href == "/" else pathname.startswith(href)
    return dmc.NavLink(
        label=label,
        href=href,
        leftSection=DashIconify(icon=icon, width=18),
        active=active,
        variant="light",
    )


# Theme toggle button
theme_toggle = dmc.ActionIcon(
    id="theme-toggle",
    variant="subtle",
    size="lg",
    children=DashIconify(icon="radix-icons:sun", width=20, id="theme-icon"),
)

# Mobile navbar toggle
navbar_toggle = dmc.ActionIcon(
    DashIconify(icon="radix-icons:hamburger-menu", width=20),
    id="navbar-toggle",
    variant="subtle",
    size="lg",
    hiddenFrom="sm",
)

# Navbar component
navbar = dmc.AppShellNavbar(
    id="app-navbar",
    children=dmc.Stack(
        [
            # Header
            dmc.Group(
                [
                    DashIconify(icon="radix-icons:shield", width=24, id="logo-icon"),
                    dmc.Title("CerberusRisk", order=4, id="app-title"),
                ],
                gap="xs",
                p="md",
            ),
            dmc.Divider(),
            # Navigation links
            dmc.ScrollArea(
                dmc.Stack(id="nav-links", gap=0, p="xs"),
                flex=1,
            ),
            dmc.Divider(),
            # Footer
            dmc.Group(
                [theme_toggle, navbar_toggle],
                p="md",
                justify="space-between",
            ),
        ],
        gap=0,
        h="100%",
    ),
)

app.layout = dmc.MantineProvider(
    id="mantine-provider",
    theme=theme,
    forceColorScheme="dark",
    children=[
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="color-scheme-store", storage_type="local", data="dark"),
        dcc.Store(id="navbar-opened", storage_type="memory", data=False),
        dmc.AppShell(
            id="app-shell",
            children=[
                navbar,
                dmc.AppShellMain(
                    dmc.Container(
                        dash.page_container,
                        size="xl",
                        py="md",
                    ),
                    id="app-main",
                ),
            ],
            navbar={
                "width": 240,
                "breakpoint": "sm",
                "collapsed": {"mobile": True},
            },
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


# Toggle navbar on mobile
clientside_callback(
    """
    function(n_clicks, currentState, pathname) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) return currentState;

        const triggerId = ctx.triggered[0].prop_id.split('.')[0];

        // Close navbar on navigation
        if (triggerId === 'url') return false;

        // Toggle on button click
        if (triggerId === 'navbar-toggle') return !currentState;

        return currentState;
    }
    """,
    Output("navbar-opened", "data"),
    Input("navbar-toggle", "n_clicks"),
    Input("url", "pathname"),
    State("navbar-opened", "data"),
    prevent_initial_call=True,
)


# Update navbar collapsed state
clientside_callback(
    """
    function(opened) {
        return {
            width: 240,
            breakpoint: 'sm',
            collapsed: { mobile: !opened }
        };
    }
    """,
    Output("app-shell", "navbar"),
    Input("navbar-opened", "data"),
)


# Update theme icon
@callback(
    Output("theme-icon", "icon"),
    Input("color-scheme-store", "data"),
)
def update_theme_icon(scheme):
    return "radix-icons:moon" if scheme == "dark" else "radix-icons:sun"


# Update navbar and shell styles
@callback(
    Output("app-navbar", "style"),
    Output("app-shell", "style"),
    Output("app-main", "style"),
    Output("app-title", "c"),
    Output("logo-icon", "color"),
    Output("theme-toggle", "color"),
    Output("navbar-toggle", "color"),
    Input("color-scheme-store", "data"),
)
def update_styles(scheme):
    palette = PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT
    navbar_style = {
        "backgroundColor": palette["surface"],
        "borderColor": palette["border"],
    }
    shell_style = {"backgroundColor": palette["background"]}
    main_style = {"backgroundColor": palette["background"]}
    return (
        navbar_style,
        shell_style,
        main_style,
        palette["primary"],
        palette["primary"],
        palette["text"],
        palette["text"],
    )


# Update navigation links
@callback(
    Output("nav-links", "children"),
    Input("color-scheme-store", "data"),
    Input("url", "pathname"),
)
def update_nav(scheme, pathname):
    pathname = pathname or "/"
    portfolios = get_portfolios()

    # Build portfolio nav links
    portfolio_links = [
        nav_link(p["name"], f"/portfolio/{p['id']}", "radix-icons:dot-filled", pathname)
        for p in portfolios
    ]

    return [
        nav_link("Home", "/", "radix-icons:home", pathname),
        dmc.NavLink(
            label="Portfolios",
            leftSection=DashIconify(icon="radix-icons:layers", width=18),
            childrenOffset=24,
            opened=pathname.startswith("/portfolio"),
            variant="light",
            children=portfolio_links if portfolio_links else [
                dmc.Text("No portfolios", size="sm", c="dimmed", p="xs")
            ],
        ),
        nav_link("Stress Test", "/stress", "radix-icons:mix", pathname),
    ]


if __name__ == "__main__":
    import os
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8050, debug=debug)
