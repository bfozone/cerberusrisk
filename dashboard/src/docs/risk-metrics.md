# Risk Metrics

Comprehensive guide to all risk metrics calculated by CerberusRisk.

---

## Core Risk Metrics

### Value at Risk (VaR)

VaR estimates the maximum potential loss over a given time period at a specified confidence level using the historical simulation method.

| Metric | Description |
|--------|-------------|
| **VaR 95%** | 5% chance of exceeding this loss in a single day |
| **VaR 99%** | 1% chance of exceeding this loss in a single day |

**Interpretation**: A VaR 95% of -2.5% means there's a 95% probability that daily losses won't exceed 2.5%.

---

### Conditional VaR (CVaR)

Also known as **Expected Shortfall (ES)**, CVaR measures the average loss in the worst-case scenarios beyond the VaR threshold.

| Metric | Description |
|--------|-------------|
| **CVaR 95%** | Average loss in the worst 5% of days |
| **CVaR 99%** | Average loss in the worst 1% of days |

**Why it matters**: CVaR captures tail risk better than VaR by answering "when things go bad, how bad do they get?"

---

### Volatility

Annualized standard deviation of daily returns, measuring return dispersion.

**Formula**: σ_annual = σ_daily × √252

| Range | Interpretation |
|-------|----------------|
| < 10% | Low volatility (bonds, stable stocks) |
| 10-20% | Moderate volatility (diversified equity) |
| 20-30% | High volatility (growth stocks, emerging markets) |
| > 30% | Very high volatility (crypto, leveraged products) |

---

### Drawdown

Measures decline from peak portfolio value.

| Metric | Description |
|--------|-------------|
| **Maximum Drawdown** | Largest peak-to-trough decline in history |
| **Current Drawdown** | Current decline from most recent peak |

**Interpretation**: A max drawdown of -15% means the portfolio lost 15% from its highest point before recovering.

---

## Risk-Adjusted Returns

### Sharpe Ratio

Measures excess return per unit of risk.

**Formula**: Sharpe = (R_p - R_f) / σ_p

Where:
- R_p = Portfolio return (annualized)
- R_f = Risk-free rate (5%)
- σ_p = Portfolio volatility

| Value | Interpretation |
|-------|----------------|
| < 0 | Underperforming risk-free rate |
| 0 - 1 | Acceptable |
| 1 - 2 | Good |
| > 2 | Excellent |

---

### Sortino Ratio

Like Sharpe, but only penalizes downside volatility.

**Formula**: Sortino = (R_p - R_f) / σ_downside

**Why it matters**: Distinguishes between "good" volatility (upside gains) and "bad" volatility (downside losses).

---

### Treynor Ratio

Measures excess return per unit of systematic risk (beta).

**Formula**: Treynor = (R_p - R_f) / β

**Use case**: Comparing portfolios with different market exposures.

---

### Calmar Ratio

Measures return relative to maximum drawdown risk.

**Formula**: Calmar = Annualized Return / |Max Drawdown|

**Interpretation**: Higher values indicate better risk-adjusted performance through drawdowns.

---

## Advanced Risk Analytics

### Monte Carlo Simulation

Projects 10,000 possible portfolio paths over a 1-year horizon using Geometric Brownian Motion (GBM).

**Parameters**:
- Paths: 10,000 simulations
- Horizon: 252 trading days (1 year)
- Model: GBM with historical drift and volatility

**Output Percentiles**:
| Percentile | Interpretation |
|------------|----------------|
| 1% | Worst-case scenario |
| 5% | VaR 95% boundary |
| 25% | Lower quartile |
| 50% | Median outcome |
| 75% | Upper quartile |
| 95% | Best reasonable case |
| 99% | Best-case scenario |

---

### Factor Exposures

Decomposes portfolio risk into systematic factors using OLS regression.

| Factor | Proxy | Interpretation |
|--------|-------|----------------|
| **Market Beta** | SPY | Sensitivity to broad market |
| **Size Beta** | IWM | Exposure to small-cap premium |
| **Value Beta** | IVE | Exposure to value premium |

**R-squared**: Percentage of portfolio variance explained by factors (higher = more systematic risk).

---

### Tail Risk Statistics

Analyzes distribution characteristics beyond normal assumptions.

| Metric | Description |
|--------|-------------|
| **Skewness** | Asymmetry of returns (negative = left tail, more crashes) |
| **Excess Kurtosis** | Fat tails relative to normal (higher = more extreme events) |
| **Worst 10 Days** | Ten largest single-day losses |
| **Best 10 Days** | Ten largest single-day gains |

---

### Beta Analysis

Measures portfolio sensitivity to benchmark movements.

| Metric | Description |
|--------|-------------|
| **Beta** | Sensitivity to benchmark (1.0 = moves with market) |
| **Alpha** | Excess return above benchmark-implied return |
| **R-squared** | Correlation strength with benchmark |

**Interpretation**:
- Beta > 1: More volatile than benchmark
- Beta < 1: Less volatile than benchmark
- Alpha > 0: Outperforming on risk-adjusted basis

---

### Rolling Metrics

20-day rolling windows showing how risk evolves over time.

**Tracked Metrics**:
- Rolling Volatility
- Rolling VaR 95%
- Rolling Drawdown

**Use case**: Identify regime changes and periods of elevated risk.

---

### Liquidity Risk

Estimates days to liquidate each position based on average daily volume.

| Score | Days to Liquidate | Risk Level |
|-------|-------------------|------------|
| 95-100 | < 1 day | Very liquid |
| 80-95 | 1-3 days | Liquid |
| 50-80 | 3-10 days | Moderate |
| < 50 | > 10 days | Illiquid |

---

### Sector Concentration

Measures portfolio diversification using the Herfindahl-Hirschman Index (HHI).

**Formula**: HHI = Σ(weight_i × 100)²

| HHI Range | Interpretation |
|-----------|----------------|
| < 1,500 | Well diversified |
| 1,500 - 2,500 | Moderately concentrated |
| > 2,500 | Highly concentrated |

---

## Risk Contribution

Decomposes total portfolio risk to individual positions.

**Component VaR**: Each position's contribution to total portfolio VaR, accounting for correlations.

**Use case**: Identify which positions drive the most risk and optimize allocations.

---

## VaR Backtesting

Validates VaR model accuracy by counting historical breaches.

| Metric | Description |
|--------|-------------|
| **Expected Breaches** | 5% of days for VaR 95% |
| **Actual Breaches** | Observed days exceeding VaR |
| **Breach Rate** | Actual / Total days |

**Model Quality**:
- Breach rate ≈ 5%: Well-calibrated
- Breach rate < 5%: Conservative (overestimates risk)
- Breach rate > 5%: Aggressive (underestimates risk)
