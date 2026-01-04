import dash
from dash import html, dcc, callback, Output, Input
import dash_mantine_components as dmc

from src.api import (
    get_portfolios,
    get_portfolio,
    get_portfolio_value,
    get_portfolio_risk,
    get_risk_contributions,
    get_correlation,
    get_stress_scenarios,
    run_stress_test,
)
from src.components import metric_card, data_table, bar_chart, pie_chart, heatmap_chart, empty_figure
from src.components.charts import CHART_COLORS

dash.register_page(__name__, path="/analytics", name="Portfolio Analytics")


def layout():
    portfolios = get_portfolios()
    if not portfolios:
        return dmc.Text("No portfolios available")

    portfolio_options = [{"label": p["name"], "value": str(p["id"])} for p in portfolios]
    default_id = portfolios[0]["id"]

    scenarios = get_stress_scenarios()
    scenario_options = [{"label": s["name"], "value": s["id"]} for s in scenarios]

    return dmc.Stack(
        [
            dcc.Store(id="selected-portfolio-store", data=default_id),

            # Portfolio selector
            dmc.Select(
                id="portfolio-select",
                data=portfolio_options,
                value=str(default_id),
                label="Portfolio",
                w={"base": "100%", "sm": 300},
            ),

            # Tabs
            dmc.Tabs(
                id="analytics-tabs",
                value="risk",
                children=[
                    dmc.TabsList([
                        dmc.TabsTab("Risk Metrics", value="risk"),
                        dmc.TabsTab("Stress Testing", value="stress"),
                    ]),
                    dmc.TabsPanel(html.Div(id="risk-content"), value="risk", pt="md"),
                    dmc.TabsPanel(html.Div(id="stress-content"), value="stress", pt="md"),
                ],
            ),

            # Hidden stores for scenario selection
            dcc.Store(id="scenario-options-store", data=scenario_options),
        ],
        gap="md",
    )


# Update selected portfolio store
@callback(
    Output("selected-portfolio-store", "data"),
    Input("portfolio-select", "value"),
)
def update_selected_portfolio(value):
    return int(value) if value else None


# ============================================================================
# RISK METRICS TAB
# ============================================================================

def render_risk_cards(risk):
    """Render risk metric cards."""
    if not risk:
        return dmc.Text("Loading risk metrics...", c="dimmed")

    metrics = [
        ("VaR 95%", f"{risk['var_95']}%", "orange"),
        ("VaR 99%", f"{risk['var_99']}%", "red"),
        ("CVaR 95%", f"{risk['cvar_95']}%", "orange"),
        ("Volatility", f"{risk['volatility']}%", "blue"),
        ("Sharpe", f"{risk['sharpe']}", "green" if risk["sharpe"] > 0.5 else "gray"),
        ("Max DD", f"{risk['max_drawdown']}%", "red"),
    ]
    return dmc.Grid(
        [dmc.GridCol(metric_card(name, value, color), span={"base": 4, "sm": 2}) for name, value, color in metrics],
        gutter="xs",
    )


def render_holdings_table(portfolio, value_data):
    """Render holdings table."""
    positions = value_data["positions"] if value_data else portfolio["positions"]
    headers = ["Ticker", "Name", "Weight", "Price", "Change"]
    rows = []
    row_colors = []

    for pos in positions:
        price = pos.get("price", "—")
        change = pos.get("change_pct")
        change_color = None
        change_str = "—"
        if change is not None:
            change_color = "green" if change >= 0 else "red"
            change_str = f"{change:+.2f}%"

        rows.append([
            pos["ticker"],
            pos["name"],
            f"{pos['weight']*100:.1f}%",
            f"${price}" if isinstance(price, (int, float)) else price,
            change_str,
        ])
        row_colors.append([None, None, None, None, change_color])

    return data_table(headers, rows, row_colors)


