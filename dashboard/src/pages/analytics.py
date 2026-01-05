"""Story-driven portfolio analytics dashboard.

7 tabs answering key investment questions:
0. Summary - Executive overview with key metrics
1. Portfolio - "What do I own?"
2. Performance - "How am I doing?" (vs benchmark)
3. Risk - "What could hurt me?" (vs benchmark)
4. Scenarios - "What if things go wrong?"
5. Compliance - "Am I within bounds?"
6. Actions - "What should I do?"
"""

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
    get_gips_metrics,
    get_esg_metrics,
    get_guidelines,
    refresh_portfolio_data,
)
from src.components import (
    metric_card,
    data_table,
    bar_chart,
    pie_chart,
    empty_figure,
    line_chart,
    area_chart,
    grouped_bar_chart,
    fan_chart,
    correlation_heatmap,
    benchmark_line_chart,
    waterfall_chart,
    benchmark_comparison_cards,
    compliance_banner,
    action_card,
    section_header,
    metric_cards_row,
)
from src.components.charts import CHART_COLORS

dash.register_page(__name__, path="/analytics", name="Portfolio Analytics", title="CerberusRisk - Analytics")


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
            dcc.Store(id="scenario-options-store", data=scenario_options),

            # Portfolio selector with data info and refresh button
            dmc.Group(
                [
                    dmc.Select(
                        id="portfolio-select",
                        data=portfolio_options,
                        value=str(default_id),
                        label="Portfolio",
                        w={"base": "100%", "sm": 300},
                    ),
                    dmc.Group(
                        [
                            html.Div(id="data-info-display"),
                            dmc.Tooltip(
                                dmc.ActionIcon(
                                    dmc.Text("↻", size="lg"),
                                    id="refresh-data-btn",
                                    variant="subtle",
                                    size="lg",
                                ),
                                label="Refresh market data",
                            ),
                        ],
                        gap="xs",
                        align="center",
                    ),
                ],
                align="flex-end",
                gap="lg",
            ),
            dcc.Loading(
                html.Div(id="refresh-status"),
                type="circle",
                color="#a78bfa",
            ),

            # 7 Story-Driven Tabs (Summary first)
            dmc.Tabs(
                id="analytics-tabs",
                value="summary",
                children=[
                    dmc.TabsList([
                        dmc.TabsTab("Summary", value="summary"),
                        dmc.TabsTab("Portfolio", value="portfolio"),
                        dmc.TabsTab("Performance", value="performance"),
                        dmc.TabsTab("Risk", value="risk"),
                        dmc.TabsTab("Scenarios", value="scenarios"),
                        dmc.TabsTab("Compliance", value="compliance"),
                        dmc.TabsTab("Actions", value="actions"),
                    ]),
                    dmc.TabsPanel(html.Div(id="summary-content"), value="summary", pt="md"),
                    dmc.TabsPanel(html.Div(id="portfolio-content"), value="portfolio", pt="md"),
                    dmc.TabsPanel(html.Div(id="performance-content"), value="performance", pt="md"),
                    dmc.TabsPanel(html.Div(id="risk-content"), value="risk", pt="md"),
                    dmc.TabsPanel(html.Div(id="scenarios-content"), value="scenarios", pt="md"),
                    dmc.TabsPanel(html.Div(id="compliance-content"), value="compliance", pt="md"),
                    dmc.TabsPanel(html.Div(id="actions-content"), value="actions", pt="md"),
                ],
            ),
        ],
        gap="md",
    )


@callback(
    Output("selected-portfolio-store", "data"),
    Input("portfolio-select", "value"),
)
def update_selected_portfolio(value):
    return int(value) if value else None


@callback(
    Output("data-info-display", "children"),
    Input("selected-portfolio-store", "data"),
    Input("refresh-status", "children"),  # Trigger update after refresh
)
def update_data_info(portfolio_id, _refresh_status):
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


@callback(
    Output("refresh-status", "children"),
    Input("refresh-data-btn", "n_clicks"),
    State("selected-portfolio-store", "data"),
    prevent_initial_call=True,
)
def handle_refresh(n_clicks, portfolio_id):
    if not n_clicks or not portfolio_id:
        return None
    result = refresh_portfolio_data(portfolio_id)
    if result and result.get("status") == "ok":
        tickers = result.get("tickers_refreshed", {})
        total = sum(v for v in tickers.values() if isinstance(v, int))
        return dmc.Alert(
            f"Refreshed {len(tickers)} tickers ({total} data points)",
            title="Data refreshed",
            color="green",
            withCloseButton=True,
        )
    return dmc.Alert(
        "Failed to refresh data",
        title="Error",
        color="red",
        withCloseButton=True,
    )


