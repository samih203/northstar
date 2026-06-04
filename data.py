"""
utils/data.py — Core data fetching utilities
Uses yfinance, requests, feedparser for real data
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import feedparser
from datetime import datetime, timedelta
import time


# ── Index tickers ────────────────────────────────────────────────
INDEX_TICKERS = {
    "S&P 500":  "^GSPC",
    "NASDAQ":   "^IXIC",
    "DOW":      "^DJI",
    "Russell 2000": "^RUT",
    "VIX":      "^VIX",
}

# ── Sector ETFs ──────────────────────────────────────────────────
SECTOR_ETFS = {
    "Technology":       "XLK",
    "Healthcare":       "XLV",
    "Financials":       "XLF",
    "Energy":           "XLE",
    "Consumer Disc.":   "XLY",
    "Industrials":      "XLI",
    "Materials":        "XLB",
    "Real Estate":      "XLRE",
    "Utilities":        "XLU",
    "Comm. Services":   "XLC",
    "Consumer Staples": "XLP",
    "Clean Energy":     "ICLN",
    "AI/Robotics":      "BOTZ",
    "Biotech":          "XBI",
    "Semiconductors":   "SOXX",
    "Cybersecurity":    "HACK",
    "Space":            "UFO",
    "Water":            "PHO",
}

# ── Niche / thematic watchlists ──────────────────────────────────
THEMATIC_STOCKS = {
    "AI Infrastructure": ["NVDA","AMD","SMCI","AVGO","MRVL","ARM","ALAB"],
    "Nuclear Energy":    ["CEG","VST","NNE","SMR","OKLO","BWX","ETN"],
    "Biotech Emerging":  ["RXRX","VERA","ACHR","IOVA","LEGN","KYMR"],
    "Defense Tech":      ["PLTR","RCAT","JOBY","ACHR","KTOS","HII"],
    "Water Tech":        ["ERII","AWK","MSEX","CWCO","ZEUS"],
    "Reshoring/Mfg":     ["EMR","ROK","GNRC","CFX","ASTE"],
    "GLP-1 / Obesity":   ["LLY","NVO","VKTX","ZFOX","RYTM","ALVO"],
    "Quantum Computing": ["IONQ","RGTI","QUBT","IBM","GOOGL"],
}

RSS_FEEDS = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA,AAPL,MSFT&region=US&lang=en-US",
]


@st.cache_data(ttl=300)
def get_quote(ticker: str) -> dict:
    """Fetch a single ticker's info + latest price."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="2d", interval="1d")
        if hist.empty:
            return {}
        price = float(hist["Close"].iloc[-1])
        prev  = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
        chg   = price - prev
        pct   = chg / prev * 100 if prev else 0
        return {
            "ticker": ticker,
            "price": price,
            "change": chg,
            "change_pct": pct,
            "volume": hist["Volume"].iloc[-1],
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "debt_equity": info.get("debtToEquity"),
            "roe": info.get("returnOnEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "gross_margin": info.get("grossMargins"),
            "short_ratio": info.get("shortRatio"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low":  info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "name": info.get("longName", ticker),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "summary": info.get("longBusinessSummary", ""),
            "analyst_target": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationMean"),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


@st.cache_data(ttl=300)
def get_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        return df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_index_data() -> dict:
    out = {}
    for name, tick in INDEX_TICKERS.items():
        q = get_quote(tick)
        if q:
            out[name] = q
    return out


@st.cache_data(ttl=600)
def get_sector_performance() -> pd.DataFrame:
    rows = []
    for name, etf in SECTOR_ETFS.items():
        try:
            hist = yf.Ticker(etf).history(period="5d", interval="1d")
            if len(hist) >= 2:
                chg  = (hist["Close"].iloc[-1] - hist["Close"].iloc[-2]) / hist["Close"].iloc[-2] * 100
                w1   = (hist["Close"].iloc[-1] - hist["Close"].iloc[0])  / hist["Close"].iloc[0]  * 100
                rows.append({"Sector": name, "ETF": etf, "1D%": round(chg, 2), "5D%": round(w1, 2), "Price": round(hist["Close"].iloc[-1], 2)})
        except:
            pass
    return pd.DataFrame(rows)


@st.cache_data(ttl=900)
def get_news(query: str = "stock market", count: int = 20) -> list[dict]:
    """Pull news from Yahoo Finance RSS (free, no key needed)."""
    items = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                items.append({
                    "title":    entry.get("title", ""),
                    "summary":  entry.get("summary", entry.get("description", "")),
                    "link":     entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source":   feed.feed.get("title", "Financial News"),
                })
        except:
            pass
    # deduplicate by title
    seen = set()
    unique = []
    for item in items:
        if item["title"] not in seen:
            seen.add(item["title"])
            unique.append(item)
    return unique[:count]


@st.cache_data(ttl=1800)
def screen_undervalued(universe: list[str] = None) -> pd.DataFrame:
    """
    Screen a list of tickers for undervalued signals using
    value + growth + momentum composite scoring.
    """
    if universe is None:
        # Broader universe of ~80 mid/small cap tickers
        universe = [
            # Tech value plays
            "CSCO","HPQ","INTC","STX","WDC","NTAP","JNPR",
            # Industrials
            "GEO","ASTE","REVG","GNRC","ESE","KTOS",
            # Healthcare
            "EHAB","ACAD","HIMS","EVER","CERT","HALO",
            # Energy
            "CIVI","MGY","CHX","TALO","VTLE","ESTE",
            # Financials
            "COOP","PFSI","UWMC","GPOR","CALM",
            # Materials
            "ZEUS","MP","CSTM","CLW",
            # Emerging tech
            "IONQ","SMAR","ASAN","FRSH","BRZE","PCVX",
            # Consumer
            "GDEN","JACK","RICK","PRGO","CENT",
        ]

    rows = []
    progress = st.progress(0, text="Screening universe…")
    for i, tick in enumerate(universe):
        progress.progress((i + 1) / len(universe), text=f"Scanning {tick}…")
        q = get_quote(tick)
        if not q or "error" in q:
            continue

        # Score 0–100
        score = 0
        signals = []

        pe = q.get("pe_ratio")
        fpe = q.get("forward_pe")
        pb = q.get("pb_ratio")
        ps = q.get("ps_ratio")
        rev_g = q.get("revenue_growth") or 0
        earn_g = q.get("earnings_growth") or 0
        roe = q.get("roe") or 0
        beta = q.get("beta") or 1
        gm = q.get("gross_margin") or 0
        hi52 = q.get("52w_high")
        price = q.get("price")

        # Value scoring
        if pe and 5 < pe < 20:    score += 20; signals.append("Low P/E")
        elif pe and 20 < pe < 35: score += 10
        if pb and 0 < pb < 2:     score += 15; signals.append("Low P/B")
        elif pb and 2 < pb < 4:   score += 7
        if ps and ps < 3:         score += 10; signals.append("Low P/S")

        # Growth scoring
        if rev_g > 0.20:   score += 15; signals.append("High Rev Growth")
        elif rev_g > 0.10: score += 8
        if earn_g > 0.15:  score += 10; signals.append("Earnings Growth")

        # Quality
        if roe > 0.15:   score += 10; signals.append("High ROE")
        if gm > 0.40:    score += 10; signals.append("Fat Margins")

        # Discount from 52w high
        if price and hi52 and hi52 > 0:
            disc = (hi52 - price) / hi52 * 100
            if disc > 30: score += 10; signals.append(f"{disc:.0f}% off high")
            elif disc > 15: score += 5

        # Upside to analyst target
        tgt = q.get("analyst_target")
        if tgt and price and tgt > price:
            upside = (tgt - price) / price * 100
            if upside > 25: score += 10; signals.append(f"+{upside:.0f}% analyst upside")

        rows.append({
            "Ticker": tick,
            "Name": (q.get("name") or tick)[:28],
            "Price": round(price, 2) if price else None,
            "Score": min(score, 100),
            "Signals": ", ".join(signals[:3]),
            "P/E": round(pe, 1) if pe else None,
            "Fwd P/E": round(fpe, 1) if fpe else None,
            "P/B": round(pb, 2) if pb else None,
            "Rev Growth": f"{rev_g*100:.1f}%" if rev_g else None,
            "Sector": q.get("sector", ""),
            "Change%": round(q.get("change_pct", 0), 2),
        })
        time.sleep(0.05)  # be polite to yfinance

    progress.empty()
    df = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)
    return df


def simple_sentiment(text: str) -> str:
    """Keyword-based sentiment (no paid API required)."""
    text_l = text.lower()
    pos = ["surge","rally","beat","growth","gains","bullish","record","strong","rise","boost","profit","soar"]
    neg = ["crash","plunge","miss","loss","bearish","concern","risk","decline","fall","warning","layoff","recession"]
    p = sum(1 for w in pos if w in text_l)
    n = sum(1 for w in neg if w in text_l)
    if p > n:   return "positive"
    if n > p:   return "negative"
    return "neutral"


def get_thematic_performance(theme: str) -> pd.DataFrame:
    tickers = THEMATIC_STOCKS.get(theme, [])
    rows = []
    for tick in tickers:
        q = get_quote(tick)
        if q and not q.get("error"):
            rows.append({
                "Ticker": tick,
                "Name": (q.get("name") or tick)[:22],
                "Price": round(q.get("price", 0), 2),
                "1D%": round(q.get("change_pct", 0), 2),
                "Mkt Cap": q.get("market_cap"),
            })
    return pd.DataFrame(rows)
