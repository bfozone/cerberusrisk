from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Portfolio
from src.services.market_data import MarketDataService
from src.services.risk_engine import RiskEngine
from src.services.risk_models import (
    BetaMetrics,
    FactorExposures,
    MonteCarloResult,
    PerformanceMetrics,
    PortfolioLiquidity,
    RollingMetrics,
    SectorConcentration,
    TailRiskStats,
    VarBacktest,
    WhatIfResult,
)
from src.config import settings

router = APIRouter(prefix="/api/portfolios", tags=["risk-advanced"])
market_service = MarketDataService(settings.valkey_host, settings.valkey_port)
risk_engine = RiskEngine()


# ============================================================================
# HELPER
# ============================================================================


def get_portfolio_data(portfolio_id: int, db: Session):
    """Common helper to get portfolio, tickers, weights, and histories."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    weights = {p.ticker: p.weight for p in portfolio.positions}
    histories = market_service.get_histories(tickers)

    return portfolio, tickers, weights, histories


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/{portfolio_id}/risk/rolling", response_model=RollingMetrics)
def get_rolling_metrics(portfolio_id: int, window: int = 20, db: Session = Depends(get_db)):
    """Get rolling VaR, volatility, and drawdown time series."""
    _, _, weights, histories = get_portfolio_data(portfolio_id, db)

    result = risk_engine.calculate_rolling_metrics(histories, weights, window)
    if result is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    return result


@router.get("/{portfolio_id}/risk/tail", response_model=TailRiskStats)
def get_tail_risk(portfolio_id: int, n: int = 10, db: Session = Depends(get_db)):
    """Get tail risk statistics (skewness, kurtosis, worst/best days)."""
    _, _, weights, histories = get_portfolio_data(portfolio_id, db)

    result = risk_engine.calculate_tail_risk(histories, weights, n)
    if result is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    return result


@router.get("/{portfolio_id}/risk/beta", response_model=BetaMetrics)
def get_beta(portfolio_id: int, benchmark: str = "SPY", db: Session = Depends(get_db)):
    """Get beta, alpha, and R-squared vs benchmark."""
    _, tickers, weights, histories = get_portfolio_data(portfolio_id, db)

    # Get benchmark history
    benchmark_hist = market_service.get_history(benchmark)
    if not benchmark_hist:
        raise HTTPException(status_code=400, detail=f"Cannot fetch {benchmark} data")

    # Calculate returns
    portfolio_returns = risk_engine.calculate_portfolio_returns(histories, weights)
    if portfolio_returns is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    # Align benchmark returns with portfolio
    benchmark_prices = [d["close"] for d in benchmark_hist]
    benchmark_returns = risk_engine.calculate_returns(benchmark_prices)

    # Trim to same length
    min_len = min(len(portfolio_returns), len(benchmark_returns))
    portfolio_returns = portfolio_returns[-min_len:]
    benchmark_returns = benchmark_returns[-min_len:]

    result = risk_engine.calculate_beta(portfolio_returns, benchmark_returns)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot calculate beta")

    return result


@router.get("/{portfolio_id}/risk/backtest", response_model=VarBacktest)
def get_var_backtest(portfolio_id: int, window: int = 60, db: Session = Depends(get_db)):
    """Get VaR backtest (predicted vs realized)."""
    _, _, weights, histories = get_portfolio_data(portfolio_id, db)

    result = risk_engine.backtest_var(histories, weights, window)
    if result is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    return result


@router.get("/{portfolio_id}/concentration/sector", response_model=SectorConcentration)
def get_sector_concentration(portfolio_id: int, db: Session = Depends(get_db)):
    """Get sector concentration and HHI."""
    _, tickers, weights, _ = get_portfolio_data(portfolio_id, db)

    # Get sector info for all tickers
    ticker_info = market_service.get_ticker_info(tickers)
    sector_map = {t: info["sector"] if info else "Unknown" for t, info in ticker_info.items()}

    return risk_engine.calculate_sector_concentration(weights, sector_map)


@router.get("/{portfolio_id}/liquidity", response_model=PortfolioLiquidity)
def get_liquidity(portfolio_id: int, db: Session = Depends(get_db)):
    """Get liquidity scores for portfolio positions."""
    _, tickers, weights, _ = get_portfolio_data(portfolio_id, db)

    volume_data = market_service.get_volume_data(tickers)
    return risk_engine.calculate_liquidity(weights, volume_data)


class WhatIfRequest(BaseModel):
    changes: dict[str, float]  # {ticker: new_weight} - set to 0 to remove


@router.post("/{portfolio_id}/risk/whatif", response_model=WhatIfResult)
def run_what_if(portfolio_id: int, request: WhatIfRequest, db: Session = Depends(get_db)):
    """Calculate risk impact of position changes."""
    _, tickers, weights, histories = get_portfolio_data(portfolio_id, db)

    # Apply changes to create modified weights
    modified_weights = weights.copy()
    for ticker, new_weight in request.changes.items():
        if new_weight <= 0:
            modified_weights.pop(ticker, None)
        else:
            modified_weights[ticker] = new_weight

    # Fetch any new tickers
    new_tickers = [t for t in modified_weights.keys() if t not in histories and t != "CASH"]
    if new_tickers:
        new_histories = market_service.get_histories(new_tickers)
        histories.update(new_histories)

    result = risk_engine.calculate_what_if(histories, weights, modified_weights)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot calculate what-if")

    return result


@router.get("/{portfolio_id}/risk/montecarlo", response_model=MonteCarloResult)
def get_monte_carlo(portfolio_id: int, simulations: int = 10000, db: Session = Depends(get_db)):
    """Get Monte Carlo VaR simulation."""
    _, _, weights, histories = get_portfolio_data(portfolio_id, db)

    result = risk_engine.calculate_monte_carlo(histories, weights, simulations)
    if result is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    return result


@router.get("/{portfolio_id}/risk/factors", response_model=FactorExposures)
def get_factor_exposures(portfolio_id: int, db: Session = Depends(get_db)):
    """Get factor exposures (market, size, value)."""
    _, _, weights, histories = get_portfolio_data(portfolio_id, db)

    # Get factor ETF histories
    factors = ["SPY", "IWM", "IVE"]
    factor_histories = market_service.get_histories(factors)

    # Calculate portfolio returns
    portfolio_returns = risk_engine.calculate_portfolio_returns(histories, weights)
    if portfolio_returns is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    # Calculate factor returns and align
    factor_returns = {}
    min_len = len(portfolio_returns)

    for factor in factors:
        if not factor_histories.get(factor):
            raise HTTPException(status_code=400, detail=f"Cannot fetch {factor} data")
        prices = [d["close"] for d in factor_histories[factor]]
        returns = risk_engine.calculate_returns(prices)
        min_len = min(min_len, len(returns))
        factor_returns[factor] = returns

    # Trim all to same length
    portfolio_returns = portfolio_returns[-min_len:]
    for factor in factors:
        factor_returns[factor] = factor_returns[factor][-min_len:]

    result = risk_engine.calculate_factor_exposures(portfolio_returns, factor_returns)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot calculate factor exposures")

    return result


@router.get("/{portfolio_id}/performance", response_model=PerformanceMetrics)
def get_performance(portfolio_id: int, benchmark: str = "SPY", db: Session = Depends(get_db)):
    """Get comprehensive performance metrics with benchmark comparison."""
    _, _, weights, histories = get_portfolio_data(portfolio_id, db)

    # Get benchmark history
    benchmark_history = market_service.get_history(benchmark)

    result = risk_engine.calculate_performance_metrics(histories, weights, benchmark_history)
    if result is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    return result
