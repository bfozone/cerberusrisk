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