# ============================================================================
# TAB 0: SUMMARY - Executive Overview
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

    # Fetch all data needed for summary
    portfolio = get_portfolio_value(portfolio_id)
    perf = get_performance(portfolio_id)
    risk = get_portfolio_risk(portfolio_id)
    guidelines = get_guidelines(portfolio_id)
    esg = get_esg_metrics(portfolio_id)
    risk_contrib = get_risk_contributions(portfolio_id)

    if not portfolio:
        return dmc.Text("Portfolio not found")

    # === PORTFOLIO SECTION ===
    positions = portfolio.get("positions", [])
    total_value = 1_000_000  # Demo AUM
    cash_pos = next((p for p in positions if p["ticker"] == "CASH"), None)
    cash_pct = (cash_pos["weight"] * 100) if cash_pos and cash_pos.get("weight") else 0
    top_holding = max(positions, key=lambda p: p.get("weight", 0)) if positions else None

    portfolio_cards = metric_cards_row([
        ("AUM", f"${total_value:,.0f}", "violet"),
        ("Positions", str(len(positions)), "blue"),
        ("Cash", f"{cash_pct:.1f}%", "green" if cash_pct >= 2 else "orange"),
        ("Top Holding", f"{top_holding['ticker']}" if top_holding else "—", "blue"),
    ], span=3)

    # === PERFORMANCE SECTION ===
    perf_cards = None
    if perf:
        period = perf.get("period_returns", {})
        bench = perf.get("benchmark", {})
        ytd = period.get("ytd", 0)
        bench_ytd = bench.get("benchmark_return", 0)
        active = bench.get("active_return", 0)

        perf_cards = metric_cards_row([
            ("YTD Return", f"{ytd:+.2f}%", "green" if ytd >= 0 else "red"),
            ("Benchmark", f"{bench_ytd:+.2f}%", "gray"),
            ("Active Return", f"{active:+.2f}%", "green" if active > 0 else "red"),
            ("Sharpe", f"{perf.get('risk_adjusted', {}).get('sharpe', 0):.2f}", "blue"),
        ], span=3)

    # === RISK SECTION ===
    risk_cards = None
    if risk:
        port = risk.get("portfolio", {})
        bench = risk.get("benchmark", {})
        var_delta = port.get("var_95", 0) - bench.get("var_95", 0)

        risk_cards = metric_cards_row([
            ("VaR 95%", f"{port.get('var_95', 0):.2f}%", "orange"),
            ("Volatility", f"{port.get('volatility', 0):.2f}%", "orange"),
            ("Max Drawdown", f"{port.get('max_drawdown', 0):.2f}%", "red"),
            ("vs Bench VaR", f"{var_delta:+.2f}%", "green" if var_delta < 0 else "red"),
        ], span=3)

    # === COMPLIANCE SECTION ===
    compliance_summary = None
    if guidelines:
        status = guidelines.get("overall_status", "unknown")
        status_color = {"compliant": "green", "warning": "yellow", "breach": "red"}.get(status, "gray")
        status_icon = {"compliant": "✓", "warning": "⚠", "breach": "✗"}.get(status, "?")

        compliance_summary = metric_cards_row([
            ("Status", f"{status_icon} {status.upper()}", status_color),
            ("Compliant", str(guidelines.get("compliant_count", 0)), "green"),
            ("Warnings", str(guidelines.get("warning_count", 0)), "yellow"),
            ("Breaches", str(guidelines.get("breach_count", 0)), "red"),
        ], span=3)

    # === ACTIONS SECTION ===
    alert_count = 0
    top_alert = None

    if guidelines:
        for g in guidelines.get("guidelines", []):
            if g["status"] == "breach":
                alert_count += 1
                if not top_alert:
                    top_alert = f"Breach: {g['guideline']['name']}"
            elif g["status"] == "warning":
                alert_count += 1
                if not top_alert:
                    top_alert = f"Warning: {g['guideline']['name']}"

    if esg:
        for p in esg.get("positions", []):
            if p.get("controversy_flag"):
                alert_count += 1
                if not top_alert:
                    top_alert = f"ESG: {p['ticker']} controversy"

    actions_cards = metric_cards_row([
        ("Alerts", str(alert_count), "red" if alert_count > 0 else "green"),
        ("Top Issue", (top_alert or "None")[:25], "orange" if top_alert else "green"),
    ], span=6)

    # Build layout with clickable section headers
    def section_link(title, tab_value):
        return dmc.Anchor(
            dmc.Text(title, fw=600, className="text-primary"),
            href="#",
            id={"type": "summary-link", "tab": tab_value},
            underline="never",
        )

    return dmc.Stack(
        [
            section_header("Executive Summary", "Key metrics at a glance"),

            dmc.Text("Portfolio", fw=600, className="text-primary", size="sm"),
            portfolio_cards,

            dmc.Divider(my="sm"),

            dmc.Text("Performance", fw=600, className="text-primary", size="sm"),
            perf_cards if perf_cards else dmc.Text("Insufficient market data (need 20+ days per ticker)", c="dimmed", size="sm"),

            dmc.Divider(my="sm"),

            dmc.Text("Risk", fw=600, className="text-primary", size="sm"),
            risk_cards if risk_cards else dmc.Text("Insufficient market data (need 20+ days per ticker)", c="dimmed", size="sm"),

            dmc.Divider(my="sm"),

            dmc.Text("Compliance", fw=600, className="text-primary", size="sm"),
            compliance_summary if compliance_summary else dmc.Text("Unable to load", c="dimmed", size="sm"),

            dmc.Divider(my="sm"),

            dmc.Text("Actions Required", fw=600, className="text-primary", size="sm"),
            actions_cards,
        ],
        gap="xs",
    )


# ============================================================================
# TAB 1: PORTFOLIO - "What do I own?"
# ============================================================================


