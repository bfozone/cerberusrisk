"""ESG (Environmental, Social, Governance) metrics service.

This module provides ESG scoring and carbon metrics for portfolio analysis.

Note: ESG data is mocked for demonstration purposes. In production, this would
integrate with data providers like MSCI ESG, Sustainalytics, or Bloomberg ESG.

Data structure mirrors real ESG providers:
- E/S/G sub-scores (0-100)
- Overall ESG score (weighted average)
- Carbon intensity (tCO2e per $M revenue)
- Controversy flags
"""

import hashlib
from src.services.risk_models import PortfolioESG, PositionESG


# Mock ESG data based on sector patterns
# In production: MSCI ESG API, Sustainalytics API, or Bloomberg ESG
SECTOR_ESG_PROFILES = {
    "Technology": {"e": 65, "s": 70, "g": 75, "carbon": 45},
    "Financial Services": {"e": 55, "s": 65, "g": 80, "carbon": 25},
    "Healthcare": {"e": 60, "s": 75, "g": 70, "carbon": 55},
    "Consumer Cyclical": {"e": 50, "s": 60, "g": 65, "carbon": 120},
    "Communication Services": {"e": 60, "s": 55, "g": 70, "carbon": 35},
    "Industrials": {"e": 45, "s": 60, "g": 65, "carbon": 250},
    "Consumer Defensive": {"e": 55, "s": 65, "g": 70, "carbon": 150},
    "Energy": {"e": 30, "s": 55, "g": 60, "carbon": 450},
    "Utilities": {"e": 40, "s": 60, "g": 65, "carbon": 380},
    "Basic Materials": {"e": 35, "s": 55, "g": 60, "carbon": 320},
    "Real Estate": {"e": 50, "s": 60, "g": 70, "carbon": 85},
    "Unknown": {"e": 50, "s": 50, "g": 50, "carbon": 150},
    "Cash": {"e": 100, "s": 100, "g": 100, "carbon": 0},
}

# Controversies by sector (for demo)
CONTROVERSY_TICKERS = {"XOM", "CVX", "META", "GOOGL"}


