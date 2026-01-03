from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Portfolio
from src.services.stress_testing import StressTestingService, StressScenario, StressResult

router = APIRouter(prefix="/api", tags=["stress"])
stress_service = StressTestingService()


class StressCompareResult(BaseModel):
    scenario: StressScenario
    results: list[StressResult]


@router.get("/stress/scenarios", response_model=list[StressScenario])
def list_stress_scenarios():
    return stress_service.get_scenarios()


@router.get("/portfolios/{portfolio_id}/stress/{scenario_id}", response_model=StressResult)
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


@router.get("/stress/compare/{scenario_id}", response_model=StressCompareResult)
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
