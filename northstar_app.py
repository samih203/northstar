import streamlit as st
import sys, os, importlib, time
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import requests, feedparser
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import yfinance as yf

st.set_page_config(
    page_title="Northstar — Market Intelligence",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
:root{--bg:#0a0e1a;--surface:#111827;--border:#1f2937;--accent:#00d4aa;--accent2:#f59e0b;--accent3:#ef4444;--text:#e5e7eb;--muted:#6b7280;}
html,body,[data-testid="stAppViewContainer"]{background-color:var(--bg)!important;color:var(--text)!important;font-family:'IBM Plex Sans',sans-serif;}
[data-testid="stSidebar"]{background-color:#0d1117!important;border-right:1px solid var(--border);}
[data-testid="stSidebar"] *{color:var(--text)!important;}
h1,h2,h3{font-family:'DM Serif Display',serif!important;color:var(--text)!important;}
.metric-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1.2rem;margin-bottom:.75rem;}
.stMetric{background:var(--surface);padding:1rem;border-radius:8px;border:1px solid var(--border);}
.stMetric label{color:var(--muted)!important;font-family:'Space Mono',monospace!important;font-size:.7rem!important;text-transform:uppercase;letter-spacing:.08em;}
.stMetric [data-testid="stMetricValue"]{font-family:'Space Mono',monospace!important;color:var(--accent)!important;}
.stButton>button{background:transparent!important;border:1px solid var(--accent)!important;color:var(--accent)!important;font-family:'Space Mono',monospace!important;font-size:.75rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;border-radius:4px!important;}
.stButton>button:hover{background:rgba(0,212,170,.1)!important;}
.news-card{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:6px;padding:1rem 1.2rem;margin-bottom:.75rem;}
.news-card.negative{border-left-color:var(--accent3);}
.news-card.neutral{border-left-color:var(--muted);}
.terminal-header{font-family:'Space Mono',monospace;font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:.15em;border-bottom:1px solid var(--border);padding-bottom:.5rem;margin-bottom:1rem;}
.stTabs [data-baseweb="tab-list"]{background:var(--surface)!important;border-bottom:1px solid var(--border);}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--muted)!important;font-family:'Space Mono',monospace!important;font-size:.7rem!important;text-transform:uppercase;letter-spacing:.1em;border-bottom:2px solid transparent!important;}
.stTabs [aria-selected="true"]{color:var(--accent)!important;border-bottom:2px solid var(--accent)!important;}
[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:6px!important;}
hr{border-color:var(--border)!important;}
.block-container{padding-top:1.5rem!important;max-width:1400px;}
div[data-testid="metric-container"]{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1rem 1.2rem;}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ────────────────────────────────────────────────────────────────
INDEX_TICKERS = {"S&P 500":"^GSPC","NASDAQ":"^IXIC","DOW":"^DJI","Russell 2000":"^RUT","VIX":"^VIX"}
SECTOR_ETFS = {"Technology":"XLK","Healthcare":"XLV","Financials":"XLF","Energy":"XLE","Consumer Disc.":"XLY","Industrials":"XLI","Materials":"XLB","Real Estate":"XLRE","Utilities":"XLU","Comm. Services":"XLC","Consumer Staples":"XLP","Clean Energy":"ICLN","AI/Robotics":"BOTZ","Biotech":"XBI","Semiconductors":"SOXX","Cybersecurity":"HACK","Space":"UFO","Water":"PHO"}
THEMATIC_STOCKS = {"AI Infrastructure":["NVDA","AMD","SMCI","AVGO","MRVL","ARM","ALAB"],"Nuclear Energy":["CEG","VST","NNE","SMR","OKLO","BWX","ETN"],"Biotech Emerging":["RXRX","VERA","ACHR","IOVA","LEGN","KYMR"],"Defense Tech":["PLTR","RCAT","JOBY","ACHR","KTOS","HII"],"Water Tech":["ERII","AWK","MSEX","CWCO","ZEUS"],"Reshoring/Mfg":["EMR","ROK","GNRC","CFX","ASTE"],"GLP-1 / Obesity":["LLY","NVO","VKTX","RYTM","ALVO"],"Quantum Computing":["IONQ","RGTI","QUBT","IBM","GOOGL"]}
RSS_FEEDS = ["https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US","https://feeds.marketwatch.com/marketwatch/topstories/","https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA,AAPL,MSFT&region=US&lang=en-US"]
CHART_THEME = dict(paper_bgcolor="#111827",plot_bgcolor="#0a0e1a",font=dict(color="#9ca3af",family="Space Mono, monospace",size=10),xaxis=dict(gridcolor="#1f2937",showgrid=True),yaxis=dict(gridcolor="#1f2937",showgrid=True))
AI_WATCHLIST = {"High Conviction":{"tickers":["CEG","NNE","NVDA","PLTR","LLY"],"rationale":"Nuclear renaissance, AI infrastructure dominance, defense tech, and GLP-1 wave — three independent multi-year secular growth themes.","time_horizon":"12–24 months","risk":"Medium"},"Deep Value":{"tickers":["INTC","CSCO","STX","HPQ","CIVI"],"rationale":"Beaten-down tech and energy names trading at or below tangible book value with potential catalyst for re-rating.","time_horizon":"6–18 months","risk":"Medium-High"},"Aggressive Growth":{"tickers":["IONQ","SMR","OKLO","RXRX","ACHR"],"rationale":"Early-stage technology in quantum computing, nuclear SMRs, and biotech platforms. High risk, asymmetric upside.","time_horizon":"24–48 months","risk":"High"},"Income + Safety":{"tickers":["NEE","AWK","ETN","MSEX","WM"],"rationale":"Defensive positions with reliable dividends: water utilities, clean energy infrastructure, and waste management.","time_horizon":"Long-term hold","risk":"Low-Medium"}}
RISK_COLORS = {"Low-Medium":"#00d4aa","Medium":"#f59e0b","Medium-High":"#fb923c","High":"#ef4444"}

# ── DATA FUNCTIONS ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_quote(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="5d", interval="1d")
        if hist.empty: return {}
        price = float(hist["Close"].iloc[-1])
        prev  = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
        chg   = price - prev
        pct   = chg / prev * 100 if prev else 0
        return {"ticker":ticker,"price":price,"change":chg,"change_pct":pct,"volume":hist["Volume"].iloc[-1],"market_cap":info.get("marketCap"),"pe_ratio":info.get("trailingPE"),"forward_pe":info.get("forwardPE"),"pb_ratio":info.get("priceToBook"),"ps_ratio":info.get("priceToSalesTrailing12Months"),"ev_ebitda":info.get("enterpriseToEbitda"),"debt_equity":info.get("debtToEquity"),"roe":info.get("returnOnEquity"),"revenue_growth":info.get("revenueGrowth"),"earnings_growth":info.get("earningsGrowth"),"gross_margin":info.get("grossMargins"),"52w_high":info.get("fiftyTwoWeekHigh"),"52w_low":info.get("fiftyTwoWeekLow"),"beta":info.get("beta"),"name":info.get("longName",ticker),"sector":info.get("sector",""),"industry":info.get("industry",""),"summary":info.get("longBusinessSummary",""),"analyst_target":info.get("targetMeanPrice"),"recommendation":info.get("recommendationMean")}
    except Exception as e:
        if "RateLimit" in str(type(e).__name__):
            time.sleep(2)
        return {"ticker":ticker,"error":"fetch failed"}

@st.cache_data(ttl=300)
def get_history(ticker, period="1y", interval="1d"):
    for attempt in range(3):
        try:
            time.sleep(0.3 * attempt)
            df = yf.Ticker(ticker).history(period=period, interval=interval)
            return df
        except Exception:
            if attempt == 2: return pd.DataFrame()
            time.sleep(2 ** attempt)
    return pd.DataFrame()

