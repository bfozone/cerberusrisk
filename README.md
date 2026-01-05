# CerberusRisk

**Demo application** showcasing a portfolio risk analytics platform for institutional investors.

## Features

- **Risk Analytics** - VaR, CVaR, volatility, Sharpe ratio, drawdown
- **Monte Carlo** - 10,000 path simulations with fan charts
- **Stress Testing** - 6 macro scenarios (equity crash, rate shocks, stagflation)
- **Compliance** - GIPS returns, ESG scoring, investment guidelines
- **Performance** - Attribution, benchmark comparison, risk-adjusted ratios

## Quick Start

```bash
make up
```

Open http://localhost:8050

## Commands

| Command | Description |
|---------|-------------|
| `make up` | Start services |
| `make down` | Stop services |
| `make logs` | View logs |
| `make ps` | Container status |
| `make test` | Test API |
| `make clean` | Reset everything |

## Stack

- **Frontend**: Dash + Mantine + Plotly
- **Backend**: FastAPI + SQLAlchemy
- **Database**: PostgreSQL + Valkey
- **Data**: yfinance, NumPy, SciPy

## License

MIT
