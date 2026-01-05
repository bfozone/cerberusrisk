# CerberusRisk Documentation

Welcome to CerberusRisk, a portfolio risk analytics platform.

## Features

- **Portfolio Overview** - View all portfolios with key risk metrics
- **Risk Analytics** - VaR, CVaR, volatility, and Monte Carlo simulations
- **Stress Testing** - Scenario-based impact analysis
- **Compliance** - GIPS, ESG, and investment guidelines monitoring

## Getting Started

Navigate to the **Home** page to see your portfolios, or dive into **Portfolio Analytics** for detailed risk analysis.

## Architecture

```mermaid
flowchart LR
    subgraph Frontend
        D[Dashboard<br/>Dash + Mantine]
    end

    subgraph Backend
        A[REST API<br/>FastAPI]
        R[Risk Engine]
        M[Market Data]
    end

    subgraph Data
        DB[(Database)]
    end

    D -->|HTTP| A
    A --> R
    A --> M
    R --> DB
    M --> DB
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant D as Dashboard
    participant A as API
    participant R as Risk Engine

    U->>D: Select Portfolio
    D->>A: GET /portfolios/{id}/risk
    A->>R: Calculate VaR, CVaR
    R-->>A: Risk Metrics
    A-->>D: JSON Response
    D-->>U: Display Charts
```

## Component Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| Dashboard | Dash + Mantine | Interactive UI |
| API | FastAPI | REST endpoints |
| Risk Engine | Python | Risk calculations |
| Charts | Plotly | Visualizations |