@st.cache_data(ttl=300)
def get_index_data():
    out = {}
    tickers_str = " ".join(INDEX_TICKERS.values())
    try:
        data = yf.download(tickers_str, period="5d", interval="1d",
                           group_by="ticker", auto_adjust=True, progress=False)
        for name, tick in INDEX_TICKERS.items():
            try:
                if len(INDEX_TICKERS) > 1:
                    hist = data[tick]["Close"].dropna()
                else:
                    hist = data["Close"].dropna()
                if len(hist) >= 2:
                    price = float(hist.iloc[-1])
                    prev  = float(hist.iloc[-2])
                    chg   = price - prev
                    pct   = chg / prev * 100 if prev else 0
                    out[name] = {"price": price, "change": chg, "change_pct": pct}
            except:
                pass
    except:
        pass
    return out

@st.cache_data(ttl=600)
def get_sector_performance():
    rows = []
    etf_list = list(SECTOR_ETFS.items())
    try:
        tickers_str = " ".join([etf for _,etf in etf_list])
        data = yf.download(tickers_str, period="5d", interval="1d",
                           group_by="ticker", auto_adjust=True, progress=False)
        # Handle both MultiIndex (multi-ticker) and flat (single ticker) DataFrames
        is_multi = isinstance(data.columns, pd.MultiIndex)
        for name, etf in etf_list:
            try:
                if is_multi:
                    hist = data["Close"][etf].dropna()
                else:
                    hist = data["Close"].dropna()
                if len(hist) >= 2:
                    chg = (hist.iloc[-1]-hist.iloc[-2])/hist.iloc[-2]*100
                    w1  = (hist.iloc[-1]-hist.iloc[0])/hist.iloc[0]*100
                    rows.append({"Sector":name,"ETF":etf,"1D%":round(float(chg),2),
                                 "5D%":round(float(w1),2),"Price":round(float(hist.iloc[-1]),2)})
            except:
                pass
    except Exception:
        pass
    return pd.DataFrame(rows)

@st.cache_data(ttl=900)
def get_news(count=20):
    items, seen = [], set()
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:8]:
                t = e.get("title","")
                if t not in seen:
                    seen.add(t)
                    items.append({"title":t,"summary":e.get("summary",e.get("description","")),"link":e.get("link",""),"published":e.get("published",""),"source":feed.feed.get("title","Financial News")})
        except: pass
    return items[:count]

def simple_sentiment(text):
    t = text.lower()
    pos = sum(1 for w in ["surge","rally","beat","growth","gains","bullish","record","strong","rise","boost","profit","soar"] if w in t)
    neg = sum(1 for w in ["crash","plunge","miss","loss","bearish","concern","risk","decline","fall","warning","layoff","recession"] if w in t)
    return "positive" if pos>neg else "negative" if neg>pos else "neutral"

@st.cache_data(ttl=1800)
def screen_undervalued():
    """
    5-Factor Quant Score. Uses yf.Tickers() bulk fetch to avoid rate limits,
    then scores each stock on Value, Quality, Growth, Momentum, Analyst signals.
    Falls back gracefully if any field is missing — no stock gets skipped
    just because one metric is unavailable.
    """
    universe = [
        "CSCO","HPQ","INTC","STX","WDC","NTAP",
        "GNRC","ESE","KTOS","EMR","ROK","ASTE",
        "HIMS","HALO","PRGO","ACAD",
        "CIVI","MGY","CHX","TALO",
        "COOP","PFSI","CALM",
        "ZEUS","MP","CLW",
        "IONQ","SMAR","ASAN","FRSH",
        "GDEN","JACK","CENT",
    ]

    rows = []
    prog = st.progress(0, text="Fetching fundamentals in bulk…")

    # ── Step 1: Batch price history for momentum signals ──────────────
    prog.progress(0.05, text="Downloading price history…")
    try:
        price_data = yf.download(
            " ".join(universe), period="1y", interval="1d",
            group_by="ticker", auto_adjust=True, progress=False
        )
        is_multi = isinstance(price_data.columns, pd.MultiIndex)
    except Exception:
        price_data = pd.DataFrame()
        is_multi = False

    # ── Step 2: Fetch fundamentals in small batches to avoid rate limits ──
    def safe_info(tick):
        for attempt in range(3):
            try:
                info = yf.Ticker(tick).info
                # yfinance sometimes returns a nearly-empty dict with just "trailingPegRatio"
                if info and len(info) > 5:
                    return info
            except Exception:
                pass
            time.sleep(1.5 * (attempt + 1))
        return {}

    total = len(universe)
    for i, tick in enumerate(universe):
        prog.progress(0.1 + 0.9 * (i / total), text=f"Scoring {tick} ({i+1}/{total})…")

        info = safe_info(tick)

        # ── Price & momentum from batch download ──────────────────────
        try:
            if not price_data.empty:
                hist = price_data["Close"][tick].dropna() if is_multi else price_data["Close"].dropna()
            else:
                hist = pd.Series(dtype=float)
        except Exception:
            hist = pd.Series(dtype=float)

        price  = float(hist.iloc[-1]) if len(hist) > 0 else (info.get("currentPrice") or info.get("regularMarketPrice") or 0)
        hi52   = info.get("fiftyTwoWeekHigh") or (float(hist.max()) if len(hist) > 0 else price)
        lo52   = info.get("fiftyTwoWeekLow")  or (float(hist.min()) if len(hist) > 0 else price)

        # Momentum: 3m and 6m returns from price history
        ret_3m = float((hist.iloc[-1] / hist.iloc[-63] - 1) * 100) if len(hist) >= 63 else None
        ret_6m = float((hist.iloc[-1] / hist.iloc[-126] - 1) * 100) if len(hist) >= 126 else None

        # ── Fundamental fields ────────────────────────────────────────
        ev_eb  = info.get("enterpriseToEbitda")
        pb     = info.get("priceToBook")
        ps     = info.get("priceToSalesTrailing12Months")
        fpe    = info.get("forwardPE")
        roe    = info.get("returnOnEquity") or 0
        gm     = info.get("grossMargins") or 0
        de     = info.get("debtToEquity") or 0
        rev_g  = info.get("revenueGrowth") or 0
        earn_g = info.get("earningsGrowth") or 0
        tgt    = info.get("targetMeanPrice")
        name   = info.get("longName") or info.get("shortName") or tick
        sector = info.get("sector") or ""

        # 1-day change from history
        chg_pct = float((hist.iloc[-1]/hist.iloc[-2]-1)*100) if len(hist) >= 2 else 0

        score   = 0
        signals = []

        # ── FACTOR 1: VALUE (max 25pts) ──────────────────────────────
        v = 0
        if ev_eb and 0 < ev_eb < 8:    v += 10; signals.append(f"EV/EBITDA {ev_eb:.1f}x")
        elif ev_eb and ev_eb < 14:      v += 5
        if pb and 0 < pb < 1.5:         v += 8;  signals.append(f"P/B {pb:.1f}x")
        elif pb and pb < 3:              v += 4
        if ps and ps < 1.5:             v += 7;  signals.append(f"P/S {ps:.1f}x")
        elif ps and ps < 3:              v += 3
        score += min(v, 25)

        # ── FACTOR 2: QUALITY (max 25pts) ────────────────────────────
        q2 = 0
        if roe > 0.20:   q2 += 10; signals.append(f"ROE {roe*100:.0f}%")
        elif roe > 0.12: q2 += 6
        elif roe > 0.06: q2 += 3
        if gm > 0.50:    q2 += 8;  signals.append("High Margins")
        elif gm > 0.35:  q2 += 5
        elif gm > 0.20:  q2 += 2
        if de < 30:      q2 += 7;  signals.append("Low Debt")   # yfinance D/E is in %, not ratio
        elif de < 80:    q2 += 4
        elif de > 200:   q2 -= 3
        score += min(q2, 25)

        # ── FACTOR 3: GROWTH (max 20pts) ─────────────────────────────
        g = 0
        if rev_g > 0.20:   g += 10; signals.append(f"Rev +{rev_g*100:.0f}%")
        elif rev_g > 0.08: g += 6
        elif rev_g > 0:    g += 2
        if earn_g > 0.15:  g += 7;  signals.append("Earn↑")
        elif earn_g > 0.05: g += 4
        if fpe and earn_g and earn_g > 0:
            peg = fpe / (earn_g * 100)
            if 0 < peg < 0.8:   g += 3; signals.append(f"PEG {peg:.2f}")
            elif peg < 1.5:     g += 1
        score += min(g, 20)

        # ── FACTOR 4: MOMENTUM (max 20pts) ───────────────────────────
        m = 0
        if price > 0 and hi52 > lo52:
            rng = hi52 - lo52
            pos = (price - lo52) / rng if rng > 0 else 0.5
            if 0.35 < pos < 0.80:  m += 8
            elif pos >= 0.80:      m += 5
            else:                  m += 2
            disc = (hi52 - price) / hi52 * 100
            if 10 < disc < 40:   m += 7; signals.append(f"{disc:.0f}% off high")
            elif disc <= 10:     m += 3
        if ret_3m is not None and ret_3m > 5:   m += 3
        if ret_6m is not None and ret_6m > 10:  m += 2
        score += min(m, 20)

        # ── FACTOR 5: ANALYST (max 10pts) ────────────────────────────
        a = 0
        if tgt and price and price > 0:
            upside = (tgt - price) / price * 100
            if upside > 25:   a += 7; signals.append(f"+{upside:.0f}% target")
            elif upside > 10: a += 4
            elif upside > 0:  a += 2
        score += min(a, 10)

        score = max(0, min(score, 100))

        # Always append — even low scorers show up so user sees the full picture
        rows.append({
            "Ticker":     tick,
            "Name":       name[:28],
            "Price":      round(price, 2) if price else 0,
            "Score":      score,
            "Signals":    " · ".join(signals[:3]) if signals else "—",
            "EV/EBITDA":  round(ev_eb, 1) if ev_eb else None,
            "P/B":        round(pb, 2) if pb else None,
            "ROE":        f"{roe*100:.1f}%" if roe else None,
            "Rev Growth": f"{rev_g*100:.1f}%" if rev_g else None,
            "Fwd PEG":    round(fpe/(earn_g*100), 2) if fpe and earn_g and earn_g > 0 else None,
            "D/E":        round(de, 1) if de else None,
            "Sector":     sector,
            "Change%":    round(chg_pct, 2),
        })
        time.sleep(0.5)  # respectful delay between info() calls

    prog.empty()
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("Score", ascending=False).reset_index(drop=True)