@callback(
    Output("portfolio-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_portfolio_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    portfolio = get_portfolio_value(portfolio_id)
    if not portfolio:
        return dmc.Text("Portfolio not found")

    sectors = get_sector_concentration(portfolio_id)
    risk = get_portfolio_risk(portfolio_id)

    # Calculate key metrics
    # API doesn't return total_value; use $1M AUM for demo
    positions = portfolio.get("positions", [])
    total_value = 1_000_000  # Demo portfolio base value
    cash_pos = next((p for p in positions if p["ticker"] == "CASH"), None)
    cash_pct = (cash_pos["weight"] * 100) if cash_pos and cash_pos.get("weight") else 0
    top_holding = max(positions, key=lambda p: p.get("weight", 0)) if positions else None

    # Headline cards
    headline_cards = metric_cards_row([
        ("Total Value", f"${total_value:,.0f}" if total_value else "—", "violet"),
        ("Positions", str(len(positions)), "blue"),
        ("Cash", f"{cash_pct:.1f}%", "green" if cash_pct >= 2 else "orange"),
        ("Top Holding", f"{top_holding['ticker']} ({top_holding.get('weight', 0)*100:.1f}%)" if top_holding else "—", "blue"),
    ], span=3)

    # Allocation pie chart
    labels = [p["ticker"] for p in positions if p.get("weight", 0) > 0.01]
    values = [p.get("weight", 0) * 100 for p in positions if p.get("weight", 0) > 0.01]
    pie_fig = pie_chart(labels, values, scheme=scheme)

    # Sector comparison with benchmark (if available)
    sector_fig = empty_figure(scheme=scheme)
    hhi_card = None
    if sectors and sectors.get("sectors"):
        sector_labels = [s["sector"] for s in sectors["sectors"]]
        sector_weights = [s["weight"] for s in sectors["sectors"]]

        # For now, show portfolio sectors (benchmark sectors would need API extension)
        sector_fig = bar_chart(
            sector_labels,
            sector_weights,
            text=[f"{w:.1f}%" for w in sector_weights],
            yaxis_title="Weight %",
            scheme=scheme,
        )
        # Extend Y-axis to give room for text labels above bars
        sector_fig.update_layout(yaxis=dict(range=[0, max(sector_weights) * 1.2]))

        hhi = sectors.get("hhi", 0)
        hhi_color = "green" if hhi < 2500 else "orange" if hhi < 5000 else "red"
        hhi_card = metric_card("HHI Index", f"{hhi:.0f}", hhi_color)

    # Holdings table
    holdings_headers = ["Ticker", "Name", "Weight", "Value", "Price"]
    holdings_rows = []
    for p in sorted(positions, key=lambda x: -(x.get("weight") or 0)):
        weight = p.get("weight") or 0
        position_value = weight * total_value  # Calculate from weight * AUM
        holdings_rows.append([
            p.get("ticker", "—"),
            (p.get("name") or "")[:25],
            f"{weight*100:.1f}%",
            f"${position_value:,.0f}",
            f"${p.get('price', 0):,.2f}" if p.get("price") else "—",
        ])

    return dmc.Stack(
        [
            section_header("Portfolio Overview", "What do I own?"),
            headline_cards,

            dmc.Divider(my="md"),

            dmc.Grid(
                [
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Text("Asset Allocation", fw=600, className="text-primary"),
                            dcc.Graph(figure=pie_fig, config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 5},
                    ),
                    dmc.GridCol(
                        dmc.Stack([
                            dmc.Group([
                                dmc.Text("Sector Breakdown", fw=600, className="text-primary"),
                                hhi_card,
                            ], justify="space-between") if hhi_card else dmc.Text("Sector Breakdown", fw=600, className="text-primary"),
                            dcc.Graph(figure=sector_fig, config={"displayModeBar": False}),
                        ], gap="sm"),
                        span={"base": 12, "md": 7},
                    ),
                ],
                gutter="md",
            ),

            dmc.Divider(my="md"),

            dmc.Text("Holdings", fw=600, className="text-primary"),
            data_table(holdings_headers, holdings_rows, None),
        ],
        gap="sm",
    )


# ============================================================================
# TAB 2: PERFORMANCE - "How am I doing?" (vs benchmark)
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
    gips = get_gips_metrics(portfolio_id)

    if not perf:
        return dmc.Text("Unable to load performance data", c="dimmed")

    period = perf["period_returns"]
    bench = perf["benchmark"]
    ratios = perf["risk_adjusted"]
    attrib = perf["attribution"]

    # Main comparison: Portfolio vs Benchmark
    ann_return = period.get("annualized", 0)
    bench_return = bench.get("benchmark_return", 0)

    main_comparison = benchmark_comparison_cards(
        "Annualized Return",
        ann_return,
        bench_return,
        unit="%",
        decimals=2,
    )

    # Period returns comparison chart
    periods = ["MTD", "QTD", "YTD", "1Y", "Total"]
    port_returns = [
        period.get("mtd") or 0,
        period.get("qtd") or 0,
        period.get("ytd") or 0,
        period.get("one_year") or 0,
        period.get("since_inception", 0),
    ]
    # Note: We'd need benchmark period returns from API for full comparison
    # For now, show portfolio returns
    period_fig = bar_chart(
        periods,
        port_returns,
        color=[CHART_COLORS["positive"] if v >= 0 else CHART_COLORS["negative"] for v in port_returns],
        text=[f"{v:+.2f}%" if v else "—" for v in port_returns],
        yaxis_title="Return %",
        scheme=scheme,
    )
    # Extend Y-axis for text labels
    y_min = min(port_returns) if port_returns else 0
    y_max = max(port_returns) if port_returns else 0
    period_fig.update_layout(yaxis=dict(range=[y_min * 1.2 if y_min < 0 else 0, y_max * 1.2 if y_max > 0 else 0]))

    # Benchmark metrics cards
    bench_metrics = metric_cards_row([
        ("Active Return", f"{bench['active_return']:+.2f}%", "green" if bench["active_return"] > 0 else "red"),
        ("Tracking Error", f"{bench['tracking_error']:.2f}%", "orange"),
        ("Info Ratio", f"{bench['information_ratio']:.2f}" if bench.get("information_ratio") else "—",
         "green" if bench.get("information_ratio") and bench["information_ratio"] > 0.5 else "gray"),
    ], span=4)

    # Risk-adjusted ratios
    ratios_cards = metric_cards_row([
        ("Sharpe", f"{ratios['sharpe']:.2f}", "green" if ratios["sharpe"] > 0.5 else "gray"),
        ("Sortino", f"{ratios['sortino']:.2f}", "green" if ratios["sortino"] > 0.5 else "gray"),
        ("Treynor", f"{ratios['treynor']:.2f}" if ratios.get("treynor") else "—", "blue"),
        ("Calmar", f"{ratios['calmar']:.2f}" if ratios.get("calmar") else "—", "blue"),
    ], span=3)

    # Cumulative return chart (from GIPS drawdown series)
    cumulative_fig = empty_figure(scheme=scheme)
    has_cumulative = False
    if gips and gips.get("drawdown_series"):
        # Use drawdown_series dates and reconstruct cumulative returns
        # We can derive from period_returns or use a simpler approach
        pass  # Will use rolling returns dates with cumulative calculation

    # If we have period returns, build cumulative
    if gips and gips.get("period_returns"):
        periods = gips["period_returns"]
        if len(periods) >= 3:
            has_cumulative = True
            dates = [p["period"] for p in periods]
            # Calculate cumulative from monthly returns
            port_cumulative = []
            bench_cumulative = []
            port_cum = 0
            bench_cum = 0
            for p in periods:
                port_cum += p.get("twr_gross", 0)
                bench_cum += p.get("benchmark_return", 0)
                port_cumulative.append(port_cum)
                bench_cumulative.append(bench_cum)
            cumulative_fig = benchmark_line_chart(
                dates,
                port_cumulative,
                bench_cumulative,
                portfolio_label="Portfolio",
                benchmark_label="Benchmark (SPY)",
                scheme=scheme,
                yaxis_title="Cumulative Return %",
            )

    # Rolling returns chart (from GIPS data)
    rolling_fig = empty_figure(scheme=scheme)
    has_rolling = False
    if gips and gips.get("rolling_returns"):
        rolling = gips["rolling_returns"]
        if rolling:
            has_rolling = True
            dates = [r["date"] for r in rolling]
            port_rolling = [r["rolling_12m"] for r in rolling]
            bench_rolling = [r.get("benchmark_12m") or 0 for r in rolling]
            rolling_fig = benchmark_line_chart(
                dates,
                port_rolling,
                bench_rolling,
                portfolio_label="Portfolio (12M)",
                benchmark_label="Benchmark (12M)",
                scheme=scheme,
                yaxis_title="Rolling 12M Return %",
            )

    # Attribution chart
    attrib_fig = empty_figure(scheme=scheme)
    attrib_table = None
    if attrib and attrib.get("contributions"):
        contrib = attrib["contributions"]
        tickers = [c["ticker"] for c in contrib]
        values = [c["contribution"] for c in contrib]
        attrib_fig = waterfall_chart(
            tickers,
            values,
            horizontal=True,
            scheme=scheme,
        )

        # Attribution table
        attrib_headers = ["Ticker", "Weight", "Return", "Contribution"]
        attrib_rows = [
            [c["ticker"], f"{c['weight']:.1f}%", f"{c['position_return']:+.2f}%", f"{c['contribution']:+.2f}%"]
            for c in contrib
        ]
        attrib_colors = [
            [None, None, "green" if c["position_return"] >= 0 else "red", "green" if c["contribution"] >= 0 else "red"]
            for c in contrib
        ]
        attrib_table = data_table(attrib_headers, attrib_rows, attrib_colors)

    # GIPS Section - Calendar Year Returns and Key Metrics
    gips_section = None
    if gips:
        # GIPS key metrics cards
        gips_cards = metric_cards_row([
            ("Cumulative (Gross)", f"{gips.get('cumulative_gross', 0):.2f}%", "violet"),
            ("Cumulative (Net)", f"{gips.get('cumulative_net', 0):.2f}%", "violet"),
            ("Benchmark", f"{gips.get('cumulative_benchmark', 0):.2f}%", "gray"),
            ("Max Drawdown", f"{gips.get('max_drawdown', 0):.2f}%", "red"),
        ], span=3)

        # Calendar year returns table
        cal_table = None
        if gips.get("calendar_year_returns"):
            cal_headers = ["Year", "Gross", "Net", "Benchmark", "Excess"]
            cal_rows = []
            cal_colors = []
            for yr in gips["calendar_year_returns"]:
                gross = yr.get("gross", 0)
                net = yr.get("net", 0)
                bench = yr.get("benchmark", 0)
                excess = yr.get("excess", gross - bench)
                cal_rows.append([
                    str(yr.get("year", "")),
                    f"{gross:.2f}%",
                    f"{net:.2f}%",
                    f"{bench:.2f}%",
                    f"{excess:+.2f}%",
                ])
                cal_colors.append([
                    None,
                    "green" if gross >= 0 else "red",
                    "green" if net >= 0 else "red",
                    None,
                    "green" if excess >= 0 else "red",
                ])
            cal_table = data_table(cal_headers, cal_rows, cal_colors)

        # Monthly period returns table
        monthly_table = None
        if gips.get("period_returns"):
            monthly_headers = ["Period", "Gross", "Net", "Benchmark", "Excess"]
            monthly_rows = []
            monthly_colors = []
            for pr in gips["period_returns"][-6:]:  # Last 6 months
                gross = pr.get("twr_gross", 0)
                net = pr.get("twr_net", 0)
                bench = pr.get("benchmark_return", 0)
                excess = pr.get("excess_return", gross - bench)
                monthly_rows.append([
                    pr.get("period", ""),
                    f"{gross:.2f}%",
                    f"{net:.2f}%",
                    f"{bench:.2f}%",
                    f"{excess:+.2f}%",
                ])
                monthly_colors.append([
                    None,
                    "green" if gross >= 0 else "red",
                    "green" if net >= 0 else "red",
                    None,
                    "green" if excess >= 0 else "red",
                ])
            monthly_table = data_table(monthly_headers, monthly_rows, monthly_colors)

        gips_children = [
            dmc.Text("GIPS Performance Summary", fw=600, className="text-primary"),
            dmc.Text(f"Inception: {gips.get('inception_date', 'N/A')} | Fee: {gips.get('fee_schedule', 'N/A')}", c="dimmed", size="sm"),
            gips_cards,
        ]
        if cal_table:
            gips_children.extend([
                dmc.Text("Calendar Year Returns", fw=500, size="sm", mt="md"),
                cal_table,
            ])
        if monthly_table:
            gips_children.extend([
                dmc.Text("Monthly Returns (Last 6 Months)", fw=500, size="sm", mt="md"),
                monthly_table,
            ])

        gips_section = dmc.Stack(gips_children, gap="xs")

    return dmc.Stack(
        [
            section_header("Performance vs Benchmark", "How is the portfolio performing relative to SPY?"),

            main_comparison,
            bench_metrics,

            dmc.Divider(my="md"),

            dmc.Text("Cumulative Returns", fw=600, className="text-primary"),
            dcc.Graph(figure=cumulative_fig, config={"displayModeBar": False}) if has_cumulative else dmc.Text("Insufficient data", c="dimmed"),

            dmc.Divider(my="md"),

            dmc.Text("Period Returns", fw=600, className="text-primary"),
            dcc.Graph(figure=period_fig, config={"displayModeBar": False}),

            dmc.Divider(my="md"),

            dmc.Text("Risk-Adjusted Metrics", fw=600, className="text-primary"),
            ratios_cards,

            dmc.Divider(my="md"),

            dmc.Text("Rolling 12-Month Returns", fw=600, className="text-primary"),
            dcc.Graph(figure=rolling_fig, config={"displayModeBar": False}) if has_rolling else dmc.Text("Requires 1+ year of history", c="dimmed"),

            dmc.Divider(my="md"),

            dmc.Text("Performance Attribution", fw=600, className="text-primary"),
            dmc.Text(f"Total Return: {attrib['total_return']:.2f}%" if attrib else "", c="dimmed", size="sm"),
            dmc.Grid(
                [
                    dmc.GridCol(dcc.Graph(figure=attrib_fig, config={"displayModeBar": False}), span={"base": 12, "md": 6}),
                    dmc.GridCol(attrib_table if attrib_table else html.Div(), span={"base": 12, "md": 6}),
                ],
                gutter="md",
            ),

            dmc.Divider(my="md"),

            gips_section if gips_section else dmc.Text("GIPS data unavailable", c="dimmed"),
        ],
        gap="sm",
    )


# ============================================================================
# TAB 3: RISK - "What could hurt me?" (vs benchmark)
# ============================================================================


@callback(
    Output("risk-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_risk_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    risk = get_portfolio_risk(portfolio_id)
    contributions = get_risk_contributions(portfolio_id)
    rolling = get_rolling_metrics(portfolio_id)
    tail = get_tail_risk(portfolio_id)
    mc = get_monte_carlo(portfolio_id)
    correlation = get_correlation(portfolio_id)
    beta_data = get_beta(portfolio_id)
    factors = get_factor_exposures(portfolio_id)

    if not risk:
        return dmc.Text("Unable to load risk data", c="dimmed")

    port = risk["portfolio"]
    bench = risk["benchmark"]

    # Main risk comparisons (all vs benchmark)
    var_comparison = benchmark_comparison_cards("VaR 95%", port["var_95"], bench["var_95"], "%", 2, invert=True)
    vol_comparison = benchmark_comparison_cards("Volatility", port["volatility"], bench["volatility"], "%", 2, invert=True)
    sharpe_comparison = benchmark_comparison_cards("Sharpe Ratio", port["sharpe"], bench["sharpe"], "", 2, invert=False)
    dd_comparison = benchmark_comparison_cards("Max Drawdown", port["max_drawdown"], bench["max_drawdown"], "%", 2, invert=True)

    # Risk metrics grouped bar chart
    risk_metrics = ["VaR 95%", "VaR 99%", "CVaR 95%", "Volatility"]
    port_vals = [port["var_95"], port["var_99"], port["cvar_95"], port["volatility"]]
    bench_vals = [bench["var_95"], bench["var_99"], bench["cvar_95"], bench["volatility"]]
    risk_bar_fig = grouped_bar_chart(
        risk_metrics,
        {"Portfolio": port_vals, "Benchmark": bench_vals},
        scheme=scheme,
        yaxis_title="%",
    )

    # Beta and factor cards
    beta_cards = None
    if beta_data:
        beta_cards = metric_cards_row([
            ("Beta", f"{beta_data['beta']:.2f}", "blue"),
            ("Alpha", f"{beta_data['alpha']:+.2f}%", "green" if beta_data["alpha"] > 0 else "red"),
            ("R²", f"{beta_data['r_squared']:.2f}", "blue"),
            ("Correlation", f"{beta_data['correlation']:.2f}", "blue"),
        ], span=3)

    # Risk contribution chart
    contrib_fig = empty_figure(scheme=scheme)
    if contributions:
        tickers = [c["ticker"] for c in contributions]
        pct_contrib = [c["pct_contribution"] for c in contributions]
        contrib_fig = waterfall_chart(
            tickers,
            pct_contrib,
            horizontal=True,
            scheme=scheme,
        )

    # Rolling volatility chart (portfolio vs benchmark)
    rolling_fig = empty_figure(scheme=scheme)
    drawdown_fig = empty_figure(scheme=scheme)
    if rolling:
        # Rolling volatility
        rolling_fig = line_chart(
            rolling["dates"],
            {"Portfolio Vol": rolling["rolling_volatility"]},
            scheme=scheme,
            yaxis_title="Volatility % (Annualized)",
        )
        # Drawdown
        drawdown_fig = area_chart(
            rolling["dates"],
            rolling["drawdown_series"],
            color=CHART_COLORS["negative"],
            scheme=scheme,
            yaxis_title="Drawdown %",
        )

    # Monte Carlo fan chart
    mc_fig = empty_figure(scheme=scheme)
    mc_cards = None
    if mc:
        mc_cards = metric_cards_row([
            ("MC VaR 95%", f"{mc['var_95']:.2f}%", "orange"),
            ("MC VaR 99%", f"{mc['var_99']:.2f}%", "red"),
            ("MC CVaR 95%", f"{mc['cvar_95']:.2f}%", "orange"),
            ("MC CVaR 99%", f"{mc['cvar_99']:.2f}%", "red"),
        ], span=3)

        if mc.get("fan_chart"):
            fc = mc["fan_chart"]
            mc_fig = fan_chart(
                days=fc["days"],
                percentiles={
                    "p1": fc["p1"], "p5": fc["p5"], "p25": fc["p25"],
                    "p50": fc["p50"], "p75": fc["p75"], "p95": fc["p95"], "p99": fc["p99"],
                },
                height=400,
                scheme=scheme,
            )

    # Correlation heatmap
    corr_fig = empty_figure(scheme=scheme)
    if correlation and correlation.get("matrix"):
        corr_fig = correlation_heatmap(
            correlation["matrix"],
            correlation["tickers"],
            correlation["tickers"],
            scheme=scheme,
        )

    # Tail risk table
    tail_section = None
    if tail:
        worst_headers = ["Date", "Return"]
        worst_rows = [[d["date"], f"{d['return_pct']:+.2f}%"] for d in tail["worst_days"]]
        worst_colors = [[None, "red"] for _ in tail["worst_days"]]
        best_rows = [[d["date"], f"{d['return_pct']:+.2f}%"] for d in tail["best_days"]]
        best_colors = [[None, "green"] for _ in tail["best_days"]]

        tail_section = dmc.Grid(
            [
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Text("Worst Days", fw=600, c="red"),
                        data_table(worst_headers, worst_rows, worst_colors),
                    ], gap="xs"),
                    span={"base": 12, "md": 6},
                ),
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Text("Best Days", fw=600, c="green"),
                        data_table(worst_headers, best_rows, best_colors),
                    ], gap="xs"),
                    span={"base": 12, "md": 6},
                ),
            ],
            gutter="md",
        )

    return dmc.Stack(
        [
            section_header("Risk Analysis vs Benchmark", "How does portfolio risk compare to SPY?"),

            # Main risk comparisons
            dmc.Grid([
                dmc.GridCol(var_comparison, span={"base": 12, "md": 6}),
                dmc.GridCol(vol_comparison, span={"base": 12, "md": 6}),
            ], gutter="md"),
            dmc.Grid([
                dmc.GridCol(sharpe_comparison, span={"base": 12, "md": 6}),
                dmc.GridCol(dd_comparison, span={"base": 12, "md": 6}),
            ], gutter="md"),

            dmc.Divider(my="md"),

            # Beta and factors
            dmc.Text("Market Sensitivity", fw=600, className="text-primary"),
            beta_cards if beta_cards else dmc.Text("Unable to load beta data", c="dimmed"),

            dmc.Divider(my="md"),

            # Risk metrics comparison chart
            dmc.Grid([
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Text("Risk Metrics Comparison", fw=600, className="text-primary"),
                        dcc.Graph(figure=risk_bar_fig, config={"displayModeBar": False}),
                    ], gap="xs"),
                    span={"base": 12, "md": 6},
                ),
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Text("Risk Contribution by Position", fw=600, className="text-primary"),
                        dcc.Graph(figure=contrib_fig, config={"displayModeBar": False}),
                    ], gap="xs"),
                    span={"base": 12, "md": 6},
                ),
            ], gutter="md"),

            dmc.Divider(my="md"),

            # Rolling metrics
            dmc.Grid([
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Text("Rolling Volatility", fw=600, className="text-primary"),
                        dcc.Graph(figure=rolling_fig, config={"displayModeBar": False}),
                    ], gap="xs"),
                    span={"base": 12, "md": 6},
                ),
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Text("Drawdown History", fw=600, className="text-primary"),
                        dcc.Graph(figure=drawdown_fig, config={"displayModeBar": False}),
                    ], gap="xs"),
                    span={"base": 12, "md": 6},
                ),
            ], gutter="md"),

            dmc.Divider(my="md"),

            # Monte Carlo
            dmc.Text("Monte Carlo Simulation (1-Year Horizon)", fw=600, className="text-primary"),
            mc_cards if mc_cards else dmc.Text("Unable to load Monte Carlo data", c="dimmed"),
            dcc.Graph(figure=mc_fig, config={"displayModeBar": False}),

            dmc.Divider(my="md"),

            # Correlation and tail risk
            dmc.Grid([
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Text("Position Correlations", fw=600, className="text-primary"),
                        dcc.Graph(figure=corr_fig, config={"displayModeBar": False}),
                    ], gap="xs"),
                    span={"base": 12, "md": 6},
                ),
                dmc.GridCol(
                    dmc.Stack([
                        dmc.Text("Tail Risk", fw=600, className="text-primary"),
                        tail_section if tail_section else dmc.Text("Unable to load tail risk", c="dimmed"),
                    ], gap="xs"),
                    span={"base": 12, "md": 6},
                ),
            ], gutter="md"),
        ],
        gap="sm",
    )


