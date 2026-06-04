"""pages/ai_picks.py — AI-Powered Investment Suggestions"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import get_quote, get_history, THEMATIC_STOCKS
from models.ml import predict_direction, get_technical_signals


AI_WATCHLIST = {
    "High Conviction": {
        "tickers": ["CEG","NNE","NVDA","PLTR","LLY"],
        "rationale": "Combines nuclear renaissance, AI infrastructure dominance, defense tech, and GLP-1 wave — three independent multi-year secular growth themes.",
        "time_horizon": "12–24 months",
        "risk": "Medium",
    },
    "Deep Value": {
        "tickers": ["INTC","CSCO","STX","HPQ","CIVI"],
        "rationale": "Beaten-down tech and energy names trading at or below tangible book value with potential catalyst for re-rating.",
        "time_horizon": "6–18 months",
        "risk": "Medium-High",
    },
    "Aggressive Growth": {
        "tickers": ["IONQ","SMR","OKLO","RXRX","ACHR"],
        "rationale": "Early-stage technology in quantum computing, nuclear SMRs, and biotech platforms. High risk, asymmetric upside.",
        "time_horizon": "24–48 months",
        "risk": "High",
    },
    "Income + Safety": {
        "tickers": ["NEE","AWK","ETN","MSEX","WM"],
        "rationale": "Defensive positions with reliable dividends: water utilities, clean energy infrastructure, and waste management.",
        "time_horizon": "Long-term hold",
        "risk": "Low-Medium",
    },
}

RISK_COLORS = {
    "Low-Medium": "#00d4aa",
    "Medium": "#f59e0b",
    "Medium-High": "#fb923c",
    "High": "#ef4444",
}

CHART_THEME = dict(
    paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
    font=dict(color="#9ca3af", family="Space Mono, monospace", size=10),
    gridcolor="#1f2937",
)


def render():
    st.markdown("## AI Picks")
    st.markdown("<div class='terminal-header'>ML PREDICTIONS + CURATED INVESTMENT THESES</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🤖  ML Prediction Engine", "💡  Curated AI Portfolios"])

    # ── Tab 1: ML Prediction Engine ───────────────────────────────
    with tab1:
        st.markdown("### Run ML Prediction on Any Stock")
        st.markdown("""
        <div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:0.75rem 1rem;margin-bottom:1rem;font-family:IBM Plex Sans,sans-serif;font-size:0.8rem;color:#9ca3af;'>
        <strong style='color:#e5e7eb;'>Model:</strong> Random Forest (200 trees, 18 technical features) trained on historical OHLCV data.
        Predicts 5-day directional movement with probability scores. <strong style='color:#f59e0b;'>Not financial advice.</strong>
        Uses RSI, MACD, Bollinger Bands, volume ratios, moving average cross-signals, and price momentum.
        </div>
        """, unsafe_allow_html=True)

        col_input, col_period = st.columns([3, 1])
        with col_input:
            ticker_input = st.text_input("Ticker Symbol", placeholder="e.g. NVDA, AAPL, CEG").upper().strip()
        with col_period:
            period = st.selectbox("Training Data", ["2y", "5y", "1y"], index=0)

        run_btn = st.button("▶  Run ML Prediction", use_container_width=False)

        if run_btn and ticker_input:
            with st.spinner(f"Training model on {ticker_input}…"):
                df = get_history(ticker_input, period=period)
                if df.empty:
                    st.error(f"No data found for {ticker_input}")
                else:
                    result = predict_direction(ticker_input, df)
                    signals = get_technical_signals(df)
                    quote = get_quote(ticker_input)

                    if "error" in result:
                        st.warning(result["error"])
                    else:
                        _render_prediction(ticker_input, result, signals, quote, df)

        st.markdown("---")
        st.markdown("### Batch Scan — AI Scores for Watchlist")

        if st.button("▶  Scan High-Conviction Watchlist"):
            tickers = AI_WATCHLIST["High Conviction"]["tickers"] + AI_WATCHLIST["Deep Value"]["tickers"]
            results = []
            prog = st.progress(0)
            for i, tick in enumerate(tickers):
                prog.progress((i+1)/len(tickers), text=f"Scanning {tick}…")
                df = get_history(tick, "2y")
                if not df.empty:
                    res = predict_direction(tick, df)
                    q = get_quote(tick)
                    if "error" not in res:
                        results.append({
                            "Ticker": tick,
                            "Price": round(q.get("price", 0), 2),
                            "Signal": res["prediction"],
                            "Bull%": res["bull_prob"],
                            "Conf%": res["confidence"],
                            "Model Acc%": res.get("model_accuracy"),
                            "RSI": res.get("last_rsi"),
                            "Vol Ratio": res.get("vol_ratio"),
                        })
            prog.empty()

            if results:
                df_r = pd.DataFrame(results)

                def style_signal(val):
                    return "color:#00d4aa;font-weight:bold" if val == "BULLISH" else "color:#ef4444;font-weight:bold"

                def style_bull(val):
                    if isinstance(val, float):
                        if val >= 65: return "color:#00d4aa"
                        if val <= 35: return "color:#ef4444"
                    return "color:#f59e0b"

                styled = df_r.style\
                    .applymap(style_signal, subset=["Signal"])\
                    .applymap(style_bull, subset=["Bull%"])\
                    .format({
                        "Price": "${:.2f}",
                        "Bull%": "{:.1f}%",
                        "Conf%": "{:.1f}%",
                        "Model Acc%": lambda x: f"{x:.1f}%" if x else "—",
                        "RSI": lambda x: f"{x:.1f}" if x else "—",
                        "Vol Ratio": lambda x: f"{x:.2f}x" if x else "—",
                    })\
                    .set_properties(**{
                        "background-color": "#111827", "color": "#e5e7eb",
                        "border": "1px solid #1f2937",
                        "font-family": "Space Mono, monospace", "font-size": "11px",
                    })
                st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Tab 2: Curated AI Portfolios ──────────────────────────────
    with tab2:
        st.markdown("### Curated AI-Analyzed Portfolios")
        st.markdown("""
        <div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:0.75rem 1rem;margin-bottom:1.5rem;font-family:IBM Plex Sans,sans-serif;font-size:0.8rem;color:#9ca3af;'>
        Portfolios are built from multi-factor analysis: current world events, sector momentum, valuations, and technical signals.
        Updated weekly. Each portfolio has a distinct risk/reward profile.
        </div>
        """, unsafe_allow_html=True)

        for portfolio_name, portfolio_data in AI_WATCHLIST.items():
            risk = portfolio_data["risk"]
            risk_color = RISK_COLORS.get(risk, "#6b7280")

            with st.expander(f"📂  {portfolio_name}  ·  Risk: {risk}  ·  Horizon: {portfolio_data['time_horizon']}", expanded=(portfolio_name=="High Conviction")):
                st.markdown(f"""
                <div style='border-left:3px solid {risk_color};padding-left:1rem;margin-bottom:1rem;'>
                    <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:{risk_color};text-transform:uppercase;letter-spacing:0.1em;'>Investment Thesis</div>
                    <div style='font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;color:#d1d5db;margin-top:0.3rem;'>{portfolio_data["rationale"]}</div>
                </div>
                """, unsafe_allow_html=True)

                tickers = portfolio_data["tickers"]
                cols = st.columns(len(tickers))
                for col, tick in zip(cols, tickers):
                    with col:
                        q = get_quote(tick)
                        if q and not q.get("error"):
                            pct = q.get("change_pct", 0)
                            pc = "#00d4aa" if pct >= 0 else "#ef4444"
                            tgt = q.get("analyst_target")
                            upside = f"+{(tgt-q.get('price',0))/q.get('price',1)*100:.0f}%" if tgt and q.get("price") and tgt > q.get("price") else ""
                            st.markdown(f"""
                            <div class='metric-card' style='text-align:center;'>
                                <div style='font-family:Space Mono,monospace;font-size:0.95rem;font-weight:700;color:#e5e7eb;'>{tick}</div>
                                <div style='font-family:Space Mono,monospace;font-size:1rem;color:#e5e7eb;margin:4px 0;'>${q.get("price",0):,.2f}</div>
                                <div style='font-family:Space Mono,monospace;font-size:0.8rem;color:{pc};'>{pct:+.2f}%</div>
                                {f'<div style="font-family:Space Mono,monospace;font-size:0.65rem;color:#00d4aa;margin-top:3px;">Analyst upside {upside}</div>' if upside else ''}
                            </div>
                            """, unsafe_allow_html=True)

                # Performance chart
                st.markdown("<br/>", unsafe_allow_html=True)
                fig = go.Figure()
                palette = ["#00d4aa","#f59e0b","#a78bfa","#60a5fa","#f87171"]
                import yfinance as yf
                for tick, color in zip(tickers, palette):
                    hist = yf.Ticker(tick).history(period="6mo")
                    if not hist.empty:
                        base = hist["Close"].iloc[0]
                        fig.add_trace(go.Scatter(
                            x=hist.index, y=(hist["Close"]/base-1)*100,
                            name=tick, line=dict(color=color, width=1.5),
                        ))
                fig.update_layout(
                    **CHART_THEME,
                    height=250, margin=dict(l=0,r=0,t=10,b=0),
                    yaxis_title="Return %", yaxis=dict(gridcolor="#1f2937"),
                    xaxis=dict(gridcolor="#1f2937"),
                    legend=dict(bgcolor="#111827", bordercolor="#1f2937", borderwidth=1,
                                font=dict(size=9, family="Space Mono, monospace")),
                )
                st.plotly_chart(fig, use_container_width=True)


def _render_prediction(ticker, result, signals, quote, df):
    pred = result["prediction"]
    conf = result["confidence"]
    bull = result["bull_prob"]
    pred_color = "#00d4aa" if pred == "BULLISH" else "#ef4444"

    # Header
    q_price = quote.get("price", 0)
    q_pct   = quote.get("change_pct", 0)
    q_name  = quote.get("name", ticker)

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;'>5-Day Direction Prediction</div>
            <div style='font-family:DM Serif Display,serif;font-size:2.5rem;color:{pred_color};margin:0.3rem 0;'>{pred}</div>
            <div style='font-family:Space Mono,monospace;font-size:0.85rem;color:#9ca3af;'>
                {bull:.1f}% bull probability &nbsp;·&nbsp; {conf:.1f}% confidence<br/>
                {f"Model accuracy on test set: {result['model_accuracy']}%" if result.get('model_accuracy') else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.metric("Current Price", f"${q_price:,.2f}", delta=f"{q_pct:+.2f}%")
        st.metric("RSI (14)", f"{result.get('last_rsi','—')}")

    with c3:
        st.metric("BB Position", f"{result.get('bb_pos','—'):.2f}" if result.get('bb_pos') else "—")
        st.metric("Volume Ratio", f"{result.get('vol_ratio','—'):.2f}x" if result.get('vol_ratio') else "—")

    # Bull/Bear bar
    st.markdown(f"""
    <div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:0.8rem 1rem;margin:1rem 0;'>
        <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#6b7280;margin-bottom:0.5rem;'>BULL / BEAR PROBABILITY</div>
        <div style='display:flex;align-items:center;gap:0.5rem;'>
            <span style='font-family:Space Mono,monospace;font-size:0.75rem;color:#00d4aa;width:40px;'>{bull:.0f}%</span>
            <div style='flex:1;background:#1f2937;border-radius:4px;height:12px;overflow:hidden;'>
                <div style='width:{bull}%;background:linear-gradient(90deg,#00d4aa,#059669);height:100%;border-radius:4px;'></div>
            </div>
            <div style='flex:1;background:#1f2937;border-radius:4px;height:12px;overflow:hidden;'>
                <div style='width:{100-bull}%;background:linear-gradient(90deg,#ef4444,#b91c1c);height:100%;border-radius:4px;float:right;'></div>
            </div>
            <span style='font-family:Space Mono,monospace;font-size:0.75rem;color:#ef4444;width:40px;text-align:right;'>{100-bull:.0f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Technical signals
    if signals:
        st.markdown("**Technical Signals**")
        sig_cols = st.columns(len(signals))
        sig_color_map = {"green": "#00d4aa", "red": "#ef4444", "neutral": "#6b7280"}
        for col, (name, (val, color)) in zip(sig_cols, signals.items()):
            with col:
                c = sig_color_map.get(color, "#9ca3af")
                st.markdown(f"""
                <div class='metric-card' style='text-align:center;padding:0.6rem;'>
                    <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#6b7280;text-transform:uppercase;'>{name}</div>
                    <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:{c};margin-top:4px;'>{val}</div>
                </div>
                """, unsafe_allow_html=True)

    # Feature importances
    top_feats = result.get("top_features", [])
    if top_feats:
        st.markdown("**Top Predictive Features**")
        fig = go.Figure(go.Bar(
            x=[v*100 for _, v in top_feats],
            y=[k for k, _ in top_feats],
            orientation="h",
            marker_color="#a78bfa",
        ))
        fig.update_layout(
            paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
            font=dict(color="#9ca3af", family="Space Mono, monospace", size=9),
            height=180, margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(gridcolor="#1f2937", title="Importance (%)"),
            yaxis=dict(gridcolor="#1f2937"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Price chart with MAs
    st.markdown("**Price Chart (6M) with Moving Averages**")
    hist_6m = df.last("180D")
    fig2 = go.Figure()
    fig2.add_trace(go.Candlestick(
        x=hist_6m.index, open=hist_6m["Open"], high=hist_6m["High"],
        low=hist_6m["Low"], close=hist_6m["Close"],
        increasing_line_color="#00d4aa", decreasing_line_color="#ef4444",
        name="Price",
    ))
    for window, color in [(20, "#f59e0b"), (50, "#a78bfa")]:
        ma = hist_6m["Close"].rolling(window).mean()
        fig2.add_trace(go.Scatter(x=hist_6m.index, y=ma, name=f"SMA{window}",
                                  line=dict(color=color, width=1, dash="dot")))
    fig2.update_layout(
        paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
        font=dict(color="#9ca3af", family="Space Mono, monospace", size=9),
        height=320, margin=dict(l=0,r=0,t=10,b=0),
        xaxis=dict(gridcolor="#1f2937", rangeslider_visible=False),
        yaxis=dict(gridcolor="#1f2937"),
        legend=dict(bgcolor="#111827", bordercolor="#1f2937", borderwidth=1,
                    font=dict(size=9, family="Space Mono, monospace")),
        xaxis_rangeslider_visible=False,
    )
    st.plotly_chart(fig2, use_container_width=True)