@callback(
    Output("risk-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_risk_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        return dmc.Text("Portfolio not found")

    value_data = get_portfolio_value(portfolio_id)
    risk = get_portfolio_risk(portfolio_id)
    contributions = get_risk_contributions(portfolio_id)
    correlation = get_correlation(portfolio_id)

    # Generate all figures in one pass (no separate callbacks = no double-render)
    labels = [p["ticker"] for p in portfolio["positions"]]
    values = [p["weight"] for p in portfolio["positions"]]
    pie_fig = pie_chart(labels, values, scheme=scheme)

    if contributions:
        tickers = [c["ticker"] for c in contributions]
        pct_contrib = [c["pct_contribution"] for c in contributions]
        contrib_fig = bar_chart(
            tickers,
            pct_contrib,
            color=CHART_COLORS["negative"],
            text=[f"{v:.1f}%" for v in pct_contrib],
            yaxis_title="% Contribution to VaR",
            showlegend=False,
            scheme=scheme,
        )
    else:
        contrib_fig = empty_figure()

    if correlation and correlation["matrix"]:
        corr_fig = heatmap_chart(
            correlation["matrix"],
            correlation["tickers"],
            correlation["tickers"],
            scheme=scheme,
        )
    else:
        corr_fig = empty_figure()

    return dmc.Stack(
        [
            # Portfolio header
            dmc.Title(portfolio["name"], order=3),
            dmc.Text(portfolio["description"], c="dimmed"),

            # Risk metrics
            dmc.Title("Risk Metrics", order=5, mt="md"),
            render_risk_cards(risk),

            dmc.Divider(my="md"),

            # Holdings and allocation
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Stack([dmc.Title("Holdings", order=5), render_holdings_table(portfolio, value_data)], gap="sm"),
                        span={"base": 12, "md": 7},
                    ),
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Title("Allocation", order=5),
                            dcc.Graph(figure=pie_fig, config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 5},
                    ),
                ],
                gutter="md",
            ),

            dmc.Divider(my="md"),

            # Risk analysis
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Title("Risk Contribution", order=5),
                            dcc.Graph(figure=contrib_fig, config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 6},
                    ),
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Title("Correlation Matrix", order=5),
                            dcc.Graph(figure=corr_fig, config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 6},
                    ),
                ],
                gutter="md",
            ),
        ],
        gap="sm",
    )


# ============================================================================
# STRESS TESTING TAB
# ============================================================================

@callback(
    Output("stress-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
    Input("scenario-options-store", "data"),
)
def render_stress_tab(portfolio_id, scheme, scenario_options):
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    return dmc.Stack(
        [
            dmc.Select(
                id="scenario-dropdown",
                label="Select Scenario",
                data=scenario_options or [],
                value="equity_crash" if scenario_options else None,
                w={"base": "100%", "sm": 300},
            ),
            html.Div(id="stress-results"),
        ],
        gap="md",
    )


@callback(
    Output("stress-results", "children"),
    Input("scenario-dropdown", "value"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def update_stress_results(scenario_id, portfolio_id, scheme):
    scheme = scheme or "dark"

    if not scenario_id or not portfolio_id:
        return dmc.Text("Select a scenario to view results", c="dimmed")

    result = run_stress_test(portfolio_id, scenario_id)
    if not result:
        return dmc.Text("Error loading stress results")

    # Get scenario details (result only has scenario_id and scenario_name)
    scenarios = get_stress_scenarios()
    scenario = next((s for s in scenarios if s["id"] == scenario_id), None)

    positions = result["positions"]
    total_pnl = result["total_pnl_pct"]

    # Scenario description card
    scenario_card = dmc.Card(
        [
            dmc.Title(result["scenario_name"], order=5),
            dmc.Text(scenario["description"] if scenario else "", c="dimmed", size="sm"),
            dmc.Title("Shocks by Asset Class:", order=6, mt="sm"),
            dmc.List(
                [dmc.ListItem(f"{k}: {v:+.0f}%") for k, v in scenario["shocks"].items()] if scenario else [],
                size="sm",
            ),
        ],
        withBorder=True,
        padding="md",
    )

    # Position breakdown table
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
    total_color = "red" if total_pnl < 0 else "green"

    # P&L summary
    pnl_summary = dmc.Group(
        [
            dmc.Text("Total Portfolio P&L:", fw=500),
            dmc.Text(f"{total_pnl:+.2f}%", c=total_color, fw=700, size="xl"),
        ],
        gap="sm",
    )

    return dmc.Stack(
        [
            scenario_card,
            dmc.Divider(my="md"),
            dmc.Title("Position Breakdown", order=5),
            detail_table,
            dmc.Divider(my="md"),
            pnl_summary,
        ],
        gap="md",
    )
