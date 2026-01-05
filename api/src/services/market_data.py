import json
from datetime import datetime

import redis
import yfinance as yf
from pydantic import BaseModel


class Quote(BaseModel):
    ticker: str
    price: float
    change: float
    change_pct: float
    timestamp: datetime


class MarketDataService:
    PRICE_TTL = 900  # 15 minutes
    HISTORY_TTL = 86400  # 24 hours
    INFO_TTL = 86400 * 7  # 7 days for sector info

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    def _cache_key(self, ticker: str) -> str:
        return f"quote:{ticker}"

    def _history_key(self, ticker: str) -> str:
        return f"history:{ticker}"

    def get_history(self, ticker: str, period: str = "1y") -> list[dict] | None:
        cache_key = self._history_key(ticker)
        cached = self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, auto_adjust=True)

            if hist.empty:
                return None

            data = [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "close": round(row["Close"], 2),
                }
                for idx, row in hist.iterrows()
            ]

            self.redis.setex(cache_key, self.HISTORY_TTL, json.dumps(data))
            return data

        except Exception:
            return None

    def get_histories(self, tickers: list[str], period: str = "1y") -> dict[str, list[dict] | None]:
        results = {}
        uncached = []

        for ticker in tickers:
            cache_key = self._history_key(ticker)
            cached = self.redis.get(cache_key)
            if cached:
                results[ticker] = json.loads(cached)
            else:
                uncached.append(ticker)

        if uncached:
            try:
                data = yf.download(
                    uncached,
                    period=period,
                    progress=False,
                    auto_adjust=True,
                    threads=True,
                )

                for ticker in uncached:
                    try:
                        if len(uncached) == 1:
                            close_series = data["Close"]
                        else:
                            close_series = data["Close"][ticker]

                        closes = close_series.dropna()
                        if len(closes) > 0:
                            hist_data = [
                                {"date": idx.strftime("%Y-%m-%d"), "close": round(float(val), 2)}
                                for idx, val in closes.items()
                            ]
                            self.redis.setex(
                                self._history_key(ticker), self.HISTORY_TTL, json.dumps(hist_data)
                            )
                            results[ticker] = hist_data
                        else:
                            results[ticker] = None
                    except Exception:
                        results[ticker] = None
            except Exception:
                for ticker in uncached:
                    results[ticker] = None

        return results

    def get_quote(self, ticker: str) -> Quote | None:
        cache_key = self._cache_key(ticker)
        cached = self.redis.get(cache_key)

        if cached:
            data = json.loads(cached)
            return Quote(**data)

        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info

            price = info.last_price
            prev_close = info.previous_close

            if price is None or prev_close is None:
                return None

            change = price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0

            quote = Quote(
                ticker=ticker,
                price=round(price, 2),
                change=round(change, 2),
                change_pct=round(change_pct, 2),
                timestamp=datetime.now(),
            )

            self.redis.setex(cache_key, self.PRICE_TTL, quote.model_dump_json())
            return quote

        except Exception:
            return None

    def get_quotes(self, tickers: list[str]) -> dict[str, Quote | None]:
        results = {}
        uncached = []

        for ticker in tickers:
            cache_key = self._cache_key(ticker)
            cached = self.redis.get(cache_key)
            if cached:
                results[ticker] = Quote(**json.loads(cached))
            else:
                uncached.append(ticker)

        if uncached:
            try:
                data = yf.download(
                    uncached,
                    period="2d",
                    progress=False,
                    auto_adjust=True,
                    threads=True,
                )

                for ticker in uncached:
                    try:
                        if len(uncached) == 1:
                            close_series = data["Close"]
                        else:
                            close_series = data["Close"][ticker]

                        closes = close_series.dropna()
                        if len(closes) >= 2:
                            price = float(closes.iloc[-1])
                            prev_close = float(closes.iloc[-2])
                            change = price - prev_close
                            change_pct = (change / prev_close) * 100 if prev_close else 0

                            quote = Quote(
                                ticker=ticker,
                                price=round(price, 2),
                                change=round(change, 2),
                                change_pct=round(change_pct, 2),
                                timestamp=datetime.now(),
                            )
                            self.redis.setex(
                                self._cache_key(ticker), self.PRICE_TTL, quote.model_dump_json()
                            )
                            results[ticker] = quote
                        else:
                            results[ticker] = None
                    except Exception:
                        results[ticker] = None
            except Exception:
                for ticker in uncached:
                    results[ticker] = None

        return results

    # ========================================================================
    # ADVANCED DATA METHODS
    # ========================================================================

    def _info_key(self, ticker: str) -> str:
        return f"info:{ticker}"

    def _volume_key(self, ticker: str) -> str:
        return f"volume:{ticker}"

    def get_ticker_info(self, tickers: list[str]) -> dict[str, dict | None]:
        """Get sector, industry, marketCap for each ticker."""
        results = {}
        uncached = []

        for ticker in tickers:
            if ticker == "CASH":
                results[ticker] = {"sector": "Cash", "industry": "Cash", "marketCap": 0}
                continue

            cache_key = self._info_key(ticker)
            cached = self.redis.get(cache_key)
            if cached:
                results[ticker] = json.loads(cached)
            else:
                uncached.append(ticker)

        for ticker in uncached:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                data = {
                    "sector": info.get("sector", "Unknown"),
                    "industry": info.get("industry", "Unknown"),
                    "marketCap": info.get("marketCap", 0),
                }
                self.redis.setex(self._info_key(ticker), self.INFO_TTL, json.dumps(data))
                results[ticker] = data
            except Exception:
                results[ticker] = None

        return results

    def get_volume_data(self, tickers: list[str], period: str = "3mo") -> dict[str, dict | None]:
        """Get average volume and price for liquidity calculations."""
        results = {}
        uncached = []

        for ticker in tickers:
            if ticker == "CASH":
                continue

            cache_key = self._volume_key(ticker)
            cached = self.redis.get(cache_key)
            if cached:
                results[ticker] = json.loads(cached)
            else:
                uncached.append(ticker)

        if uncached:
            try:
                data = yf.download(
                    uncached,
                    period=period,
                    progress=False,
                    auto_adjust=True,
                    threads=True,
                )

                for ticker in uncached:
                    try:
                        if len(uncached) == 1:
                            volume_series = data["Volume"]
                            close_series = data["Close"]
                        else:
                            volume_series = data["Volume"][ticker]
                            close_series = data["Close"][ticker]

                        volumes = volume_series.dropna()
                        closes = close_series.dropna()

                        if len(volumes) > 0 and len(closes) > 0:
                            vol_data = {
                                "avg_volume": float(volumes.mean()),
                                "avg_price": float(closes.mean()),
                            }
                            self.redis.setex(
                                self._volume_key(ticker), self.HISTORY_TTL, json.dumps(vol_data)
                            )
                            results[ticker] = vol_data
                        else:
                            results[ticker] = None
                    except Exception:
                        results[ticker] = None
            except Exception:
                for ticker in uncached:
                    results[ticker] = None

        return results

    def get_sectors(self, tickers: list[str]) -> dict[str, str]:
        """Get sector mapping for tickers."""
        info = self.get_ticker_info(tickers)
        return {
            ticker: data.get("sector", "Unknown") if data else "Unknown"
            for ticker, data in info.items()
        }

    def clear_cache(self, tickers: list[str]) -> int:
        """Clear cached data for given tickers. Returns count of keys deleted."""
        keys_deleted = 0
        for ticker in tickers:
            for key in [
                self._history_key(ticker),
                self._cache_key(ticker),
                self._info_key(ticker),
                self._volume_key(ticker),
            ]:
                if self.redis.delete(key):
                    keys_deleted += 1
        return keys_deleted

    def refresh_histories(self, tickers: list[str], period: str = "1y") -> dict[str, int]:
        """Clear cache and fetch fresh history data. Returns status per ticker."""
        self.clear_cache(tickers)
        histories = self.get_histories(tickers, period)
        return {
            ticker: len(data) if data else 0
            for ticker, data in histories.items()
        }
