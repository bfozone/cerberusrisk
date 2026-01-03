import enum

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from src.database import Base


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
