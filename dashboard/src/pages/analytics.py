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
    get_performance,
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


# ============================================================================
# HELPER COMPONENTS (DRY)
# ============================================================================


def metric_cards_row(metrics: list[tuple[str, str, str]], span: int = 2) -> dmc.Grid:
    """Render a row of metric cards. Each tuple: (name, value, color)."""
    return dmc.Grid(
        [dmc.GridCol(metric_card(n, v, c), span={"base": 6, "sm": span}) for n, v, c in metrics],
        gutter="xs",
    )


def comparison_row(
    portfolio_val: float,
    benchmark_val: float | None,
    label: str,
    unit: str = "%",
    invert_delta: bool = False,
) -> dmc.Grid:
    """Render portfolio vs benchmark comparison cards."""
    if benchmark_val is not None:
        delta = portfolio_val - benchmark_val
        # For metrics like VaR where lower is better, invert the color logic
        delta_color = "green" if (delta < 0 if invert_delta else delta > 0) else "red"
        return dmc.Grid(
            [
                dmc.GridCol(metric_card(f"Portfolio", f"{portfolio_val}{unit}", "blue"), span={"base": 6, "sm": 4}),
                dmc.GridCol(metric_card(f"Benchmark", f"{benchmark_val}{unit}", "gray"), span={"base": 6, "sm": 4}),
                dmc.GridCol(metric_card("Delta", f"{delta:+.2f}{unit}", delta_color), span={"base": 6, "sm": 4}),
            ],
            gutter="xs",
        )
    else:
        return dmc.Grid(
            [dmc.GridCol(metric_card(label, f"{portfolio_val}{unit}", "blue"), span=12)],
            gutter="xs",
        )


# ============================================================================
# LAYOUT
# ============================================================================


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

            # 7 Tabs
            dmc.Tabs(
                id="analytics-tabs",
                value="summary",
                children=[
                    dmc.TabsList([
                        dmc.TabsTab("Summary", value="summary"),
                        dmc.TabsTab("Performance", value="performance"),
                        dmc.TabsTab("Market Risk", value="market-risk"),
                        dmc.TabsTab("Factors", value="factors"),
                        dmc.TabsTab("Concentration", value="concentration"),
                        dmc.TabsTab("Stress Testing", value="stress"),
                        dmc.TabsTab("What-If", value="whatif"),
                    ]),
                    dmc.TabsPanel(html.Div(id="summary-content"), value="summary", pt="md"),
                    dmc.TabsPanel(html.Div(id="performance-content"), value="performance", pt="md"),
                    dmc.TabsPanel(html.Div(id="market-risk-content"), value="market-risk", pt="md"),
                    dmc.TabsPanel(html.Div(id="factors-content"), value="factors", pt="md"),
                    dmc.TabsPanel(html.Div(id="concentration-content"), value="concentration", pt="md"),
                    dmc.TabsPanel(html.Div(id="stress-content"), value="stress", pt="md"),
                    dmc.TabsPanel(html.Div(id="whatif-content"), value="whatif", pt="md"),
                ],
            ),

            # Hidden stores
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
# SUMMARY TAB (NEW)
# ============================================================================


