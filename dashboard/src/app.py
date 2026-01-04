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


def nav_link(label, href, icon, pathname, collapsed=False):
    """Single reusable nav link component."""
    active = pathname == href if href == "/" else pathname.startswith(href)
    return dmc.NavLink(
        label=None if collapsed else label,
        href=href,
        leftSection=DashIconify(icon=icon, width=20 if collapsed else 18),
        active=active,
        variant="light",
        style={"justifyContent": "center"} if collapsed else None,
    )


# Theme toggle button
theme_toggle = dmc.ActionIcon(
    id="theme-toggle",
    variant="subtle",
    size="lg",
    children=DashIconify(icon="radix-icons:sun", width=20, id="theme-icon"),
)

# Desktop collapse toggle (inside navbar)
collapse_toggle = dmc.ActionIcon(
    id="collapse-toggle",
    variant="subtle",
    size="lg",
    children=DashIconify(icon="radix-icons:chevron-left", width=20, id="collapse-icon"),
    visibleFrom="sm",
)

# Mobile close button (inside navbar, closes it)
mobile_close = dmc.ActionIcon(
    DashIconify(icon="radix-icons:cross-1", width=20),
    id="mobile-close",
    variant="subtle",
    size="lg",
    hiddenFrom="sm",
)

# Floating mobile open button (outside navbar, visible when closed)
mobile_fab = dmc.Affix(
    dmc.ActionIcon(
        DashIconify(icon="radix-icons:hamburger-menu", width=22),
        id="mobile-open",
        variant="filled",
        size="xl",
        radius="xl",
        color="violet",
    ),
    position={"bottom": 20, "left": 20},
    hiddenFrom="sm",
    id="mobile-fab",
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
                id="navbar-header",
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
                [theme_toggle, collapse_toggle, mobile_close],
                p="md",
                justify="space-between",
                id="navbar-footer",
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
        dcc.Store(id="mobile-opened", storage_type="memory", data=False),
        dcc.Store(id="desktop-collapsed", storage_type="local", data=False),
        mobile_fab,
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
                "collapsed": {"mobile": True, "desktop": False},
            },
            padding="md",
        ),
    ],
)


# Toggle color scheme
clientside_callback(
    """
    function(n_clicks, currentScheme) {
        if (n_clicks === undefined) return window.dash_clientside.no_update;
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
    """function(scheme) { return scheme; }""",
    Output("mantine-provider", "forceColorScheme"),
    Input("color-scheme-store", "data"),
)

# Toggle mobile navbar
clientside_callback(
    """
    function(openClicks, closeClicks, pathname, currentState) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered.length) return currentState;
        const triggerId = ctx.triggered[0].prop_id.split('.')[0];
        if (triggerId === 'url') return false;
        if (triggerId === 'mobile-open') return true;
        if (triggerId === 'mobile-close') return false;
        return currentState;
    }
    """,
    Output("mobile-opened", "data"),
    Input("mobile-open", "n_clicks"),
    Input("mobile-close", "n_clicks"),
    Input("url", "pathname"),
    State("mobile-opened", "data"),
    prevent_initial_call=True,
)

# Toggle desktop collapsed state
clientside_callback(
    """
    function(n_clicks, currentState) {
        if (n_clicks === undefined) return window.dash_clientside.no_update;
        return !currentState;
    }
    """,
    Output("desktop-collapsed", "data"),
    Input("collapse-toggle", "n_clicks"),
    State("desktop-collapsed", "data"),
    prevent_initial_call=True,
)

# Update navbar config based on mobile/desktop state
clientside_callback(
    """
    function(mobileOpened, desktopCollapsed) {
        return {
            width: desktopCollapsed ? 70 : 240,
            breakpoint: 'sm',
            collapsed: {
                mobile: !mobileOpened,
                desktop: false
            }
        };
    }
    """,
    Output("app-shell", "navbar"),
    Input("mobile-opened", "data"),
    Input("desktop-collapsed", "data"),
)

# Hide mobile FAB when navbar is open
clientside_callback(
    """
    function(mobileOpened) {
        return { display: mobileOpened ? 'none' : 'block' };
    }
    """,
    Output("mobile-fab", "style"),
    Input("mobile-opened", "data"),
)

# Update collapse icon direction
clientside_callback(
    """
    function(collapsed) {
        return collapsed ? 'radix-icons:chevron-right' : 'radix-icons:chevron-left';
    }
    """,
    Output("collapse-icon", "icon"),
    Input("desktop-collapsed", "data"),
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
    Output("logo-icon", "color"),
    Output("theme-toggle", "color"),
    Output("collapse-toggle", "color"),
    Output("mobile-close", "color"),
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
        palette["text"],
        palette["text"],
        palette["text"],
    )


# Update navbar header visibility when collapsed
@callback(
    Output("navbar-header", "children"),
    Output("navbar-header", "justify"),
    Input("desktop-collapsed", "data"),
    Input("color-scheme-store", "data"),
)
def update_navbar_header(collapsed, scheme):
    palette = PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT
    if collapsed:
        return (
            DashIconify(icon="radix-icons:shield", width=24, id="logo-icon", color=palette["primary"]),
            "center",
        )
    return (
        [
            DashIconify(icon="radix-icons:shield", width=24, id="logo-icon", color=palette["primary"]),
            dmc.Title("CerberusRisk", order=4, c=palette["primary"]),
        ],
        "flex-start",
    )


# Update navigation links
@callback(
    Output("nav-links", "children"),
    Input("color-scheme-store", "data"),
    Input("url", "pathname"),
    Input("desktop-collapsed", "data"),
)
def update_nav(scheme, pathname, collapsed):
    pathname = pathname or "/"
    portfolios = get_portfolios()

    if collapsed:
        # Collapsed: icons only, no nested items
        return [
            nav_link("Home", "/", "radix-icons:home", pathname, collapsed=True),
            nav_link("Portfolios", "/portfolio/1", "radix-icons:layers", pathname, collapsed=True),
            nav_link("Stress Test", "/stress", "radix-icons:mix", pathname, collapsed=True),
        ]

    # Expanded: full nav with nested portfolios
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


# Update footer layout when collapsed
@callback(
    Output("navbar-footer", "children"),
    Output("navbar-footer", "justify"),
    Output("navbar-footer", "style"),
    Input("desktop-collapsed", "data"),
)
def update_navbar_footer(collapsed):
    if collapsed:
        return (
            dmc.Stack(
                [theme_toggle, collapse_toggle, mobile_close],
                gap="xs",
                align="center",
            ),
            "center",
            {"padding": "8px"},
        )
    return (
        [theme_toggle, collapse_toggle, mobile_close],
        "space-between",
        {"padding": "16px"},
    )


if __name__ == "__main__":
    import os
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8050, debug=debug)
