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


class MonteCarloResult(BaseModel):
    simulations: int
    var_95: float
    var_99: float
    cvar_95: float
    percentiles: list[float]
