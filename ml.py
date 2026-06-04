"""
models/ml.py — ML prediction models (Random Forest + simple LSTM-style)
Uses scikit-learn; no GPU / heavy deps required.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import streamlit as st


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicator features to OHLCV dataframe."""
    d = df.copy()
    c = d["Close"]

    # Moving averages
    d["sma_5"]  = c.rolling(5).mean()
    d["sma_20"] = c.rolling(20).mean()
    d["sma_50"] = c.rolling(50).mean()
    d["ema_12"] = c.ewm(span=12).mean()
    d["ema_26"] = c.ewm(span=26).mean()

    # MACD
    d["macd"]        = d["ema_12"] - d["ema_26"]
    d["macd_signal"] = d["macd"].ewm(span=9).mean()
    d["macd_hist"]   = d["macd"] - d["macd_signal"]

    # RSI
    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    d["rsi"] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    std20 = c.rolling(20).std()
    d["bb_upper"] = d["sma_20"] + 2 * std20
    d["bb_lower"] = d["sma_20"] - 2 * std20
    d["bb_width"] = (d["bb_upper"] - d["bb_lower"]) / d["sma_20"]
    d["bb_pos"]   = (c - d["bb_lower"]) / (d["bb_upper"] - d["bb_lower"] + 1e-9)

    # ATR (volatility)
    hl   = d["High"] - d["Low"]
    hpc  = (d["High"] - c.shift(1)).abs()
    lpc  = (d["Low"]  - c.shift(1)).abs()
    tr   = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean()

    # Volume features
    d["vol_ratio"] = d["Volume"] / d["Volume"].rolling(20).mean()

    # Price change features
    for lag in [1, 3, 5, 10]:
        d[f"ret_{lag}d"] = c.pct_change(lag)

    # Cross-signals
    d["above_sma20"] = (c > d["sma_20"]).astype(int)
    d["above_sma50"] = (c > d["sma_50"]).astype(int)
    d["golden_cross"] = ((d["sma_20"] > d["sma_50"]) &
                          (d["sma_20"].shift(1) <= d["sma_50"].shift(1))).astype(int)

    return d


FEATURE_COLS = [
    "sma_5", "sma_20", "sma_50",
    "macd", "macd_signal", "macd_hist",
    "rsi", "bb_width", "bb_pos",
    "atr", "vol_ratio",
    "ret_1d", "ret_3d", "ret_5d", "ret_10d",
    "above_sma20", "above_sma50", "golden_cross",
]


@st.cache_data(ttl=3600, show_spinner=False)
def predict_direction(ticker: str, df: pd.DataFrame) -> dict:
    """
    Predict 5-day price direction using Random Forest.
    Returns dict with prediction, confidence, feature importances.
    """
    if df.empty or len(df) < 100:
        return {"error": "Insufficient data (need ≥100 rows)"}

    d = add_features(df)

    # Target: 1 if price is higher 5 days later, else 0
    d["target"] = (d["Close"].shift(-5) > d["Close"]).astype(int)
    d = d.dropna()

    if len(d) < 80:
        return {"error": "Not enough clean rows after feature engineering"}

    X = d[FEATURE_COLS]
    y = d["target"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Time-series split: train on older data, evaluate on recent
    split = int(len(X_scaled) * 0.8)
    X_train, X_test = X_scaled[:split], X_scaled[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = RandomForestClassifier(
        n_estimators=200, max_depth=6, min_samples_leaf=5,
        random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Accuracy on test set
    if len(X_test) > 0:
        acc = model.score(X_test, y_test)
    else:
        acc = None

    # Predict on most recent row
    last_row = X_scaled[-1].reshape(1, -1)
    pred  = model.predict(last_row)[0]
    proba = model.predict_proba(last_row)[0]

    # Feature importances
    fi = dict(zip(FEATURE_COLS, model.feature_importances_))
    top_features = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "ticker": ticker,
        "prediction": "BULLISH" if pred == 1 else "BEARISH",
        "confidence": round(float(max(proba)) * 100, 1),
        "bull_prob": round(float(proba[1]) * 100, 1),
        "bear_prob": round(float(proba[0]) * 100, 1),
        "model_accuracy": round(acc * 100, 1) if acc else None,
        "top_features": top_features,
        "last_rsi": round(float(d["rsi"].iloc[-1]), 1),
        "last_macd": round(float(d["macd"].iloc[-1]), 4),
        "bb_pos": round(float(d["bb_pos"].iloc[-1]), 3),
        "vol_ratio": round(float(d["vol_ratio"].iloc[-1]), 2),
    }


def get_technical_signals(df: pd.DataFrame) -> dict:
    """Return a simple dict of current technical signal states."""
    if df.empty or len(df) < 50:
        return {}
    d = add_features(df)
    last = d.iloc[-1]
    prev = d.iloc[-2]
    c    = float(last["Close"])

    signals = {}

    # RSI zones
    rsi = last["rsi"]
    if rsi < 30:   signals["RSI"] = ("Oversold", "green")
    elif rsi > 70: signals["RSI"] = ("Overbought", "red")
    else:          signals["RSI"] = (f"{rsi:.1f}", "neutral")

    # MACD crossover
    if last["macd"] > last["macd_signal"] and prev["macd"] <= prev["macd_signal"]:
        signals["MACD"] = ("Bullish Cross", "green")
    elif last["macd"] < last["macd_signal"] and prev["macd"] >= prev["macd_signal"]:
        signals["MACD"] = ("Bearish Cross", "red")
    else:
        val = "Above Signal" if last["macd"] > last["macd_signal"] else "Below Signal"
        signals["MACD"] = (val, "green" if last["macd"] > last["macd_signal"] else "red")

    # Bollinger
    bp = last["bb_pos"]
    if bp > 0.9:   signals["Bollinger"] = ("Near Upper Band", "red")
    elif bp < 0.1: signals["Bollinger"] = ("Near Lower Band (Potential Bounce)", "green")
    else:          signals["Bollinger"] = (f"Mid Band ({bp:.2f})", "neutral")

    # MA trend
    sma20 = last["sma_20"]
    sma50 = last["sma_50"]
    if c > sma20 > sma50:  signals["Trend"] = ("Strong Uptrend", "green")
    elif c > sma20:        signals["Trend"] = ("Above 20MA", "green")
    elif c < sma20 < sma50: signals["Trend"] = ("Strong Downtrend", "red")
    else:                  signals["Trend"] = ("Mixed", "neutral")

    # Volume
    vr = last["vol_ratio"]
    if vr > 1.5:   signals["Volume"] = (f"High ({vr:.1f}x avg)", "green")
    elif vr < 0.5: signals["Volume"] = ("Low volume", "neutral")
    else:          signals["Volume"] = ("Normal", "neutral")

    return signals
