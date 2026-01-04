from pydantic import BaseModel


# ============================================================================
# CORE RISK MODELS
# ============================================================================


class RiskMetrics(BaseModel):
    var_95: float
    var_99: float
    cvar_95: float
    volatility: float
    sharpe: float
    max_drawdown: float
    current_drawdown: float


class ComparativeRiskMetrics(BaseModel):
    """Portfolio vs Benchmark risk comparison."""

    portfolio: RiskMetrics
    benchmark: RiskMetrics | None = None
    delta: dict[str, float] | None = None


class RiskContribution(BaseModel):
    ticker: str
    weight: float
    volatility: float
    marginal_var: float
    component_var: float
    pct_contribution: float


# ============================================================================
# TIME SERIES MODELS
# ============================================================================


class RollingMetrics(BaseModel):
    dates: list[str]
    rolling_var_95: list[float]
    rolling_volatility: list[float]
    drawdown_series: list[float]


class VarBacktest(BaseModel):
    dates: list[str]
    predicted_var: list[float]
    realized_returns: list[float]
    breaches: int
    breach_rate: float


class TailRiskStats(BaseModel):
    skewness: float
    kurtosis: float
    worst_days: list[dict]
    best_days: list[dict]


# ============================================================================
# FACTOR MODELS
# ============================================================================


class BetaMetrics(BaseModel):
    beta: float
    alpha: float
    r_squared: float
    correlation: float


class FactorExposures(BaseModel):
    market_beta: float
    size_beta: float
    value_beta: float
    r_squared: float


# ============================================================================
# CONCENTRATION MODELS
# ============================================================================


class SectorExposure(BaseModel):
    sector: str
    weight: float
    tickers: list[str]


class SectorConcentration(BaseModel):
    sectors: list[SectorExposure]
    hhi: float


class PositionLiquidity(BaseModel):
    ticker: str
    avg_volume: float
    avg_dollar_volume: float
    days_to_liquidate: float
    score: float


class PortfolioLiquidity(BaseModel):
    positions: list[PositionLiquidity]
    weighted_score: float


# ============================================================================
# PERFORMANCE MODELS
# ============================================================================


class PeriodReturns(BaseModel):
    mtd: float | None
    qtd: float | None
    ytd: float | None
    one_year: float | None
    since_inception: float
    annualized: float


class BenchmarkComparison(BaseModel):
    portfolio_return: float
    benchmark_return: float
    active_return: float
    tracking_error: float
    information_ratio: float | None


class RiskAdjustedRatios(BaseModel):
    sharpe: float
    sortino: float
    treynor: float | None
    calmar: float | None


class PositionContribution(BaseModel):
    ticker: str
    weight: float
    position_return: float
    contribution: float
    pct_of_total: float


class PerformanceAttribution(BaseModel):
    total_return: float
    contributions: list[PositionContribution]


class PerformanceMetrics(BaseModel):
    period_returns: PeriodReturns
    benchmark: BenchmarkComparison
    risk_adjusted: RiskAdjustedRatios
    attribution: PerformanceAttribution


# ============================================================================
# SIMULATION MODELS
# ============================================================================


class WhatIfResult(BaseModel):
    original: RiskMetrics
    modified: RiskMetrics
    delta: dict[str, float]


class MonteCarloFanChart(BaseModel):
    """Fan chart data for Monte Carlo simulation paths."""

    days: list[int]  # 0, 1, 2, ..., horizon
    p1: list[float]  # 1st percentile
    p5: list[float]  # 5th percentile
    p25: list[float]  # 25th percentile
    p50: list[float]  # 50th percentile (median)
    p75: list[float]  # 75th percentile
    p95: list[float]  # 95th percentile
    p99: list[float]  # 99th percentile


class MonteCarloResult(BaseModel):
    simulations: int
    horizon: int  # days
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    fan_chart: MonteCarloFanChart
    terminal_distribution: list[float]  # final values for histogram


# ============================================================================
# GIPS COMPLIANCE MODELS
# ============================================================================


class GIPSPeriodReturn(BaseModel):
    """Single period return for GIPS reporting."""

    period: str  # e.g., "2024-Q1", "2024-01"
    start_date: str
    end_date: str
    twr_gross: float  # Time-weighted return (gross)
    twr_net: float  # Time-weighted return (net of fees)
    benchmark_return: float
    excess_return: float


class GIPSCalendarYearReturn(BaseModel):
    """Calendar year return for GIPS reporting."""

    year: int
    gross: float
    net: float
    benchmark: float
    excess: float


class GIPSRollingReturn(BaseModel):
    """Rolling return data point."""

    date: str
    rolling_12m: float
    benchmark_12m: float | None = None