class ESGService:
    """ESG scoring and carbon metrics service."""

    BENCHMARK_CARBON_INTENSITY = 140  # SPY average ~140 tCO2e/$M

    def _generate_deterministic_variation(self, ticker: str, base: float, range_pct: float = 0.2) -> float:
        """Generate consistent variation for a ticker using hash."""
        hash_val = int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16)
        variation = (hash_val % 100 - 50) / 50 * range_pct
        return max(0, min(100, base * (1 + variation)))

    def get_position_esg(
        self,
        ticker: str,
        name: str,
        weight: float,
        sector: str,
    ) -> PositionESG:
        """Get ESG data for a single position.

        Note: Mock data for demo. Production would call ESG data provider API.
        """
        if ticker == "CASH":
            return PositionESG(
                ticker=ticker,
                name=name,
                weight=round(weight * 100, 2),
                esg_score=100,
                environmental=100,
                social=100,
                governance=100,
                carbon_intensity=0,
                controversy_flag=False,
                controversy_details=None,
            )

        profile = SECTOR_ESG_PROFILES.get(sector, SECTOR_ESG_PROFILES["Unknown"])

        # Generate deterministic but varied scores per ticker
        env_score = self._generate_deterministic_variation(ticker + "_E", profile["e"])
        soc_score = self._generate_deterministic_variation(ticker + "_S", profile["s"])
        gov_score = self._generate_deterministic_variation(ticker + "_G", profile["g"])

        # ESG score is weighted average (typical MSCI weighting)
        esg_score = env_score * 0.35 + soc_score * 0.30 + gov_score * 0.35

        # Carbon intensity with variation
        carbon = self._generate_deterministic_variation(
            ticker + "_C", profile["carbon"], 0.3
        )

        # Controversy check
        has_controversy = ticker in CONTROVERSY_TICKERS
        controversy_details = None
        if has_controversy:
            if ticker in {"XOM", "CVX"}:
                controversy_details = "Environmental litigation - climate change disclosure"
            elif ticker == "META":
                controversy_details = "Data privacy and content moderation concerns"
            elif ticker == "GOOGL":
                controversy_details = "Antitrust investigations in multiple jurisdictions"

        return PositionESG(
            ticker=ticker,
            name=name,
            weight=round(weight * 100, 2),
            esg_score=round(esg_score, 1),
            environmental=round(env_score, 1),
            social=round(soc_score, 1),
            governance=round(gov_score, 1),
            carbon_intensity=round(carbon, 1),
            controversy_flag=has_controversy,
            controversy_details=controversy_details,
        )

    def _get_esg_rating(self, score: float) -> str:
        """Convert numeric ESG score to letter rating (MSCI style)."""
        if score >= 85:
            return "AAA"
        elif score >= 70:
            return "AA"
        elif score >= 60:
            return "A"
        elif score >= 50:
            return "BBB"
        elif score >= 40:
            return "BB"
        elif score >= 30:
            return "B"
        else:
            return "CCC"

    def calculate_portfolio_esg(
        self,
        positions: list[dict],
        sector_map: dict[str, str],
    ) -> PortfolioESG:
        """Calculate portfolio-level ESG metrics.

        Args:
            positions: List of position dicts with ticker, name, weight
            sector_map: Mapping of ticker to sector
        """
        position_esg_data = []
        total_weight = 0
        weighted_esg = 0
        weighted_e = 0
        weighted_s = 0
        weighted_g = 0
        weighted_carbon = 0
        num_flagged = 0
        rating_dist: dict[str, int] = {}

        for pos in positions:
            ticker = pos["ticker"]
            weight = pos["weight"]

            if ticker == "CASH":
                continue

            sector = sector_map.get(ticker, "Unknown")
            esg_data = self.get_position_esg(
                ticker=ticker,
                name=pos.get("name", ticker),
                weight=weight,
                sector=sector,
            )
            position_esg_data.append(esg_data)

            # Aggregate weighted metrics
            total_weight += weight
            weighted_esg += esg_data.esg_score * weight
            weighted_e += esg_data.environmental * weight
            weighted_s += esg_data.social * weight
            weighted_g += esg_data.governance * weight
            weighted_carbon += esg_data.carbon_intensity * weight

            if esg_data.controversy_flag:
                num_flagged += 1

            # Rating distribution
            rating = self._get_esg_rating(esg_data.esg_score)
            rating_dist[rating] = rating_dist.get(rating, 0) + 1

        # Normalize to portfolio weights
        if total_weight > 0:
            portfolio_esg = weighted_esg / total_weight
            portfolio_e = weighted_e / total_weight
            portfolio_s = weighted_s / total_weight
            portfolio_g = weighted_g / total_weight
            portfolio_carbon = weighted_carbon / total_weight
        else:
            portfolio_esg = 0
            portfolio_e = 0
            portfolio_s = 0
            portfolio_g = 0
            portfolio_carbon = 0

        # Carbon vs benchmark
        carbon_vs_bench = (
            (portfolio_carbon - self.BENCHMARK_CARBON_INTENSITY)
            / self.BENCHMARK_CARBON_INTENSITY
            * 100
        )

        # Coverage (assume all non-cash has ESG data in this demo)
        coverage = total_weight * 100 if total_weight > 0 else 0

        # Sort positions by ESG score (worst first for attention)
        position_esg_data.sort(key=lambda x: x.esg_score)

        return PortfolioESG(
            portfolio_esg_score=round(portfolio_esg, 1),
            portfolio_environmental=round(portfolio_e, 1),
            portfolio_social=round(portfolio_s, 1),
            portfolio_governance=round(portfolio_g, 1),
            portfolio_carbon_intensity=round(portfolio_carbon, 1),
            benchmark_carbon_intensity=self.BENCHMARK_CARBON_INTENSITY,
            carbon_vs_benchmark=round(carbon_vs_bench, 1),
            coverage_pct=round(coverage, 1),
            num_flagged=num_flagged,
            positions=position_esg_data,
            rating_distribution=rating_dist,
        )
