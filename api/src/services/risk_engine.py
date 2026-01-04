import numpy as np
from pydantic import BaseModel
from scipy import stats


class RiskMetrics(BaseModel):
    var_95: float
    var_99: float
    cvar_95: float
    volatility: float
    sharpe: float
    max_drawdown: float
    current_drawdown: float


class RiskContribution(BaseModel):
    ticker: str
    weight: float
    volatility: float
    marginal_var: float
    component_var: float
    pct_contribution: float


# ============================================================================
# ADVANCED RISK MODELS
# ============================================================================


class RollingMetrics(BaseModel):
    dates: list[str]
    rolling_var_95: list[float]
    rolling_volatility: list[float]
    drawdown_series: list[float]


class TailRiskStats(BaseModel):
    skewness: float
    kurtosis: float
    worst_days: list[dict]
    best_days: list[dict]


class BetaMetrics(BaseModel):
    beta: float
    alpha: float
    r_squared: float
    correlation: float


class VarBacktest(BaseModel):
    dates: list[str]
    predicted_var: list[float]
    realized_returns: list[float]
    breaches: int
    breach_rate: float


class SectorExposure(BaseModel):
    sector: str
    weight: float
    tickers: list[str]


class SectorConcentration(BaseModel):
    sectors: list[SectorExposure]
    hhi: float


class PositionLiquidity(BaseModel):
    ticker: str
    avg_volume: float
    avg_dollar_volume: float
    days_to_liquidate: float
    score: float


class PortfolioLiquidity(BaseModel):
    positions: list[PositionLiquidity]
    weighted_score: float


class WhatIfResult(BaseModel):
    original: RiskMetrics
    modified: RiskMetrics
    delta: dict[str, float]


class MonteCarloResult(BaseModel):
    simulations: int
    var_95: float
    var_99: float
    cvar_95: float
    percentiles: list[float]


class FactorExposures(BaseModel):
    market_beta: float
    size_beta: float
    value_beta: float
    r_squared: float


