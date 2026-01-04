import os
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")


def get_portfolios():
    try:
        r = requests.get(f"{API_URL}/api/portfolios", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def get_portfolio(portfolio_id: int):
    try:
        r = requests.get(f"{API_URL}/api/portfolios/{portfolio_id}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_portfolio_value(portfolio_id: int):
    try:
        r = requests.get(f"{API_URL}/api/portfolios/{portfolio_id}/value", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_data_info(portfolio_id: int):
    try:
        r = requests.get(f"{API_URL}/api/portfolios/{portfolio_id}/data-info", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_portfolio_risk(portfolio_id: int):
    try:
        r = requests.get(f"{API_URL}/api/portfolios/{portfolio_id}/risk", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_risk_contributions(portfolio_id: int):
    try:
        r = requests.get(f"{API_URL}/api/portfolios/{portfolio_id}/risk/contributions", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def get_correlation(portfolio_id: int):
    try:
        r = requests.get(f"{API_URL}/api/portfolios/{portfolio_id}/correlation", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"tickers": [], "matrix": []}


def get_stress_scenarios():
    try:
        r = requests.get(f"{API_URL}/api/stress/scenarios", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def run_stress_test(portfolio_id: int, scenario_id: str):
    try:
        r = requests.get(f"{API_URL}/api/portfolios/{portfolio_id}/stress/{scenario_id}", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def compare_stress(scenario_id: str):
    try:
        r = requests.get(f"{API_URL}/api/stress/compare/{scenario_id}", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ============================================================================
# ADVANCED RISK API
# ============================================================================


def get_rolling_metrics(portfolio_id: int, window: int = 20):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/risk/rolling",
            params={"window": window},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_tail_risk(portfolio_id: int, n: int = 10):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/risk/tail",
            params={"n": n},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_beta(portfolio_id: int, benchmark: str = "SPY"):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/risk/beta",
            params={"benchmark": benchmark},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_var_backtest(portfolio_id: int, window: int = 60):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/risk/backtest",
            params={"window": window},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_sector_concentration(portfolio_id: int):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/concentration/sector",
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_liquidity(portfolio_id: int):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/liquidity",
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def run_what_if(portfolio_id: int, changes: dict):
    try:
        r = requests.post(
            f"{API_URL}/api/portfolios/{portfolio_id}/risk/whatif",
            json={"changes": changes},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_monte_carlo(portfolio_id: int, simulations: int = 10000):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/risk/montecarlo",
            params={"simulations": simulations},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_factor_exposures(portfolio_id: int):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/risk/factors",
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_performance(portfolio_id: int, benchmark: str = "SPY"):
    try:
        r = requests.get(
            f"{API_URL}/api/portfolios/{portfolio_id}/performance",
            params={"benchmark": benchmark},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None
