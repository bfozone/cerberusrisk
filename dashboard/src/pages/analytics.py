import dash
from dash import html, dcc, callback, Output, Input, State
import dash_mantine_components as dmc

from src.api import (
    get_portfolios,
    get_portfolio,
    get_portfolio_value,
    get_data_info,
    get_portfolio_risk,
    get_risk_contributions,
    get_correlation,
    get_stress_scenarios,
    run_stress_test,
    get_rolling_metrics,
    get_tail_risk,
    get_beta,
    get_var_backtest,
    get_sector_concentration,
    get_liquidity,
    run_what_if,
    get_monte_carlo,
    get_factor_exposures,
)
from src.components import (
    metric_card,
    data_table,
    bar_chart,
    pie_chart,
    heatmap_chart,
    empty_figure,
    line_chart,
    area_chart,
    histogram_chart,
    scatter_chart,
    grouped_bar_chart,
)
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

            # Portfolio selector with data info
            dmc.Group(
                [
                    dmc.Select(
                        id="portfolio-select",
                        data=portfolio_options,
                        value=str(default_id),
                        label="Portfolio",
                        w={"base": "100%", "sm": 300},
                    ),
                    html.Div(id="data-info-display"),
                ],
                align="flex-end",
                gap="lg",
            ),

            # Tabs
            dmc.Tabs(
                id="analytics-tabs",
                value="risk",
                children=[
                    dmc.TabsList([
                        dmc.TabsTab("Risk Metrics", value="risk"),
                        dmc.TabsTab("Stress Testing", value="stress"),
                        dmc.TabsTab("Time Series", value="timeseries"),
                        dmc.TabsTab("Distribution", value="distribution"),
                        dmc.TabsTab("Factors", value="factors"),
                        dmc.TabsTab("Concentration", value="concentration"),
                        dmc.TabsTab("What-If", value="whatif"),
                    ]),
                    dmc.TabsPanel(html.Div(id="risk-content"), value="risk", pt="md"),
                    dmc.TabsPanel(html.Div(id="stress-content"), value="stress", pt="md"),
                    dmc.TabsPanel(html.Div(id="timeseries-content"), value="timeseries", pt="md"),
                    dmc.TabsPanel(html.Div(id="distribution-content"), value="distribution", pt="md"),
                    dmc.TabsPanel(html.Div(id="factors-content"), value="factors", pt="md"),
                    dmc.TabsPanel(html.Div(id="concentration-content"), value="concentration", pt="md"),
                    dmc.TabsPanel(html.Div(id="whatif-content"), value="whatif", pt="md"),
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


# Update data info display
@callback(
    Output("data-info-display", "children"),
    Input("selected-portfolio-store", "data"),
)
def update_data_info(portfolio_id):
    if not portfolio_id:
        return None

    info = get_data_info(portfolio_id)
    if not info:
        return None

    return dmc.Text(
        f"Data: {info['start_date']} to {info['end_date']} ({info['trading_days']} trading days)",
        c="dimmed",
        size="sm",
    )


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


# ============================================================================
# TIME SERIES TAB
# ============================================================================


@callback(
    Output("timeseries-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_timeseries_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    rolling = get_rolling_metrics(portfolio_id)
    if not rolling:
        return dmc.Text("Unable to load time series data", c="dimmed")

    # Rolling VaR and Volatility chart
    rolling_fig = line_chart(
        rolling["dates"],
        {
            "Rolling VaR 95%": rolling["rolling_var_95"],
            "Rolling Volatility": rolling["rolling_volatility"],
        },
        scheme=scheme,
        yaxis_title="% (Annualized)",
    )

    # Drawdown chart
    drawdown_fig = area_chart(
        rolling["dates"],
        rolling["drawdown_series"],
        color=CHART_COLORS["negative"],
        scheme=scheme,
        yaxis_title="Drawdown %",
    )

    return dmc.Stack(
        [
            dmc.Title("Rolling Risk Metrics (20-day window)", order=5),
            dcc.Graph(figure=rolling_fig, config={"displayModeBar": False}),
            dmc.Divider(my="md"),
            dmc.Title("Drawdown History", order=5),
            dcc.Graph(figure=drawdown_fig, config={"displayModeBar": False}),
        ],
        gap="sm",
    )


# ============================================================================
# DISTRIBUTION TAB
# ============================================================================


@callback(
    Output("distribution-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_distribution_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    tail = get_tail_risk(portfolio_id)
    mc = get_monte_carlo(portfolio_id)

    if not tail:
        return dmc.Text("Unable to load distribution data", c="dimmed")

    # Tail risk cards
    tail_cards = dmc.Grid(
        [
            dmc.GridCol(metric_card("Skewness", f"{tail['skewness']:.3f}", "blue"), span={"base": 6, "sm": 3}),
            dmc.GridCol(metric_card("Kurtosis", f"{tail['kurtosis']:.3f}", "blue"), span={"base": 6, "sm": 3}),
            dmc.GridCol(metric_card("MC VaR 95%", f"{mc['var_95']}%" if mc else "—", "orange"), span={"base": 6, "sm": 3}),
            dmc.GridCol(metric_card("MC CVaR 95%", f"{mc['cvar_95']}%" if mc else "—", "red"), span={"base": 6, "sm": 3}),
        ],
        gutter="xs",
    )

    # Worst and best days tables
    worst_headers = ["Date", "Return"]
    worst_rows = [[d["date"], f"{d['return_pct']:+.2f}%"] for d in tail["worst_days"]]
    worst_colors = [[None, "red"] for _ in tail["worst_days"]]

    best_rows = [[d["date"], f"{d['return_pct']:+.2f}%"] for d in tail["best_days"]]
    best_colors = [[None, "green"] for _ in tail["best_days"]]

    # Monte Carlo histogram
    if mc:
        mc_fig = histogram_chart(
            mc["percentiles"],
            bins=5,
            var_line=mc["var_95"],
            scheme=scheme,
            xaxis_title="Simulated Return %",
        )
    else:
        mc_fig = empty_figure(scheme=scheme)

    return dmc.Stack(
        [
            dmc.Title("Tail Risk Statistics", order=5),
            tail_cards,
            dmc.Divider(my="md"),
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Stack([dmc.Title("Worst Days", order=5), data_table(worst_headers, worst_rows, worst_colors)], gap="sm"),
                        span={"base": 12, "md": 6},
                    ),
                    dmc.GridCol(
                        dmc.Stack([dmc.Title("Best Days", order=5), data_table(worst_headers, best_rows, best_colors)], gap="sm"),
                        span={"base": 12, "md": 6},
                    ),
                ],
                gutter="md",
            ),
            dmc.Divider(my="md"),
            dmc.Title("Monte Carlo Simulation (10,000 runs)", order=5),
            dmc.Text("Distribution percentiles: 5th, 25th, 50th, 75th, 95th", c="dimmed", size="sm"),
            dcc.Graph(figure=mc_fig, config={"displayModeBar": False}),
        ],
        gap="sm",
    )


# ============================================================================
# FACTORS TAB
# ============================================================================


@callback(
    Output("factors-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_factors_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    beta_data = get_beta(portfolio_id)
    factors = get_factor_exposures(portfolio_id)
    backtest = get_var_backtest(portfolio_id)

    # Beta cards
    if beta_data:
        beta_cards = dmc.Grid(
            [
                dmc.GridCol(metric_card("Market Beta", f"{beta_data['beta']:.2f}", "blue"), span={"base": 6, "sm": 3}),
                dmc.GridCol(metric_card("Alpha", f"{beta_data['alpha']:+.2f}%", "green" if beta_data["alpha"] > 0 else "red"), span={"base": 6, "sm": 3}),
                dmc.GridCol(metric_card("R²", f"{beta_data['r_squared']:.2f}", "blue"), span={"base": 6, "sm": 3}),
                dmc.GridCol(metric_card("Correlation", f"{beta_data['correlation']:.2f}", "blue"), span={"base": 6, "sm": 3}),
            ],
            gutter="xs",
        )
    else:
        beta_cards = dmc.Text("Unable to load beta data", c="dimmed")

    # Factor exposures chart
    if factors:
        factor_fig = bar_chart(
            ["Market (SPY)", "Size (IWM)", "Value (IVE)"],
            [factors["market_beta"], factors["size_beta"], factors["value_beta"]],
            color=[CHART_COLORS["primary"], CHART_COLORS["secondary"], CHART_COLORS["warning"]],
            text=[f"{factors['market_beta']:.2f}", f"{factors['size_beta']:.2f}", f"{factors['value_beta']:.2f}"],
            scheme=scheme,
            yaxis_title="Factor Beta",
        )
        factor_r2 = f"R² = {factors['r_squared']:.2f}"
        factor_error = None
    else:
        factor_fig = empty_figure(scheme=scheme)
        factor_r2 = ""
        factor_error = dmc.Text("Unable to load factor data (ETF data unavailable)", c="dimmed", size="sm")

    # VaR backtest chart
    if backtest:
        backtest_fig = line_chart(
            backtest["dates"],
            {
                "Predicted VaR (-)": [-v for v in backtest["predicted_var"]],
                "Realized Return": backtest["realized_returns"],
            },
            scheme=scheme,
            yaxis_title="Return %",
        )
        breach_text = f"Breaches: {backtest['breaches']} ({backtest['breach_rate']:.1f}% vs expected 5%)"
    else:
        backtest_fig = empty_figure(scheme=scheme)
        breach_text = ""

    return dmc.Stack(
        [
            dmc.Title("Market Beta vs SPY", order=5),
            beta_cards,
            dmc.Divider(my="md"),
            dmc.Title("Factor Exposures", order=5),
            dmc.Text(factor_r2, c="dimmed", size="sm") if factor_r2 else factor_error,
            dcc.Graph(figure=factor_fig, config={"displayModeBar": False}) if factors else None,
            dmc.Divider(my="md"),
            dmc.Title("VaR Backtest (60-day rolling)", order=5),
            dmc.Text(breach_text, c="dimmed", size="sm") if breach_text else None,
            dcc.Graph(figure=backtest_fig, config={"displayModeBar": False}),
        ],
        gap="sm",
    )


# ============================================================================
# CONCENTRATION TAB
# ============================================================================


@callback(
    Output("concentration-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_concentration_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    sectors = get_sector_concentration(portfolio_id)
    liquidity = get_liquidity(portfolio_id)

    # Sector concentration
    if sectors:
        sector_labels = [s["sector"] for s in sectors["sectors"]]
        sector_values = [s["weight"] for s in sectors["sectors"]]
        sector_fig = pie_chart(sector_labels, sector_values, scheme=scheme)
        hhi_color = "green" if sectors["hhi"] < 2500 else "orange" if sectors["hhi"] < 5000 else "red"
        hhi_card = metric_card("HHI Index", f"{sectors['hhi']:.0f}", hhi_color)
    else:
        sector_fig = empty_figure(scheme=scheme)
        hhi_card = dmc.Text("Unable to load sector data", c="dimmed")

    # Liquidity scores
    if liquidity:
        liq_tickers = [p["ticker"] for p in liquidity["positions"]]
        liq_scores = [p["score"] for p in liquidity["positions"]]
        liq_colors = [CHART_COLORS["positive"] if s >= 80 else CHART_COLORS["warning"] if s >= 50 else CHART_COLORS["negative"] for s in liq_scores]
        liq_fig = bar_chart(
            liq_tickers,
            liq_scores,
            color=liq_colors,
            text=[f"{s:.0f}" for s in liq_scores],
            scheme=scheme,
            yaxis_title="Liquidity Score (0-100)",
        )
        weighted_card = metric_card("Weighted Score", f"{liquidity['weighted_score']:.0f}", "blue")

        # Liquidity details table
        liq_headers = ["Ticker", "Avg Volume", "$ Volume", "Days to Liq.", "Score"]
        liq_rows = [
            [
                p["ticker"],
                f"{p['avg_volume']:,.0f}",
                f"${p['avg_dollar_volume']:,.0f}",
                f"{p['days_to_liquidate']:.1f}",
                f"{p['score']:.0f}",
            ]
            for p in liquidity["positions"]
        ]
        liq_colors_table = [[None, None, None, None, "green" if p["score"] >= 80 else "orange" if p["score"] >= 50 else "red"] for p in liquidity["positions"]]
    else:
        liq_fig = empty_figure(scheme=scheme)
        weighted_card = dmc.Text("Unable to load liquidity data", c="dimmed")
        liq_headers, liq_rows, liq_colors_table = [], [], []

    return dmc.Stack(
        [
            dmc.Title("Sector Concentration", order=5),
            dmc.Grid(
                [
                    dmc.GridCol(dcc.Graph(figure=sector_fig, config={"displayModeBar": False}), span={"base": 12, "md": 8}),
                    dmc.GridCol(hhi_card, span={"base": 12, "md": 4}),
                ],
                gutter="md",
            ),
            dmc.Divider(my="md"),
            dmc.Title("Liquidity Analysis", order=5),
            dmc.Grid(
                [
                    dmc.GridCol(dcc.Graph(figure=liq_fig, config={"displayModeBar": False}), span={"base": 12, "md": 8}),
                    dmc.GridCol(weighted_card, span={"base": 12, "md": 4}),
                ],
                gutter="md",
            ),
            data_table(liq_headers, liq_rows, liq_colors_table) if liq_rows else None,
        ],
        gap="sm",
    )


# ============================================================================
# WHAT-IF TAB
# ============================================================================


@callback(
    Output("whatif-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_whatif_tab(portfolio_id, scheme):
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        return dmc.Text("Portfolio not found")

    positions = portfolio["positions"]

    # Create input fields for each position
    position_inputs = []
    for pos in positions:
        position_inputs.append(
            dmc.Grid(
                [
                    dmc.GridCol(dmc.Text(pos["ticker"], fw=500), span=3),
                    dmc.GridCol(dmc.Text(pos["name"], c="dimmed", size="sm"), span=5),
                    dmc.GridCol(
                        dmc.NumberInput(
                            id={"type": "whatif-weight", "ticker": pos["ticker"]},
                            value=round(pos["weight"] * 100, 1),
                            min=0,
                            max=100,
                            step=0.1,
                            suffix="%",
                            size="sm",
                        ),
                        span=4,
                    ),
                ],
                gutter="xs",
                align="center",
            )
        )

    return dmc.Stack(
        [
            dmc.Title("Modify Position Weights", order=5),
            dmc.Text("Adjust weights below and click 'Analyze' to see the impact on risk metrics.", c="dimmed", size="sm"),
            dmc.Card(
                dmc.Stack(position_inputs, gap="xs"),
                withBorder=True,
                padding="md",
            ),
            dmc.Button("Analyze Impact", id="whatif-analyze-btn", color="violet"),
            html.Div(id="whatif-results"),
        ],
        gap="md",
    )


@callback(
    Output("whatif-results", "children"),
    Input("whatif-analyze-btn", "n_clicks"),
    State("selected-portfolio-store", "data"),
    State({"type": "whatif-weight", "ticker": dash.ALL}, "value"),
    State({"type": "whatif-weight", "ticker": dash.ALL}, "id"),
    State("color-scheme-store", "data"),
    prevent_initial_call=True,
)
def analyze_whatif(n_clicks, portfolio_id, weights, ids, scheme):
    scheme = scheme or "dark"
    if not n_clicks or not portfolio_id:
        return None

    # Build changes dict
    changes = {}
    for weight, id_obj in zip(weights, ids):
        ticker = id_obj["ticker"]
        changes[ticker] = weight / 100  # Convert from percentage

    result = run_what_if(portfolio_id, changes)
    if not result:
        return dmc.Text("Unable to calculate what-if scenario", c="red")

    orig = result["original"]
    mod = result["modified"]
    delta = result["delta"]

    # Comparison chart
    metrics = ["VaR 95%", "VaR 99%", "CVaR 95%", "Volatility", "Max DD"]
    orig_vals = [orig["var_95"], orig["var_99"], orig["cvar_95"], orig["volatility"], orig["max_drawdown"]]
    mod_vals = [mod["var_95"], mod["var_99"], mod["cvar_95"], mod["volatility"], mod["max_drawdown"]]

    comparison_fig = grouped_bar_chart(
        metrics,
        {"Original": orig_vals, "Modified": mod_vals},
        scheme=scheme,
        yaxis_title="%",
    )

    # Delta cards
    delta_cards = dmc.Grid(
        [
            dmc.GridCol(
                metric_card("Δ VaR 95%", f"{delta['var_95']:+.2f}%", "green" if delta["var_95"] < 0 else "red"),
                span={"base": 6, "sm": 4},
            ),
            dmc.GridCol(
                metric_card("Δ Volatility", f"{delta['volatility']:+.2f}%", "green" if delta["volatility"] < 0 else "red"),
                span={"base": 6, "sm": 4},
            ),
            dmc.GridCol(
                metric_card("Δ Sharpe", f"{delta['sharpe']:+.2f}", "green" if delta["sharpe"] > 0 else "red"),
                span={"base": 6, "sm": 4},
            ),
        ],
        gutter="xs",
    )

    return dmc.Stack(
        [
            dmc.Divider(my="md"),
            dmc.Title("Impact Analysis", order=5),
            delta_cards,
            dmc.Divider(my="md"),
            dmc.Title("Before vs After Comparison", order=5),
            dcc.Graph(figure=comparison_fig, config={"displayModeBar": False}),
        ],
        gap="sm",
    )
