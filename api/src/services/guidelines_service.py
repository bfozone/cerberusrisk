"""Investment Guidelines monitoring service.

This module provides investment guideline/limit monitoring for portfolios:
- Single position limits
- Sector concentration limits
- Asset class limits
- Issuer limits
- Liquidity requirements

Implements a traffic light system:
- Green (Compliant): Within limits with >10% headroom
- Yellow (Warning): Within limits but <10% headroom
- Red (Breach): Limit exceeded
"""

from datetime import datetime
from src.services.risk_models import (
    GuidelineDefinition,
    GuidelineBreachDetail,
    GuidelinesReport,
    GuidelineStatus,
)


# Standard investment guideline templates
# In production, these would be stored in a database per portfolio/fund
DEFAULT_GUIDELINES = [
    GuidelineDefinition(
        id="single_position_max",
        name="Single Position Limit",
        description="No single position shall exceed 10% of portfolio value",
        limit_type="max_weight",
        limit_value=10.0,
        scope="position",
    ),
    GuidelineDefinition(
        id="sector_max",
        name="Sector Concentration",
        description="No single sector shall exceed 30% of portfolio value",
        limit_type="max_weight",
        limit_value=30.0,
        scope="sector",
    ),
    GuidelineDefinition(
        id="top5_concentration",
        name="Top 5 Concentration",
        description="Top 5 positions shall not exceed 50% of portfolio value",
        limit_type="max_weight",
        limit_value=50.0,
        scope="portfolio",
        scope_filter="top5",
    ),
    GuidelineDefinition(
        id="cash_min",
        name="Minimum Cash",
        description="Cash allocation shall be at least 2% for liquidity",
        limit_type="min_weight",
        limit_value=2.0,
        scope="asset_class",
        scope_filter="cash",
    ),
    GuidelineDefinition(
        id="single_issuer",
        name="Single Issuer Limit",
        description="Exposure to single issuer (bonds + equity) max 5%",
        limit_type="max_weight",
        limit_value=5.0,
        scope="issuer",
    ),
    GuidelineDefinition(
        id="max_positions",
        name="Maximum Positions",
        description="Portfolio shall hold no more than 50 positions",
        limit_type="max_count",
        limit_value=50.0,
        scope="portfolio",
        scope_filter="position_count",
    ),
    GuidelineDefinition(
        id="equity_range",
        name="Equity Allocation Range",
        description="Equity allocation shall be between 40% and 80%",
        limit_type="range",
        limit_value=40.0,
        limit_value_upper=80.0,
        scope="asset_class",
        scope_filter="equity",
    ),
]

# Asset class mapping for tickers (simplified)
# In production, this comes from security master data
ASSET_CLASS_MAP = {
    "AAPL": "equity",
    "MSFT": "equity",
    "GOOGL": "equity",
    "AMZN": "equity",
    "META": "equity",
    "NVDA": "equity",
    "JPM": "equity",
    "V": "equity",
    "JNJ": "equity",
    "UNH": "equity",
    "PG": "equity",
    "XOM": "equity",
    "CVX": "equity",
    "HD": "equity",
    "MA": "equity",
    "DIS": "equity",
    "NFLX": "equity",
    "PYPL": "equity",
    "ADBE": "equity",
    "CRM": "equity",
    "SPY": "equity",
    "IWM": "equity",
    "IVE": "equity",
    "CASH": "cash",
    "BND": "fixed_income",
    "AGG": "fixed_income",
    "TLT": "fixed_income",
    "LQD": "fixed_income",
    "HYG": "fixed_income",
    "GLD": "commodity",
    "SLV": "commodity",
    "USO": "commodity",
}