# ── ML FUNCTIONS ──────────────────────────────────────────────────────────────
def add_features(df):
    d = df.copy(); c = d["Close"]
    d["sma_5"]=c.rolling(5).mean(); d["sma_20"]=c.rolling(20).mean(); d["sma_50"]=c.rolling(50).mean()
    d["ema_12"]=c.ewm(span=12).mean(); d["ema_26"]=c.ewm(span=26).mean()
    d["macd"]=d["ema_12"]-d["ema_26"]; d["macd_signal"]=d["macd"].ewm(span=9).mean(); d["macd_hist"]=d["macd"]-d["macd_signal"]
    delta=c.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=(-delta.clip(upper=0)).rolling(14).mean()
    d["rsi"]=100-(100/(1+gain/loss.replace(0,np.nan)))
    std20=c.rolling(20).std(); d["bb_upper"]=d["sma_20"]+2*std20; d["bb_lower"]=d["sma_20"]-2*std20
    d["bb_width"]=(d["bb_upper"]-d["bb_lower"])/d["sma_20"]; d["bb_pos"]=(c-d["bb_lower"])/(d["bb_upper"]-d["bb_lower"]+1e-9)
    hl=d["High"]-d["Low"]; hpc=(d["High"]-c.shift(1)).abs(); lpc=(d["Low"]-c.shift(1)).abs()
    d["atr"]=pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).mean()
    d["vol_ratio"]=d["Volume"]/d["Volume"].rolling(20).mean()
    for lag in [1,3,5,10]: d[f"ret_{lag}d"]=c.pct_change(lag)
    d["above_sma20"]=(c>d["sma_20"]).astype(int); d["above_sma50"]=(c>d["sma_50"]).astype(int)
    d["golden_cross"]=((d["sma_20"]>d["sma_50"])&(d["sma_20"].shift(1)<=d["sma_50"].shift(1))).astype(int)
    return d

FEATURE_COLS = ["sma_5","sma_20","sma_50","macd","macd_signal","macd_hist","rsi","bb_width","bb_pos","atr","vol_ratio","ret_1d","ret_3d","ret_5d","ret_10d","above_sma20","above_sma50","golden_cross"]

@st.cache_data(ttl=3600, show_spinner=False)
def predict_direction(ticker, _df):
    df = _df.copy()
    if df.empty or len(df)<100: return {"error":"Insufficient data"}
    d = add_features(df)
    d["target"]=(d["Close"].shift(-5)>d["Close"]).astype(int)
    d = d.dropna()
    if len(d)<80: return {"error":"Not enough clean rows"}
    X = d[FEATURE_COLS]; y = d["target"]
    scaler = StandardScaler(); X_scaled = scaler.fit_transform(X)
    split = int(len(X_scaled)*0.8)
    X_train,X_test = X_scaled[:split],X_scaled[split:]
    y_train,y_test = y.iloc[:split],y.iloc[split:]
    model = RandomForestClassifier(n_estimators=200,max_depth=6,min_samples_leaf=5,random_state=42,n_jobs=-1)
    model.fit(X_train,y_train)
    acc = model.score(X_test,y_test) if len(X_test)>0 else None
    last = X_scaled[-1].reshape(1,-1)
    pred = model.predict(last)[0]; proba = model.predict_proba(last)[0]
    fi = dict(zip(FEATURE_COLS,model.feature_importances_))
    top_features = sorted(fi.items(),key=lambda x:x[1],reverse=True)[:5]
    return {"ticker":ticker,"prediction":"BULLISH" if pred==1 else "BEARISH","confidence":round(float(max(proba))*100,1),"bull_prob":round(float(proba[1])*100,1),"bear_prob":round(float(proba[0])*100,1),"model_accuracy":round(acc*100,1) if acc else None,"top_features":top_features,"last_rsi":round(float(d["rsi"].iloc[-1]),1),"last_macd":round(float(d["macd"].iloc[-1]),4),"bb_pos":round(float(d["bb_pos"].iloc[-1]),3),"vol_ratio":round(float(d["vol_ratio"].iloc[-1]),2)}

