"""pages/overview.py — Market Overview Dashboard"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import get_index_data, get_sector_performance, get_history, INDEX_TICKERS

CHART_THEME = dict(
    paper_bgcolor="#111827",
    plot_bgcolor="#0a0e1a",
    font=dict(color="#9ca3af", family="Space Mono, monospace", size=11),
    gridcolor="#1f2937",
    xaxis=dict(gridcolor="#1f2937", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1f2937", showgrid=True, zeroline=False),
)


def render():
    st.markdown("## Market Overview")
    st.markdown("<div class='terminal-header'>LIVE INDICES — AUTO-REFRESH EVERY 5 MIN</div>", unsafe_allow_html=True)

    col_refresh, _ = st.columns([1, 6])
    with col_refresh:
        if st.button("↺  Refresh"):
            st.cache_data.clear()
            st.rerun()

    # ── Indices row ──────────────────────────────────────────────
    indices = get_index_data()
    if indices:
        cols = st.columns(len(indices))
        for col, (name, data) in zip(cols, indices.items()):
            price = data.get("price")
            pct   = data.get("change_pct", 0)
            delta_str = f"{pct:+.2f}%"
            with col:
                st.metric(
                    label=name,
                    value=f"{price:,.2f}" if price else "—",
                    delta=delta_str,
                )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Index chart ──────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### S&P 500 — 1 Year")
        df = get_history("^GSPC", "1y")
        if not df.empty:
            fig = go.Figure()
            color_line = "#00d4aa" if df["Close"].iloc[-1] >= df["Close"].iloc[0] else "#ef4444"
            fig.add_trace(go.Scatter(
                x=df.index, y=df["Close"],
                mode="lines",
                line=dict(color=color_line, width=1.5),
                fill="tozeroy",
                fillcolor=f"rgba(0,212,170,0.05)" if color_line == "#00d4aa" else "rgba(239,68,68,0.05)",
                name="S&P 500",
            ))
            fig.update_layout(
                **CHART_THEME,
                height=280, margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("#### Sector Performance (1D%)")
        sector_df = get_sector_performance()
        if not sector_df.empty:
            sector_df_sorted = sector_df.sort_values("1D%", ascending=True)
            fig2 = go.Figure(go.Bar(
                x=sector_df_sorted["1D%"],
                y=sector_df_sorted["Sector"],
                orientation="h",
                marker_color=[
                    "#00d4aa" if v >= 0 else "#ef4444"
                    for v in sector_df_sorted["1D%"]
                ],
                text=[f"{v:+.2f}%" for v in sector_df_sorted["1D%"]],
                textposition="outside",
                textfont=dict(size=9, family="Space Mono, monospace"),
            ))
            fig2.update_layout(
                **CHART_THEME,
                height=280, margin=dict(l=0, r=10, t=10, b=0),
                xaxis_title="", yaxis_title="",
                bargap=0.35,
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ── Sector table ─────────────────────────────────────────────
    st.markdown("#### Sector ETF Dashboard")
    sector_df = get_sector_performance()
    if not sector_df.empty:
        def color_val(val):
            if isinstance(val, float):
                if val > 0: return "color: #00d4aa"
                if val < 0: return "color: #ef4444"
            return "color: #9ca3af"

        styled = sector_df.style\
            .applymap(color_val, subset=["1D%","5D%"])\
            .format({"Price": "${:.2f}", "1D%": "{:+.2f}%", "5D%": "{:+.2f}%"})\
            .set_properties(**{"background-color": "#111827", "color": "#e5e7eb",
                               "border": "1px solid #1f2937", "font-family": "Space Mono, monospace", "font-size": "11px"})
        st.dataframe(styled, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Multi-index comparison ────────────────────────────────────
    st.markdown("#### Index Comparison — YTD Performance (%)")
    comparison_tickers = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "Russell 2000": "^RUT"}
    fig3 = go.Figure()
    colors = ["#00d4aa","#f59e0b","#a78bfa"]
    for (name, tick), color in zip(comparison_tickers.items(), colors):
        df = get_history(tick, "ytd")
        if not df.empty:
            base = df["Close"].iloc[0]
            norm = (df["Close"] / base - 1) * 100
            fig3.add_trace(go.Scatter(
                x=df.index, y=norm,
                name=name,
                line=dict(color=color, width=1.5),
                mode="lines",
            ))
    fig3.update_layout(
        **CHART_THEME,
        height=300, margin=dict(l=0, r=0, t=10, b=0),
        yaxis_title="Return %",
        legend=dict(
            bgcolor="#111827", bordercolor="#1f2937", borderwidth=1,
            font=dict(size=10, family="Space Mono, monospace"),
        )
    )
    st.plotly_chart(fig3, use_container_width=True)
