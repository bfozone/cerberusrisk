"""GIPS (Global Investment Performance Standards) calculation service.

This module implements GIPS-compliant performance calculations including:
- Time-Weighted Return (TWR) with sub-period linking
- Composite statistics and dispersion
- Gross vs Net returns

Note: In production, this would integrate with a transaction system for cash flow
adjustments. This demo uses daily price data to calculate TWR.
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np

from src.services.risk_models import (
    GIPSCalendarYearReturn,
    GIPSCompositeStats,
    GIPSDisclosureItem,
    GIPSDrawdownPoint,
    GIPSMetrics,
    GIPSPeriodReturn,
    GIPSRollingReturn,
)


class GIPSService:
    """GIPS-compliant performance calculation service."""

    TRADING_DAYS = 252
    RISK_FREE_RATE = 0.05
    DEFAULT_FEE_BPS = 50  # 50 bps annual management fee

    def calculate_twr(self, prices: list[float]) -> float:
        """Calculate Time-Weighted Return using geometric linking.

        TWR = Product of (1 + sub-period returns) - 1

        This method assumes no external cash flows within the period.
        In production, would adjust for cash flows using Modified Dietz
        or True Daily Valuation.
        """
        if len(prices) < 2:
            return 0.0

        # Calculate daily returns and link geometrically
        cumulative = 1.0
        for i in range(1, len(prices)):
            daily_return = (prices[i] / prices[i - 1]) - 1
            cumulative *= 1 + daily_return

        return cumulative - 1

    def calculate_portfolio_twr(
        self, histories: dict[str, list[dict]], weights: dict[str, float]
    ) -> tuple[list[float], list[str]] | None:
        """Calculate portfolio TWR series from position histories."""
        tickers = [t for t in weights.keys() if t != "CASH" and histories.get(t)]
        if not tickers:
            return None

        min_len = min(len(histories[t]) for t in tickers)
        if min_len < 20:
            return None

        # Get dates from first ticker
        dates = [d["date"] for d in histories[tickers[0]][-min_len:]]

        # Calculate portfolio value series
        portfolio_values = []
        for i in range(min_len):
            daily_value = 0
            for ticker in tickers:
                price = histories[ticker][-min_len + i]["close"]
                # Normalize: assume initial investment based on weight
                if i == 0:
                    base_price = price
                    daily_value += weights[ticker] * 100  # Start at 100 per unit
                else:
                    base_price = histories[ticker][-min_len]["close"]
                    daily_value += weights[ticker] * 100 * (price / base_price)
            portfolio_values.append(daily_value)

        return portfolio_values, dates

    def calculate_period_returns(
        self,
        portfolio_values: list[float],
        dates: list[str],
        benchmark_prices: list[float],
        fee_bps: int = DEFAULT_FEE_BPS,
    ) -> list[GIPSPeriodReturn]:
        """Calculate monthly period returns for GIPS reporting."""
        if not portfolio_values or not dates:
            return []

        # Parse dates
        parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]

        # Group by month
        monthly_returns = []
        current_month = None
        month_start_idx = 0
        month_start_bench_idx = 0

        for i, dt in enumerate(parsed_dates):
            month_key = f"{dt.year}-{dt.month:02d}"

            if current_month is None:
                current_month = month_key
                month_start_idx = i
                month_start_bench_idx = i

            elif month_key != current_month:
                # Calculate return for completed month
                start_val = portfolio_values[month_start_idx]
                end_val = portfolio_values[i - 1]
                gross_return = (end_val / start_val) - 1 if start_val > 0 else 0

                # Net return (subtract prorated annual fee)
                daily_fee = fee_bps / 10000 / self.TRADING_DAYS
                trading_days_in_month = i - month_start_idx
                net_return = gross_return - (daily_fee * trading_days_in_month)

                # Benchmark return
                if benchmark_prices and len(benchmark_prices) > i - 1:
                    bench_start = benchmark_prices[month_start_bench_idx]
                    bench_end = benchmark_prices[i - 1]
                    bench_return = (bench_end / bench_start) - 1 if bench_start > 0 else 0
                else:
                    bench_return = 0

                prev_dt = parsed_dates[month_start_idx]
                monthly_returns.append(
                    GIPSPeriodReturn(
                        period=current_month,
                        start_date=prev_dt.strftime("%Y-%m-%d"),
                        end_date=parsed_dates[i - 1].strftime("%Y-%m-%d"),
                        twr_gross=round(gross_return * 100, 2),
                        twr_net=round(net_return * 100, 2),
                        benchmark_return=round(bench_return * 100, 2),
                        excess_return=round((gross_return - bench_return) * 100, 2),
                    )
                )

                current_month = month_key
                month_start_idx = i
                month_start_bench_idx = i

        # Handle last partial month
        if month_start_idx < len(portfolio_values) - 1:
            start_val = portfolio_values[month_start_idx]
            end_val = portfolio_values[-1]
            gross_return = (end_val / start_val) - 1 if start_val > 0 else 0
            daily_fee = fee_bps / 10000 / self.TRADING_DAYS
            trading_days = len(portfolio_values) - month_start_idx
            net_return = gross_return - (daily_fee * trading_days)

            if benchmark_prices and len(benchmark_prices) >= len(portfolio_values):
                bench_start = benchmark_prices[month_start_bench_idx]
                bench_end = benchmark_prices[-1]
                bench_return = (bench_end / bench_start) - 1 if bench_start > 0 else 0
            else:
                bench_return = 0

            monthly_returns.append(
                GIPSPeriodReturn(
                    period=current_month,
                    start_date=parsed_dates[month_start_idx].strftime("%Y-%m-%d"),
                    end_date=dates[-1],
                    twr_gross=round(gross_return * 100, 2),
                    twr_net=round(net_return * 100, 2),
                    benchmark_return=round(bench_return * 100, 2),
                    excess_return=round((gross_return - bench_return) * 100, 2),
                )
            )

        return monthly_returns

    def calculate_composite_stats(
        self, portfolio_return: float, num_portfolios: int = 8
    ) -> GIPSCompositeStats:
        """Simulate composite statistics for demo purposes.

        In production, this would aggregate returns across multiple accounts
        within the composite. Here we simulate dispersion around the portfolio return.
        """
        # Simulate returns for other portfolios in composite
        np.random.seed(42)
        simulated_returns = np.random.normal(
            portfolio_return, abs(portfolio_return * 0.1) + 0.5, num_portfolios - 1
        )
        all_returns = np.append(simulated_returns, portfolio_return)

        # Calculate dispersion (equal-weighted standard deviation)
        dispersion = float(np.std(all_returns)) if num_portfolios >= 6 else None

        # Simulate AUM distribution for representativeness
        np.random.seed(42)
        aum_weights = np.random.dirichlet(np.ones(num_portfolios) * 2)
        aum_weights = np.sort(aum_weights)[::-1]  # Sort descending
        largest_pct = float(aum_weights[0] * 100)
        top5_pct = float(np.sum(aum_weights[:5]) * 100) if num_portfolios >= 5 else 100.0

        return GIPSCompositeStats(
            num_portfolios=num_portfolios,
            total_aum=125_000_000,  # Simulated AUM
            dispersion=round(dispersion, 2) if dispersion else None,
            high_return=round(float(np.max(all_returns)), 2),
            low_return=round(float(np.min(all_returns)), 2),
            median_return=round(float(np.median(all_returns)), 2),
            largest_portfolio_pct=round(largest_pct, 1),
            top5_concentration_pct=round(top5_pct, 1),
            portfolio_returns=[round(float(r), 2) for r in all_returns],
        )

    def calculate_calendar_year_returns(
        self,
        portfolio_values: list[float],
        dates: list[str],
        benchmark_prices: list[float],
        fee_bps: int = DEFAULT_FEE_BPS,
    ) -> list[GIPSCalendarYearReturn]:
        """Calculate calendar year returns for GIPS reporting."""
        if not portfolio_values or not dates:
            return []

        parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        yearly_returns = {}

        for i, dt in enumerate(parsed_dates):
            year = dt.year
            if year not in yearly_returns:
                yearly_returns[year] = {"start_idx": i, "end_idx": i}
            yearly_returns[year]["end_idx"] = i

        results = []
        for year, indices in sorted(yearly_returns.items()):
            start_idx = indices["start_idx"]
            end_idx = indices["end_idx"]

            if end_idx <= start_idx:
                continue

            # Portfolio return
            start_val = portfolio_values[start_idx]
            end_val = portfolio_values[end_idx]
            gross = (end_val / start_val) - 1 if start_val > 0 else 0

            # Net return
            trading_days = end_idx - start_idx
            daily_fee = fee_bps / 10000 / self.TRADING_DAYS
            net = gross - (daily_fee * trading_days)

            # Benchmark return
            if benchmark_prices and len(benchmark_prices) > end_idx:
                bench_start = benchmark_prices[start_idx]
                bench_end = benchmark_prices[end_idx]
                bench = (bench_end / bench_start) - 1 if bench_start > 0 else 0
            else:
                bench = 0

            results.append(
                GIPSCalendarYearReturn(
                    year=year,
                    gross=round(gross * 100, 2),
                    net=round(net * 100, 2),
                    benchmark=round(bench * 100, 2),
                    excess=round((gross - bench) * 100, 2),
                )
            )

        return results

    def calculate_rolling_returns(
        self,
        portfolio_values: list[float],
        dates: list[str],
        benchmark_prices: list[float],
        window_days: int = 240,  # ~11.5 months of trading days
    ) -> list[GIPSRollingReturn]:
        """Calculate rolling 12-month returns."""
        if len(portfolio_values) < window_days:
            return []

        results = []
        for i in range(window_days, len(portfolio_values)):
            start_val = portfolio_values[i - window_days]
            end_val = portfolio_values[i]
            rolling_return = (end_val / start_val) - 1 if start_val > 0 else 0

            bench_return = None
            if benchmark_prices and len(benchmark_prices) > i:
                bench_start = benchmark_prices[i - window_days]
                bench_end = benchmark_prices[i]
                bench_return = (
                    round(((bench_end / bench_start) - 1) * 100, 2)
                    if bench_start > 0
                    else 0
                )

            results.append(
                GIPSRollingReturn(
                    date=dates[i],
                    rolling_12m=round(rolling_return * 100, 2),
                    benchmark_12m=bench_return,
                )
            )

        return results

    def calculate_drawdown_series(
        self, portfolio_values: list[float], dates: list[str]
    ) -> tuple[list[GIPSDrawdownPoint], float, float]:
        """Calculate drawdown series and max/current drawdown."""
        if not portfolio_values:
            return [], 0.0, 0.0

        running_max = portfolio_values[0]
        drawdowns = []
        max_dd = 0.0

        for i, val in enumerate(portfolio_values):
            running_max = max(running_max, val)
            dd = (val / running_max) - 1 if running_max > 0 else 0
            drawdowns.append(
                GIPSDrawdownPoint(date=dates[i], drawdown=round(dd * 100, 2))
            )
            max_dd = min(max_dd, dd)

        current_dd = drawdowns[-1].drawdown if drawdowns else 0.0
        return drawdowns, round(max_dd * 100, 2), current_dd

    def build_disclosure_checklist(
        self,
        n_days: int,
        has_benchmark: bool,
        num_portfolios: int,
        fee_schedule: str,
        has_gross_net: bool,
    ) -> list[GIPSDisclosureItem]:
        """Build GIPS disclosure readiness checklist."""
        items = []

        # Benchmark history
        items.append(
            GIPSDisclosureItem(
                item="Benchmark history complete",
                status="pass" if has_benchmark else "fail",
                detail="SPY benchmark aligned" if has_benchmark else "No benchmark data",
            )
        )

        # Minimum 1-year history
        has_1y = n_days >= 252
        items.append(
            GIPSDisclosureItem(
                item="Minimum 1-year history",
                status="pass" if has_1y else "warning",
                detail=f"{n_days} trading days available",
            )
        )

        # Dispersion available (6+ portfolios)
        has_dispersion = num_portfolios >= 6
        items.append(
            GIPSDisclosureItem(
                item="Dispersion available (6+ portfolios)",
                status="pass" if has_dispersion else "warning",
                detail=f"{num_portfolios} portfolios in composite",
            )
        )

        # Fee schedule documented
        has_fees = bool(fee_schedule)
        items.append(
            GIPSDisclosureItem(
                item="Fee schedule documented",
                status="pass" if has_fees else "fail",
                detail=fee_schedule if has_fees else "Not documented",
            )
        )

        # Gross & net returns
        items.append(
            GIPSDisclosureItem(
                item="Gross & net returns calculated",
                status="pass" if has_gross_net else "fail",
                detail="Both returns available" if has_gross_net else "Missing returns",
            )
        )

        # 5-year history
        has_5y = n_days >= 252 * 5
        items.append(
            GIPSDisclosureItem(
                item="5-year history (GIPS requirement)",
                status="pass" if has_5y else "warning",
                detail=f"{n_days // 252} years available" if n_days >= 252 else "< 1 year",
            )
        )

        # 10-year history
        has_10y = n_days >= 252 * 10
        items.append(
            GIPSDisclosureItem(
                item="10-year history (full compliance)",
                status="pass" if has_10y else "warning",
                detail=(
                    "Full history available"
                    if has_10y
                    else f"{n_days // 252} of 10 years"
                ),
            )
        )

        return items

    def calculate_gips_metrics(
        self,
        histories: dict[str, list[dict]],
        weights: dict[str, float],
        benchmark_history: list[dict] | None = None,
        fee_bps: int = DEFAULT_FEE_BPS,
    ) -> GIPSMetrics | None:
        """Calculate comprehensive GIPS-compliant metrics."""
        result = self.calculate_portfolio_twr(histories, weights)
        if result is None:
            return None

        portfolio_values, dates = result

        # Extract benchmark prices
        benchmark_prices = []
        if benchmark_history:
            # Align benchmark to same date range
            min_len = len(portfolio_values)
            benchmark_prices = [d["close"] for d in benchmark_history[-min_len:]]

        # Period returns
        period_returns = self.calculate_period_returns(
            portfolio_values, dates, benchmark_prices, fee_bps
        )

        # Cumulative returns
        cumulative_gross = (portfolio_values[-1] / portfolio_values[0]) - 1
        n_days = len(portfolio_values)

        # Apply fee for net return
        annual_fee = fee_bps / 10000
        years = n_days / self.TRADING_DAYS
        cumulative_net = cumulative_gross - (annual_fee * years)

        # Benchmark cumulative
        if benchmark_prices and len(benchmark_prices) >= 2:
            cumulative_benchmark = (benchmark_prices[-1] / benchmark_prices[0]) - 1
        else:
            cumulative_benchmark = 0

        # Annualized returns
        annualized_gross = (1 + cumulative_gross) ** (self.TRADING_DAYS / n_days) - 1
        annualized_net = (1 + cumulative_net) ** (self.TRADING_DAYS / n_days) - 1
        annualized_benchmark = (
            (1 + cumulative_benchmark) ** (self.TRADING_DAYS / n_days) - 1
            if cumulative_benchmark != 0
            else 0
        )

        # Risk metrics
        daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]
        annualized_vol = float(np.std(daily_returns) * np.sqrt(self.TRADING_DAYS))

        # Tracking error and info ratio
        if benchmark_prices and len(benchmark_prices) == len(portfolio_values):
            bench_returns = np.diff(benchmark_prices) / benchmark_prices[:-1]
            active_returns = daily_returns - bench_returns
            tracking_error = float(np.std(active_returns) * np.sqrt(self.TRADING_DAYS))
            active_ann = float(np.mean(active_returns) * self.TRADING_DAYS)
            info_ratio = active_ann / tracking_error if tracking_error > 0 else None
        else:
            tracking_error = 0
            info_ratio = None

        # Sharpe ratio
        excess_return = annualized_gross - self.RISK_FREE_RATE
        sharpe = excess_return / annualized_vol if annualized_vol > 0 else 0

        # Composite stats
        composite_stats = self.calculate_composite_stats(annualized_gross * 100)

        # Calendar year returns
        calendar_year_returns = self.calculate_calendar_year_returns(
            portfolio_values, dates, benchmark_prices, fee_bps
        )

        # Rolling returns (12-month)
        rolling_returns = self.calculate_rolling_returns(
            portfolio_values, dates, benchmark_prices
        )

        # Drawdown series
        drawdown_series, max_drawdown, current_drawdown = self.calculate_drawdown_series(
            portfolio_values, dates
        )

        # Disclosure checklist
        fee_schedule = f"{fee_bps} bps annual management fee"
        disclosure_checklist = self.build_disclosure_checklist(
            n_days=n_days,
            has_benchmark=bool(benchmark_prices),
            num_portfolios=composite_stats.num_portfolios,
            fee_schedule=fee_schedule,
            has_gross_net=True,
        )

        return GIPSMetrics(
            annualized_return_gross=round(annualized_gross * 100, 2),
            annualized_return_net=round(annualized_net * 100, 2),
            annualized_benchmark=round(annualized_benchmark * 100, 2),
            annualized_excess=round((annualized_gross - annualized_benchmark) * 100, 2),
            annualized_volatility=round(annualized_vol * 100, 2),
            tracking_error=round(tracking_error * 100, 2),
            information_ratio=round(info_ratio, 2) if info_ratio else None,
            sharpe_ratio=round(sharpe, 2),
            period_returns=period_returns,
            composite_stats=composite_stats,
            cumulative_gross=round(cumulative_gross * 100, 2),
            cumulative_net=round(cumulative_net * 100, 2),
            cumulative_benchmark=round(cumulative_benchmark * 100, 2),
            inception_date=dates[0] if dates else "",
            reporting_currency="USD",
            fee_schedule=fee_schedule,
            # New fields
            calendar_year_returns=calendar_year_returns,
            rolling_returns=rolling_returns,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            drawdown_series=drawdown_series,
            disclosure_checklist=disclosure_checklist,
            history_days=n_days,
        )
