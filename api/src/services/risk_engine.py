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