@callback(
    Output("summary-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_summary_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        return dmc.Text("Portfolio not found")

    risk = get_portfolio_risk(portfolio_id)
    perf = get_performance(portfolio_id)
    beta_data = get_beta(portfolio_id)

    # Extract portfolio and benchmark risk metrics
    port_risk = risk["portfolio"] if risk else None
    bench_risk = risk["benchmark"] if risk else None

    # 6 headline KPIs
    kpi_metrics = []
    if perf:
        period = perf["period_returns"]
        ytd_color = "green" if period["ytd"] and period["ytd"] > 0 else "red" if period["ytd"] else "gray"
        ann_color = "green" if period["annualized"] > 0 else "red"
        kpi_metrics.extend([
            ("YTD Return", f"{period['ytd']}%" if period["ytd"] is not None else "—", ytd_color),
            ("Annualized", f"{period['annualized']}%", ann_color),
        ])
    if port_risk:
        sharpe_color = "green" if port_risk["sharpe"] > 0.5 else "gray"
        kpi_metrics.extend([
            ("Sharpe", f"{port_risk['sharpe']}", sharpe_color),
            ("VaR 95%", f"{port_risk['var_95']}%", "orange"),
            ("Volatility", f"{port_risk['volatility']}%", "blue"),
            ("Max DD", f"{port_risk['max_drawdown']}%", "red"),
        ])

    kpi_cards = metric_cards_row(kpi_metrics, span=2) if kpi_metrics else dmc.Text("Loading...", c="dimmed")

    # Allocation pie
    labels = [p["ticker"] for p in portfolio["positions"]]
    values = [p["weight"] for p in portfolio["positions"]]
    pie_fig = pie_chart(labels, values, scheme=scheme)

    # Benchmark comparison section
    bench_section = []
    if perf:
        bench = perf["benchmark"]
        active_color = "green" if bench["active_return"] > 0 else "red"
        bench_section.extend([
            dmc.Text(f"Portfolio: {bench['portfolio_return']:+.2f}%", fw=500),
            dmc.Text(f"Benchmark (SPY): {bench['benchmark_return']:+.2f}%", c="dimmed"),
            dmc.Text(f"Active Return: {bench['active_return']:+.2f}%", c=active_color, fw=500),
        ])

    # Risk comparison
    risk_section = []
    if port_risk and bench_risk:
        risk_section.extend([
            dmc.Text(f"Vol: {port_risk['volatility']}% vs {bench_risk['volatility']}%", size="sm"),
            dmc.Text(f"Sharpe: {port_risk['sharpe']} vs {bench_risk['sharpe']}", size="sm"),
            dmc.Text(f"Max DD: {port_risk['max_drawdown']}% vs {bench_risk['max_drawdown']}%", size="sm"),
        ])
    if beta_data:
        risk_section.append(dmc.Text(f"Beta: {beta_data['beta']}", size="sm"))

    return dmc.Stack(
        [
            # Portfolio header
            dmc.Title(portfolio["name"], order=3),
            dmc.Text(
                f"{len(portfolio['positions'])} positions | {portfolio['description']}",
                c="dimmed",
            ),

            # Headline KPIs
            dmc.Title("Key Metrics", order=5, mt="md"),
            kpi_cards,

            dmc.Divider(my="md"),

            # Two-column layout
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Stack(
                            [
                                dmc.Title("Allocation", order=5),
                                dcc.Graph(figure=pie_fig, config={"displayModeBar": False}),
                            ],
                            gap="sm",
                        ),
                        span={"base": 12, "md": 6},
                    ),
                    dmc.GridCol(
                        dmc.Stack(
                            [
                                dmc.Title("vs Benchmark (SPY)", order=5),
                                dmc.Stack(bench_section, gap="xs") if bench_section else None,
                                dmc.Divider(my="sm"),
                                dmc.Title("Risk Comparison", order=6),
                                dmc.Stack(risk_section, gap="xs") if risk_section else None,
                            ],
                            gap="sm",
                        ),
                        span={"base": 12, "md": 6},
                    ),
                ],
                gutter="md",
            ),
        ],
        gap="sm",
    )


# ============================================================================
# PERFORMANCE TAB
# ============================================================================


