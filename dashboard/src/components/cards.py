from dash import html
import dash_bootstrap_components as dbc


def metric_card(label: str, value: str, color: str = "primary", width: int = 2):
    """Create a single metric card."""
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.P(label, className="text-muted mb-1 small"),
                    html.H4(value, className=f"text-{color} mb-0"),
                ]
            ),
            className="text-center",
        ),
        md=width,
    )


def portfolio_card(portfolio: dict, risk: dict | None):
    """Create a portfolio summary card with risk metrics."""
    risk_color = "success" if risk and risk.get("var_95", 0) < 15 else "warning"

    return dbc.Card(
        [
            dbc.CardHeader(html.H5(portfolio["name"], className="mb-0")),
            dbc.CardBody(
                [
                    html.P(portfolio["description"], className="text-muted small"),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P("VaR 95%", className="text-muted mb-0 small"),
                                    html.H4(
                                        f"{risk['var_95']}%" if risk else "—",
                                        className=f"text-{risk_color}",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.P("Volatility", className="text-muted mb-0 small"),
                                    html.H4(f"{risk['volatility']}%" if risk else "—"),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P("Sharpe", className="text-muted mb-0 small"),
                                    html.H4(f"{risk['sharpe']}" if risk else "—"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.P("Max DD", className="text-muted mb-0 small"),
                                    html.H4(
                                        f"{risk['max_drawdown']}%" if risk else "—",
                                        className="text-danger",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mt-2",
                    ),
                    html.Hr(),
                    dbc.Button(
                        "View Details",
                        href=f"/portfolio/{portfolio['id']}",
                        color="primary",
                        size="sm",
                    ),
                ]
            ),
        ],
        className="h-100",
    )
