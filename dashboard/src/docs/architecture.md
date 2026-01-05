# Architecture

Technical architecture and system design of CerberusRisk.

---

## System Overview

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Browser[Web Browser]
    end

    subgraph Frontend["Frontend - Port 8050"]
        Dash[Dash Application]
        Mantine[Mantine Components]
        Plotly[Plotly Charts]
    end

    subgraph Backend["Backend - Port 8000"]
        FastAPI[FastAPI Server]

        subgraph Routers["API Routers"]
            R1[portfolios.py]
            R2[risk.py]
            R3[risk_advanced.py]
            R4[stress.py]
            R5[compliance.py]
        end

        subgraph Services["Business Logic"]
            S1[risk_engine.py]
            S2[market_data.py]
            S3[stress_testing.py]
            S4[gips_service.py]
            S5[esg_service.py]
            S6[guidelines_service.py]
        end
    end

    subgraph Data["Data Layer"]
        PostgreSQL[(PostgreSQL)]
        Valkey[(Valkey Cache)]
        Yahoo[Yahoo Finance API]
    end

    Browser --> Dash
    Dash --> Mantine
    Dash --> Plotly
    Dash -->|HTTP| FastAPI
    FastAPI --> Routers
    Routers --> Services
    S1 --> PostgreSQL
    S2 --> Valkey
    S2 --> Yahoo
    S4 --> PostgreSQL
```

---

## Component Details

### Frontend (Dashboard)

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Dash 2.18+ | Interactive web application |
| UI Library | Dash Mantine Components | Material Design components |
| Charts | Plotly 5.24+ | Interactive visualizations |
| Server | Gunicorn | Production WSGI server |

**Pages**:
- `home.py` - Executive dashboard with KPIs
- `analytics.py` - 7-tab portfolio analysis
- `docs.py` - Documentation viewer

---

### Backend (API)

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI 0.115+ | High-performance REST API |
| ORM | SQLAlchemy 2.0+ | Database abstraction |
| Validation | Pydantic | Request/response schemas |
| Math | NumPy, SciPy | Numerical computations |

**Routers**:
| Router | Endpoints | Responsibility |
|--------|-----------|----------------|
| portfolios.py | 5 | CRUD, valuations, data info |
| risk.py | 3 | Core risk metrics |
| risk_advanced.py | 10 | Advanced analytics |
| stress.py | 3 | Scenario analysis |
| compliance.py | 4 | GIPS, ESG, guidelines |

---

### Data Layer

#### PostgreSQL

Stores portfolio and position data.

```mermaid
erDiagram
    PORTFOLIO {
        int id PK
        string name
        enum type
        string description
    }

    POSITION {
        int id PK
        int portfolio_id FK
        string ticker
        string name
        float weight
        string asset_class
    }

    PORTFOLIO ||--o{ POSITION : contains
```

#### Valkey Cache

High-performance caching for market data.

| Key Pattern | TTL | Data |
|-------------|-----|------|
| `quote:{ticker}` | 15 min | Live price, change |
| `history:{ticker}` | 24 hours | 1-year price history |
| `sector:{ticker}` | 7 days | Sector classification |

---

## Data Flow Patterns

### Risk Calculation Flow

```mermaid
sequenceDiagram
    participant D as Dashboard
    participant A as API
    participant R as Risk Engine
    participant M as Market Data
    participant C as Cache
    participant Y as Yahoo Finance

    D->>A: GET /portfolios/{id}/risk
    A->>M: get_portfolio_history()
    M->>C: Check cache

    alt Cache Hit
        C-->>M: Cached prices
    else Cache Miss
        M->>Y: Fetch 1-year data
        Y-->>M: Price history
        M->>C: Store in cache
    end

    M-->>A: Historical prices
    A->>R: calculate_risk_metrics()
    R->>R: Calculate returns
    R->>R: VaR, CVaR, volatility
    R-->>A: RiskMetrics
    A-->>D: JSON response
```

### Monte Carlo Flow

```mermaid
sequenceDiagram
    participant D as Dashboard
    participant A as API
    participant R as Risk Engine

    D->>A: GET /portfolios/{id}/monte-carlo
    A->>R: calculate_monte_carlo()
    R->>R: Calculate drift & volatility
    R->>R: Generate 10,000 GBM paths
    R->>R: Compute percentiles
    R-->>A: MonteCarloResult
    A-->>D: Fan chart data
```

---

## Service Layer

### Risk Engine (847 LOC)

Core quantitative module handling all risk calculations.

**Key Methods**:
```
calculate_returns()          → Log returns from prices
calculate_risk_metrics()     → VaR, CVaR, volatility, Sharpe
calculate_risk_contributions()→ Component VaR by position
calculate_correlation_matrix()→ Position correlations
calculate_rolling_metrics()  → 20-day rolling windows
calculate_tail_risk()        → Skewness, kurtosis
calculate_beta()             → Beta, alpha, R-squared
backtest_var()               → VaR breach analysis
calculate_monte_carlo()      → 10k path simulation
calculate_factor_exposures() → Multi-factor regression
```

### Market Data Service (329 LOC)

Handles price fetching and caching.

**Key Methods**:
```
get_quote()           → Live price with cache
get_history()         → 1-year price history
get_portfolio_quotes()→ Batch quote fetching
get_sector_info()     → Sector classification
refresh_cache()       → Force cache invalidation
```

---

## Deployment Architecture

```mermaid
flowchart LR
    subgraph Docker["Docker Compose"]
        subgraph Net["Internal Network"]
            API[api:8000]
            Dashboard[dashboard:8050]
            DB[postgres:5432]
            Cache[valkey:6379]
        end
    end

    User[User] -->|:8050| Dashboard
    Dashboard -->|internal| API
    API -->|internal| DB
    API -->|internal| Cache
```

### Container Configuration

| Service | Image | Ports | Health Check |
|---------|-------|-------|--------------|
| postgres | postgres:16-alpine | 5432 | pg_isready |
| valkey | valkey/valkey:8-alpine | 6379 | valkey-cli ping |
| api | python:3.12-slim | 8000 | - |
| dashboard | python:3.12-slim | 8050 | - |

---

## Security

### Middleware

- **CORS**: Configurable origins via environment
- **Security Headers**:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - Content-Security-Policy: default-src 'self'

### Production Mode

- API documentation disabled
- Debug mode off
- Environment-based configuration
