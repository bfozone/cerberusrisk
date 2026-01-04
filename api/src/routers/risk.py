from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Portfolio
from src.services.market_data import MarketDataService
from src.services.risk_engine import RiskEngine
from src.services.risk_models import ComparativeRiskMetrics, RiskContribution
from src.config import settings

router = APIRouter(prefix="/api/portfolios", tags=["risk"])
market_service = MarketDataService(settings.valkey_host, settings.valkey_port)
risk_engine = RiskEngine()


@router.get("/{portfolio_id}/risk", response_model=ComparativeRiskMetrics)
def get_portfolio_risk(portfolio_id: int, db: Session = Depends(get_db)):
    """Get portfolio risk metrics with benchmark (SPY) comparison."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    weights = {p.ticker: p.weight for p in portfolio.positions}

    histories = market_service.get_histories(tickers)

    # Get benchmark (SPY) history for comparison
    benchmark_history = market_service.get_history("SPY")

    result = risk_engine.calculate_comparative_risk(histories, weights, benchmark_history)
    if result is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    return result


@router.get("/{portfolio_id}/risk/contributions", response_model=list[RiskContribution])
def get_risk_contributions(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    weights = {p.ticker: p.weight for p in portfolio.positions}

    histories = market_service.get_histories(tickers)
    return risk_engine.calculate_risk_contributions(histories, weights)


@router.get("/{portfolio_id}/correlation")
def get_correlation(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions]
    histories = market_service.get_histories([t for t in tickers if t != "CASH"])
    return risk_engine.calculate_correlation_matrix(histories, tickers)
