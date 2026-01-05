"""Benchmark comparison components for story-driven dashboard.

Provides reusable components for displaying portfolio vs benchmark metrics
with consistent styling and color-coded deltas.
"""

import dash_mantine_components as dmc
from dash import html

from src.components.cards import metric_card


def benchmark_comparison_cards(
    label: str,
    portfolio_val: float,
    benchmark_val: float | None,
    unit: str = "%",
    decimals: int = 2,
    invert: bool = False,
) -> dmc.Grid:
    """Three-card row showing Portfolio | Benchmark | Delta.

    Args:
        label: Metric name displayed on portfolio card
        portfolio_val: Portfolio metric value
        benchmark_val: Benchmark metric value (None for single card)
        unit: Unit suffix (default "%")
        decimals: Decimal places for formatting
        invert: If True, negative delta is green (for metrics like VaR where lower is better)

    Returns:
        Grid with 3 cards (or 1 if no benchmark)
    """
    fmt = f"{{:.{decimals}f}}{unit}"

    if benchmark_val is not None:
        delta = portfolio_val - benchmark_val
        # For inverted metrics (VaR, drawdown), lower portfolio value is better
        delta_color = "green" if (delta < 0 if invert else delta > 0) else "red"

        return dmc.Grid(
            [
                dmc.GridCol(
                    metric_card(label, fmt.format(portfolio_val), "violet"),
                    span={"base": 12, "sm": 4},
                ),
                dmc.GridCol(
                    metric_card("Benchmark", fmt.format(benchmark_val), "gray"),
                    span={"base": 6, "sm": 4},
                ),
                dmc.GridCol(
                    metric_card("vs Bench", f"{delta:+.{decimals}f}{unit}", delta_color),
                    span={"base": 6, "sm": 4},
                ),
            ],
            gutter="xs",
        )
    else:
        return dmc.Grid(
            [
                dmc.GridCol(
                    metric_card(label, fmt.format(portfolio_val), "violet"),
                    span=12,
                ),
            ],
            gutter="xs",
        )


def delta_badge(
    value: float,
    unit: str = "%",
    decimals: int = 2,
    invert: bool = False,
) -> dmc.Badge:
    """Colored badge showing delta value.

    Args:
        value: Delta value
        unit: Unit suffix
        decimals: Decimal places
        invert: If True, negative is green

    Returns:
        Colored Badge component
    """
    color = "green" if (value < 0 if invert else value > 0) else "red"
    return dmc.Badge(
        f"{value:+.{decimals}f}{unit}",
        color=color,
        variant="light",
        size="lg",
    )


def compliance_banner(
    status: str,
    compliant: int,
    warnings: int,
    breaches: int,
) -> dmc.Paper:
    """Full-width colored banner with compliance summary.

    Args:
        status: Overall status ("compliant", "warning", "breach")
        compliant: Count of compliant rules
        warnings: Count of warnings
        breaches: Count of breaches

    Returns:
        Colored Paper component with status
    """
    colors = {
        "compliant": ("green", "All guidelines compliant"),
        "warning": ("yellow", "Attention required"),
        "breach": ("red", "Compliance breaches detected"),
    }
    color, message = colors.get(status, ("gray", "Unknown status"))
    total = compliant + warnings + breaches

    return dmc.Paper(
        dmc.Group(
            [
                dmc.ThemeIcon(
                    dmc.Text(
                        "!" if status == "breach" else ("?" if status == "warning" else "✓"),
                        fw=700,
                    ),
                    color=color,
                    size="xl",
                    radius="xl",
                    variant="light",
                ),
                dmc.Stack(
                    [
                        dmc.Text(message, fw=600, size="lg"),
                        dmc.Text(
                            f"{compliant}/{total} compliant · {warnings} warnings · {breaches} breaches",
                            size="sm",
                            c="dimmed",
                        ),
                    ],
                    gap=0,
                ),
            ],
            gap="md",
        ),
        p="md",
        radius="md",
        withBorder=True,
        style={"borderColor": f"var(--mantine-color-{color}-6)"},
    )


def action_card(
    title: str,
    description: str,
    severity: str,
    details: str | None = None,
) -> dmc.Paper:
    """Alert card for actionable recommendations.

    Args:
        title: Alert title
        description: Alert description
        severity: "high" (red), "medium" (orange), "low" (yellow)
        details: Optional additional details

    Returns:
        Styled Paper component
    """
    colors = {"high": "red", "medium": "orange", "low": "yellow"}
    color = colors.get(severity, "gray")

    content = [
        dmc.Group(
            [
                dmc.Badge(severity.upper(), color=color, variant="light", size="sm"),
                dmc.Text(title, fw=600, size="sm"),
            ],
            gap="xs",
        ),
        dmc.Text(description, size="sm", c="dimmed"),
    ]

    if details:
        content.append(dmc.Text(details, size="xs", c="dimmed", fs="italic"))

    return dmc.Paper(
        dmc.Stack(content, gap="xs"),
        p="sm",
        radius="md",
        withBorder=True,
        style={"borderLeftWidth": "3px", "borderLeftColor": f"var(--mantine-color-{color}-6)"},
    )


def section_header(title: str, subtitle: str | None = None) -> dmc.Stack:
    """Section header with title and optional subtitle.

    Args:
        title: Section title
        subtitle: Optional description

    Returns:
        Stack with title and subtitle
    """
    content = [dmc.Text(title, fw=600, size="lg", className="text-primary")]
    if subtitle:
        content.append(dmc.Text(subtitle, size="sm", c="dimmed"))
    return dmc.Stack(content, gap=2)


def metric_cards_row(
    metrics: list[tuple[str, str, str]],
    span: int | dict = 3,
) -> dmc.Grid:
    """Render a row of metric cards.

    Args:
        metrics: List of (name, value, color) tuples
        span: Grid span for each card (int or responsive dict)

    Returns:
        Grid of metric cards
    """
    if isinstance(span, int):
        span = {"base": 6, "sm": span}

    return dmc.Grid(
        [dmc.GridCol(metric_card(n, v, c), span=span) for n, v, c in metrics],
        gutter="xs",
    )
