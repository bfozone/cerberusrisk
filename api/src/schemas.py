from pydantic import BaseModel

from src.models import PortfolioType


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


class PortfolioValueOut(BaseModel):
    portfolio_id: int
    portfolio_name: str
    positions: list[dict]
    total_value: float | None
