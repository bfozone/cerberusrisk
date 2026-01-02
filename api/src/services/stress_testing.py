from pydantic import BaseModel


class StressScenario(BaseModel):
    id: str
    name: str
    description: str
    shocks: dict[str, float]  # asset_class -> shock percentage


class StressResult(BaseModel):
    scenario_id: str
    scenario_name: str
    portfolio_id: int
    portfolio_name: str
    positions: list[dict]
    total_pnl_pct: float
    total_pnl_absolute: float | None


SCENARIOS = [
    StressScenario(
        id="equity_crash",
        name="Equity Crash",
        description="Equity -20%, Flight to quality (bonds +5%)",
        shocks={"equity": -20.0, "fixed_income": 5.0, "commodity": -10.0, "cash": 0.0},
    ),
    StressScenario(
        id="rate_shock_up",
        name="Rate Shock Up",
        description="Rates +200bps, Bonds down significantly",
        shocks={"equity": -5.0, "fixed_income": -15.0, "commodity": 0.0, "cash": 0.0},
    ),
    StressScenario(
        id="rate_shock_down",
        name="Rate Shock Down",
        description="Rates -100bps, Bonds rally",
        shocks={"equity": 3.0, "fixed_income": 10.0, "commodity": 5.0, "cash": 0.0},
    ),
    StressScenario(
        id="credit_spread",
        name="Credit Spread Widening",
        description="IG +100bps, HY +300bps, Treasuries rally",
        shocks={"equity": -10.0, "fixed_income": -8.0, "commodity": -5.0, "cash": 0.0},
    ),
    StressScenario(
        id="stagflation",
        name="Stagflation",
        description="Equity -15%, Rates +150bps, Gold +10%",
        shocks={"equity": -15.0, "fixed_income": -12.0, "commodity": 10.0, "cash": 0.0},
    ),
    StressScenario(
        id="risk_off",
        name="Risk-Off",
        description="Equity -10%, Credit spreads +150bps, Gold +5%",
        shocks={"equity": -10.0, "fixed_income": -3.0, "commodity": 5.0, "cash": 0.0},
    ),
]

SCENARIO_MAP = {s.id: s for s in SCENARIOS}


class StressTestingService:
    def get_scenarios(self) -> list[StressScenario]:
        return SCENARIOS

    def get_scenario(self, scenario_id: str) -> StressScenario | None:
        return SCENARIO_MAP.get(scenario_id)

    def run_stress_test(
        self,
        scenario_id: str,
        portfolio_id: int,
        portfolio_name: str,
        positions: list[dict],
    ) -> StressResult | None:
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return None

        position_results = []
        total_pnl = 0.0

        for pos in positions:
            asset_class = pos.get("asset_class", "equity")
            weight = pos.get("weight", 0)
            shock = scenario.shocks.get(asset_class, 0)

            pnl_pct = weight * shock
            total_pnl += pnl_pct

            position_results.append({
                "ticker": pos["ticker"],
                "name": pos["name"],
                "weight": weight,
                "asset_class": asset_class,
                "shock": shock,
                "pnl_pct": round(pnl_pct, 2),
            })

        return StressResult(
            scenario_id=scenario_id,
            scenario_name=scenario.name,
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            positions=position_results,
            total_pnl_pct=round(total_pnl, 2),
            total_pnl_absolute=None,
        )

    def run_custom_stress(
        self,
        shocks: dict[str, float],
        portfolio_id: int,
        portfolio_name: str,
        positions: list[dict],
    ) -> StressResult:
        position_results = []
        total_pnl = 0.0

        for pos in positions:
            asset_class = pos.get("asset_class", "equity")
            weight = pos.get("weight", 0)
            shock = shocks.get(asset_class, 0)

            pnl_pct = weight * shock
            total_pnl += pnl_pct

            position_results.append({
                "ticker": pos["ticker"],
                "name": pos["name"],
                "weight": weight,
                "asset_class": asset_class,
                "shock": shock,
                "pnl_pct": round(pnl_pct, 2),
            })

        return StressResult(
            scenario_id="custom",
            scenario_name="Custom Scenario",
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            positions=position_results,
            total_pnl_pct=round(total_pnl, 2),
            total_pnl_absolute=None,
        )
