import dash
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc

from src.api import get_stress_scenarios, compare_stress
from src.components import data_table, bar_chart

dash.register_page(__name__, path="/stress", name="Stress Testing")


def layout():
    scenarios = get_stress_scenarios()
    scenario_options = [{"label": s["name"], "value": s["id"]} for s in scenarios]

    return html.Div(
        [
            html.H2("Stress Testing", className="mb-4"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Select Scenario", className="mb-2"),
                            dcc.Dropdown(
                                id="scenario-dropdown",
                                options=scenario_options,
                                value="equity_crash" if scenario_options else None,
                                className="mb-3",
                            ),
                        ],
                        md=4,
                    ),
                ],
                className="mb-4",
            ),
            html.Div(id="stress-results"),
        ]
    )


@callback(
    Output("stress-results", "children"),
    Input("scenario-dropdown", "value"),
)
def update_stress_results(scenario_id):
    if not scenario_id:
        return html.P("Select a scenario to view results")

    data = compare_stress(scenario_id)
    if not data:
        return html.P("Error loading stress results")

    scenario = data["scenario"]
    results = data["results"]

    # Scenario description card
    scenario_card = dbc.Card(
        dbc.CardBody(
            [
                html.H5(scenario["name"], className="mb-2"),
                html.P(scenario["description"], className="text-muted mb-3"),
                html.H6("Shocks by Asset Class:", className="mb-2"),
                html.Ul([html.Li(f"{k}: {v:+.0f}%") for k, v in scenario["shocks"].items()]),
            ]
        ),
        className="mb-4",
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
    summary_classes = []
    for result in results:
        pnl = result["total_pnl_pct"]
        pnl_class = "text-danger" if pnl < 0 else "text-success"
        summary_rows.append([result["portfolio_name"], f"{pnl:+.2f}%"])
        summary_classes.append(["", pnl_class])

    results_table = data_table(["Portfolio", "P&L Impact"], summary_rows, summary_classes)

    # Detailed breakdown for each portfolio
    detail_cards = []
    for result in results:
        positions = result["positions"]
        headers = ["Ticker", "Weight", "Asset Class", "Shock", "P&L"]
        rows = []
        row_classes = []

        for pos in positions:
            pnl = pos["pnl_pct"]
            pnl_class = "text-danger" if pnl < 0 else "text-success"
            rows.append([
                pos["ticker"],
                f"{pos['weight']*100:.1f}%",
                pos["asset_class"],
                f"{pos['shock']:+.0f}%",
                f"{pnl:+.2f}%",
            ])
            row_classes.append(["", "", "", "", pnl_class])

        detail_table = data_table(headers, rows, row_classes, size="sm")

        total_pnl = result["total_pnl_pct"]
        total_class = "text-danger" if total_pnl < 0 else "text-success"

        detail_cards.append(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.Div(
                                [
                                    html.Span(result["portfolio_name"]),
                                    html.Span(f"{total_pnl:+.2f}%", className=f"float-end {total_class}"),
                                ]
                            )
                        ),
                        dbc.CardBody(detail_table),
                    ]
                ),
                md=4,
                className="mb-3",
            )
        )

    return html.Div(
        [
            scenario_card,
            html.H5("Portfolio Comparison", className="mb-3"),
            dcc.Graph(figure=comparison_fig, config={"displayModeBar": False}, style={"height": "300px"}),
            html.Hr(),
            html.H5("Detailed Breakdown", className="mb-3"),
            dbc.Row(detail_cards),
        ]
    )