# ============================================================================
# TAB 4: SCENARIOS - "What if things go wrong?"
# ============================================================================


@callback(
    Output("scenarios-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
    Input("scenario-options-store", "data"),
)
def render_scenarios_tab(portfolio_id, scheme, scenario_options):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        return dmc.Text("Portfolio not found")

    return dmc.Stack(
        [
            section_header("Scenario Analysis", "How would the portfolio perform under stress?"),

            # Stress Testing Section
            dmc.Text("Stress Testing", fw=600, className="text-primary"),
            dmc.Select(
                id="scenario-dropdown",
                label="Select Scenario",
                data=scenario_options or [],
                value="equity_crash" if scenario_options else None,
                w={"base": "100%", "sm": 300},
            ),
            html.Div(id="stress-results"),

            dmc.Divider(my="lg"),

            # All scenarios comparison
            dmc.Text("Compare All Scenarios", fw=600, className="text-primary"),
            html.Div(id="all-scenarios-comparison"),

            dmc.Divider(my="lg"),

            # What-If Section
            dmc.Text("What-If Analysis", fw=600, className="text-primary"),
            dmc.Text("Adjust position weights to see risk impact", c="dimmed", size="sm"),
            _render_whatif_inputs(portfolio),
        ],
        gap="md",
    )


def _render_whatif_inputs(portfolio):
    """Render what-if weight inputs."""
    positions = portfolio.get("positions", [])
    position_inputs = []
    for pos in positions[:10]:  # Limit to top 10 for UI
        position_inputs.append(
            dmc.Grid(
                [
                    dmc.GridCol(dmc.Text(pos["ticker"], fw=500, size="sm"), span=3),
                    dmc.GridCol(dmc.Text(pos.get("name", "")[:20], c="dimmed", size="xs"), span=5),
                    dmc.GridCol(
                        dmc.NumberInput(
                            id={"type": "whatif-weight", "ticker": pos["ticker"]},
                            value=round(pos["weight"] * 100, 1),
                            min=0, max=100, step=0.1,
                            suffix="%", size="xs",
                        ),
                        span=4,
                    ),
                ],
                gutter="xs",
                align="center",
            )
        )

    return dmc.Stack([
        dmc.Card(
            dmc.Stack(position_inputs, gap="xs"),
            withBorder=True,
            padding="sm",
        ),
        dmc.Button("Analyze Impact", id="whatif-analyze-btn", color="violet", size="sm"),
        html.Div(id="whatif-results"),
    ], gap="sm")


@callback(
    Output("stress-results", "children"),
    Input("scenario-dropdown", "value"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def update_stress_results(scenario_id, portfolio_id, scheme):
    scheme = scheme or "dark"
    if not scenario_id or not portfolio_id:
        return dmc.Text("Select a scenario", c="dimmed")

    result = run_stress_test(portfolio_id, scenario_id)
    scenarios = get_stress_scenarios()

    if not result:
        return dmc.Text("Error loading stress results", c="red")

    scenario = next((s for s in scenarios if s["id"] == scenario_id), None)
    total_pnl = result["total_pnl_pct"]

    # Large P&L card
    pnl_color = "red" if total_pnl < -5 else "orange" if total_pnl < 0 else "green"
    pnl_card = dmc.Card(
        dmc.Stack([
            dmc.Text(result["scenario_name"], fw=600),
            dmc.Text(scenario["description"] if scenario else "", size="sm", c="dimmed"),
            dmc.Title(f"{total_pnl:+.2f}%", order=2, c=pnl_color),
            dmc.Text("Estimated Portfolio Impact", size="xs", c="dimmed"),
        ], gap="xs", align="center"),
        withBorder=True,
        padding="lg",
        style={"textAlign": "center"},
    )

    # Position waterfall
    positions = result["positions"]
    tickers = [p["ticker"] for p in positions]
    pnls = [p["pnl_pct"] for p in positions]
    waterfall_fig = waterfall_chart(tickers, pnls, horizontal=True, scheme=scheme)

    return dmc.Stack([
        pnl_card,
        dmc.Text("Position Breakdown", fw=600, mt="md", className="text-primary"),
        dcc.Graph(figure=waterfall_fig, config={"displayModeBar": False}),
    ], gap="sm")


@callback(
    Output("all-scenarios-comparison", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_all_scenarios(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return None

    scenarios = get_stress_scenarios()
    if not scenarios:
        return dmc.Text("No scenarios available", c="dimmed")

    # Run all scenarios
    scenario_names = []
    scenario_pnls = []
    for s in scenarios:
        result = run_stress_test(portfolio_id, s["id"])
        if result:
            scenario_names.append(s["name"])
            scenario_pnls.append(result["total_pnl_pct"])

    if not scenario_names:
        return dmc.Text("Unable to run scenarios", c="dimmed")

    colors = [CHART_COLORS["positive"] if v >= 0 else CHART_COLORS["negative"] for v in scenario_pnls]
    fig = bar_chart(
        scenario_names,
        scenario_pnls,
        color=colors,
        text=[f"{v:+.2f}%" for v in scenario_pnls],
        yaxis_title="Portfolio Impact %",
        scheme=scheme,
    )
    # Extend Y-axis for text labels
    y_min = min(scenario_pnls) if scenario_pnls else 0
    y_max = max(scenario_pnls) if scenario_pnls else 0
    fig.update_layout(yaxis=dict(range=[y_min * 1.2 if y_min < 0 else 0, y_max * 1.2 if y_max > 0 else 0]))

    return dcc.Graph(figure=fig, config={"displayModeBar": False})


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

    changes = {id_obj["ticker"]: weight / 100 for weight, id_obj in zip(weights, ids)}
    result = run_what_if(portfolio_id, changes)

    if not result:
        return dmc.Text("Unable to calculate what-if scenario", c="red")

    orig = result["original"]
    mod = result["modified"]
    delta = result["delta"]

    # Delta cards
    delta_cards = metric_cards_row([
        ("Δ VaR 95%", f"{delta['var_95']:+.2f}%", "green" if delta["var_95"] < 0 else "red"),
        ("Δ Volatility", f"{delta['volatility']:+.2f}%", "green" if delta["volatility"] < 0 else "red"),
        ("Δ Sharpe", f"{delta['sharpe']:+.2f}", "green" if delta["sharpe"] > 0 else "red"),
    ], span=4)

    # Comparison chart
    metrics = ["VaR 95%", "VaR 99%", "Volatility", "Sharpe"]
    orig_vals = [orig["var_95"], orig["var_99"], orig["volatility"], orig["sharpe"]]
    mod_vals = [mod["var_95"], mod["var_99"], mod["volatility"], mod["sharpe"]]

    fig = grouped_bar_chart(
        metrics,
        {"Original": orig_vals, "Modified": mod_vals},
        scheme=scheme,
    )

    return dmc.Stack([
        dmc.Divider(my="sm"),
        dmc.Text("Impact Analysis", fw=600, className="text-primary"),
        delta_cards,
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
    ], gap="sm")


# ============================================================================
# TAB 5: COMPLIANCE - "Am I within bounds?"
# ============================================================================


@callback(
    Output("compliance-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_compliance_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    guidelines = get_guidelines(portfolio_id)
    esg = get_esg_metrics(portfolio_id)
    gips = get_gips_metrics(portfolio_id)

    if not guidelines:
        return dmc.Text("Unable to load compliance data", c="dimmed")

    # Compliance banner
    banner = compliance_banner(
        guidelines["overall_status"],
        guidelines["compliant_count"],
        guidelines["warning_count"],
        guidelines["breach_count"],
    )

    # Summary count cards
    total_guidelines = guidelines["compliant_count"] + guidelines["warning_count"] + guidelines["breach_count"]
    summary_cards = metric_cards_row([
        ("Compliant", str(guidelines["compliant_count"]), "green"),
        ("Warning", str(guidelines["warning_count"]), "yellow"),
        ("Breach", str(guidelines["breach_count"]), "red"),
        ("Total", str(total_guidelines), "blue"),
    ], span=3)

    # Guidelines table
    status_icons = {"compliant": "✓", "warning": "⚠", "breach": "✗"}
    status_colors = {"compliant": "green", "warning": "yellow", "breach": "red"}

    guide_headers = ["Guideline", "Status", "Current", "Limit", "Headroom"]
    guide_rows = []
    guide_colors = []

    for g in guidelines["guidelines"]:
        gd = g["guideline"]
        status = g["status"]

        if gd["limit_type"] == "range":
            limit_str = f"{gd['limit_value']:.0f}%-{gd['limit_value_upper']:.0f}%"
        elif gd["limit_type"] == "max_count":
            limit_str = f"≤ {gd['limit_value']:.0f}"
        elif gd["limit_type"] == "min_weight":
            limit_str = f"≥ {gd['limit_value']:.1f}%"
        else:
            limit_str = f"≤ {gd['limit_value']:.1f}%"

        current_str = f"{g['current_value']:.0f}" if gd["limit_type"] == "max_count" else f"{g['current_value']:.1f}%"
        headroom_str = f"{g['headroom']:+.1f}%" if gd["limit_type"] != "max_count" else f"{g['headroom']:+.0f}"

        guide_rows.append([
            gd["name"],
            f"{status_icons[status]} {status.upper()}",
            current_str,
            limit_str,
            headroom_str,
        ])
        guide_colors.append([None, status_colors[status], None, None, "green" if g["headroom"] > 0 else "red"])

    # ESG section
    esg_section = None
    if esg:
        def esg_color(score):
            return "green" if score >= 70 else "yellow" if score >= 50 else "red"

        esg_cards = metric_cards_row([
            ("ESG Score", f"{esg['portfolio_esg_score']:.0f}", esg_color(esg["portfolio_esg_score"])),
            ("Environmental", f"{esg['portfolio_environmental']:.0f}", esg_color(esg["portfolio_environmental"])),
            ("Social", f"{esg['portfolio_social']:.0f}", esg_color(esg["portfolio_social"])),
            ("Governance", f"{esg['portfolio_governance']:.0f}", esg_color(esg["portfolio_governance"])),
        ], span=3)

        carbon_comparison = benchmark_comparison_cards(
            "Carbon Intensity (WACI)",
            esg["portfolio_carbon_intensity"],
            esg["benchmark_carbon_intensity"],
            unit=" tCO2e/$M",
            decimals=0,
            invert=True,
        )

        # Controversy alerts
        flagged = [p for p in esg["positions"] if p["controversy_flag"]]
        controversy_alerts = None
        if flagged:
            controversy_alerts = dmc.Alert(
                dmc.Stack([
                    dmc.Text(f"Controversy Flags ({len(flagged)})", fw=500),
                    dmc.List([
                        dmc.ListItem(f"{p['ticker']}: {p['controversy_details']}")
                        for p in flagged
                    ], size="sm"),
                ], gap="xs"),
                color="red",
                variant="light",
            )

        esg_children = [
            dmc.Text("ESG Compliance", fw=600, className="text-primary"),
            esg_cards,
            carbon_comparison,
        ]
        if controversy_alerts:
            esg_children.append(controversy_alerts)

        esg_section = dmc.Stack(esg_children, gap="sm")

    # GIPS disclosure checklist
    gips_section = None
    if gips and gips.get("disclosure_checklist"):
        checklist = gips["disclosure_checklist"]
        pass_count = sum(1 for i in checklist if isinstance(i, dict) and i.get("status") == "pass")
        total = len(checklist)

        checklist_items = []
        for item in checklist:
            if isinstance(item, dict):
                status = item.get("status", "unknown")
                color = {"pass": "green", "warning": "yellow", "fail": "red"}.get(status, "gray")
                icon = {"pass": "✓", "warning": "⚠", "fail": "✗"}.get(status, "?")
                checklist_items.append(
                    dmc.Group([
                        dmc.Badge(f"{icon}", color=color, size="sm"),
                        dmc.Text(item.get("item", ""), size="sm"),
                    ], gap="xs")
                )

        gips_section = dmc.Stack([
            dmc.Text("GIPS Readiness", fw=600, className="text-primary"),
            dmc.Text(f"{pass_count}/{total} requirements met", c="dimmed", size="sm"),
            dmc.Card(
                dmc.Stack(checklist_items, gap="xs"),
                withBorder=True,
                padding="sm",
            ),
        ], gap="sm")

    # Build children list filtering out None values
    children = [
        section_header("Compliance Status", "Are all guidelines and constraints being met?"),
        banner,
        summary_cards,
        dmc.Divider(my="md"),
        dmc.Text("Investment Guidelines", fw=600, className="text-primary"),
        data_table(guide_headers, guide_rows, guide_colors),
    ]

    if esg_section:
        children.extend([dmc.Divider(my="md"), esg_section])

    if gips_section:
        children.extend([dmc.Divider(my="md"), gips_section])

    return dmc.Stack(children, gap="sm")


# ============================================================================
# TAB 6: ACTIONS - "What should I do?"
# ============================================================================


@callback(
    Output("actions-content", "children"),
    Input("selected-portfolio-store", "data"),
    Input("color-scheme-store", "data"),
)
def render_actions_tab(portfolio_id, scheme):
    scheme = scheme or "dark"
    if not portfolio_id:
        return dmc.Text("Select a portfolio")

    # Gather data from multiple sources
    guidelines = get_guidelines(portfolio_id)
    esg = get_esg_metrics(portfolio_id)
    risk_contrib = get_risk_contributions(portfolio_id)
    perf = get_performance(portfolio_id)
    liquidity = get_liquidity(portfolio_id)

    alerts = []

    # Priority alerts from guidelines
    if guidelines:
        for g in guidelines.get("guidelines", []):
            if g["status"] == "breach":
                alerts.append(action_card(
                    f"Guideline Breach: {g['guideline']['name']}",
                    f"Current: {g['current_value']:.1f}%, Limit: {g['guideline']['limit_value']:.1f}%",
                    "high",
                ))
            elif g["status"] == "warning":
                alerts.append(action_card(
                    f"Approaching Limit: {g['guideline']['name']}",
                    f"Only {g['headroom']:.1f}% headroom remaining",
                    "medium",
                ))

    # ESG controversies
    if esg:
        for p in esg.get("positions", []):
            if p.get("controversy_flag"):
                alerts.append(action_card(
                    f"ESG Controversy: {p['ticker']}",
                    p.get("controversy_details", "Review required"),
                    "medium",
                ))

    # Low liquidity positions
    if liquidity:
        for p in liquidity.get("positions", []):
            if p.get("score", 100) < 50:
                alerts.append(action_card(
                    f"Low Liquidity: {p['ticker']}",
                    f"Liquidity score: {p['score']:.0f}/100",
                    "low",
                ))

    # Risk reduction opportunities
    risk_section = None
    if risk_contrib:
        top_contributors = sorted(risk_contrib, key=lambda x: -x["pct_contribution"])[:3]
        risk_headers = ["Ticker", "Weight", "Risk Contribution"]
        risk_rows = [
            [c["ticker"], f"{c['weight']:.1f}%", f"{c['pct_contribution']:.1f}%"]
            for c in top_contributors
        ]
        risk_colors = [[None, None, "orange"] for _ in top_contributors]
        risk_section = dmc.Stack([
            dmc.Text("Top Risk Contributors", fw=600, className="text-primary"),
            dmc.Text("Consider reducing weight to lower portfolio risk", c="dimmed", size="sm"),
            data_table(risk_headers, risk_rows, risk_colors),
        ], gap="sm")

    # Performance detractors
    perf_section = None
    if perf and perf.get("attribution", {}).get("contributions"):
        detractors = [c for c in perf["attribution"]["contributions"] if c["contribution"] < 0]
        detractors = sorted(detractors, key=lambda x: x["contribution"])[:3]
        if detractors:
            perf_headers = ["Ticker", "Return", "Contribution"]
            perf_rows = [
                [c["ticker"], f"{c['position_return']:+.2f}%", f"{c['contribution']:+.2f}%"]
                for c in detractors
            ]
            perf_colors = [[None, "red", "red"] for _ in detractors]
            perf_section = dmc.Stack([
                dmc.Text("Performance Detractors", fw=600, className="text-primary"),
                dmc.Text("Positions dragging down returns", c="dimmed", size="sm"),
                data_table(perf_headers, perf_rows, perf_colors),
            ], gap="sm")

    # Rebalancing suggestions (positions approaching limits)
    rebalance_section = None
    if guidelines:
        near_limits = [
            g for g in guidelines.get("guidelines", [])
            if g["status"] == "warning" or (g["status"] == "compliant" and abs(g["headroom"]) < 3)
        ]
        if near_limits:
            rebal_headers = ["Guideline", "Current", "Limit", "Headroom"]
            rebal_rows = []
            rebal_colors = []
            for g in near_limits[:5]:
                gd = g["guideline"]
                limit_str = f"{gd['limit_value']:.1f}%"
                if gd["limit_type"] == "range":
                    limit_str = f"{gd['limit_value']:.0f}%-{gd['limit_value_upper']:.0f}%"
                rebal_rows.append([
                    gd["name"],
                    f"{g['current_value']:.1f}%",
                    limit_str,
                    f"{g['headroom']:+.1f}%",
                ])
                rebal_colors.append([
                    None, None, None,
                    "orange" if g["headroom"] < 2 else "yellow",
                ])
            rebalance_section = dmc.Stack([
                dmc.Text("Rebalancing Suggestions", fw=600, className="text-primary"),
                dmc.Text("Positions approaching guideline limits", c="dimmed", size="sm"),
                data_table(rebal_headers, rebal_rows, rebal_colors),
            ], gap="sm")

    # No issues message
    if not alerts and not risk_section and not perf_section and not rebalance_section:
        return dmc.Stack([
            section_header("Action Items", "What needs attention?"),
            dmc.Alert(
                "No immediate actions required. Portfolio is within all guidelines.",
                color="green",
                variant="light",
            ),
        ], gap="sm")

    # Build children list filtering out None values
    children = [
        section_header("Action Items", "What needs attention?"),
    ]

    # Priority alerts
    if alerts:
        children.append(dmc.Text("Priority Alerts", fw=600, className="text-primary"))
        children.append(dmc.Stack(alerts, gap="xs"))
    else:
        children.append(dmc.Text("No alerts", c="dimmed", size="sm"))

    if risk_section:
        children.extend([dmc.Divider(my="md"), risk_section])

    if perf_section:
        children.extend([dmc.Divider(my="md"), perf_section])

    if rebalance_section:
        children.extend([dmc.Divider(my="md"), rebalance_section])

    return dmc.Stack(children, gap="sm")
