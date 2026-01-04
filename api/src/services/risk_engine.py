import numpy as np
from scipy import stats

from src.services.risk_models import (
    BenchmarkComparison,
    BetaMetrics,
    ComparativeRiskMetrics,
    FactorExposures,
    MonteCarloFanChart,
    MonteCarloResult,
    PerformanceAttribution,
    PerformanceMetrics,
    PeriodReturns,
    PortfolioLiquidity,
    PositionContribution,
    PositionLiquidity,
    RiskAdjustedRatios,
    RiskContribution,
    RiskMetrics,
    RollingMetrics,
    SectorConcentration,
    SectorExposure,
    TailRiskStats,
    VarBacktest,
    WhatIfResult,
)


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

    def _calculate_delta(self, a: RiskMetrics, b: RiskMetrics) -> dict[str, float]:
        """Calculate difference between two RiskMetrics (a - b)."""
        return {
            "var_95": round(a.var_95 - b.var_95, 2),
            "var_99": round(a.var_99 - b.var_99, 2),
            "cvar_95": round(a.cvar_95 - b.cvar_95, 2),
            "volatility": round(a.volatility - b.volatility, 2),
            "sharpe": round(a.sharpe - b.sharpe, 2),
            "max_drawdown": round(a.max_drawdown - b.max_drawdown, 2),
        }

    def calculate_comparative_risk(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
        benchmark_history: list[dict] | None = None,
    ) -> ComparativeRiskMetrics | None:
        """Calculate risk metrics for both portfolio and benchmark."""
        portfolio_returns = self.calculate_portfolio_returns(histories, weights)
        if portfolio_returns is None:
            return None

        portfolio_metrics = self.calculate_risk_metrics(portfolio_returns)

        if benchmark_history:
            benchmark_prices = [d["close"] for d in benchmark_history]
            benchmark_returns = self.calculate_returns(benchmark_prices)
            # Align lengths
            min_len = min(len(portfolio_returns), len(benchmark_returns))
            benchmark_returns = benchmark_returns[-min_len:]
            benchmark_metrics = self.calculate_risk_metrics(benchmark_returns)
            delta = self._calculate_delta(portfolio_metrics, benchmark_metrics)
        else:
            benchmark_metrics = None
            delta = None

        return ComparativeRiskMetrics(
            portfolio=portfolio_metrics,
            benchmark=benchmark_metrics,
            delta=delta,
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
        horizon: int = 252,
    ) -> MonteCarloResult | None:
        """Simulate portfolio paths using GBM and calculate VaR distribution.

        Uses Geometric Brownian Motion: dS/S = μdt + σdW
        Returns fan chart percentile bands and terminal distribution.
        """
        returns = self.calculate_portfolio_returns(histories, weights)
        if returns is None:
            return None

        # Estimate parameters from historical returns
        mu = np.mean(returns)  # daily drift
        sigma = np.std(returns)  # daily volatility

        # Generate random walks for all simulations
        np.random.seed(42)
        dt = 1  # 1 day steps
        random_shocks = np.random.normal(0, 1, (simulations, horizon))

        # GBM simulation: S(t+dt) = S(t) * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
        # Start at 100 (normalized portfolio value)
        log_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * random_shocks
        cumulative_returns = np.cumsum(log_returns, axis=1)

        # Convert to price paths (starting at 100)
        paths = 100 * np.exp(cumulative_returns)

        # Add starting point (day 0 = 100)
        paths = np.column_stack([np.full(simulations, 100), paths])

        # Calculate percentile bands at each time step
        days = list(range(horizon + 1))
        p1 = [round(float(np.percentile(paths[:, i], 1)), 2) for i in range(horizon + 1)]
        p5 = [round(float(np.percentile(paths[:, i], 5)), 2) for i in range(horizon + 1)]
        p25 = [round(float(np.percentile(paths[:, i], 25)), 2) for i in range(horizon + 1)]
        p50 = [round(float(np.percentile(paths[:, i], 50)), 2) for i in range(horizon + 1)]
        p75 = [round(float(np.percentile(paths[:, i], 75)), 2) for i in range(horizon + 1)]
        p95 = [round(float(np.percentile(paths[:, i], 95)), 2) for i in range(horizon + 1)]
        p99 = [round(float(np.percentile(paths[:, i], 99)), 2) for i in range(horizon + 1)]

        # Terminal distribution (final values as returns from 100)
        terminal_values = paths[:, -1]
        terminal_returns = (terminal_values - 100) / 100  # as decimal returns

        # VaR and CVaR at horizon (as percentage loss from starting value)
        var_95 = 100 - np.percentile(terminal_values, 5)  # 5th percentile of value = 95% VaR
        var_99 = 100 - np.percentile(terminal_values, 1)  # 1st percentile of value = 99% VaR
        cvar_95 = 100 - np.mean(terminal_values[terminal_values <= np.percentile(terminal_values, 5)])
        cvar_99 = 100 - np.mean(terminal_values[terminal_values <= np.percentile(terminal_values, 1)])

        # Sample terminal distribution for histogram (500 random samples)
        sample_indices = np.random.choice(simulations, min(500, simulations), replace=False)
        terminal_sample = [round(float(terminal_values[i]), 2) for i in sample_indices]

        return MonteCarloResult(
            simulations=simulations,
            horizon=horizon,
            var_95=round(var_95, 2),
            var_99=round(var_99, 2),
            cvar_95=round(cvar_95, 2),
            cvar_99=round(cvar_99, 2),
            fan_chart=MonteCarloFanChart(
                days=days,
                p1=p1,
                p5=p5,
                p25=p25,
                p50=p50,
                p75=p75,
                p95=p95,
                p99=p99,
            ),
            terminal_distribution=terminal_sample,
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

    # ========================================================================
    # PERFORMANCE METHODS
    # ========================================================================

    def _get_period_start_index(self, dates: list[str], period: str) -> int | None:
        """Find index for period start (MTD, QTD, YTD, 1Y)."""
        from datetime import datetime, timedelta

        if not dates:
            return None

        end_date = datetime.strptime(dates[-1], "%Y-%m-%d")

        if period == "MTD":
            target = end_date.replace(day=1)
        elif period == "QTD":
            quarter_month = ((end_date.month - 1) // 3) * 3 + 1
            target = end_date.replace(month=quarter_month, day=1)
        elif period == "YTD":
            target = end_date.replace(month=1, day=1)
        elif period == "1Y":
            target = end_date - timedelta(days=365)
        else:
            return None

        # Find closest date >= target
        for i, d in enumerate(dates):
            if datetime.strptime(d, "%Y-%m-%d") >= target:
                return i
        return None

    def calculate_period_returns(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
    ) -> PeriodReturns | None:
        """Calculate returns for various periods."""
        returns, dates = self._get_aligned_returns_with_dates(histories, weights)
        if returns is None or len(returns) < 2:
            return None

        # Cumulative returns for full period
        cumulative = np.cumprod(1 + returns)
        total_return = (cumulative[-1] - 1)
        n_days = len(returns)
        annualized = (1 + total_return) ** (self.TRADING_DAYS / n_days) - 1

        # Period returns
        period_returns = {}
        for period in ["MTD", "QTD", "YTD", "1Y"]:
            idx = self._get_period_start_index(dates, period)
            if idx is not None and idx < len(cumulative):
                start_val = cumulative[idx - 1] if idx > 0 else 1.0
                period_returns[period] = (cumulative[-1] / start_val) - 1
            else:
                period_returns[period] = None

        return PeriodReturns(
            mtd=round(period_returns["MTD"] * 100, 2) if period_returns["MTD"] is not None else None,
            qtd=round(period_returns["QTD"] * 100, 2) if period_returns["QTD"] is not None else None,
            ytd=round(period_returns["YTD"] * 100, 2) if period_returns["YTD"] is not None else None,
            one_year=round(period_returns["1Y"] * 100, 2) if period_returns["1Y"] is not None else None,
            since_inception=round(total_return * 100, 2),
            annualized=round(annualized * 100, 2),
        )

    def calculate_benchmark_comparison(
        self,
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray,
    ) -> BenchmarkComparison | None:
        """Compare portfolio vs benchmark performance."""
        if len(portfolio_returns) != len(benchmark_returns):
            min_len = min(len(portfolio_returns), len(benchmark_returns))
            portfolio_returns = portfolio_returns[-min_len:]
            benchmark_returns = benchmark_returns[-min_len:]

        if len(portfolio_returns) < 20:
            return None

        # Total returns
        port_total = np.prod(1 + portfolio_returns) - 1
        bench_total = np.prod(1 + benchmark_returns) - 1
        active_return = port_total - bench_total

        # Tracking error (annualized volatility of active returns)
        active_returns = portfolio_returns - benchmark_returns
        tracking_error = np.std(active_returns) * np.sqrt(self.TRADING_DAYS)

        # Information ratio (annualized)
        active_return_ann = np.mean(active_returns) * self.TRADING_DAYS
        info_ratio = active_return_ann / tracking_error if tracking_error > 0 else None

        return BenchmarkComparison(
            portfolio_return=round(port_total * 100, 2),
            benchmark_return=round(bench_total * 100, 2),
            active_return=round(active_return * 100, 2),
            tracking_error=round(tracking_error * 100, 2),
            information_ratio=round(info_ratio, 2) if info_ratio is not None else None,
        )

    def calculate_risk_adjusted_ratios(
        self,
        returns: np.ndarray,
        beta: float | None = None,
        max_drawdown: float | None = None,
    ) -> RiskAdjustedRatios:
        """Calculate Sharpe, Sortino, Treynor, Calmar ratios."""
        mean_return = np.mean(returns) * self.TRADING_DAYS
        volatility = np.std(returns) * np.sqrt(self.TRADING_DAYS)
        excess_return = mean_return - self.RISK_FREE_RATE

        # Sharpe
        sharpe = excess_return / volatility if volatility > 0 else 0

        # Sortino (downside deviation)
        negative_returns = returns[returns < 0]
        downside_vol = np.std(negative_returns) * np.sqrt(self.TRADING_DAYS) if len(negative_returns) > 0 else 0
        sortino = excess_return / downside_vol if downside_vol > 0 else 0

        # Treynor (requires beta)
        treynor = excess_return / beta if beta and beta > 0 else None

        # Calmar (requires max drawdown)
        calmar = mean_return / max_drawdown if max_drawdown and max_drawdown > 0 else None

        return RiskAdjustedRatios(
            sharpe=round(sharpe, 2),
            sortino=round(sortino, 2),
            treynor=round(treynor, 2) if treynor is not None else None,
            calmar=round(calmar, 2) if calmar is not None else None,
        )

    def calculate_performance_attribution(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
    ) -> PerformanceAttribution | None:
        """Calculate contribution of each position to total return."""
        tickers = [t for t in weights.keys() if t != "CASH" and histories.get(t)]
        if not tickers:
            return None

        min_len = min(len(histories[t]) for t in tickers)
        if min_len < 2:
            return None

        contributions = []
        total_contribution = 0

        for ticker in tickers:
            prices = [d["close"] for d in histories[ticker][-min_len:]]
            position_return = (prices[-1] / prices[0]) - 1
            weight = weights[ticker]
            contribution = weight * position_return
            total_contribution += contribution

            contributions.append({
                "ticker": ticker,
                "weight": weight,
                "position_return": position_return,
                "contribution": contribution,
            })

        # Calculate percentage of total
        result = []
        for c in contributions:
            pct = (c["contribution"] / total_contribution * 100) if total_contribution != 0 else 0
            result.append(PositionContribution(
                ticker=c["ticker"],
                weight=round(c["weight"] * 100, 2),
                position_return=round(c["position_return"] * 100, 2),
                contribution=round(c["contribution"] * 100, 2),
                pct_of_total=round(pct, 1),
            ))

        # Sort by contribution (descending)
        result.sort(key=lambda x: x.contribution, reverse=True)

        return PerformanceAttribution(
            total_return=round(total_contribution * 100, 2),
            contributions=result,
        )

    def calculate_performance_metrics(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
        benchmark_history: list[dict] | None = None,
    ) -> PerformanceMetrics | None:
        """Calculate comprehensive performance metrics."""
        # Period returns
        period_returns = self.calculate_period_returns(histories, weights)
        if period_returns is None:
            return None

        # Portfolio returns for other calculations
        portfolio_returns = self.calculate_portfolio_returns(histories, weights)
        if portfolio_returns is None:
            return None

        # Benchmark comparison
        if benchmark_history:
            bench_prices = [d["close"] for d in benchmark_history]
            bench_returns = self.calculate_returns(bench_prices)
            # Align lengths
            min_len = min(len(portfolio_returns), len(bench_returns))
            benchmark = self.calculate_benchmark_comparison(
                portfolio_returns[-min_len:],
                bench_returns[-min_len:],
            )
            # Get beta for Treynor
            beta_metrics = self.calculate_beta(portfolio_returns[-min_len:], bench_returns[-min_len:])
            beta = beta_metrics.beta if beta_metrics else None
        else:
            benchmark = BenchmarkComparison(
                portfolio_return=period_returns.since_inception,
                benchmark_return=0,
                active_return=period_returns.since_inception,
                tracking_error=0,
                information_ratio=None,
            )
            beta = None

        # Risk metrics for Calmar
        risk_metrics = self.calculate_risk_metrics(portfolio_returns)
        max_dd = risk_metrics.max_drawdown / 100 if risk_metrics else None

        # Risk-adjusted ratios
        risk_adjusted = self.calculate_risk_adjusted_ratios(
            portfolio_returns,
            beta=beta,
            max_drawdown=max_dd,
        )

        # Attribution
        attribution = self.calculate_performance_attribution(histories, weights)
        if attribution is None:
            attribution = PerformanceAttribution(total_return=0, contributions=[])

        return PerformanceMetrics(
            period_returns=period_returns,
            benchmark=benchmark,
            risk_adjusted=risk_adjusted,
            attribution=attribution,
        )
