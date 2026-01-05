# API Reference

Complete reference for all CerberusRisk REST API endpoints.

**Base URL**: `http://localhost:8000/api`

---

## Portfolios

### List Portfolios

```
GET /portfolios
```

Returns all portfolios with their positions.

**Response**:
```json
[
  {
    "id": 1,
    "name": "Global Equity",
    "type": "equity",
    "description": "Diversified global equity portfolio",
    "positions": [
      {"ticker": "AAPL", "name": "Apple Inc", "weight": 0.15, "asset_class": "equity"}
    ]
  }
]
```

---

### Get Portfolio

```
GET /portfolios/{id}
```

Returns a single portfolio by ID.

| Parameter | Type | Description |
|-----------|------|-------------|
| id | int | Portfolio ID |

---

### Get Portfolio Value

```
GET /portfolios/{id}/value
```

Returns current portfolio valuation with live quotes.

**Response**:
```json
{
  "portfolio_id": 1,
  "total_value": 1000000,
  "positions": [
    {"ticker": "AAPL", "weight": 0.15, "price": 185.50, "change_pct": 1.2}
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Get Data Info

```
GET /portfolios/{id}/data-info
```

Returns historical data availability for portfolio positions.

---

### Refresh Data

```
POST /portfolios/{id}/refresh-data
```

Forces cache refresh for portfolio market data.

---

## Core Risk

### Get Risk Metrics

```
GET /portfolios/{id}/risk
```

Returns core risk metrics vs benchmark.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| benchmark | string | SPY | Benchmark ticker |

**Response**:
```json
{
  "portfolio": {
    "var_95": -0.025,
    "var_99": -0.038,
    "cvar_95": -0.032,
    "cvar_99": -0.045,
    "volatility": 0.18,
    "sharpe_ratio": 1.2,
    "max_drawdown": -0.12,
    "current_drawdown": -0.03
  },
  "benchmark": { ... },
  "comparison": {
    "excess_var_95": 0.005,
    "excess_volatility": -0.02
  }
}
```

---

### Get Risk Contributions

```
GET /portfolios/{id}/risk/contributions
```

Returns risk attribution by position.

**Response**:
```json
[
  {
    "ticker": "AAPL",
    "name": "Apple Inc",
    "weight": 0.15,
    "volatility": 0.28,
    "var_contribution": 0.004,
    "pct_of_total_var": 0.16
  }
]
```

---

### Get Correlation Matrix

```
GET /portfolios/{id}/correlation
```

Returns position-level correlation matrix.

---

## Advanced Risk

### Rolling Metrics

```
GET /portfolios/{id}/risk/rolling
```

Returns 20-day rolling risk metrics.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| window | int | 20 | Rolling window size |

---

### Tail Risk

```
GET /portfolios/{id}/risk/tail
```

Returns tail risk statistics.

**Response**:
```json
{
  "skewness": -0.45,
  "kurtosis": 4.2,
  "excess_kurtosis": 1.2,
  "worst_days": [
    {"date": "2024-01-10", "return": -0.035}
  ],
  "best_days": [
    {"date": "2024-01-05", "return": 0.028}
  ]
}
```

---

### Beta Analysis

```
GET /portfolios/{id}/risk/beta
```

Returns beta, alpha, R-squared vs benchmark.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| benchmark | string | SPY | Benchmark ticker |

---

### VaR Backtest

```
GET /portfolios/{id}/risk/var-backtest
```

Returns VaR model validation results.

---

### Sector Concentration

```
GET /portfolios/{id}/risk/sector-concentration
```

Returns HHI and sector breakdown.

---

### Liquidity Analysis

```
GET /portfolios/{id}/risk/liquidity
```

Returns position-level liquidity scores.

---

### What-If Analysis

```
POST /portfolios/{id}/what-if
```

Models impact of proposed position changes.

**Request Body**:
```json
{
  "changes": [
    {"ticker": "AAPL", "new_weight": 0.20},
    {"ticker": "MSFT", "new_weight": 0.10}
  ]
}
```

---

### Monte Carlo Simulation

```
GET /portfolios/{id}/monte-carlo
```

Returns 10,000-path GBM simulation results.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| horizon | int | 252 | Days to simulate |
| paths | int | 10000 | Number of paths |

**Response**:
```json
{
  "horizon_days": 252,
  "num_paths": 10000,
  "percentiles": {
    "p1": [1.0, 0.98, ...],
    "p5": [1.0, 0.99, ...],
    "p25": [1.0, 1.01, ...],
    "p50": [1.0, 1.02, ...],
    "p75": [1.0, 1.04, ...],
    "p95": [1.0, 1.06, ...],
    "p99": [1.0, 1.08, ...]
  },
  "var_95_1y": -0.15,
  "var_99_1y": -0.22,
  "cvar_95_1y": -0.20,
  "cvar_99_1y": -0.28
}
```

---

### Factor Exposures

```
GET /portfolios/{id}/factor-exposures
```

Returns multi-factor regression results.

---

### Performance Metrics

```
GET /portfolios/{id}/performance
```

Returns comprehensive performance analysis.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| benchmark | string | SPY | Benchmark ticker |

---

## Stress Testing

### List Scenarios

```
GET /stress/scenarios
```

Returns all available stress scenarios.

**Response**:
```json
[
  {
    "id": "equity_crash",
    "name": "Equity Market Crash",
    "description": "Severe equity market decline",
    "shocks": {
      "equity": -0.20,
      "government_bond": 0.05
    }
  }
]
```

---

### Run Scenario

```
GET /portfolios/{id}/stress/{scenario_id}
```

Returns impact analysis for a specific scenario.

**Response**:
```json
{
  "scenario": "equity_crash",
  "portfolio_impact": -0.15,
  "position_impacts": [
    {"ticker": "AAPL", "shock": -0.20, "contribution": -0.03}
  ]
}
```

---

### Compare Portfolios

```
GET /stress/compare/{scenario_id}
```

Compares scenario impact across all portfolios.

---

## Compliance

### GIPS Report

```
GET /portfolios/{id}/gips
```

Returns GIPS-compliant performance report.

**Response**:
```json
{
  "composite_name": "Global Equity",
  "reporting_currency": "USD",
  "periods": [
    {
      "period": "2024-01",
      "gross_return": 0.025,
      "net_return": 0.023,
      "benchmark_return": 0.020
    }
  ],
  "annualized_return": 0.12,
  "annualized_volatility": 0.18,
  "sharpe_ratio": 0.67
}
```

---

### ESG Scores

```
GET /portfolios/{id}/esg
```

Returns portfolio ESG analysis.

**Response**:
```json
{
  "overall_score": 72,
  "environmental": 68,
  "social": 75,
  "governance": 73,
  "carbon_intensity": 125.5,
  "controversies": 1,
  "rating_distribution": {
    "AAA": 2, "AA": 3, "A": 4
  }
}
```

---

### Guideline Definitions

```
GET /guidelines/definitions
```

Returns all investment guideline rules.

---

### Guideline Compliance

```
GET /portfolios/{id}/guidelines
```

Returns compliance status for all guidelines.

**Response**:
```json
{
  "overall_status": "warning",
  "guidelines": [
    {
      "name": "Single Position Limit",
      "limit": 0.10,
      "current": 0.15,
      "status": "breach",
      "message": "AAPL exceeds 10% limit"
    }
  ]
}
```

---

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Portfolio not found"
}
```

| Status | Description |
|--------|-------------|
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 500 | Internal server error |
