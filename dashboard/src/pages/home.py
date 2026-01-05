import dash
from dash import dcc, callback, Output, Input, html
import dash_mantine_components as dmc

from src.api import (
    get_portfolios,
    get_portfolio_risk,
    get_portfolio_value,
    get_performance,
    get_rolling_metrics,
    get_guidelines,
    get_esg_metrics,
    get_liquidity,
)
from src.components import (
    portfolio_card_enhanced,
    metric_cards_row,
    action_card,
    section_header,
)

dash.register_page(__name__, path="/", name="Home", title="CerberusRisk - Executive Dashboard")


def layout():
    return dmc.Stack(
        [
            # Header
            section_header("Executive Dashboard", "Real-time portfolio overview"),
            # KPI cards placeholder - will be populated by callback
            html.Div(id="home-kpi-cards"),
            dmc.Divider(),
            # Portfolio cards section
            dmc.Title("Portfolios", order=4),
            html.Div(id="home-portfolio-cards"),
            dmc.Divider(),
            # Alerts section
            dmc.Title("Alerts & Attention", order=4),
            html.Div(id="home-alerts"),
        ],
        gap="md",
    )


def _format_currency(value: float) -> str:
    """Format value as currency with appropriate suffix (K, M, B)."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.0f}K"
    else:
        return f"${value:.0f}"


def _collect_alerts(portfolios_data: list) -> list:
    """Collect and sort alerts from all portfolios."""
    alerts = []

    for data in portfolios_data:
        portfolio_name = data["portfolio"]["name"]
        portfolio_id = data["portfolio"]["id"]

        # Check guidelines
        guidelines = data.get("guidelines")
        if guidelines:
            status = guidelines.get("status", "").lower()
            if status == "breach":
                breach_count = guidelines.get("summary", {}).get("breaches", 0)
                alerts.append({
                    "title": f"{portfolio_name}: Guideline Breach",
                    "description": f"{breach_count} guideline(s) breached",
                    "severity": "high",
                    "portfolio_id": portfolio_id,
                })
            elif status == "warning":
                warning_count = guidelines.get("summary", {}).get("warnings", 0)
                alerts.append({
                    "title": f"{portfolio_name}: Guideline Warning",
                    "description": f"{warning_count} guideline(s) approaching limits",
                    "severity": "medium",
                    "portfolio_id": portfolio_id,
                })

        # Check ESG controversies
        esg = data.get("esg")
        if esg:
            flagged = esg.get("num_flagged", 0)
            if flagged > 0:
                alerts.append({
                    "title": f"{portfolio_name}: ESG Controversy",
                    "description": f"{flagged} position(s) flagged for ESG issues",
                    "severity": "medium",
                    "portfolio_id": portfolio_id,
                })

        # Check liquidity
        liquidity = data.get("liquidity")
        if liquidity:
            score = liquidity.get("portfolio_score", 1.0)
            if score < 0.5:
                alerts.append({
                    "title": f"{portfolio_name}: Low Liquidity",
                    "description": f"Portfolio liquidity score: {score:.0%}",
                    "severity": "low",
                    "portfolio_id": portfolio_id,
                })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return alerts[:5]  # Return top 5


@callback(
    [
        Output("home-kpi-cards", "children"),
        Output("home-portfolio-cards", "children"),
        Output("home-alerts", "children"),
    ],
    Input("color-scheme-store", "data"),
)
def update_dashboard(scheme):
    scheme = scheme or "dark"
    portfolios = get_portfolios()

    if not portfolios:
        return (
            dmc.Text("No portfolios found", c="dimmed"),
            dmc.Text("No portfolios found", c="dimmed"),
            dmc.Text("No alerts", c="dimmed"),
        )

    # Fetch all data for each portfolio
    portfolios_data = []
    total_aum = 0
    weighted_ytd_sum = 0
    weighted_var_sum = 0

    for p in portfolios:
        pid = p["id"]
        risk = get_portfolio_risk(pid)
        performance = get_performance(pid)
        rolling = get_rolling_metrics(pid)
        guidelines = get_guidelines(pid)
        esg = get_esg_metrics(pid)
        liquidity = get_liquidity(pid)
        value = get_portfolio_value(pid)

        # Calculate portfolio value (sum of position values)
        portfolio_value = 0
        if value and value.get("positions"):
            for pos in value["positions"]:
                weight = pos.get("weight", 0)
                # Assume $10M per portfolio as base (can be adjusted)
                portfolio_value += weight * 100000

        # Get metrics for aggregation
        port_risk = risk.get("portfolio") if risk else None
        var_95 = port_risk.get("var_95", 0) if port_risk else 0
        ytd_return = 0
        if performance and performance.get("period_returns"):
            ytd_return = performance["period_returns"].get("ytd", 0) or 0

        # Accumulate for weighted averages
        total_aum += portfolio_value
        weighted_ytd_sum += ytd_return * portfolio_value
        weighted_var_sum += var_95 * portfolio_value

        # Get drawdown series for sparkline
        drawdown_series = None
        if rolling and rolling.get("drawdown_series"):
            drawdown_series = rolling["drawdown_series"]

        portfolios_data.append({
            "portfolio": p,
            "risk": risk,
            "performance": performance,
            "drawdown_series": drawdown_series,
            "guidelines": guidelines,
            "esg": esg,
            "liquidity": liquidity,
            "value": portfolio_value,
        })

    # Calculate aggregate KPIs
    avg_ytd = weighted_ytd_sum / total_aum if total_aum > 0 else 0
    avg_var = weighted_var_sum / total_aum if total_aum > 0 else 0

    # Count compliance issues
    breach_count = sum(
        1 for d in portfolios_data
        if d.get("guidelines", {}).get("status", "").lower() == "breach"
    )
    warning_count = sum(
        1 for d in portfolios_data
        if d.get("guidelines", {}).get("status", "").lower() == "warning"
    )

    if breach_count > 0:
        compliance_text = f"{breach_count} Breach"
        compliance_color = "red"
    elif warning_count > 0:
        compliance_text = f"{warning_count} Warning"
        compliance_color = "orange"
    else:
        compliance_text = "All Clear"
        compliance_color = "green"

    # Build KPI cards
    ytd_color = "green" if avg_ytd > 0 else "red"
    var_color = "green" if avg_var < 15 else "orange" if avg_var < 25 else "red"

    kpi_cards = metric_cards_row(
        [
            ("Total AUM", _format_currency(total_aum), "violet"),
            ("Avg YTD Return", f"{avg_ytd:+.1f}%", ytd_color),
            ("Avg VaR 95%", f"{avg_var:.1f}%", var_color),
            ("Compliance", compliance_text, compliance_color),
        ],
        span={"base": 6, "sm": 3},
    )

    # Build portfolio cards
    portfolio_cards = dmc.Grid(
        [
            dmc.GridCol(
                portfolio_card_enhanced(
                    d["portfolio"],
                    d["risk"],
                    d["performance"],
                    d["drawdown_series"],
                    scheme=scheme,
                ),
                span={"base": 12, "sm": 6, "md": 4},
            )
            for d in portfolios_data
        ],
        gutter="md",
    )

    # Build alerts
    alerts = _collect_alerts(portfolios_data)
    if alerts:
        alerts_content = dmc.Stack(
            [
                action_card(
                    a["title"],
                    a["description"],
                    a["severity"],
                )
                for a in alerts
            ],
            gap="xs",
        )
    else:
        alerts_content = dmc.Paper(
            dmc.Group(
                [
                    dmc.ThemeIcon(
                        dmc.Text("✓", size="lg"),
                        color="green",
                        size="lg",
                        radius="xl",
                    ),
                    dmc.Text("No alerts - all portfolios are healthy", c="dimmed"),
                ],
                gap="sm",
            ),
            p="md",
            withBorder=True,
        )

    return kpi_cards, portfolio_cards, alerts_content
