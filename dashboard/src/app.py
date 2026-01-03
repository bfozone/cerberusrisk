import dash
from dash import Dash, html
import dash_mantine_components as dmc

from src.theme import theme

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)

navbar = dmc.Group(
    [
        dmc.Anchor("Home", href="/", c="white", underline="never"),
        dmc.Anchor("Global Equity", href="/portfolio/1", c="white", underline="never"),
        dmc.Anchor("Fixed Income", href="/portfolio/2", c="white", underline="never"),
        dmc.Anchor("Multi-Asset", href="/portfolio/3", c="white", underline="never"),
        dmc.Anchor("Stress Test", href="/stress", c="white", underline="never"),
    ],
    gap="lg",
)

header = dmc.AppShellHeader(
    dmc.Group(
        [
            dmc.Title("CerberusRisk", order=3, c="white"),
            navbar,
        ],
        justify="space-between",
        h="100%",
        px="md",
    )
)

app.layout = dmc.MantineProvider(
    theme=theme,
    forceColorScheme="dark",
    children=dmc.AppShell(
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
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
