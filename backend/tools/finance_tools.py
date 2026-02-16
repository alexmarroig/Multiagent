"""Ferramentas financeiras com yfinance e pandas."""

from __future__ import annotations

import json

from crewai_tools import tool
import yfinance as yf


@tool("get_stock_data")
def get_stock_data(ticker: str, period: str = "1y") -> str:
    """Obtém dados de ações e retorna JSON com métricas e histórico."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return json.dumps({"error": f"Sem dados para {ticker}"}, ensure_ascii=False)

        info = stock.info or {}
        first_close = float(hist["Close"].iloc[0])
        last_close = float(hist["Close"].iloc[-1])
        period_change_pct = ((last_close - first_close) / first_close) * 100 if first_close else 0
        last_30 = hist.tail(30).reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
        last_30["Date"] = last_30["Date"].astype(str)

        payload = {
            "ticker": ticker,
            "current_price": last_close,
            "period_change_pct": round(period_change_pct, 2),
            "period_max": float(hist["High"].max()),
            "period_min": float(hist["Low"].min()),
            "avg_volume": float(hist["Volume"].mean()),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "sector": info.get("sector"),
            "history_last_30_days": last_30.to_dict(orient="records"),
        }
        return json.dumps(payload, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