class GIPSDrawdownPoint(BaseModel):
    """Drawdown time series point."""

    date: str
    drawdown: float  # Negative percentage


class GIPSDisclosureItem(BaseModel):
    """Disclosure checklist item."""

    item: str
    status: str  # "pass", "warning", "fail"
    detail: str | None = None


class GIPSCompositeStats(BaseModel):
    """GIPS composite statistics."""

    num_portfolios: int
    total_aum: float
    dispersion: float | None  # Internal dispersion (std dev of returns)
    high_return: float
    low_return: float
    median_return: float
    # Representativeness metrics
    largest_portfolio_pct: float = 0.0  # Largest portfolio as % of AUM
    top5_concentration_pct: float = 0.0  # Top 5 as % of AUM
    portfolio_returns: list[float] = []  # Individual returns for dispersion viz


class GIPSMetrics(BaseModel):
    """GIPS-compliant performance metrics."""

    # Annualized returns
    annualized_return_gross: float
    annualized_return_net: float
    annualized_benchmark: float
    annualized_excess: float

    # Risk metrics
    annualized_volatility: float
    tracking_error: float
    information_ratio: float | None
    sharpe_ratio: float

    # Period returns
    period_returns: list[GIPSPeriodReturn]

    # Composite stats (simulated for demo)
    composite_stats: GIPSCompositeStats

    # Cumulative returns
    cumulative_gross: float
    cumulative_net: float
    cumulative_benchmark: float

    # Data quality
    inception_date: str
    reporting_currency: str
    fee_schedule: str

    # Calendar year returns (new)
    calendar_year_returns: list[GIPSCalendarYearReturn] = []

    # Rolling returns (new)
    rolling_returns: list[GIPSRollingReturn] = []

    # Drawdown metrics (new)
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    drawdown_series: list[GIPSDrawdownPoint] = []

    # Rolling volatility (new) - only if 3Y+ history
    rolling_volatility: list[dict] = []  # [{date, vol_1y}]

    # Disclosure readiness (new)
    disclosure_checklist: list[GIPSDisclosureItem] = []
    history_days: int = 0


# ============================================================================
# ESG MODELS
# ============================================================================


class PositionESG(BaseModel):
    """ESG scores for a single position."""

    ticker: str
    name: str
    weight: float
    esg_score: float  # 0-100
    environmental: float  # 0-100
    social: float  # 0-100
    governance: float  # 0-100
    carbon_intensity: float  # tCO2e / $M revenue
    controversy_flag: bool
    controversy_details: str | None


class PortfolioESG(BaseModel):
    """Portfolio-level ESG metrics."""

    # Weighted scores
    portfolio_esg_score: float
    portfolio_environmental: float
    portfolio_social: float
    portfolio_governance: float

    # Carbon metrics
    portfolio_carbon_intensity: float  # WACI
    benchmark_carbon_intensity: float
    carbon_vs_benchmark: float  # % difference

    # Coverage
    coverage_pct: float  # % of portfolio with ESG data
    num_flagged: int  # Positions with controversies

    # Position details
    positions: list[PositionESG]

    # Rating distribution
    rating_distribution: dict[str, int]  # e.g., {"AAA": 2, "AA": 3, ...}


# ============================================================================
# INVESTMENT GUIDELINES MODELS
# ============================================================================


class GuidelineDefinition(BaseModel):
    """Definition of an investment guideline/limit."""

    id: str
    name: str
    description: str
    limit_type: str  # "max_weight", "min_weight", "max_count", "range"
    limit_value: float
    limit_value_upper: float | None = None  # For range limits
    scope: str  # "position", "sector", "asset_class", "issuer", "portfolio"
    scope_filter: str | None = None  # e.g., sector name, asset class


class GuidelineBreachDetail(BaseModel):
    """Details of a single guideline breach."""

    ticker: str | None
    sector: str | None
    current_value: float
    limit_value: float
    breach_amount: float
    breach_pct: float


class GuidelineStatus(BaseModel):
    """Status of a single guideline check."""

    guideline: GuidelineDefinition
    status: str  # "compliant", "warning", "breach"
    current_value: float
    headroom: float  # Distance to limit (positive = OK, negative = breach)
    headroom_pct: float
    breach_details: list[GuidelineBreachDetail] | None = None


class GuidelinesReport(BaseModel):
    """Complete guidelines compliance report."""

    portfolio_id: int
    portfolio_name: str
    check_timestamp: str
    overall_status: str  # "compliant", "warning", "breach"
    total_guidelines: int
    compliant_count: int
    warning_count: int
    breach_count: int
    guidelines: list[GuidelineStatus]
