from sqlalchemy.orm import Session

from src.models import Portfolio, Position, PortfolioType


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
