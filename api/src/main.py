from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
import enum


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "cerberusrisk"
    postgres_user: str = "cerberus"
    postgres_password: str = "devpassword"
    valkey_host: str = "localhost"
    valkey_port: int = 6379

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

from src.services.market_data import MarketDataService, Quote
from src.services.risk_engine import RiskEngine, RiskMetrics, RiskContribution
from src.services.stress_testing import StressTestingService, StressScenario, StressResult

market_service = MarketDataService(settings.valkey_host, settings.valkey_port)
risk_engine = RiskEngine()
stress_service = StressTestingService()


class PortfolioType(enum.Enum):
    equity = "equity"
    fixed_income = "fixed_income"
    multi_asset = "multi_asset"


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(SQLEnum(PortfolioType), nullable=False)
    description = Column(String)

    positions = relationship("Position", back_populates="portfolio")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    ticker = Column(String, nullable=False)
    name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    asset_class = Column(String, nullable=False)

    portfolio = relationship("Portfolio", back_populates="positions")


class PositionOut(BaseModel):
    id: int
    ticker: str
    name: str
    weight: float
    asset_class: str

    class Config:
        from_attributes = True


class PortfolioOut(BaseModel):
    id: int
    name: str
    type: PortfolioType
    description: str | None

    class Config:
        from_attributes = True


class PortfolioDetailOut(PortfolioOut):
    positions: list[PositionOut] = []


PORTFOLIO_DATA = [
    {
        "name": "Global Equity",
        "type": PortfolioType.equity,
        "description": "Diversified global equity portfolio with US, European, and tech exposure",
        "positions": [
            ("AAPL", "Apple", 0.12, "equity"),
            ("MSFT", "Microsoft", 0.12, "equity"),
            ("NVDA", "Nvidia", 0.10, "equity"),
            ("AMZN", "Amazon", 0.10, "equity"),
            ("JPM", "JPMorgan", 0.08, "equity"),
            ("JNJ", "Johnson & Johnson", 0.08, "equity"),
            ("NESN.SW", "Nestlé", 0.08, "equity"),
            ("ASML", "ASML", 0.08, "equity"),
            ("NOVO-B.CO", "Novo Nordisk", 0.08, "equity"),
            ("MC.PA", "LVMH", 0.08, "equity"),
            ("CASH", "Cash", 0.08, "cash"),
        ],
    },
    {
        "name": "Fixed Income",
        "type": PortfolioType.fixed_income,
        "description": "Bond portfolio spanning treasuries, investment grade, and high yield",
        "positions": [
            ("TLT", "20+ Year Treasury", 0.25, "fixed_income"),
            ("IEF", "7-10 Year Treasury", 0.25, "fixed_income"),
            ("LQD", "Investment Grade Corp", 0.20, "fixed_income"),
            ("HYG", "High Yield Corp", 0.15, "fixed_income"),
            ("AGG", "US Aggregate Bond", 0.15, "fixed_income"),
        ],
    },
    {
        "name": "Multi-Asset Balanced",
        "type": PortfolioType.multi_asset,
        "description": "Balanced allocation across equities, bonds, and gold",
        "positions": [
            ("SPY", "S&P 500", 0.35, "equity"),
            ("VGK", "Europe Equity", 0.15, "equity"),
            ("VWO", "Emerging Markets", 0.10, "equity"),
            ("TLT", "20+ Year Treasury", 0.15, "fixed_income"),
            ("LQD", "Investment Grade Corp", 0.10, "fixed_income"),
            ("GLD", "Gold", 0.10, "commodity"),
            ("CASH", "Cash", 0.05, "cash"),
        ],
    },
]


def seed_portfolios(db: Session):
    if db.query(Portfolio).count() == 0:
        for pdata in PORTFOLIO_DATA:
            portfolio = Portfolio(
                name=pdata["name"],
                type=pdata["type"],
                description=pdata["description"],
            )
            db.add(portfolio)
            db.flush()

            for ticker, name, weight, asset_class in pdata["positions"]:
                position = Position(
                    portfolio_id=portfolio.id,
                    ticker=ticker,
                    name=name,
                    weight=weight,
                    asset_class=asset_class,
                )
                db.add(position)

        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_portfolios(db)
    yield


app = FastAPI(title="CerberusRisk API", lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/portfolios", response_model=list[PortfolioOut])
def list_portfolios(db: Session = Depends(get_db)):
    return db.query(Portfolio).all()


@app.get("/api/portfolios/{portfolio_id}", response_model=PortfolioDetailOut)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@app.get("/api/portfolios/{portfolio_id}/positions", response_model=list[PositionOut])
def get_portfolio_positions(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio.positions


@app.get("/api/market/{ticker}", response_model=Quote)
def get_quote(ticker: str):
    quote = market_service.get_quote(ticker.upper())
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote not found for {ticker}")
    return quote


class PortfolioValueOut(BaseModel):
    portfolio_id: int
    portfolio_name: str
    positions: list[dict]
    total_value: float | None


@app.get("/api/portfolios/{portfolio_id}/value", response_model=PortfolioValueOut)
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
        total_value=None,  # Would need AUM to calculate
    )


@app.get("/api/portfolios/{portfolio_id}/risk", response_model=RiskMetrics)
def get_portfolio_risk(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    weights = {p.ticker: p.weight for p in portfolio.positions}

    histories = market_service.get_histories(tickers)
    returns = risk_engine.calculate_portfolio_returns(histories, weights)

    if returns is None:
        raise HTTPException(status_code=400, detail="Insufficient price history")

    return risk_engine.calculate_risk_metrics(returns)


@app.get("/api/portfolios/{portfolio_id}/risk/contributions", response_model=list[RiskContribution])
def get_risk_contributions(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions if p.ticker != "CASH"]
    weights = {p.ticker: p.weight for p in portfolio.positions}

    histories = market_service.get_histories(tickers)
    return risk_engine.calculate_risk_contributions(histories, weights)


@app.get("/api/portfolios/{portfolio_id}/correlation")
def get_correlation(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    tickers = [p.ticker for p in portfolio.positions]
    histories = market_service.get_histories([t for t in tickers if t != "CASH"])
    return risk_engine.calculate_correlation_matrix(histories, tickers)


@app.get("/api/stress/scenarios", response_model=list[StressScenario])
def list_stress_scenarios():
    return stress_service.get_scenarios()


@app.get("/api/portfolios/{portfolio_id}/stress/{scenario_id}", response_model=StressResult)
def run_stress_test(portfolio_id: int, scenario_id: str, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    positions = [
        {"ticker": p.ticker, "name": p.name, "weight": p.weight, "asset_class": p.asset_class}
        for p in portfolio.positions
    ]

    result = stress_service.run_stress_test(scenario_id, portfolio_id, portfolio.name, positions)
    if not result:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return result


class StressCompareResult(BaseModel):
    scenario: StressScenario
    results: list[StressResult]


@app.get("/api/stress/compare/{scenario_id}", response_model=StressCompareResult)
def compare_portfolios_stress(scenario_id: str, db: Session = Depends(get_db)):
    scenario = stress_service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    portfolios = db.query(Portfolio).all()
    results = []

    for portfolio in portfolios:
        positions = [
            {"ticker": p.ticker, "name": p.name, "weight": p.weight, "asset_class": p.asset_class}
            for p in portfolio.positions
        ]
        result = stress_service.run_stress_test(scenario_id, portfolio.id, portfolio.name, positions)
        if result:
            results.append(result)

    return StressCompareResult(scenario=scenario, results=results)