@callback(
    Output("performance-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_performance_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    perf = get_performance(portfolio_id)
    if not perf:
        return dmc.Text("Unable to load performance data", c="dimmed")

    period = perf["period_returns"]
    bench = perf["benchmark"]
    ratios = perf["risk_adjusted"]
    attrib = perf["attribution"]

    # Period returns cards
    period_cards = metric_cards_row([
        ("MTD", f"{period['mtd']}%" if period["mtd"] is not None else "—", "blue"),
        ("QTD", f"{period['qtd']}%" if period["qtd"] is not None else "—", "blue"),
        ("YTD", f"{period['ytd']}%" if period["ytd"] is not None else "—", "blue"),
        ("1 Year", f"{period['one_year']}%" if period["one_year"] is not None else "—", "blue"),
        ("Total", f"{period['since_inception']}%", "green" if period["since_inception"] > 0 else "red"),
        ("Annualized", f"{period['annualized']}%", "green" if period["annualized"] > 0 else "red"),
    ], span=2)

    # Benchmark comparison cards
    active_color = "green" if bench["active_return"] > 0 else "red"
    ir_color = "green" if bench["information_ratio"] and bench["information_ratio"] > 0.5 else "gray"
    bench_cards = metric_cards_row([
        ("Portfolio", f"{bench['portfolio_return']}%", "blue"),
        ("Benchmark (SPY)", f"{bench['benchmark_return']}%", "gray"),
        ("Active Return", f"{bench['active_return']:+.2f}%", active_color),
        ("Tracking Error", f"{bench['tracking_error']}%", "orange"),
        ("Info Ratio", f"{bench['information_ratio']}" if bench["information_ratio"] else "—", ir_color),
    ], span=2)

    # Risk-adjusted ratios cards
    ratios_cards = metric_cards_row([
        ("Sharpe", f"{ratios['sharpe']}", "green" if ratios["sharpe"] > 0.5 else "gray"),
        ("Sortino", f"{ratios['sortino']}", "green" if ratios["sortino"] > 0.5 else "gray"),
        ("Treynor", f"{ratios['treynor']}" if ratios["treynor"] else "—", "blue"),
        ("Calmar", f"{ratios['calmar']}" if ratios["calmar"] else "—", "blue"),
    ], span=3)

    # Attribution chart
    if attrib["contributions"]:
        contrib_tickers = [c["ticker"] for c in attrib["contributions"]]
        contrib_values = [c["contribution"] for c in attrib["contributions"]]
        contrib_colors = [CHART_COLORS["positive"] if v >= 0 else CHART_COLORS["negative"] for v in contrib_values]
        contrib_fig = bar_chart(
            contrib_tickers,
            contrib_values,
            color=contrib_colors,
            text=[f"{v:+.2f}%" for v in contrib_values],
            yaxis_title="Contribution to Return (%)",
            scheme=scheme,
        )

        # Attribution table
        attrib_headers = ["Ticker", "Weight", "Return", "Contribution", "% of Total"]
        attrib_rows = [
            [c["ticker"], f"{c['weight']}%", f"{c['position_return']:+.2f}%", f"{c['contribution']:+.2f}%", f"{c['pct_of_total']}%"]
            for c in attrib["contributions"]
        ]
        attrib_colors = [
            [None, None, "green" if c["position_return"] >= 0 else "red", "green" if c["contribution"] >= 0 else "red", None]
            for c in attrib["contributions"]
        ]
    else:
        contrib_fig = empty_figure(scheme=scheme)
        attrib_headers, attrib_rows, attrib_colors = [], [], []

    return dmc.Stack(
        [
            dmc.Title("Period Returns", order=5),
            period_cards,
            dmc.Divider(my="md"),
            dmc.Title("Benchmark Comparison (vs SPY)", order=5),
            bench_cards,
            dmc.Divider(my="md"),
            dmc.Title("Risk-Adjusted Ratios", order=5),
            ratios_cards,
            dmc.Divider(my="md"),
            dmc.Title("Performance Attribution", order=5),
            dmc.Text(f"Total Portfolio Return: {attrib['total_return']}%", fw=500),
            dmc.Grid(
                [
                    dmc.GridCol(
                        dcc.Graph(figure=contrib_fig, config={"displayModeBar": False}),
                        span={"base": 12, "md": 6},
                    ),
                    dmc.GridCol(
                        data_table(attrib_headers, attrib_rows, attrib_colors) if attrib_rows else None,
                        span={"base": 12, "md": 6},
                    ),
                ],
                gutter="md",
            ),
        ],
        gap="sm",
    )


# ============================================================================
# MARKET RISK TAB (MERGED)
# ============================================================================


@callback(
    Output("market-risk-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_market_risk_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    portfolio = get_portfolio(portfolio_id)
    risk = get_portfolio_risk(portfolio_id)
    contributions = get_risk_contributions(portfolio_id)
    correlation = get_correlation(portfolio_id)
    rolling = get_rolling_metrics(portfolio_id)
    tail = get_tail_risk(portfolio_id)
    mc = get_monte_carlo(portfolio_id)
    backtest = get_var_backtest(portfolio_id)

    # Extract portfolio and benchmark risk
    port_risk = risk["portfolio"] if risk else None
    bench_risk = risk["benchmark"] if risk else None

    # Risk comparison cards
    if port_risk and bench_risk:
        risk_cards = dmc.Stack([
            dmc.Title("VaR 95%", order=6),
            comparison_row(port_risk["var_95"], bench_risk["var_95"], "VaR 95%", "%", invert_delta=True),
            dmc.Title("Volatility", order=6, mt="sm"),
            comparison_row(port_risk["volatility"], bench_risk["volatility"], "Volatility", "%", invert_delta=True),
            dmc.Title("Sharpe Ratio", order=6, mt="sm"),
            comparison_row(port_risk["sharpe"], bench_risk["sharpe"], "Sharpe", "", invert_delta=False),
        ], gap="xs")
    elif port_risk:
        risk_cards = metric_cards_row([
            ("VaR 95%", f"{port_risk['var_95']}%", "orange"),
            ("VaR 99%", f"{port_risk['var_99']}%", "red"),
            ("CVaR 95%", f"{port_risk['cvar_95']}%", "orange"),
            ("Volatility", f"{port_risk['volatility']}%", "blue"),
            ("Sharpe", f"{port_risk['sharpe']}", "green" if port_risk["sharpe"] > 0.5 else "gray"),
            ("Max DD", f"{port_risk['max_drawdown']}%", "red"),
        ], span=2)
    else:
        risk_cards = dmc.Text("Unable to load risk metrics", c="dimmed")

    # Rolling metrics charts
    if rolling:
        rolling_fig = line_chart(
            rolling["dates"],
            {
                "Rolling VaR 95%": rolling["rolling_var_95"],
                "Rolling Volatility": rolling["rolling_volatility"],
            },
            scheme=scheme,
            yaxis_title="% (Annualized)",
        )
        drawdown_fig = area_chart(
            rolling["dates"],
            rolling["drawdown_series"],
            color=CHART_COLORS["negative"],
            scheme=scheme,
            yaxis_title="Drawdown %",
        )
    else:
        rolling_fig = empty_figure(scheme=scheme)
        drawdown_fig = empty_figure(scheme=scheme)

    # Tail risk cards
    tail_cards = None
    worst_table = None
    best_table = None
    if tail:
        tail_cards = metric_cards_row([
            ("Skewness", f"{tail['skewness']:.3f}", "blue"),
            ("Kurtosis", f"{tail['kurtosis']:.3f}", "blue"),
            ("MC VaR 95%", f"{mc['var_95']}%" if mc else "—", "orange"),
            ("MC CVaR 95%", f"{mc['cvar_95']}%" if mc else "—", "red"),
        ], span=3)

        worst_headers = ["Date", "Return"]
        worst_rows = [[d["date"], f"{d['return_pct']:+.2f}%"] for d in tail["worst_days"]]
        worst_colors = [[None, "red"] for _ in tail["worst_days"]]
        worst_table = data_table(worst_headers, worst_rows, worst_colors)

        best_rows = [[d["date"], f"{d['return_pct']:+.2f}%"] for d in tail["best_days"]]
        best_colors = [[None, "green"] for _ in tail["best_days"]]
        best_table = data_table(worst_headers, best_rows, best_colors)

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

    # Contribution chart
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
        contrib_fig = empty_figure(scheme=scheme)

    # Correlation heatmap
    if correlation and correlation["matrix"]:
        corr_fig = heatmap_chart(
            correlation["matrix"],
            correlation["tickers"],
            correlation["tickers"],
            scheme=scheme,
        )
    else:
        corr_fig = empty_figure(scheme=scheme)

    return dmc.Stack(
        [
            # Risk metrics comparison
            dmc.Title("Risk Metrics (Portfolio vs Benchmark)", order=5),
            risk_cards,

            dmc.Divider(my="md"),

            # Rolling metrics
            dmc.Title("Rolling Risk Metrics (20-day window)", order=5),
            dcc.Graph(figure=rolling_fig, config={"displayModeBar": False}),
            dmc.Title("Drawdown History", order=5, mt="md"),
            dcc.Graph(figure=drawdown_fig, config={"displayModeBar": False}),

            dmc.Divider(my="md"),

            # Tail risk and Monte Carlo
            dmc.Title("Tail Risk & Monte Carlo", order=5),
            tail_cards if tail_cards else dmc.Text("Unable to load tail risk", c="dimmed"),
            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Stack([dmc.Title("Worst Days", order=6), worst_table], gap="sm") if worst_table else None,
                        span={"base": 12, "md": 4},
                    ),
                    dmc.GridCol(
                        dmc.Stack([dmc.Title("Best Days", order=6), best_table], gap="sm") if best_table else None,
                        span={"base": 12, "md": 4},
                    ),
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Title("Monte Carlo (10k sims)", order=6),
                            dcc.Graph(figure=mc_fig, config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 4},
                    ),
                ],
                gutter="md",
            ),

            dmc.Divider(my="md"),

            # VaR backtest
            dmc.Title("VaR Backtest (60-day rolling)", order=5),
            dmc.Text(breach_text, c="dimmed", size="sm") if breach_text else None,
            dcc.Graph(figure=backtest_fig, config={"displayModeBar": False}),

            dmc.Divider(my="md"),

            # Risk contribution and correlation
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

    # Beta cards
    if beta_data:
        beta_cards = metric_cards_row([
            ("Market Beta", f"{beta_data['beta']:.2f}", "blue"),
            ("Alpha", f"{beta_data['alpha']:+.2f}%", "green" if beta_data["alpha"] > 0 else "red"),
            ("R²", f"{beta_data['r_squared']:.2f}", "blue"),
            ("Correlation", f"{beta_data['correlation']:.2f}", "blue"),
        ], span=3)
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
    else:
        factor_fig = empty_figure(scheme=scheme)
        factor_r2 = ""

    return dmc.Stack(
        [
            dmc.Title("Market Beta vs SPY", order=5),
            beta_cards,
            dmc.Divider(my="md"),
            dmc.Title("Factor Exposures", order=5),
            dmc.Text(factor_r2, c="dimmed", size="sm") if factor_r2 else None,
            dcc.Graph(figure=factor_fig, config={"displayModeBar": False}) if factors else None,
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

    # Get scenario details
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
    delta_cards = metric_cards_row([
        ("Δ VaR 95%", f"{delta['var_95']:+.2f}%", "green" if delta["var_95"] < 0 else "red"),
        ("Δ Volatility", f"{delta['volatility']:+.2f}%", "green" if delta["volatility"] < 0 else "red"),
        ("Δ Sharpe", f"{delta['sharpe']:+.2f}", "green" if delta["sharpe"] > 0 else "red"),
    ], span=4)

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
