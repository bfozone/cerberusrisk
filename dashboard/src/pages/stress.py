import dash
from dash import html, dcc, callback, Output, Input
import dash_mantine_components as dmc

from src.api import get_stress_scenarios, compare_stress
from src.components import data_table, bar_chart

dash.register_page(__name__, path="/stress", name="Stress Testing")


def layout():
    scenarios = get_stress_scenarios()
    scenario_options = [{"label": s["name"], "value": s["id"]} for s in scenarios]

    return dmc.Stack(
        [
            dmc.Title("Stress Testing", order=2),
            dmc.Select(
                id="scenario-dropdown",
                label="Select Scenario",
                data=scenario_options,
                value="equity_crash" if scenario_options else None,
                w=300,
            ),
            html.Div(id="stress-results"),
        ],
        gap="md",
    )


@callback(
    Output("stress-results", "children"),
    Input("scenario-dropdown", "value"),
)
def update_stress_results(scenario_id):
    if not scenario_id:
        return dmc.Text("Select a scenario to view results")

    data = compare_stress(scenario_id)
    if not data:
        return dmc.Text("Error loading stress results")

    scenario = data["scenario"]
    results = data["results"]

    # Scenario description card
    scenario_card = dmc.Card(
        [
            dmc.Title(scenario["name"], order=5),
            dmc.Text(scenario["description"], c="dimmed", size="sm"),
            dmc.Title("Shocks by Asset Class:", order=6, mt="sm"),
            dmc.List(
                [dmc.ListItem(f"{k}: {v:+.0f}%") for k, v in scenario["shocks"].items()],
                size="sm",
            ),
        ],
        withBorder=True,
        padding="md",
        radius="sm",
    )

    # Comparison chart
    portfolio_names = [r["portfolio_name"] for r in results]
    pnl_values = [r["total_pnl_pct"] for r in results]
    colors = ["#e74c3c" if v < 0 else "#27ae60" for v in pnl_values]

    comparison_fig = bar_chart(
        portfolio_names,
        pnl_values,
        color=colors,
        text=[f"{v:+.1f}%" for v in pnl_values],
        height=300,
        yaxis_title="Portfolio P&L (%)",
    )

    # Summary table
    summary_rows = []
    summary_colors = []
    for result in results:
        pnl = result["total_pnl_pct"]
        pnl_color = "red" if pnl < 0 else "green"
        summary_rows.append([result["portfolio_name"], f"{pnl:+.2f}%"])
        summary_colors.append([None, pnl_color])

    # Detailed breakdown for each portfolio
    detail_cards = []
    for result in results:
        positions = result["positions"]
        headers = ["Ticker", "Weight", "Asset Class", "Shock", "P&L"]
        rows = []
        row_colors = []

        for pos in positions:
            pnl = pos["pnl_pct"]
            pnl_color = "red" if pnl < 0 else "green"
            rows.append([
                pos["ticker"],
                f"{pos['weight']*100:.1f}%",
                pos["asset_class"],
                f"{pos['shock']:+.0f}%",
                f"{pnl:+.2f}%",
            ])
            row_colors.append([None, None, None, None, pnl_color])

        detail_table = data_table(headers, rows, row_colors)

        total_pnl = result["total_pnl_pct"]
        total_color = "red" if total_pnl < 0 else "green"

        detail_cards.append(
            dmc.GridCol(
                dmc.Card(
                    [
                        dmc.CardSection(
                            dmc.Group(
                                [
                                    dmc.Text(result["portfolio_name"], fw=500),
                                    dmc.Text(f"{total_pnl:+.2f}%", c=total_color, fw=600),
                                ],
                                justify="space-between",
                                p="sm",
                            ),
                            withBorder=True,
                        ),
                        detail_table,
                    ],
                    withBorder=True,
                    padding="sm",
                    radius="sm",
                ),
                span=4,
            )
        )

    return dmc.Stack(
        [
            scenario_card,
            dmc.Title("Portfolio Comparison", order=5),
            dcc.Graph(figure=comparison_fig, config={"displayModeBar": False}),
            dmc.Divider(my="md"),
            dmc.Title("Detailed Breakdown", order=5),
            dmc.Grid(detail_cards),
        ],
        gap="md",
    )
