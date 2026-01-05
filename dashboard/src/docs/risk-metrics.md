# Risk Metrics

This page explains the risk metrics used in CerberusRisk.

## Value at Risk (VaR)

VaR estimates the maximum potential loss over a given time period at a specified confidence level.

- **VaR 95%** - 5% chance of exceeding this loss
- **VaR 99%** - 1% chance of exceeding this loss

## Conditional VaR (CVaR)

Also known as Expected Shortfall (ES), CVaR measures the average loss in the worst-case scenarios beyond VaR.

$$CVaR_\alpha = E[X | X > VaR_\alpha]$$

## Volatility

Annualized standard deviation of returns, measuring the dispersion of returns over time.

## Sharpe Ratio

Risk-adjusted return metric:

$$Sharpe = \frac{R_p - R_f}{\sigma_p}$$

Where:
- $R_p$ = Portfolio return
- $R_f$ = Risk-free rate
- $\sigma_p$ = Portfolio volatility
