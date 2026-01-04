import dash
from dash import Dash, dcc, html, callback, Output, Input, State, clientside_callback
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from src.theme import theme, PALETTE_DARK, PALETTE_LIGHT
from src.api import get_portfolios
from src.components.icons import Icon

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    assets_folder="assets",
)
app._favicon = "favicon.svg"
server = app.server


def nav_link(label, href, icon_name, pathname, color="#e4e4e7"):
    """Nav link with label that fades via CSS when collapsed."""
    active = pathname == href if href == "/" else pathname.startswith(href)
    return dmc.Tooltip(
        dmc.NavLink(
            label=html.Span(label, className="nav-label"),
            href=href,
            leftSection=Icon(icon_name, size=18, color=color),
            active=active,
            variant="light",
        ),
        label=label,
        position="right",
        className="nav-tooltip",
    )


# Theme toggle button (dynamic icon - keep DashIconify)
theme_toggle = dmc.ActionIcon(
    id="theme-toggle",
    variant="subtle",
    size="lg",
    children=DashIconify(icon="radix-icons:sun", width=20, id="theme-icon"),
)

# Desktop collapse toggle (dynamic icon - keep DashIconify)
collapse_toggle = dmc.ActionIcon(
    id="collapse-toggle",
    variant="subtle",
    size="lg",
    children=DashIconify(icon="radix-icons:chevron-left", width=20, id="collapse-icon"),
    visibleFrom="sm",
)

# Mobile close button (static - use local icon)
mobile_close = dmc.ActionIcon(
    id="mobile-close",
    variant="subtle",
    size="lg",
    hiddenFrom="sm",
)

# Floating mobile FAB (static - use local icon)
mobile_fab = dmc.Affix(
    dmc.ActionIcon(
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

# Navbar with inner wrapper for animations
navbar = dmc.AppShellNavbar(
    id="app-navbar",
    children=html.Div(
        className="navbar-inner",
        children=[
            # Header
            dmc.Group(
                id="navbar-header",
                gap="xs",
                p="md",
                className="navbar-header",
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
                className="navbar-footer",
            ),
        ],
    ),
)

# Main layout with data attributes on wrapper
app.layout = dmc.MantineProvider(
    id="mantine-provider",
    theme=theme,
    forceColorScheme="dark",
    children=[
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="color-scheme-store", storage_type="local", data="dark"),
        dcc.Store(id="mobile-opened", storage_type="memory", data=False),
        dcc.Store(id="desktop-collapsed", storage_type="local", data=False),
        # Wrapper with data attributes for CSS animations
        html.Div(
            id="app-wrapper",
            **{"data-navbar-collapsed": "false", "data-navbar-mobile-open": "false"},
            children=[
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
                        "width": {"base": 240, "sm": 240},
                        "breakpoint": "sm",
                        "collapsed": {"mobile": True, "desktop": False},
                    },
                    padding="md",
                ),
            ],
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

# Update wrapper data attributes and AppShell navbar config
clientside_callback(
    """
    function(mobileOpened, desktopCollapsed) {
        // Update data attributes on wrapper for CSS (with safety check)
        setTimeout(function() {
            var wrapper = document.getElementById('app-wrapper');
            if (wrapper) {
                wrapper.setAttribute('data-navbar-collapsed', String(desktopCollapsed));
                wrapper.setAttribute('data-navbar-mobile-open', String(mobileOpened));
            }
        }, 0);

        // Return navbar config for Mantine
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
        return {
            opacity: mobileOpened ? 0 : 1,
            transform: mobileOpened ? 'scale(0.8)' : 'scale(1)',
            pointerEvents: mobileOpened ? 'none' : 'auto',
            transition: 'opacity 0.25s ease, transform 0.25s ease'
        };
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


# Update colors and icons based on theme
@callback(
    Output("app-navbar", "style"),
    Output("app-shell", "style"),
    Output("app-main", "style"),
    Output("navbar-header", "children"),
    Output("mobile-close", "children"),
    Output("mobile-open", "children"),
    Output("app-title", "style"),
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
    title_style = {"color": palette["primary"], "fontWeight": 600, "fontSize": "1.1rem"}

    # Header with logo
    header_children = [
        Icon("nodes-down", size=24, color=palette["primary"]),
        html.Span("CerberusRisk", className="nav-label logo-text", id="app-title",
                  style=title_style),
    ]

    # Mobile button icons
    close_icon = Icon("cross-1", size=20, color=palette["text"])
    open_icon = Icon("hamburger-menu", size=22, color="#ffffff")

    return (
        navbar_style,
        shell_style,
        main_style,
        header_children,
        close_icon,
        open_icon,
        title_style,
        palette["text"],
        palette["text"],
        palette["text"],
    )


# Update navigation links
@callback(
    Output("nav-links", "children"),
    Input("url", "pathname"),
    Input("color-scheme-store", "data"),
)
def update_nav(pathname, scheme):
    pathname = pathname or "/"
    portfolios = get_portfolios()
    palette = PALETTE_DARK if scheme == "dark" else PALETTE_LIGHT
    icon_color = palette["text"]

    portfolio_links = [
        nav_link(p["name"], f"/portfolio/{p['id']}", "dot-filled", pathname, icon_color)
        for p in portfolios
    ]

    return [
        nav_link("Home", "/", "home", pathname, icon_color),
        dmc.NavLink(
            label=html.Span("Portfolios", className="nav-label"),
            leftSection=Icon("layers", size=18, color=icon_color),
            childrenOffset=28,
            opened=pathname.startswith("/portfolio"),
            variant="light",
            children=portfolio_links if portfolio_links else [
                dmc.Text("No portfolios", size="sm", c="dimmed", p="xs")
            ],
        ),
        nav_link("Stress Test", "/stress", "mix", pathname, icon_color),
    ]


if __name__ == "__main__":
    import os
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=8050, debug=debug)