def get_technical_signals(df):
    if df.empty or len(df)<50: return {}
    d = add_features(df); last = d.iloc[-1]; prev = d.iloc[-2]; c = float(last["Close"])
    signals = {}
    rsi = last["rsi"]
    if rsi<30: signals["RSI"]=("Oversold","green")
    elif rsi>70: signals["RSI"]=("Overbought","red")
    else: signals["RSI"]=(f"{rsi:.1f}","neutral")
    if last["macd"]>last["macd_signal"] and prev["macd"]<=prev["macd_signal"]: signals["MACD"]=("Bullish Cross","green")
    elif last["macd"]<last["macd_signal"] and prev["macd"]>=prev["macd_signal"]: signals["MACD"]=("Bearish Cross","red")
    else: signals["MACD"]=("Above Signal" if last["macd"]>last["macd_signal"] else "Below Signal","green" if last["macd"]>last["macd_signal"] else "red")
    bp=last["bb_pos"]
    if bp>0.9: signals["Bollinger"]=("Near Upper Band","red")
    elif bp<0.1: signals["Bollinger"]=("Near Lower (Bounce?)","green")
    else: signals["Bollinger"]=(f"Mid Band ({bp:.2f})","neutral")
    sma20=last["sma_20"]; sma50=last["sma_50"]
    if c>sma20>sma50: signals["Trend"]=("Strong Uptrend","green")
    elif c>sma20: signals["Trend"]=("Above 20MA","green")
    elif c<sma20<sma50: signals["Trend"]=("Strong Downtrend","red")
    else: signals["Trend"]=("Mixed","neutral")
    vr=last["vol_ratio"]
    if vr>1.5: signals["Volume"]=(f"High ({vr:.1f}x avg)","green")
    elif vr<0.5: signals["Volume"]=("Low volume","neutral")
    else: signals["Volume"]=("Normal","neutral")
    return signals

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1rem 0 1.5rem 0;'>
        <div style='font-family:Space Mono,monospace;font-size:.6rem;color:#6b7280;letter-spacing:.2em;text-transform:uppercase;margin-bottom:.3rem;'>SYSTEM ONLINE</div>
        <div style='font-family:DM Serif Display,serif;font-size:1.8rem;color:#e5e7eb;line-height:1;'>North<span style="color:#00d4aa;">star</span></div>
        <div style='font-family:Space Mono,monospace;font-size:.6rem;color:#6b7280;letter-spacing:.1em;margin-top:.3rem;'>Guiding Your Market Edge</div>
    </div>
    <hr style='border-color:#1f2937;margin:0 0 1.5rem 0;'/>
    """, unsafe_allow_html=True)
    st.markdown("**NAVIGATION**")
    page = st.radio("",["📡  Market Overview","🔍  Stock Scanner","📰  News Intelligence","💡  AI Picks","📊  Deep Analysis"],label_visibility="collapsed")
    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("""<div style='font-family:Space Mono,monospace;font-size:.6rem;color:#6b7280;text-transform:uppercase;letter-spacing:.1em;'>Data Sources<br/><span style='color:#374151;'>──────────────</span><br/>Yahoo Finance API<br/>RSS News Feeds<br/>ML: Random Forest</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MARKET OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if "Market Overview" in page:
    st.markdown("## Market Overview")
    st.markdown("<div class='terminal-header'>LIVE INDICES — AUTO-REFRESH EVERY 5 MIN</div>", unsafe_allow_html=True)
    col_refresh,_ = st.columns([1,6])
    with col_refresh:
        if st.button("↺  Refresh"): st.cache_data.clear(); st.rerun()

    indices = get_index_data()
    if indices:
        cols = st.columns(len(indices))
        for col,(name,data) in zip(cols,indices.items()):
            price=data.get("price"); pct=data.get("change_pct",0)
            with col: st.metric(label=name,value=f"{price:,.2f}" if price else "—",delta=f"{pct:+.2f}%")

    st.markdown("<br/>", unsafe_allow_html=True)
    col_left,col_right = st.columns([3,2])
    with col_left:
        st.markdown("#### S&P 500 — 1 Year")
        df = get_history("^GSPC","1y")
        if not df.empty:
            cl="#00d4aa" if df["Close"].iloc[-1]>=df["Close"].iloc[0] else "#ef4444"
            fig=go.Figure(); fig.add_trace(go.Scatter(x=df.index,y=df["Close"],mode="lines",line=dict(color=cl,width=1.5),fill="tozeroy",fillcolor="rgba(0,212,170,0.05)" if cl=="#00d4aa" else "rgba(239,68,68,0.05)",name="S&P 500"))
            fig.update_layout(**CHART_THEME,height=280,margin=dict(l=0,r=0,t=10,b=0),showlegend=False)
            st.plotly_chart(fig,use_container_width=True, key="overview_sp500")
    with col_right:
        st.markdown("#### Sector Performance (1D%)")
        sdf=get_sector_performance()
        if not sdf.empty:
            sdf_s=sdf.sort_values("1D%",ascending=True)
            fig2=go.Figure(go.Bar(x=sdf_s["1D%"],y=sdf_s["Sector"],orientation="h",marker_color=["#00d4aa" if v>=0 else "#ef4444" for v in sdf_s["1D%"]],text=[f"{v:+.2f}%" for v in sdf_s["1D%"]],textposition="outside",textfont=dict(size=9,family="Space Mono, monospace")))
            fig2.update_layout(**CHART_THEME,height=280,margin=dict(l=0,r=10,t=10,b=0),bargap=0.35)
            st.plotly_chart(fig2,use_container_width=True, key="overview_sector_bar")

    st.markdown("---")
    st.markdown("#### Sector ETF Dashboard")
    sdf=get_sector_performance()
    if not sdf.empty:
        def cv(val):
            if isinstance(val,float):
                if val>0: return "color:#00d4aa"
                if val<0: return "color:#ef4444"
            return "color:#9ca3af"
        styled=sdf.style.map(cv,subset=["1D%","5D%"]).format({"Price":"${:.2f}","1D%":"{:+.2f}%","5D%":"{:+.2f}%"}).set_properties(**{"background-color":"#111827","color":"#e5e7eb","border":"1px solid #1f2937","font-family":"Space Mono, monospace","font-size":"11px"})
        st.dataframe(styled,use_container_width=True,hide_index=True)

    st.markdown("---")
    st.markdown("#### Index Comparison — YTD Performance (%)")
    fig3=go.Figure()
    try:
        ytd_batch=yf.download("^GSPC ^IXIC ^RUT",period="ytd",group_by="ticker",auto_adjust=True,progress=False)
        is_multi_y=isinstance(ytd_batch.columns,pd.MultiIndex)
        for (name,tick),color in zip({"S&P 500":"^GSPC","NASDAQ":"^IXIC","Russell 2000":"^RUT"}.items(),["#00d4aa","#f59e0b","#a78bfa"]):
            try:
                hist=ytd_batch["Close"][tick].dropna() if is_multi_y else ytd_batch["Close"].dropna()
                if len(hist)>1:
                    base=hist.iloc[0]; norm=(hist/base-1)*100
                    fig3.add_trace(go.Scatter(x=hist.index,y=norm,name=name,line=dict(color=color,width=1.5),mode="lines"))
            except: pass
    except: pass
    fig3.update_layout(**CHART_THEME,height=300,margin=dict(l=0,r=0,t=10,b=0),yaxis_title="Return %",legend=dict(bgcolor="#111827",bordercolor="#1f2937",borderwidth=1,font=dict(size=10,family="Space Mono, monospace")))
    st.plotly_chart(fig3,use_container_width=True, key="overview_ytd")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: STOCK SCANNER