class RiskEngine:
    TRADING_DAYS = 252
    RISK_FREE_RATE = 0.05  # 5% annual

    def calculate_returns(self, prices: list[float]) -> np.ndarray:
        prices_arr = np.array(prices)
        returns = np.log(prices_arr[1:] / prices_arr[:-1])
        return returns

    def calculate_portfolio_returns(
        self, histories: dict[str, list[dict]], weights: dict[str, float]
    ) -> np.ndarray | None:
        tickers = [t for t in weights.keys() if t != "CASH" and histories.get(t)]

        if not tickers:
            return None

        min_len = min(len(histories[t]) for t in tickers)
        if min_len < 20:
            return None

        returns_matrix = []
        weight_list = []

        for ticker in tickers:
            prices = [d["close"] for d in histories[ticker][-min_len:]]
            returns = self.calculate_returns(prices)
            returns_matrix.append(returns)
            weight_list.append(weights[ticker])

        returns_matrix = np.array(returns_matrix)
        weights_arr = np.array(weight_list)
        weights_arr = weights_arr / weights_arr.sum()

        portfolio_returns = np.dot(weights_arr, returns_matrix)
        return portfolio_returns

    def calculate_risk_metrics(self, returns: np.ndarray) -> RiskMetrics:
        volatility = np.std(returns) * np.sqrt(self.TRADING_DAYS)
        mean_return = np.mean(returns) * self.TRADING_DAYS

        var_95 = -np.percentile(returns, 5) * np.sqrt(self.TRADING_DAYS)
        var_99 = -np.percentile(returns, 1) * np.sqrt(self.TRADING_DAYS)

        cvar_95 = -np.mean(returns[returns <= np.percentile(returns, 5)]) * np.sqrt(
            self.TRADING_DAYS
        )

        sharpe = (mean_return - self.RISK_FREE_RATE) / volatility if volatility > 0 else 0

        cumulative = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak) / peak
        max_drawdown = -np.min(drawdown)
        current_drawdown = -drawdown[-1] if len(drawdown) > 0 else 0

        return RiskMetrics(
            var_95=round(var_95 * 100, 2),
            var_99=round(var_99 * 100, 2),
            cvar_95=round(cvar_95 * 100, 2),
            volatility=round(volatility * 100, 2),
            sharpe=round(sharpe, 2),
            max_drawdown=round(max_drawdown * 100, 2),
            current_drawdown=round(current_drawdown * 100, 2),
        )

    def calculate_risk_contributions(
        self, histories: dict[str, list[dict]], weights: dict[str, float]
    ) -> list[RiskContribution]:
        tickers = [t for t in weights.keys() if t != "CASH" and histories.get(t)]

        if not tickers:
            return []

        min_len = min(len(histories[t]) for t in tickers)
        if min_len < 20:
            return []

        returns_matrix = []
        weight_list = []

        for ticker in tickers:
            prices = [d["close"] for d in histories[ticker][-min_len:]]
            returns = self.calculate_returns(prices)
            returns_matrix.append(returns)
            weight_list.append(weights[ticker])

        returns_matrix = np.array(returns_matrix)
        weights_arr = np.array(weight_list)
        weights_arr = weights_arr / weights_arr.sum()

        cov_matrix = np.cov(returns_matrix) * self.TRADING_DAYS

        portfolio_var = np.dot(weights_arr, np.dot(cov_matrix, weights_arr))
        portfolio_vol = np.sqrt(portfolio_var)

        marginal_var = np.dot(cov_matrix, weights_arr) / portfolio_vol
        component_var = weights_arr * marginal_var

        var_95_factor = stats.norm.ppf(0.95)
        contributions = []

        for i, ticker in enumerate(tickers):
            vol = np.sqrt(cov_matrix[i, i])
            contributions.append(
                RiskContribution(
                    ticker=ticker,
                    weight=round(weights_arr[i] * 100, 2),
                    volatility=round(vol * 100, 2),
                    marginal_var=round(marginal_var[i] * var_95_factor * 100, 2),
                    component_var=round(component_var[i] * var_95_factor * 100, 2),
                    pct_contribution=round(component_var[i] / portfolio_vol * 100, 2),
                )
            )

        return sorted(contributions, key=lambda x: x.pct_contribution, reverse=True)

    def calculate_correlation_matrix(
        self, histories: dict[str, list[dict]], tickers: list[str]
    ) -> dict:
        valid_tickers = [t for t in tickers if t != "CASH" and histories.get(t)]

        if len(valid_tickers) < 2:
            return {"tickers": [], "matrix": []}

        min_len = min(len(histories[t]) for t in valid_tickers)
        if min_len < 20:
            return {"tickers": [], "matrix": []}

        returns_matrix = []
        for ticker in valid_tickers:
            prices = [d["close"] for d in histories[ticker][-min_len:]]
            returns = self.calculate_returns(prices)
            returns_matrix.append(returns)

        corr_matrix = np.corrcoef(returns_matrix)

        return {
            "tickers": valid_tickers,
            "matrix": [[round(x, 2) for x in row] for row in corr_matrix.tolist()],
        }

    # ========================================================================
    # ADVANCED RISK METHODS
    # ========================================================================

    def _get_aligned_returns_with_dates(
        self, histories: dict[str, list[dict]], weights: dict[str, float]
    ) -> tuple[np.ndarray, list[str]] | tuple[None, None]:
        """Helper: get portfolio returns aligned with dates."""
        tickers = [t for t in weights.keys() if t != "CASH" and histories.get(t)]
        if not tickers:
            return None, None

        min_len = min(len(histories[t]) for t in tickers)
        if min_len < 20:
            return None, None

        # Get dates from first ticker
        dates = [d["date"] for d in histories[tickers[0]][-min_len:]][1:]

        returns_matrix = []
        weight_list = []
        for ticker in tickers:
            prices = [d["close"] for d in histories[ticker][-min_len:]]
            returns_matrix.append(self.calculate_returns(prices))
            weight_list.append(weights[ticker])

        returns_matrix = np.array(returns_matrix)
        weights_arr = np.array(weight_list)
        weights_arr = weights_arr / weights_arr.sum()

        portfolio_returns = np.dot(weights_arr, returns_matrix)
        return portfolio_returns, dates

    def calculate_rolling_metrics(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
        window: int = 20,
    ) -> RollingMetrics | None:
        """Calculate rolling VaR, volatility, and drawdown time series."""
        returns, dates = self._get_aligned_returns_with_dates(histories, weights)
        if returns is None or len(returns) < window:
            return None

        n = len(returns)
        rolling_var = []
        rolling_vol = []

        for i in range(window, n + 1):
            window_returns = returns[i - window : i]
            vol = np.std(window_returns) * np.sqrt(self.TRADING_DAYS)
            var = -np.percentile(window_returns, 5) * np.sqrt(self.TRADING_DAYS)
            rolling_vol.append(round(vol * 100, 2))
            rolling_var.append(round(var * 100, 2))

        # Drawdown series
        cumulative = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = ((cumulative - peak) / peak * 100).tolist()

        # Align dates with rolling window
        rolling_dates = dates[window - 1 :]

        return RollingMetrics(
            dates=rolling_dates,
            rolling_var_95=rolling_var,
            rolling_volatility=rolling_vol,
            drawdown_series=[round(d, 2) for d in drawdown[window - 1 :]],
        )

    def calculate_tail_risk(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
        n: int = 10,
    ) -> TailRiskStats | None:
        """Calculate skewness, kurtosis, and worst/best days."""
        returns, dates = self._get_aligned_returns_with_dates(histories, weights)
        if returns is None:
            return None

        skewness = float(stats.skew(returns))
        kurtosis = float(stats.kurtosis(returns))

        # Pair returns with dates and sort
        paired = list(zip(dates, returns * 100))
        sorted_by_return = sorted(paired, key=lambda x: x[1])

        worst_days = [{"date": d, "return_pct": round(r, 2)} for d, r in sorted_by_return[:n]]
        best_days = [{"date": d, "return_pct": round(r, 2)} for d, r in sorted_by_return[-n:][::-1]]

        return TailRiskStats(
            skewness=round(skewness, 3),
            kurtosis=round(kurtosis, 3),
            worst_days=worst_days,
            best_days=best_days,
        )

    def calculate_beta(
        self, portfolio_returns: np.ndarray, benchmark_returns: np.ndarray
    ) -> BetaMetrics | None:
        """Calculate beta, alpha, R-squared vs benchmark."""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 20:
            return None

        # Covariance / variance method
        cov = np.cov(portfolio_returns, benchmark_returns)[0, 1]
        var_benchmark = np.var(benchmark_returns)
        beta = cov / var_benchmark if var_benchmark > 0 else 0

        # Alpha (annualized)
        alpha = (np.mean(portfolio_returns) - beta * np.mean(benchmark_returns)) * self.TRADING_DAYS

        # R-squared
        correlation = np.corrcoef(portfolio_returns, benchmark_returns)[0, 1]
        r_squared = correlation**2

        return BetaMetrics(
            beta=round(beta, 3),
            alpha=round(alpha * 100, 2),
            r_squared=round(r_squared, 3),
            correlation=round(correlation, 3),
        )

    def backtest_var(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
        window: int = 60,
        confidence: float = 0.95,
    ) -> VarBacktest | None:
        """Compare predicted VaR to realized returns."""
        returns, dates = self._get_aligned_returns_with_dates(histories, weights)
        if returns is None or len(returns) < window + 1:
            return None

        percentile = (1 - confidence) * 100
        predicted_var = []
        realized = []
        backtest_dates = []

        for i in range(window, len(returns)):
            window_returns = returns[i - window : i]
            var = -np.percentile(window_returns, percentile)
            predicted_var.append(round(var * 100, 2))
            realized.append(round(returns[i] * 100, 2))
            backtest_dates.append(dates[i])

        # Count breaches (realized loss > predicted VaR)
        breaches = sum(1 for r, v in zip(realized, predicted_var) if r < -v)
        breach_rate = breaches / len(realized) if realized else 0

        return VarBacktest(
            dates=backtest_dates,
            predicted_var=predicted_var,
            realized_returns=realized,
            breaches=breaches,
            breach_rate=round(breach_rate * 100, 2),
        )

    def calculate_sector_concentration(
        self, weights: dict[str, float], sector_map: dict[str, str]
    ) -> SectorConcentration:
        """Calculate sector concentration and HHI."""
        sector_weights: dict[str, dict] = {}

        for ticker, weight in weights.items():
            if ticker == "CASH":
                sector = "Cash"
            else:
                sector = sector_map.get(ticker, "Unknown")

            if sector not in sector_weights:
                sector_weights[sector] = {"weight": 0, "tickers": []}
            sector_weights[sector]["weight"] += weight
            sector_weights[sector]["tickers"].append(ticker)

        sectors = [
            SectorExposure(
                sector=s,
                weight=round(data["weight"] * 100, 2),
                tickers=data["tickers"],
            )
            for s, data in sorted(sector_weights.items(), key=lambda x: -x[1]["weight"])
        ]

        # HHI = sum of squared weights (0-10000 scale)
        hhi = sum((data["weight"] * 100) ** 2 for data in sector_weights.values())

        return SectorConcentration(sectors=sectors, hhi=round(hhi, 0))

    def calculate_liquidity(
        self,
        weights: dict[str, float],
        volume_data: dict[str, dict],
        portfolio_value: float = 1_000_000,
    ) -> PortfolioLiquidity:
        """Calculate liquidity scores based on volume."""
        positions = []

        for ticker, weight in weights.items():
            if ticker == "CASH":
                continue

            data = volume_data.get(ticker, {})
            avg_volume = data.get("avg_volume", 0)
            avg_price = data.get("avg_price", 0)
            avg_dollar_volume = avg_volume * avg_price

            position_value = portfolio_value * weight
            days_to_liquidate = (
                position_value / (avg_dollar_volume * 0.1) if avg_dollar_volume > 0 else 999
            )

            # Score: 100 if < 1 day, decreases logarithmically
            if days_to_liquidate < 1:
                score = 100
            elif days_to_liquidate > 30:
                score = 0
            else:
                score = max(0, 100 - (np.log(days_to_liquidate + 1) / np.log(31)) * 100)

            positions.append(
                PositionLiquidity(
                    ticker=ticker,
                    avg_volume=round(avg_volume, 0),
                    avg_dollar_volume=round(avg_dollar_volume, 0),
                    days_to_liquidate=round(days_to_liquidate, 1),
                    score=round(score, 0),
                )
            )

        # Weighted average score
        total_weight = sum(weights.get(p.ticker, 0) for p in positions)
        weighted_score = (
            sum(p.score * weights.get(p.ticker, 0) for p in positions) / total_weight
            if total_weight > 0
            else 0
        )

        return PortfolioLiquidity(
            positions=sorted(positions, key=lambda x: x.score),
            weighted_score=round(weighted_score, 0),
        )

    def calculate_what_if(
        self,
        histories: dict[str, list[dict]],
        original_weights: dict[str, float],
        modified_weights: dict[str, float],
    ) -> WhatIfResult | None:
        """Calculate risk impact of position changes."""
        original_returns = self.calculate_portfolio_returns(histories, original_weights)
        modified_returns = self.calculate_portfolio_returns(histories, modified_weights)

        if original_returns is None or modified_returns is None:
            return None

        original = self.calculate_risk_metrics(original_returns)
        modified = self.calculate_risk_metrics(modified_returns)

        delta = {
            "var_95": round(modified.var_95 - original.var_95, 2),
            "var_99": round(modified.var_99 - original.var_99, 2),
            "cvar_95": round(modified.cvar_95 - original.cvar_95, 2),
            "volatility": round(modified.volatility - original.volatility, 2),
            "sharpe": round(modified.sharpe - original.sharpe, 2),
            "max_drawdown": round(modified.max_drawdown - original.max_drawdown, 2),
        }

        return WhatIfResult(original=original, modified=modified, delta=delta)

    def calculate_monte_carlo(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
        simulations: int = 10000,
        horizon: int = 1,
    ) -> MonteCarloResult | None:
        """Simulate portfolio returns and calculate VaR distribution."""
        returns = self.calculate_portfolio_returns(histories, weights)
        if returns is None:
            return None

        # Fit to historical distribution
        mean = np.mean(returns) * horizon
        std = np.std(returns) * np.sqrt(horizon)

        # Generate simulations
        np.random.seed(42)
        simulated = np.random.normal(mean, std, simulations)

        # Calculate VaR metrics from simulations
        var_95 = -np.percentile(simulated, 5)
        var_99 = -np.percentile(simulated, 1)
        cvar_95 = -np.mean(simulated[simulated <= np.percentile(simulated, 5)])

        # Percentiles for histogram (5th, 25th, 50th, 75th, 95th)
        percentiles = [float(np.percentile(simulated, p)) for p in [5, 25, 50, 75, 95]]

        return MonteCarloResult(
            simulations=simulations,
            var_95=round(var_95 * 100, 2),
            var_99=round(var_99 * 100, 2),
            cvar_95=round(cvar_95 * 100, 2),
            percentiles=[round(p * 100, 2) for p in percentiles],
        )

    def calculate_factor_exposures(
        self,
        portfolio_returns: np.ndarray,
        factor_returns: dict[str, np.ndarray],
    ) -> FactorExposures | None:
        """Multi-factor regression for exposures."""
        factors = ["SPY", "IWM", "IVE"]
        if not all(f in factor_returns for f in factors):
            return None

        n = len(portfolio_returns)
        for f in factors:
            if len(factor_returns[f]) != n:
                return None

        # Build factor matrix
        X = np.column_stack([factor_returns[f] for f in factors])
        X = np.column_stack([np.ones(n), X])  # Add intercept

        # OLS regression
        try:
            betas, residuals, rank, s = np.linalg.lstsq(X, portfolio_returns, rcond=None)
        except np.linalg.LinAlgError:
            return None

        # R-squared
        ss_res = np.sum((portfolio_returns - X @ betas) ** 2)
        ss_tot = np.sum((portfolio_returns - np.mean(portfolio_returns)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        return FactorExposures(
            market_beta=round(betas[1], 3),
            size_beta=round(betas[2], 3),
            value_beta=round(betas[3], 3),
            r_squared=round(r_squared, 3),
        )