class GuidelinesService:
    """Investment guidelines monitoring service."""

    WARNING_THRESHOLD = 0.90  # Warn at 90% of limit

    def __init__(self, guidelines: list[GuidelineDefinition] | None = None):
        self.guidelines = guidelines or DEFAULT_GUIDELINES

    def get_guidelines(self) -> list[GuidelineDefinition]:
        """Get all configured guidelines."""
        return self.guidelines

    def _get_asset_class(self, ticker: str) -> str:
        """Get asset class for a ticker."""
        return ASSET_CLASS_MAP.get(ticker, "equity")

    def _check_position_limit(
        self,
        guideline: GuidelineDefinition,
        positions: list[dict],
    ) -> GuidelineStatus:
        """Check single position weight limits."""
        breaches = []
        max_weight = 0
        max_ticker = ""

        for pos in positions:
            weight_pct = pos["weight"] * 100
            if weight_pct > max_weight:
                max_weight = weight_pct
                max_ticker = pos["ticker"]

            if weight_pct > guideline.limit_value:
                breaches.append(
                    GuidelineBreachDetail(
                        ticker=pos["ticker"],
                        sector=None,
                        current_value=round(weight_pct, 2),
                        limit_value=guideline.limit_value,
                        breach_amount=round(weight_pct - guideline.limit_value, 2),
                        breach_pct=round(
                            (weight_pct - guideline.limit_value)
                            / guideline.limit_value
                            * 100,
                            2,
                        ),
                    )
                )

        headroom = guideline.limit_value - max_weight
        headroom_pct = headroom / guideline.limit_value * 100 if guideline.limit_value > 0 else 0

        if breaches:
            status = "breach"
        elif headroom_pct < (1 - self.WARNING_THRESHOLD) * 100:
            status = "warning"
        else:
            status = "compliant"

        return GuidelineStatus(
            guideline=guideline,
            status=status,
            current_value=round(max_weight, 2),
            headroom=round(headroom, 2),
            headroom_pct=round(headroom_pct, 2),
            breach_details=breaches if breaches else None,
        )

    def _check_sector_limit(
        self,
        guideline: GuidelineDefinition,
        positions: list[dict],
        sector_map: dict[str, str],
    ) -> GuidelineStatus:
        """Check sector concentration limits."""
        sector_weights: dict[str, float] = {}

        for pos in positions:
            ticker = pos["ticker"]
            if ticker == "CASH":
                continue
            sector = sector_map.get(ticker, "Unknown")
            sector_weights[sector] = sector_weights.get(sector, 0) + pos["weight"] * 100

        breaches = []
        max_sector_weight = 0
        max_sector = ""

        for sector, weight in sector_weights.items():
            if weight > max_sector_weight:
                max_sector_weight = weight
                max_sector = sector

            if weight > guideline.limit_value:
                breaches.append(
                    GuidelineBreachDetail(
                        ticker=None,
                        sector=sector,
                        current_value=round(weight, 2),
                        limit_value=guideline.limit_value,
                        breach_amount=round(weight - guideline.limit_value, 2),
                        breach_pct=round(
                            (weight - guideline.limit_value)
                            / guideline.limit_value
                            * 100,
                            2,
                        ),
                    )
                )

        headroom = guideline.limit_value - max_sector_weight
        headroom_pct = headroom / guideline.limit_value * 100 if guideline.limit_value > 0 else 0

        if breaches:
            status = "breach"
        elif headroom_pct < (1 - self.WARNING_THRESHOLD) * 100:
            status = "warning"
        else:
            status = "compliant"

        return GuidelineStatus(
            guideline=guideline,
            status=status,
            current_value=round(max_sector_weight, 2),
            headroom=round(headroom, 2),
            headroom_pct=round(headroom_pct, 2),
            breach_details=breaches if breaches else None,
        )

    def _check_top5_limit(
        self,
        guideline: GuidelineDefinition,
        positions: list[dict],
    ) -> GuidelineStatus:
        """Check top 5 concentration limit."""
        sorted_positions = sorted(positions, key=lambda x: x["weight"], reverse=True)
        top5 = sorted_positions[:5]
        top5_weight = sum(p["weight"] for p in top5) * 100

        headroom = guideline.limit_value - top5_weight
        headroom_pct = headroom / guideline.limit_value * 100 if guideline.limit_value > 0 else 0

        breaches = None
        if top5_weight > guideline.limit_value:
            status = "breach"
            breaches = [
                GuidelineBreachDetail(
                    ticker=", ".join(p["ticker"] for p in top5),
                    sector=None,
                    current_value=round(top5_weight, 2),
                    limit_value=guideline.limit_value,
                    breach_amount=round(top5_weight - guideline.limit_value, 2),
                    breach_pct=round(
                        (top5_weight - guideline.limit_value)
                        / guideline.limit_value
                        * 100,
                        2,
                    ),
                )
            ]
        elif headroom_pct < (1 - self.WARNING_THRESHOLD) * 100:
            status = "warning"
        else:
            status = "compliant"

        return GuidelineStatus(
            guideline=guideline,
            status=status,
            current_value=round(top5_weight, 2),
            headroom=round(headroom, 2),
            headroom_pct=round(headroom_pct, 2),
            breach_details=breaches,
        )

    def _check_cash_minimum(
        self,
        guideline: GuidelineDefinition,
        positions: list[dict],
    ) -> GuidelineStatus:
        """Check minimum cash allocation."""
        cash_weight = 0
        for pos in positions:
            if pos["ticker"] == "CASH" or self._get_asset_class(pos["ticker"]) == "cash":
                cash_weight += pos["weight"] * 100

        headroom = cash_weight - guideline.limit_value
        headroom_pct = headroom / guideline.limit_value * 100 if guideline.limit_value > 0 else 0

        breaches = None
        if cash_weight < guideline.limit_value:
            status = "breach"
            breaches = [
                GuidelineBreachDetail(
                    ticker="CASH",
                    sector=None,
                    current_value=round(cash_weight, 2),
                    limit_value=guideline.limit_value,
                    breach_amount=round(guideline.limit_value - cash_weight, 2),
                    breach_pct=round(
                        (guideline.limit_value - cash_weight)
                        / guideline.limit_value
                        * 100,
                        2,
                    ),
                )
            ]
        elif headroom_pct < (1 - self.WARNING_THRESHOLD) * 100:
            status = "warning"
        else:
            status = "compliant"

        return GuidelineStatus(
            guideline=guideline,
            status=status,
            current_value=round(cash_weight, 2),
            headroom=round(headroom, 2),
            headroom_pct=round(headroom_pct, 2),
            breach_details=breaches,
        )

    def _check_position_count(
        self,
        guideline: GuidelineDefinition,
        positions: list[dict],
    ) -> GuidelineStatus:
        """Check maximum position count."""
        # Exclude cash from count
        position_count = len([p for p in positions if p["ticker"] != "CASH"])

        headroom = guideline.limit_value - position_count
        headroom_pct = headroom / guideline.limit_value * 100 if guideline.limit_value > 0 else 0

        breaches = None
        if position_count > guideline.limit_value:
            status = "breach"
            breaches = [
                GuidelineBreachDetail(
                    ticker=None,
                    sector=None,
                    current_value=position_count,
                    limit_value=guideline.limit_value,
                    breach_amount=position_count - guideline.limit_value,
                    breach_pct=round(
                        (position_count - guideline.limit_value)
                        / guideline.limit_value
                        * 100,
                        2,
                    ),
                )
            ]
        elif headroom_pct < (1 - self.WARNING_THRESHOLD) * 100:
            status = "warning"
        else:
            status = "compliant"

        return GuidelineStatus(
            guideline=guideline,
            status=status,
            current_value=position_count,
            headroom=round(headroom, 2),
            headroom_pct=round(headroom_pct, 2),
            breach_details=breaches,
        )

    def _check_asset_class_range(
        self,
        guideline: GuidelineDefinition,
        positions: list[dict],
    ) -> GuidelineStatus:
        """Check asset class allocation range."""
        target_class = guideline.scope_filter
        class_weight = 0

        for pos in positions:
            if self._get_asset_class(pos["ticker"]) == target_class:
                class_weight += pos["weight"] * 100

        lower = guideline.limit_value
        upper = guideline.limit_value_upper or 100

        if class_weight < lower:
            status = "breach"
            headroom = class_weight - lower
            breaches = [
                GuidelineBreachDetail(
                    ticker=None,
                    sector=target_class,
                    current_value=round(class_weight, 2),
                    limit_value=lower,
                    breach_amount=round(lower - class_weight, 2),
                    breach_pct=round((lower - class_weight) / lower * 100, 2),
                )
            ]
        elif class_weight > upper:
            status = "breach"
            headroom = upper - class_weight
            breaches = [
                GuidelineBreachDetail(
                    ticker=None,
                    sector=target_class,
                    current_value=round(class_weight, 2),
                    limit_value=upper,
                    breach_amount=round(class_weight - upper, 2),
                    breach_pct=round((class_weight - upper) / upper * 100, 2),
                )
            ]
        else:
            # Calculate headroom to nearest limit
            to_lower = class_weight - lower
            to_upper = upper - class_weight
            headroom = min(to_lower, to_upper)
            headroom_pct = headroom / (upper - lower) * 100 if (upper - lower) > 0 else 0

            if headroom_pct < 10:
                status = "warning"
            else:
                status = "compliant"
            breaches = None

        headroom_pct = abs(headroom) / ((upper - lower) / 2) * 100 if (upper - lower) > 0 else 0

        return GuidelineStatus(
            guideline=guideline,
            status=status,
            current_value=round(class_weight, 2),
            headroom=round(headroom, 2),
            headroom_pct=round(headroom_pct, 2),
            breach_details=breaches if status == "breach" else None,
        )

    def _check_issuer_limit(
        self,
        guideline: GuidelineDefinition,
        positions: list[dict],
    ) -> GuidelineStatus:
        """Check single issuer limit (treats each ticker as issuer for demo)."""
        # In production, would group by issuer ID from security master
        # For demo, same as single position check
        return self._check_position_limit(guideline, positions)

    def check_guidelines(
        self,
        portfolio_id: int,
        portfolio_name: str,
        positions: list[dict],
        sector_map: dict[str, str],
    ) -> GuidelinesReport:
        """Run all guideline checks for a portfolio."""
        results = []

        for guideline in self.guidelines:
            if guideline.scope == "position":
                result = self._check_position_limit(guideline, positions)
            elif guideline.scope == "sector":
                result = self._check_sector_limit(guideline, positions, sector_map)
            elif guideline.scope == "portfolio":
                if guideline.scope_filter == "top5":
                    result = self._check_top5_limit(guideline, positions)
                elif guideline.scope_filter == "position_count":
                    result = self._check_position_count(guideline, positions)
                else:
                    continue
            elif guideline.scope == "asset_class":
                if guideline.scope_filter == "cash":
                    result = self._check_cash_minimum(guideline, positions)
                elif guideline.limit_type == "range":
                    result = self._check_asset_class_range(guideline, positions)
                else:
                    continue
            elif guideline.scope == "issuer":
                result = self._check_issuer_limit(guideline, positions)
            else:
                continue

            results.append(result)

        # Calculate summary
        compliant = sum(1 for r in results if r.status == "compliant")
        warning = sum(1 for r in results if r.status == "warning")
        breach = sum(1 for r in results if r.status == "breach")

        if breach > 0:
            overall = "breach"
        elif warning > 0:
            overall = "warning"
        else:
            overall = "compliant"

        return GuidelinesReport(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            check_timestamp=datetime.now().isoformat(),
            overall_status=overall,
            total_guidelines=len(results),
            compliant_count=compliant,
            warning_count=warning,
            breach_count=breach,
            guidelines=results,
        )
