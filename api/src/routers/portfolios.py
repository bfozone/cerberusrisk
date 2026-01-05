from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Portfolio
from src.schemas import PortfolioOut, PortfolioDetailOut, PositionOut, PortfolioValueOut, DataInfoOut
from src.services.market_data import MarketDataService, Quote
from src.config import settings

router = APIRouter(prefix="/api", tags=["portfolios"])
market_service = MarketDataService(settings.valkey_host, settings.valkey_port)


@router.get("/portfolios", response_model=list[PortfolioOut])
def list_portfolios(db: Session = Depends(get_db)):
    return db.query(Portfolio).all()


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioDetailOut)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.get("/portfolios/{portfolio_id}/positions", response_model=list[PositionOut])
def get_portfolio_positions(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio.positions


@router.get("/market/{ticker}", response_model=Quote)
def get_quote(ticker: str):
    quote = market_service.get_quote(ticker.upper())
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote not found for {ticker}")
    return quote


@router.get("/portfolios/{portfolio_id}/value", response_model=PortfolioValueOut)
def get_portfolio_value(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    quotes = market_service.get_quotes(tickers)

    positions = []
    for pos in portfolio.positions:
        quote = quotes.get(pos.ticker)
        positions.append({
            "ticker": pos.ticker,
            "name": pos.name,
            "weight": pos.weight,
            "price": quote.price if quote else None,
            "change_pct": quote.change_pct if quote else None,
        })

    return PortfolioValueOut(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        positions=positions,
        total_value=None,
    )


@router.get("/portfolios/{portfolio_id}/data-info", response_model=DataInfoOut)
def get_data_info(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    if not tickers:
        raise HTTPException(status_code=400, detail="No tickers in portfolio")

    # Get history for first ticker (all should have same date range)
    history = market_service.get_history(tickers[0])
    if not history:
        raise HTTPException(status_code=400, detail="No price history available")

    return DataInfoOut(
        start_date=history[0]["date"],
        end_date=history[-1]["date"],
        trading_days=len(history),
        period="1y",
    )


@router.post("/portfolios/{portfolio_id}/refresh-data")
def refresh_portfolio_data(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    tickers.append("SPY")  # Include benchmark

    result = market_service.refresh_histories(tickers)
    return {"status": "ok", "tickers_refreshed": result}
