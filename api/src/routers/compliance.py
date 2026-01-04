"""API endpoints for GIPS, ESG, and Investment Guidelines."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Portfolio
from src.services.market_data import MarketDataService
from src.services.gips_service import GIPSService
from src.services.esg_service import ESGService
from src.services.guidelines_service import GuidelinesService
from src.services.risk_models import GIPSMetrics, PortfolioESG, GuidelinesReport, GuidelineDefinition
from src.config import settings

router = APIRouter(prefix="/api/portfolios", tags=["compliance"])
market_service = MarketDataService(settings.valkey_host, settings.valkey_port)
gips_service = GIPSService()
esg_service = ESGService()
guidelines_service = GuidelinesService()


# ============================================================================
# GIPS ENDPOINTS
# ============================================================================


@router.get("/{portfolio_id}/gips", response_model=GIPSMetrics)
def get_gips_metrics(
    portfolio_id: int,
    benchmark: str = "SPY",
    fee_bps: int = 50,
    db: Session = Depends(get_db),
):
    """Get GIPS-compliant performance metrics.

    GIPS (Global Investment Performance Standards) metrics include:
    - Time-Weighted Returns (TWR) gross and net of fees
    - Monthly period returns with benchmark comparison
    - Composite statistics and dispersion
    - Risk metrics (volatility, tracking error, information ratio)
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    weights = {p.ticker: p.weight for p in portfolio.positions}

    histories = market_service.get_histories(tickers)
    benchmark_history = market_service.get_history(benchmark)

    result = gips_service.calculate_gips_metrics(
        histories, weights, benchmark_history, fee_bps
    )
    if result is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    return result


# ============================================================================
# ESG ENDPOINTS
# ============================================================================


@router.get("/{portfolio_id}/esg", response_model=PortfolioESG)
def get_esg_metrics(
    portfolio_id: int,
    db: Session = Depends(get_db),
):
    """Get ESG (Environmental, Social, Governance) metrics.

    Note: ESG data is simulated for demonstration. Production would integrate
    with MSCI ESG, Sustainalytics, or similar data providers.

    Returns:
    - Portfolio-weighted E, S, G scores
    - Carbon intensity (WACI) vs benchmark
    - Controversy flags
    - Rating distribution
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Get positions with names
    positions = [
        {"ticker": p.ticker, "name": p.name, "weight": p.weight}
        for p in portfolio.positions
    ]

    # Get sector mapping from market data
    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    sector_map = market_service.get_sectors(tickers)

    return esg_service.calculate_portfolio_esg(positions, sector_map)


# ============================================================================
# INVESTMENT GUIDELINES ENDPOINTS
# ============================================================================


@router.get("/guidelines/definitions", response_model=list[GuidelineDefinition])
def get_guideline_definitions():
    """Get all configured investment guideline definitions.

    Returns the list of investment guidelines/limits that are monitored.
    """
    return guidelines_service.get_guidelines()


@router.get("/{portfolio_id}/guidelines", response_model=GuidelinesReport)
def check_guidelines(
    portfolio_id: int,
    db: Session = Depends(get_db),
):
    """Check portfolio compliance with investment guidelines.

    Runs all configured guideline checks and returns a compliance report
    with traffic light status:
    - compliant (green): Within limits
    - warning (yellow): Within limits but approaching threshold
    - breach (red): Limit exceeded

    Common guidelines checked:
    - Single position limits
    - Sector concentration
    - Asset class ranges
    - Liquidity requirements
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Get positions
    positions = [
        {"ticker": p.ticker, "name": p.name, "weight": p.weight}
        for p in portfolio.positions
    ]

    # Get sector mapping
    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    sector_map = market_service.get_sectors(tickers)

    return guidelines_service.check_guidelines(
        portfolio_id=portfolio_id,
        portfolio_name=portfolio.name,
        positions=positions,
        sector_map=sector_map,
    )
