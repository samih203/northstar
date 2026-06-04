"""pages/scanner.py — Undervalued & Niche Stock Scanner"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import screen_undervalued, get_thematic_performance, THEMATIC_STOCKS, get_quote, get_history

CHART_THEME = dict(
    paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
    font=dict(color="#9ca3af", family="Space Mono, monospace", size=10),
    gridcolor="#1f2937",
)


def score_bar(score: int) -> str:
    filled = int(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    color = "#00d4aa" if score >= 70 else "#f59e0b" if score >= 45 else "#ef4444"
    return f'<span style="font-family:Space Mono,monospace;color:{color};font-size:0.75rem;">{bar} {score}</span>'


def render():
    st.markdown("## Stock Scanner")
    st.markdown("<div class='terminal-header'>VALUE + GROWTH + MOMENTUM COMPOSITE SCORING</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔍  Undervalue Screener", "🎯  Thematic / Niche"])

    # ── Tab 1: Undervalue Screener ────────────────────────────────
    with tab1:
        col_a, col_b, col_c = st.columns([2, 2, 1])
        with col_a:
            min_score = st.slider("Minimum Score", 0, 100, 40, 5)
        with col_b:
            sector_filter = st.selectbox("Filter by Sector",
                ["All", "Technology", "Healthcare", "Energy", "Financials", "Industrials", "Materials"])
        with col_c:
            st.markdown("<br/>", unsafe_allow_html=True)
            run_scan = st.button("▶  Run Screen")

        st.markdown("""
        <div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:1rem;margin-bottom:1rem;'>
        <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#6b7280;letter-spacing:0.1em;text-transform:uppercase;'>Scoring Methodology</div>
        <div style='font-family:IBM Plex Sans,sans-serif;font-size:0.8rem;color:#9ca3af;margin-top:0.4rem;'>
        Score (0–100) = Value (P/E, P/B, P/S weights) + Growth (Revenue, Earnings) + Quality (ROE, Margins) + Discount from 52W High + Analyst Upside
        </div>
        </div>
        """, unsafe_allow_html=True)

        if run_scan or "screener_df" in st.session_state:
            if run_scan:
                with st.spinner("Running screen across universe…"):
                    df = screen_undervalued()
                    st.session_state["screener_df"] = df
            else:
                df = st.session_state["screener_df"]

            # Filters
            df_filtered = df[df["Score"] >= min_score].copy()
            if sector_filter != "All":
                df_filtered = df_filtered[df_filtered["Sector"].str.contains(sector_filter, na=False)]

            st.markdown(f"**{len(df_filtered)} stocks** matched your criteria")

            if not df_filtered.empty:
                # Score distribution chart
                col_chart, col_table = st.columns([1, 2])
                with col_chart:
                    fig = px.histogram(
                        df, x="Score", nbins=20,
                        color_discrete_sequence=["#00d4aa"],
                    )
                    fig.update_layout(
                        **CHART_THEME,
                        height=200, margin=dict(l=0,r=0,t=10,b=0),
                        xaxis_title="Score", yaxis_title="Count",
                        bargap=0.1,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_table:
                    top5 = df_filtered.head(5)
                    fig2 = go.Figure(go.Bar(
                        x=top5["Score"],
                        y=top5["Ticker"],
                        orientation="h",
                        marker_color="#00d4aa",
                        text=top5["Score"],
                        textposition="outside",
                    ))
                    fig2.update_layout(
                        **CHART_THEME,
                        height=200, margin=dict(l=0,r=0,t=10,b=0),
                        xaxis=dict(range=[0,110], gridcolor="#1f2937"),
                        yaxis=dict(gridcolor="#1f2937"),
                        title_text="Top 5 by Score",
                        title_font=dict(size=11, family="Space Mono, monospace"),
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                # Main table
                display_cols = ["Ticker","Name","Price","Score","Signals","P/E","Fwd P/E","P/B","Rev Growth","Sector","Change%"]
                avail = [c for c in display_cols if c in df_filtered.columns]

                def style_score(val):
                    if isinstance(val, (int, float)):
                        if val >= 70: return "background-color:#052e16;color:#00d4aa"
                        if val >= 45: return "background-color:#1c1407;color:#f59e0b"
                        return "background-color:#1c0707;color:#ef4444"
                    return ""

                def style_chg(val):
                    if isinstance(val, (int, float)):
                        return "color:#00d4aa" if val >= 0 else "color:#ef4444"
                    return ""

                styled = df_filtered[avail].head(40).style\
                    .applymap(style_score, subset=["Score"])\
                    .applymap(style_chg, subset=["Change%"])\
                    .format({
                        "Price": "${:.2f}", "Score": "{:.0f}",
                        "P/E": lambda x: f"{x:.1f}" if x == x else "—",
                        "Fwd P/E": lambda x: f"{x:.1f}" if x == x else "—",
                        "P/B": lambda x: f"{x:.2f}" if x == x else "—",
                        "Change%": lambda x: f"{x:+.2f}%" if x == x else "—",
                    })\
                    .set_properties(**{
                        "background-color": "#111827", "color": "#e5e7eb",
                        "border": "1px solid #1f2937",
                        "font-family": "Space Mono, monospace", "font-size": "11px"
                    })
                st.dataframe(styled, use_container_width=True, hide_index=True)

                # Click-through detail
                st.markdown("<br/>", unsafe_allow_html=True)
                selected = st.selectbox("Inspect a stock from the screen:", df_filtered["Ticker"].tolist())
                if selected:
                    q = get_quote(selected)
                    _show_quick_card(selected, q)

    # ── Tab 2: Thematic / Niche ───────────────────────────────────
    with tab2:
        st.markdown("### Rising & Niche Industry Themes")
        theme = st.selectbox("Select Theme", list(THEMATIC_STOCKS.keys()))

        theme_descriptions = {
            "AI Infrastructure": "Companies building the picks-and-shovels of the AI boom — chips, networking, cooling, and data center hardware.",
            "Nuclear Energy": "Nuclear renaissance driven by AI power demand and decarbonization goals. Includes utilities restarting plants and SMR developers.",
            "Biotech Emerging": "Clinical-stage biotech with platform-level science. High risk, high reward — gene therapy, RNA editing, oncology.",
            "Defense Tech": "Next-gen defense: autonomous systems, drone defense, hypersonics, and dual-use tech companies.",
            "Water Tech": "Water scarcity is a global mega-trend. Utilities, infrastructure, and purification technology companies.",
            "Reshoring/Mfg": "Beneficiaries of supply chain deglobalization — US industrial automation, smart manufacturing, and onshoring plays.",
            "GLP-1 / Obesity": "The GLP-1 drug revolution for obesity and metabolic disease. Includes drugmakers and enablers (devices, food reformulation).",
            "Quantum Computing": "Early-stage quantum hardware and software. Long time horizon, but with potential for exponential disruption.",
        }

        st.markdown(f"""
        <div style='background:#111827;border:1px solid #1f2937;border-left:3px solid #f59e0b;border-radius:6px;padding:1rem;margin-bottom:1.5rem;'>
        <span style='font-family:Space Mono,monospace;font-size:0.65rem;color:#f59e0b;text-transform:uppercase;letter-spacing:0.1em;'>THEME THESIS</span>
        <p style='font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;color:#d1d5db;margin:0.4rem 0 0 0;'>{theme_descriptions.get(theme, "")}</p>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner(f"Loading {theme}…"):
            df_theme = get_thematic_performance(theme)

        if not df_theme.empty:
            # Cards
            cols = st.columns(min(len(df_theme), 4))
            for i, (_, row) in enumerate(df_theme.iterrows()):
                with cols[i % len(cols)]:
                    pct = row.get("1D%", 0)
                    color = "#00d4aa" if pct >= 0 else "#ef4444"
                    mcap = row.get("Mkt Cap")
                    mcap_str = f"${mcap/1e9:.1f}B" if mcap and mcap >= 1e9 else (f"${mcap/1e6:.0f}M" if mcap else "—")
                    st.markdown(f"""
                    <div class='metric-card' style='text-align:center;'>
                        <div style='font-family:Space Mono,monospace;font-size:1rem;font-weight:700;color:#e5e7eb;'>{row['Ticker']}</div>
                        <div style='font-family:IBM Plex Sans,sans-serif;font-size:0.7rem;color:#6b7280;margin:2px 0 6px 0;'>{row['Name']}</div>
                        <div style='font-family:Space Mono,monospace;font-size:1.1rem;color:#e5e7eb;'>${row['Price']:,.2f}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.85rem;color:{color};'>{pct:+.2f}%</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:#6b7280;margin-top:4px;'>{mcap_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br/>", unsafe_allow_html=True)

            # Relative performance chart
            tickers = THEMATIC_STOCKS[theme]
            st.markdown(f"#### {theme} — 3-Month Relative Performance")
            fig = go.Figure()
            palette = ["#00d4aa","#f59e0b","#a78bfa","#60a5fa","#f87171","#34d399","#fb923c"]
            for tick, color in zip(tickers[:7], palette):
                import yfinance as yf
                hist = yf.Ticker(tick).history(period="3mo", interval="1d")
                if not hist.empty:
                    base = hist["Close"].iloc[0]
                    norm = (hist["Close"] / base - 1) * 100
                    fig.add_trace(go.Scatter(
                        x=hist.index, y=norm,
                        name=tick, line=dict(color=color, width=1.5),
                    ))
            fig.update_layout(
                **CHART_THEME,
                height=320, margin=dict(l=0,r=0,t=10,b=0),
                yaxis_title="Return %",
                legend=dict(bgcolor="#111827", bordercolor="#1f2937", borderwidth=1,
                            font=dict(size=10, family="Space Mono, monospace")),
                xaxis=dict(gridcolor="#1f2937"),
                yaxis=dict(gridcolor="#1f2937"),
            )
            st.plotly_chart(fig, use_container_width=True)


def _show_quick_card(ticker: str, q: dict):
    if not q or "error" in q:
        st.warning(f"Could not load data for {ticker}")
        return

    st.markdown(f"""
    <div style='background:#111827;border:1px solid #1f2937;border-radius:8px;padding:1.5rem;'>
        <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
            <div>
                <span style='font-family:Space Mono,monospace;font-size:1.2rem;font-weight:700;color:#e5e7eb;'>{ticker}</span>
                <span style='font-family:IBM Plex Sans,sans-serif;font-size:0.8rem;color:#6b7280;margin-left:0.75rem;'>{q.get("name","")}</span><br/>
                <span style='font-family:Space Mono,monospace;font-size:0.7rem;color:#9ca3af;'>{q.get("sector","")}&nbsp;·&nbsp;{q.get("industry","")}</span>
            </div>
            <div style='text-align:right;'>
                <span style='font-family:Space Mono,monospace;font-size:1.4rem;color:#e5e7eb;'>${q.get("price",0):,.2f}</span><br/>
                <span style='font-family:Space Mono,monospace;font-size:0.9rem;color:{"#00d4aa" if q.get("change_pct",0)>=0 else "#ef4444"};'>{q.get("change_pct",0):+.2f}%</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    metrics = [
        ("P/E", q.get("pe_ratio")),
        ("Fwd P/E", q.get("forward_pe")),
        ("P/B", q.get("pb_ratio")),
        ("ROE", f'{q.get("roe",0)*100:.1f}%' if q.get("roe") else None),
        ("Beta", q.get("beta")),
    ]
    for col, (label, val) in zip(cols, metrics):
        with col:
            st.metric(label, f"{val:.2f}" if isinstance(val, float) else (val or "—"))