# ══════════════════════════════════════════════════════════════════════════════
elif "Stock Scanner" in page:
    st.markdown("## Stock Scanner")
    st.markdown("<div class='terminal-header'>VALUE + GROWTH + MOMENTUM COMPOSITE SCORING</div>", unsafe_allow_html=True)
    tab1,tab2 = st.tabs(["🔍  Undervalue Screener","🎯  Thematic / Niche"])

    with tab1:
        col_a,col_b,col_c = st.columns([2,2,1])
        with col_a: min_score=st.slider("Minimum Score",0,100,40,5)
        with col_b: sector_filter=st.selectbox("Filter by Sector",["All","Technology","Healthcare","Energy","Financials","Industrials","Materials"])
        with col_c: st.markdown("<br/>",unsafe_allow_html=True); run_scan=st.button("▶  Run Screen")

        st.markdown("<div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:1rem;margin-bottom:1rem;'><div style='font-family:Space Mono,monospace;font-size:.65rem;color:#6b7280;letter-spacing:.1em;text-transform:uppercase;'>5-Factor Quant Score (0–100)</div><div style='font-family:IBM Plex Sans,sans-serif;font-size:.8rem;color:#9ca3af;margin-top:.4rem;'><strong style='color:#e5e7eb;'>Value (25pts)</strong> EV/EBITDA, P/B, P/S &nbsp;·&nbsp; <strong style='color:#e5e7eb;'>Quality (25pts)</strong> ROE, Gross Margin, D/E &nbsp;·&nbsp; <strong style='color:#e5e7eb;'>Growth (20pts)</strong> Revenue CAGR, Earnings, PEG &nbsp;·&nbsp; <strong style='color:#e5e7eb;'>Momentum (20pts)</strong> 52W position, discount from high, Beta &nbsp;·&nbsp; <strong style='color:#e5e7eb;'>Analyst (10pts)</strong> Consensus upside, short interest</div></div>",unsafe_allow_html=True)

        if run_scan or "screener_df" in st.session_state:
            if run_scan:
                with st.spinner("Running screen…"): df=screen_undervalued(); st.session_state["screener_df"]=df
            else: df=st.session_state["screener_df"]
            df_f=df[df["Score"]>=min_score].copy()
            if sector_filter!="All": df_f=df_f[df_f["Sector"].str.contains(sector_filter,na=False)]
            st.markdown(f"**{len(df_f)} stocks** matched")
            if not df_f.empty:
                c1,c2=st.columns([1,2])
                with c1:
                    fig=px.histogram(df,x="Score",nbins=20,color_discrete_sequence=["#00d4aa"])
                    fig.update_layout(**CHART_THEME,height=200,margin=dict(l=0,r=0,t=10,b=0))
                    st.plotly_chart(fig,use_container_width=True, key="scanner_score_hist")
                with c2:
                    top5=df_f.head(5)
                    fig2=go.Figure(go.Bar(x=top5["Score"],y=top5["Ticker"],orientation="h",marker_color="#00d4aa",text=top5["Score"],textposition="outside"))
                    fig2.update_layout(**CHART_THEME,height=200,margin=dict(l=0,r=0,t=10,b=0),xaxis_range=[0,110])
                    st.plotly_chart(fig2,use_container_width=True, key="scanner_top5")

                avail=[c for c in ["Ticker","Name","Price","Score","Signals","EV/EBITDA","P/B","ROE","Rev Growth","Fwd PEG","D/E","Sector","Change%"] if c in df_f.columns]
                def ss(val): return "background-color:#052e16;color:#00d4aa" if isinstance(val,(int,float)) and val>=70 else ("background-color:#1c1407;color:#f59e0b" if isinstance(val,(int,float)) and val>=45 else "background-color:#1c0707;color:#ef4444" if isinstance(val,(int,float)) else "")
                def sc(val): return "color:#00d4aa" if isinstance(val,(int,float)) and val>=0 else "color:#ef4444"
                styled=df_f[avail].head(40).style.map(ss,subset=["Score"]).map(sc,subset=["Change%"]).format({"Price":"${:.2f}","Score":"{:.0f}","Change%":lambda x:f"{x:+.2f}%" if x==x else "—"}).set_properties(**{"background-color":"#111827","color":"#e5e7eb","border":"1px solid #1f2937","font-family":"Space Mono, monospace","font-size":"11px"})
                st.dataframe(styled,use_container_width=True,hide_index=True)

    with tab2:
        st.markdown("### Rising & Niche Industry Themes")
        theme=st.selectbox("Select Theme",list(THEMATIC_STOCKS.keys()))
        descs={"AI Infrastructure":"Companies building the picks-and-shovels of the AI boom — chips, networking, cooling, and data center hardware.","Nuclear Energy":"Nuclear renaissance driven by AI power demand and decarbonization goals. Includes utilities restarting plants and SMR developers.","Biotech Emerging":"Clinical-stage biotech with platform-level science. High risk, high reward — gene therapy, RNA editing, oncology.","Defense Tech":"Next-gen defense: autonomous systems, drone defense, hypersonics, and dual-use tech companies.","Water Tech":"Water scarcity is a global mega-trend. Utilities, infrastructure, and purification technology companies.","Reshoring/Mfg":"Beneficiaries of supply chain deglobalization — US industrial automation, smart manufacturing, and onshoring plays.","GLP-1 / Obesity":"The GLP-1 drug revolution for obesity and metabolic disease. Includes drugmakers and enablers.","Quantum Computing":"Early-stage quantum hardware and software. Long time horizon, asymmetric upside."}
        st.markdown(f"<div style='background:#111827;border:1px solid #1f2937;border-left:3px solid #f59e0b;border-radius:6px;padding:1rem;margin-bottom:1.5rem;'><span style='font-family:Space Mono,monospace;font-size:.65rem;color:#f59e0b;text-transform:uppercase;letter-spacing:.1em;'>THEME THESIS</span><p style='font-family:IBM Plex Sans,sans-serif;font-size:.85rem;color:#d1d5db;margin:.4rem 0 0 0;'>{descs.get(theme,'')}</p></div>",unsafe_allow_html=True)

        tickers=THEMATIC_STOCKS[theme]; rows=[]
        with st.spinner(f"Loading {theme}…"):
            for tick in tickers:
                q=get_quote(tick)
                if q and not q.get("error"):
                    rows.append({"Ticker":tick,"Name":(q.get("name") or tick)[:22],"Price":round(q.get("price",0),2),"1D%":round(q.get("change_pct",0),2),"Mkt Cap":q.get("market_cap")})

        if rows:
            cols=st.columns(min(len(rows),4))
            for i,row in enumerate(rows):
                with cols[i%len(cols)]:
                    pct=row.get("1D%",0); pc="#00d4aa" if pct>=0 else "#ef4444"
                    mc=row.get("Mkt Cap"); mcs=f"${mc/1e9:.1f}B" if mc and mc>=1e9 else (f"${mc/1e6:.0f}M" if mc else "—")
                    st.markdown(f"<div class='metric-card' style='text-align:center;'><div style='font-family:Space Mono,monospace;font-size:.9rem;font-weight:700;color:#e5e7eb;'>{row['Ticker']}</div><div style='font-family:IBM Plex Sans,sans-serif;font-size:.7rem;color:#6b7280;'>{row['Name']}</div><div style='font-family:Space Mono,monospace;font-size:1rem;color:#e5e7eb;'>${row['Price']:,.2f}</div><div style='font-family:Space Mono,monospace;font-size:.8rem;color:{pc};'>{pct:+.2f}%</div><div style='font-family:Space Mono,monospace;font-size:.65rem;color:#6b7280;'>{mcs}</div></div>",unsafe_allow_html=True)

            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown(f"#### {theme} — 3-Month Relative Performance")
            fig=go.Figure()
            try:
                batch_t=yf.download(" ".join(tickers[:7]),period="3mo",group_by="ticker",auto_adjust=True,progress=False)
                is_multi_t=isinstance(batch_t.columns,pd.MultiIndex)
                for tick,color in zip(tickers[:7],["#00d4aa","#f59e0b","#a78bfa","#60a5fa","#f87171","#34d399","#fb923c"]):
                    try:
                        hist=batch_t["Close"][tick].dropna() if is_multi_t else batch_t["Close"].dropna()
                        if len(hist)>1:
                            base=hist.iloc[0]; norm=(hist/base-1)*100
                            fig.add_trace(go.Scatter(x=hist.index,y=norm,name=tick,line=dict(color=color,width=1.5)))
                    except: pass
            except: pass
            fig.update_layout(**CHART_THEME,height=320,margin=dict(l=0,r=0,t=10,b=0),yaxis_title="Return %",legend=dict(bgcolor="#111827",bordercolor="#1f2937",borderwidth=1,font=dict(size=10,family="Space Mono, monospace")))
            st.plotly_chart(fig,use_container_width=True, key=f"thematic_{theme.replace(" ","_").replace("/","_").lower()}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: NEWS INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
elif "News Intelligence" in page:
    st.markdown("## News Intelligence")
    st.markdown("<div class='terminal-header'>SENTIMENT-TAGGED MARKET NEWS — RSS AGGREGATION</div>", unsafe_allow_html=True)
    tab1,tab2=st.tabs(["📰  Live Feed","🌍  World Events → Trades"])

    with tab1:
        col_f,col_r=st.columns([4,1])
        with col_f: sf=st.radio("Filter:",["All","Positive","Negative","Neutral"],horizontal=True)
        with col_r: st.markdown("<br/>",unsafe_allow_html=True);
        if st.button("↺  Refresh"): st.cache_data.clear(); st.rerun()

        with st.spinner("Loading news…"): articles=get_news(count=30)
        for a in articles: a["sentiment"]=simple_sentiment(a["title"]+" "+a.get("summary",""))
        filtered=articles if sf=="All" else [a for a in articles if a["sentiment"]==sf.lower()]
        pos=sum(1 for a in articles if a["sentiment"]=="positive"); neg=sum(1 for a in articles if a["sentiment"]=="negative"); total=len(articles)
        c1,c2,c3,c4=st.columns(4)
        with c1: st.metric("Total Articles",total)
        with c2: st.metric("🟢 Positive",pos)
        with c3: st.metric("🔴 Negative",neg)
        with c4: st.metric("Market Tone","RISK-ON 📈" if pos>neg*1.3 else ("RISK-OFF 📉" if neg>pos*1.3 else "MIXED ◆"))
        st.markdown("---")
        SICONS={"positive":("▲","#00d4aa"),"negative":("▼","#ef4444"),"neutral":("◆","#6b7280")}
        for a in filtered[:20]:
            sent=a["sentiment"]; icon,color=SICONS[sent]
            css="news-card"+(" negative" if sent=="negative" else " neutral" if sent=="neutral" else "")
            st.markdown(f"<div class='{css}'><div style='display:flex;justify-content:space-between;'><div style='flex:1;'><a href='{a.get('link','#')}' target='_blank' style='font-family:DM Serif Display,serif;font-size:1rem;color:#e5e7eb;text-decoration:none;'>{a['title']}</a><div style='font-family:IBM Plex Sans,sans-serif;font-size:.75rem;color:#9ca3af;margin-top:.3rem;'>{a.get('summary','')[:160]}…</div></div><span style='font-family:Space Mono,monospace;font-size:.8rem;color:{color};margin-left:1rem;white-space:nowrap;'>{icon} {sent.upper()}</span></div><div style='font-family:Space Mono,monospace;font-size:.6rem;color:#374151;margin-top:.4rem;'>{a.get('source','')} · {a.get('published','')[:20]}</div></div>",unsafe_allow_html=True)

    with tab2:
        st.markdown("### Global Events → Investment Implications")
        THEMES={"AI & Tech Regulation":{"thesis":"Regulatory clarity on AI could re-rate software/chip stocks. Watch EU AI Act compliance costs vs US permissiveness.","tickers":["NVDA","MSFT","GOOGL","META","AMD"],"bias":"bullish"},"Energy Transition":{"thesis":"IRA incentives + AI power demand driving nuclear and grid renaissance. Utilities undervalued vs growth trajectory.","tickers":["CEG","VST","FSLR","NEE","ENPH"],"bias":"bullish"},"Geopolitical Risk":{"thesis":"Elevated geopolitical tension structurally benefits defense, domestic manufacturing, and commodity producers.","tickers":["LMT","RTX","NOC","KTOS","MP"],"bias":"neutral"},"Healthcare & GLP-1":{"thesis":"Obesity drug revolution restructuring healthcare economics. Winners: pharma, medtech. Losers: food & bariatric.","tickers":["LLY","NVO","HIMS","VKTX","DXCM"],"bias":"bullish"},"Macro / Fed Policy":{"thesis":"Rate path uncertainty drives volatility. Rate cuts benefit rate-sensitive sectors (REIT, biotech, small-caps).","tickers":["TLT","GLD","IWM","XLRE","KRE"],"bias":"neutral"}}
        st_theme=st.selectbox("Select World Event Theme:",list(THEMES.keys()))
        td=THEMES[st_theme]; bc="#00d4aa" if td["bias"]=="bullish" else "#ef4444" if td["bias"]=="bearish" else "#f59e0b"
        st.markdown(f"<div style='background:#111827;border:1px solid #1f2937;border-left:3px solid {bc};border-radius:6px;padding:1.25rem;margin-bottom:1.5rem;'><div style='font-family:Space Mono,monospace;font-size:.65rem;color:{bc};text-transform:uppercase;letter-spacing:.1em;'>{td['bias'].upper()} BIAS — INVESTMENT THESIS</div><div style='font-family:IBM Plex Sans,sans-serif;font-size:.9rem;color:#d1d5db;margin-top:.5rem;'>{td['thesis']}</div></div>",unsafe_allow_html=True)
        st.markdown("**Equity Plays to Watch**")
        tcols=st.columns(len(td["tickers"]))
        for col,tick in zip(tcols,td["tickers"]):
            with col:
                q=get_quote(tick)
                if q and not q.get("error"):
                    pct=q.get("change_pct",0); pc="#00d4aa" if pct>=0 else "#ef4444"
                    st.markdown(f"<div class='metric-card' style='text-align:center;padding:.8rem;'><div style='font-family:Space Mono,monospace;font-size:.9rem;font-weight:700;color:#e5e7eb;'>{tick}</div><div style='font-family:Space Mono,monospace;font-size:.85rem;color:#d1d5db;'>${q.get('price',0):,.2f}</div><div style='font-family:Space Mono,monospace;font-size:.75rem;color:{pc};'>{pct:+.2f}%</div></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI PICKS
# ══════════════════════════════════════════════════════════════════════════════
elif "AI Picks" in page:
    st.markdown("## AI Picks")
    st.markdown("<div class='terminal-header'>ML PREDICTIONS + CURATED INVESTMENT THESES</div>", unsafe_allow_html=True)
    tab1,tab2=st.tabs(["🤖  ML Prediction Engine","💡  Curated AI Portfolios"])

    with tab1:
        st.markdown("### Run ML Prediction on Any Stock")
        st.markdown("<div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:.75rem 1rem;margin-bottom:1rem;font-family:IBM Plex Sans,sans-serif;font-size:.8rem;color:#9ca3af;'><strong style='color:#e5e7eb;'>Model:</strong> Random Forest (200 trees, 18 technical features). Predicts 5-day directional movement. <strong style='color:#f59e0b;'>Not financial advice.</strong></div>",unsafe_allow_html=True)
        col_i,col_p=st.columns([3,1])
        with col_i: ticker_input=st.text_input("Ticker Symbol",placeholder="e.g. NVDA, AAPL, CEG").upper().strip()
        with col_p: period=st.selectbox("Training Data",["2y","5y","1y"],index=0)
        run_btn=st.button("▶  Run ML Prediction")

        if run_btn and ticker_input:
            with st.spinner(f"Training model on {ticker_input}…"):
                df=get_history(ticker_input,period=period)
                if df.empty: st.error(f"No data found for {ticker_input}")
                else:
                    result=predict_direction(ticker_input,df)
                    signals=get_technical_signals(df)
                    quote=get_quote(ticker_input)
                    if "error" in result: st.warning(result["error"])
                    else:
                        pred=result["prediction"]; conf=result["confidence"]; bull=result["bull_prob"]
                        pc="#00d4aa" if pred=="BULLISH" else "#ef4444"
                        c1,c2,c3=st.columns([2,1,1])
                        with c1: st.markdown(f"<div class='metric-card'><div style='font-family:Space Mono,monospace;font-size:.65rem;color:#6b7280;text-transform:uppercase;'>5-Day Direction Prediction</div><div style='font-family:DM Serif Display,serif;font-size:2.5rem;color:{pc};margin:.3rem 0;'>{pred}</div><div style='font-family:Space Mono,monospace;font-size:.85rem;color:#9ca3af;'>{bull:.1f}% bull probability · {conf:.1f}% confidence</div></div>",unsafe_allow_html=True)
                        with c2: st.metric("Current Price",f"${quote.get('price',0):,.2f}",delta=f"{quote.get('change_pct',0):+.2f}%"); st.metric("RSI (14)",f"{result.get('last_rsi','—')}")
                        with c3: st.metric("BB Position",f"{result.get('bb_pos',0):.2f}"); st.metric("Volume Ratio",f"{result.get('vol_ratio',0):.2f}x")
                        st.markdown(f"<div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:.8rem 1rem;margin:1rem 0;'><div style='font-family:Space Mono,monospace;font-size:.65rem;color:#6b7280;margin-bottom:.5rem;'>BULL / BEAR PROBABILITY</div><div style='display:flex;align-items:center;gap:.5rem;'><span style='font-family:Space Mono,monospace;font-size:.75rem;color:#00d4aa;width:40px;'>{bull:.0f}%</span><div style='flex:1;background:#1f2937;border-radius:4px;height:12px;overflow:hidden;'><div style='width:{bull}%;background:linear-gradient(90deg,#00d4aa,#059669);height:100%;'></div></div><div style='flex:1;background:#1f2937;border-radius:4px;height:12px;overflow:hidden;'><div style='width:{100-bull}%;background:linear-gradient(90deg,#ef4444,#b91c1c);height:100%;float:right;'></div></div><span style='font-family:Space Mono,monospace;font-size:.75rem;color:#ef4444;width:40px;text-align:right;'>{100-bull:.0f}%</span></div></div>",unsafe_allow_html=True)
                        if signals:
                            st.markdown("**Technical Signals**")
                            scols=st.columns(len(signals)); scmap={"green":"#00d4aa","red":"#ef4444","neutral":"#6b7280"}
                            for col,(name,(val,color)) in zip(scols,signals.items()):
                                with col: st.markdown(f"<div class='metric-card' style='text-align:center;padding:.6rem;'><div style='font-family:Space Mono,monospace;font-size:.6rem;color:#6b7280;text-transform:uppercase;'>{name}</div><div style='font-family:Space Mono,monospace;font-size:.7rem;color:{scmap.get(color,'#9ca3af')};margin-top:4px;'>{val}</div></div>",unsafe_allow_html=True)
                        hist_6m=df.last("180D")
                        fig2=go.Figure()
                        fig2.add_trace(go.Candlestick(x=hist_6m.index,open=hist_6m["Open"],high=hist_6m["High"],low=hist_6m["Low"],close=hist_6m["Close"],increasing_line_color="#00d4aa",decreasing_line_color="#ef4444",name=ticker_input))
                        for w,c,d in [(20,"#f59e0b","dot"),(50,"#a78bfa","dot")]:
                            ma=hist_6m["Close"].rolling(w).mean()
                            fig2.add_trace(go.Scatter(x=hist_6m.index,y=ma,name=f"SMA{w}",line=dict(color=c,width=1,dash=d)))
                        fig2.update_layout(**CHART_THEME,height=320,margin=dict(l=0,r=0,t=10,b=0),xaxis_rangeslider_visible=False,legend=dict(bgcolor="#111827",bordercolor="#1f2937",borderwidth=1,font=dict(size=9,family="Space Mono, monospace")))
                        st.plotly_chart(fig2,use_container_width=True, key=f"ml_candle_{ticker_input}")

    with tab2:
        st.markdown("### Curated AI-Analyzed Portfolios")
        for pname,pdata in AI_WATCHLIST.items():
            risk=pdata["risk"]; rc=RISK_COLORS.get(risk,"#6b7280")
            with st.expander(f"📂  {pname}  ·  Risk: {risk}  ·  Horizon: {pdata['time_horizon']}",expanded=(pname=="High Conviction")):
                st.markdown(f"<div style='border-left:3px solid {rc};padding-left:1rem;margin-bottom:1rem;'><div style='font-family:Space Mono,monospace;font-size:.65rem;color:{rc};text-transform:uppercase;'>Investment Thesis</div><div style='font-family:IBM Plex Sans,sans-serif;font-size:.85rem;color:#d1d5db;margin-top:.3rem;'>{pdata['rationale']}</div></div>",unsafe_allow_html=True)
                tcols=st.columns(len(pdata["tickers"]))
                for col,tick in zip(tcols,pdata["tickers"]):
                    with col:
                        q=get_quote(tick)
                        if q and not q.get("error"):
                            pct=q.get("change_pct",0); pc="#00d4aa" if pct>=0 else "#ef4444"
                            tgt=q.get("analyst_target"); pr=q.get("price",0)
                            up=f"+{(tgt-pr)/pr*100:.0f}%" if tgt and pr and tgt>pr else ""
                            st.markdown(f"<div class='metric-card' style='text-align:center;'><div style='font-family:Space Mono,monospace;font-size:.9rem;font-weight:700;color:#e5e7eb;'>{tick}</div><div style='font-family:Space Mono,monospace;font-size:1rem;color:#e5e7eb;'>${pr:,.2f}</div><div style='font-family:Space Mono,monospace;font-size:.8rem;color:{pc};'>{pct:+.2f}%</div>{f'<div style=\"font-family:Space Mono,monospace;font-size:.65rem;color:#00d4aa;\">Analyst upside {up}</div>' if up else ''}</div>",unsafe_allow_html=True)
                fig=go.Figure()
                tickers_str=" ".join(pdata["tickers"])
                try:
                    batch=yf.download(tickers_str,period="6mo",group_by="ticker",auto_adjust=True,progress=False)
                    is_multi=isinstance(batch.columns,pd.MultiIndex)
                    for tick,color in zip(pdata["tickers"],["#00d4aa","#f59e0b","#a78bfa","#60a5fa","#f87171"]):
                        try:
                            hist=batch["Close"][tick].dropna() if is_multi else batch["Close"].dropna()
                            if len(hist)>1:
                                base=hist.iloc[0]
                                fig.add_trace(go.Scatter(x=hist.index,y=(hist/base-1)*100,name=tick,line=dict(color=color,width=1.5)))
                        except: pass
                except: pass
                fig.update_layout(**CHART_THEME,height=250,margin=dict(l=0,r=0,t=10,b=0),yaxis_title="Return %",legend=dict(bgcolor="#111827",bordercolor="#1f2937",borderwidth=1,font=dict(size=9,family="Space Mono, monospace")))
                st.plotly_chart(fig,use_container_width=True, key=f"analysis_main_{ticker}")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DEEP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif "Deep Analysis" in page:
    st.markdown("## Deep Analysis")
    st.markdown("<div class='terminal-header'>FUNDAMENTAL + TECHNICAL + COMPARATIVE ANALYSIS</div>", unsafe_allow_html=True)
    col_in,col_cmp,col_per=st.columns([3,3,1])
    with col_in: ticker=st.text_input("Primary Ticker",placeholder="e.g. NVDA").upper().strip()
    with col_cmp: craw=st.text_input("Compare With (comma-separated)",placeholder="e.g. AMD, INTC"); ctickers=[t.strip().upper() for t in craw.split(",") if t.strip()] if craw else []
    with col_per: period=st.selectbox("Period",["1y","2y","5y","6mo","ytd"],index=0)

    if not ticker:
        st.markdown("<div style='text-align:center;padding:3rem;color:#374151;font-family:Space Mono,monospace;font-size:.75rem;'>ENTER A TICKER SYMBOL TO BEGIN ANALYSIS</div>",unsafe_allow_html=True)
    else:
        with st.spinner(f"Loading {ticker}…"):
            df=get_history(ticker,period=period); q=get_quote(ticker)
        if df.empty or not q or q.get("error"): st.error(f"Could not load data for {ticker}")
        else:
            pct=q.get("change_pct",0); pc="#00d4aa" if pct>=0 else "#ef4444"
            mc=q.get("market_cap"); mcs=f"${mc/1e9:.1f}B" if mc and mc>=1e9 else (f"${mc/1e6:.0f}M" if mc else "—")
            st.markdown(f"<div style='background:#111827;border:1px solid #1f2937;border-radius:8px;padding:1.5rem;margin-bottom:1.5rem;'><div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;'><div><span style='font-family:Space Mono,monospace;font-size:1.4rem;font-weight:700;color:#e5e7eb;'>{ticker}</span><span style='font-family:IBM Plex Sans,sans-serif;font-size:.9rem;color:#6b7280;margin-left:.75rem;'>{q.get('name','')}</span><br/><span style='font-family:Space Mono,monospace;font-size:.7rem;color:#9ca3af;'>{q.get('sector','')} · {q.get('industry','')}</span></div><div style='text-align:right;'><div style='font-family:Space Mono,monospace;font-size:1.8rem;color:#e5e7eb;'>${q.get('price',0):,.2f}</div><div style='font-family:Space Mono,monospace;font-size:1rem;color:{pc};'>{pct:+.2f}% today</div><div style='font-family:Space Mono,monospace;font-size:.7rem;color:#6b7280;'>Mkt Cap: {mcs}</div></div></div></div>",unsafe_allow_html=True)

            mets=[("P/E",q.get("pe_ratio"),None),("Fwd P/E",q.get("forward_pe"),None),("P/B",q.get("pb_ratio"),None),("P/S",q.get("ps_ratio"),None),("EV/EBITDA",q.get("ev_ebitda"),None),("D/E",q.get("debt_equity"),None),("ROE",q.get("roe"),"pct"),("Gross Margin",q.get("gross_margin"),"pct"),("Rev Growth",q.get("revenue_growth"),"pct"),("Beta",q.get("beta"),None)]
            mcols=st.columns(len(mets))
            for col,(label,val,fmt) in zip(mcols,mets):
                with col:
                    if fmt=="pct" and val is not None: dsp=f"{val*100:.1f}%"
                    elif isinstance(val,float): dsp=f"{val:.2f}"
                    else: dsp=str(val) if val else "—"
                    st.metric(label,dsp)

            tgt=q.get("analyst_target"); price=q.get("price",0)
            if tgt and price:
                up=(tgt-price)/price*100; uc="#00d4aa" if up>0 else "#ef4444"
                rec=q.get("recommendation"); rmap={1:"Strong Buy",2:"Buy",3:"Hold",4:"Underperform",5:"Sell"}
                rs=rmap.get(round(rec),"—") if rec else "—"
                st.markdown(f"<div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:.75rem 1rem;margin:1rem 0;display:flex;gap:2rem;'><div><span style='font-family:Space Mono,monospace;font-size:.6rem;color:#6b7280;text-transform:uppercase;'>Analyst Target</span><br/><span style='font-family:Space Mono,monospace;font-size:1rem;color:#e5e7eb;'>${tgt:,.2f}</span><span style='font-family:Space Mono,monospace;font-size:.8rem;color:{uc};margin-left:.5rem;'>{up:+.1f}% upside</span></div><div><span style='font-family:Space Mono,monospace;font-size:.6rem;color:#6b7280;text-transform:uppercase;'>Recommendation</span><br/><span style='font-family:Space Mono,monospace;font-size:1rem;color:#e5e7eb;'>{rs}</span></div><div><span style='font-family:Space Mono,monospace;font-size:.6rem;color:#6b7280;text-transform:uppercase;'>52W Range</span><br/><span style='font-family:Space Mono,monospace;font-size:.9rem;color:#9ca3af;'>${q.get('52w_low',0):,.2f} — ${q.get('52w_high',0):,.2f}</span></div></div>",unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Price Chart + Technical Indicators")
            df_feat=add_features(df)
            fig=make_subplots(rows=3,cols=1,shared_xaxes=True,row_heights=[0.55,0.25,0.20],vertical_spacing=0.03,subplot_titles=["","Volume","RSI (14)"])
            fig.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],increasing_line_color="#00d4aa",decreasing_line_color="#ef4444",name=ticker),row=1,col=1)
            for w,c,d in [(20,"#f59e0b","dot"),(50,"#a78bfa","dot"),(200,"#60a5fa","dash")]:
                ma=df["Close"].rolling(w).mean()
                fig.add_trace(go.Scatter(x=df.index,y=ma,name=f"SMA{w}",line=dict(color=c,width=1,dash=d)),row=1,col=1)
            if "bb_upper" in df_feat.columns:
                fig.add_trace(go.Scatter(x=df_feat.index,y=df_feat["bb_upper"],name="BB Upper",line=dict(color="#374151",width=1,dash="dash")),row=1,col=1)
                fig.add_trace(go.Scatter(x=df_feat.index,y=df_feat["bb_lower"],name="BB Lower",line=dict(color="#374151",width=1,dash="dash"),fill="tonexty",fillcolor="rgba(55,65,81,0.1)"),row=1,col=1)
            vc=["#00d4aa" if c>=o else "#ef4444" for c,o in zip(df["Close"],df["Open"])]
            fig.add_trace(go.Bar(x=df.index,y=df["Volume"],name="Volume",marker_color=vc,showlegend=False),row=2,col=1)
            if "rsi" in df_feat.columns:
                fig.add_trace(go.Scatter(x=df_feat.index,y=df_feat["rsi"],name="RSI",line=dict(color="#a78bfa",width=1.5)),row=3,col=1)
                fig.add_hline(y=70,line_dash="dash",line_color="#ef4444",line_width=1,row=3,col=1)
                fig.add_hline(y=30,line_dash="dash",line_color="#00d4aa",line_width=1,row=3,col=1)
            fig.update_layout(**CHART_THEME,height=580,margin=dict(l=0,r=0,t=30,b=0),xaxis_rangeslider_visible=False,legend=dict(bgcolor="#111827",bordercolor="#1f2937",borderwidth=1,font=dict(size=8,family="Space Mono, monospace"),orientation="h",yanchor="bottom",y=1.01))
            for i in range(1,4): fig.update_xaxes(gridcolor="#1f2937",row=i,col=1); fig.update_yaxes(gridcolor="#1f2937",row=i,col=1)
            st.plotly_chart(fig,use_container_width=True, key=f"portfolio_{pname.replace(' ','_').lower()}")

            if "macd" in df_feat.columns:
                st.markdown("#### MACD")
                fm=go.Figure()
                fm.add_trace(go.Scatter(x=df_feat.index,y=df_feat["macd"],name="MACD",line=dict(color="#00d4aa",width=1.5)))
                fm.add_trace(go.Scatter(x=df_feat.index,y=df_feat["macd_signal"],name="Signal",line=dict(color="#f59e0b",width=1.5,dash="dot")))
                hc=["#00d4aa" if v>=0 else "#ef4444" for v in df_feat["macd_hist"]]
                fm.add_trace(go.Bar(x=df_feat.index,y=df_feat["macd_hist"],name="Histogram",marker_color=hc))
                fm.update_layout(**CHART_THEME,height=200,margin=dict(l=0,r=0,t=10,b=0),legend=dict(bgcolor="#111827",bordercolor="#1f2937",borderwidth=1,font=dict(size=9,family="Space Mono, monospace")))
                st.plotly_chart(fm,use_container_width=True, key=f"analysis_macd_{ticker}")

            if ctickers:
                st.markdown("---")
                st.markdown(f"#### {ticker} vs {', '.join(ctickers)} — Normalized Performance")
                fc=go.Figure()
                try:
                    all_t=[ticker]+ctickers
                    batch_c=yf.download(" ".join(all_t),period=period,group_by="ticker",auto_adjust=True,progress=False)
                    is_multi_c=isinstance(batch_c.columns,pd.MultiIndex)
                    for tick,color in zip(all_t,["#00d4aa","#f59e0b","#a78bfa","#60a5fa","#f87171"]):
                        try:
                            hist=batch_c["Close"][tick].dropna() if is_multi_c else batch_c["Close"].dropna()
                            if len(hist)>1:
                                base=hist.iloc[0]
                                fc.add_trace(go.Scatter(x=hist.index,y=(hist/base-1)*100,name=tick,line=dict(color=color,width=1.5)))
                        except: pass
                except: pass
                fc.update_layout(**CHART_THEME,height=280,margin=dict(l=0,r=0,t=10,b=0),yaxis_title="Return %",legend=dict(bgcolor="#111827",bordercolor="#1f2937",borderwidth=1,font=dict(size=9,family="Space Mono, monospace")))
                st.plotly_chart(fc,use_container_width=True, key=f"analysis_compare_{ticker}")

            summ=q.get("summary","")
            if summ:
                st.markdown("---"); st.markdown("#### About")
                st.markdown(f"<div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:1rem;font-family:IBM Plex Sans,sans-serif;font-size:.85rem;color:#9ca3af;line-height:1.6;'>{summ[:800]}{'…' if len(summ)>800 else ''}</div>",unsafe_allow_html=True)
