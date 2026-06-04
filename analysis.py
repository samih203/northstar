"""pages/analysis.py — Deep Stock Analysis"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import get_quote, get_history
from models.ml import add_features

CHART_THEME = dict(
    paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
    font=dict(color="#9ca3af", family="Space Mono, monospace", size=10),
    gridcolor="#1f2937",
)


def render():
    st.markdown("## Deep Analysis")
    st.markdown("<div class='terminal-header'>FUNDAMENTAL + TECHNICAL + COMPARATIVE ANALYSIS</div>", unsafe_allow_html=True)

    col_in, col_compare, col_period = st.columns([3, 3, 1])
    with col_in:
        ticker = st.text_input("Primary Ticker", placeholder="e.g. NVDA").upper().strip()
    with col_compare:
        compare_raw = st.text_input("Compare With (comma-separated, optional)", placeholder="e.g. AMD, INTC")
        compare_tickers = [t.strip().upper() for t in compare_raw.split(",") if t.strip()] if compare_raw else []
    with col_period:
        period = st.selectbox("Period", ["1y","2y","5y","6mo","ytd"], index=0)

    if not ticker:
        st.markdown("""
        <div style='text-align:center;padding:3rem;color:#374151;font-family:Space Mono,monospace;font-size:0.75rem;'>
            ENTER A TICKER SYMBOL TO BEGIN ANALYSIS
        </div>
        """, unsafe_allow_html=True)
        return

    with st.spinner(f"Loading {ticker}…"):
        df   = get_history(ticker, period=period)
        q    = get_quote(ticker)

    if df.empty or not q or q.get("error"):
        st.error(f"Could not load data for {ticker}. Check the symbol and try again.")
        return

    # ── Header ────────────────────────────────────────────────────
    pct   = q.get("change_pct", 0)
    pc    = "#00d4aa" if pct >= 0 else "#ef4444"
    mcap  = q.get("market_cap")
    mcap_s = f"${mcap/1e9:.1f}B" if mcap and mcap >= 1e9 else (f"${mcap/1e6:.0f}M" if mcap else "—")

    st.markdown(f"""
    <div style='background:#111827;border:1px solid #1f2937;border-radius:8px;padding:1.5rem;margin-bottom:1.5rem;'>
        <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;'>
            <div>
                <span style='font-family:Space Mono,monospace;font-size:1.4rem;font-weight:700;color:#e5e7eb;'>{ticker}</span>
                <span style='font-family:IBM Plex Sans,sans-serif;font-size:0.9rem;color:#6b7280;margin-left:0.75rem;'>{q.get("name","")}</span><br/>
                <span style='font-family:Space Mono,monospace;font-size:0.7rem;color:#9ca3af;'>{q.get("sector","")} · {q.get("industry","")}</span>
            </div>
            <div style='text-align:right;'>
                <div style='font-family:Space Mono,monospace;font-size:1.8rem;color:#e5e7eb;'>${q.get("price",0):,.2f}</div>
                <div style='font-family:Space Mono,monospace;font-size:1rem;color:{pc};'>{pct:+.2f}%  today</div>
                <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#6b7280;'>Mkt Cap: {mcap_s}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Key metrics row ───────────────────────────────────────────
    metrics = [
        ("P/E", q.get("pe_ratio"), None),
        ("Fwd P/E", q.get("forward_pe"), None),
        ("P/B", q.get("pb_ratio"), None),
        ("P/S", q.get("ps_ratio"), None),
        ("EV/EBITDA", q.get("ev_ebitda"), None),
        ("D/E", q.get("debt_equity"), None),
        ("ROE", q.get("roe"), "pct"),
        ("Gross Margin", q.get("gross_margin"), "pct"),
        ("Rev Growth", q.get("revenue_growth"), "pct"),
        ("Beta", q.get("beta"), None),
    ]
    cols = st.columns(len(metrics))
    for col, (label, val, fmt) in zip(cols, metrics):
        with col:
            if fmt == "pct" and val is not None:
                display = f"{val*100:.1f}%"
            elif isinstance(val, float):
                display = f"{val:.2f}"
            else:
                display = str(val) if val else "—"
            st.metric(label, display)

    # ── Analyst target ────────────────────────────────────────────
    tgt = q.get("analyst_target")
    price = q.get("price", 0)
    if tgt and price:
        upside = (tgt - price) / price * 100
        up_color = "#00d4aa" if upside > 0 else "#ef4444"
        rec = q.get("recommendation")
        rec_map = {1:"Strong Buy",2:"Buy",3:"Hold",4:"Underperform",5:"Sell"}
        rec_str = rec_map.get(round(rec), "—") if rec else "—"
        st.markdown(f"""
        <div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:0.75rem 1rem;margin:1rem 0;display:flex;gap:2rem;'>
            <div>
                <span style='font-family:Space Mono,monospace;font-size:0.6rem;color:#6b7280;text-transform:uppercase;'>Analyst Consensus Target</span><br/>
                <span style='font-family:Space Mono,monospace;font-size:1rem;color:#e5e7eb;'>${tgt:,.2f}</span>
                <span style='font-family:Space Mono,monospace;font-size:0.8rem;color:{up_color};margin-left:0.5rem;'>{upside:+.1f}% upside</span>
            </div>
            <div>
                <span style='font-family:Space Mono,monospace;font-size:0.6rem;color:#6b7280;text-transform:uppercase;'>Recommendation</span><br/>
                <span style='font-family:Space Mono,monospace;font-size:1rem;color:#e5e7eb;'>{rec_str}</span>
            </div>
            <div>
                <span style='font-family:Space Mono,monospace;font-size:0.6rem;color:#6b7280;text-transform:uppercase;'>52W Range</span><br/>
                <span style='font-family:Space Mono,monospace;font-size:0.9rem;color:#9ca3af;'>${q.get("52w_low",0):,.2f} — ${q.get("52w_high",0):,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Main chart: candlestick + volume + RSI ────────────────────
    st.markdown("#### Price Chart + Technical Indicators")

    df_feat = add_features(df)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20],
        vertical_spacing=0.03,
        subplot_titles=["", "Volume", "RSI (14)"],
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#00d4aa", decreasing_line_color="#ef4444",
        name=ticker,
    ), row=1, col=1)

    # MAs
    for window, color, dash in [(20, "#f59e0b", "dot"), (50, "#a78bfa", "dot"), (200, "#60a5fa", "dash")]:
        ma = df["Close"].rolling(window).mean()
        fig.add_trace(go.Scatter(x=df.index, y=ma, name=f"SMA{window}",
                                  line=dict(color=color, width=1, dash=dash)), row=1, col=1)

    # Bollinger Bands
    if "bb_upper" in df_feat.columns:
        fig.add_trace(go.Scatter(x=df_feat.index, y=df_feat["bb_upper"], name="BB Upper",
                                  line=dict(color="#374151", width=1, dash="dash")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_feat.index, y=df_feat["bb_lower"], name="BB Lower",
                                  line=dict(color="#374151", width=1, dash="dash"),
                                  fill="tonexty", fillcolor="rgba(55,65,81,0.1)"), row=1, col=1)

    # Volume bars
    vol_colors = ["#00d4aa" if c >= o else "#ef4444"
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
                          marker_color=vol_colors, showlegend=False), row=2, col=1)

    # RSI
    if "rsi" in df_feat.columns:
        fig.add_trace(go.Scatter(x=df_feat.index, y=df_feat["rsi"], name="RSI",
                                  line=dict(color="#a78bfa", width=1.5)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00d4aa", line_width=1, row=3, col=1)

    fig.update_layout(
        **CHART_THEME,
        height=580, margin=dict(l=0,r=0,t=30,b=0),
        xaxis_rangeslider_visible=False,
        legend=dict(bgcolor="#111827", bordercolor="#1f2937", borderwidth=1,
                    font=dict(size=8, family="Space Mono, monospace"), orientation="h",
                    yanchor="bottom", y=1.01),
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="#1f2937", row=i, col=1)
        fig.update_yaxes(gridcolor="#1f2937", row=i, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # ── MACD ──────────────────────────────────────────────────────
    if "macd" in df_feat.columns:
        st.markdown("#### MACD")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df_feat.index, y=df_feat["macd"], name="MACD",
                                       line=dict(color="#00d4aa", width=1.5)))
        fig_macd.add_trace(go.Scatter(x=df_feat.index, y=df_feat["macd_signal"], name="Signal",
                                       line=dict(color="#f59e0b", width=1.5, dash="dot")))
        hist_colors = ["#00d4aa" if v >= 0 else "#ef4444" for v in df_feat["macd_hist"]]
        fig_macd.add_trace(go.Bar(x=df_feat.index, y=df_feat["macd_hist"], name="Histogram",
                                   marker_color=hist_colors))
        fig_macd.update_layout(
            **CHART_THEME,
            height=200, margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            legend=dict(bgcolor="#111827", bordercolor="#1f2937", borderwidth=1,
                        font=dict(size=9, family="Space Mono, monospace")),
        )
        st.plotly_chart(fig_macd, use_container_width=True)

    # ── Comparison ────────────────────────────────────────────────
    if compare_tickers:
        st.markdown("---")
        st.markdown(f"#### {ticker} vs {', '.join(compare_tickers)} — Normalized Performance")
        fig_cmp = go.Figure()
        palette = ["#00d4aa","#f59e0b","#a78bfa","#60a5fa","#f87171"]
        all_tickers = [ticker] + compare_tickers
        import yfinance as yf
        for tick, color in zip(all_tickers, palette):
            hist = yf.Ticker(tick).history(period=period)
            if not hist.empty:
                base = hist["Close"].iloc[0]
                fig_cmp.add_trace(go.Scatter(
                    x=hist.index, y=(hist["Close"]/base-1)*100,
                    name=tick, line=dict(color=color, width=1.5),
                ))
        fig_cmp.update_layout(
            **CHART_THEME,
            height=280, margin=dict(l=0,r=0,t=10,b=0),
            yaxis_title="Return %",
            xaxis=dict(gridcolor="#1f2937"), yaxis=dict(gridcolor="#1f2937"),
            legend=dict(bgcolor="#111827", bordercolor="#1f2937", borderwidth=1,
                        font=dict(size=9, family="Space Mono, monospace")),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

    # ── Company summary ───────────────────────────────────────────
    summary = q.get("summary", "")
    if summary:
        st.markdown("---")
        st.markdown("#### About")
        st.markdown(f"""
        <div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:1rem;font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;color:#9ca3af;line-height:1.6;'>
            {summary[:800]}{"…" if len(summary)>800 else ""}
        </div>
        """, unsafe_allow_html=True)
