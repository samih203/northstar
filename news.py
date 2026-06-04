"""pages/news.py — News Intelligence with Sentiment Analysis"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import get_news, simple_sentiment


SENTIMENT_ICONS = {
    "positive": ("▲", "#00d4aa"),
    "negative": ("▼", "#ef4444"),
    "neutral":  ("◆", "#6b7280"),
}

WORLD_THEMES = {
    "AI & Tech Regulation": {
        "feeds": ["nvidia", "AI regulation", "semiconductor"],
        "thesis": "Regulatory clarity on AI could re-rate software/chip stocks. Watch EU AI Act compliance costs vs US permissiveness.",
        "related_tickers": ["NVDA","MSFT","GOOGL","META","AMD"],
        "sentiment_bias": "bullish",
    },
    "Energy Transition": {
        "feeds": ["nuclear energy", "clean energy", "solar wind"],
        "thesis": "IRA incentives + AI power demand driving nuclear and grid renaissance. Utilities undervalued vs growth trajectory.",
        "related_tickers": ["CEG","VST","FSLR","NEE","ENPH"],
        "sentiment_bias": "bullish",
    },
    "Geopolitical Risk": {
        "feeds": ["trade war tariffs", "China Taiwan", "defense spending"],
        "thesis": "Elevated geopolitical tension structurally benefits defense, domestic manufacturing, and commodity producers.",
        "related_tickers": ["LMT","RTX","NOC","KTOS","MP"],
        "sentiment_bias": "neutral",
    },
    "Healthcare & GLP-1": {
        "feeds": ["GLP-1 obesity drug", "weight loss pharmaceutical", "biotech FDA"],
        "thesis": "Obesity drug revolution restructuring healthcare economics. Winners: pharma, medtech. Losers: food & bariatric.",
        "related_tickers": ["LLY","NVO","HIMS","VKTX","DXCM"],
        "sentiment_bias": "bullish",
    },
    "Macro / Fed Policy": {
        "feeds": ["Federal Reserve interest rates", "inflation CPI", "recession"],
        "thesis": "Rate path uncertainty drives volatility. Rate cuts benefit rate-sensitive sectors (REIT, biotech, small-caps).",
        "related_tickers": ["TLT","GLD","IWM","XLRE","KRE"],
        "sentiment_bias": "neutral",
    },
}


def render():
    st.markdown("## News Intelligence")
    st.markdown("<div class='terminal-header'>SENTIMENT-TAGGED MARKET NEWS — RSS AGGREGATION</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📰  Live Feed", "🌍  World Events → Trades"])

    # ── Tab 1: Live Feed ──────────────────────────────────────────
    with tab1:
        col_filter, col_refresh = st.columns([4, 1])
        with col_filter:
            sentiment_filter = st.radio("Filter:", ["All", "Positive", "Negative", "Neutral"], horizontal=True)
        with col_refresh:
            st.markdown("<br/>", unsafe_allow_html=True)
            if st.button("↺  Refresh"):
                st.cache_data.clear()
                st.rerun()

        with st.spinner("Loading news…"):
            articles = get_news(count=30)

        # Tag sentiment
        for a in articles:
            a["sentiment"] = simple_sentiment(a["title"] + " " + a.get("summary", ""))

        # Filter
        filtered = articles
        if sentiment_filter == "Positive":
            filtered = [a for a in articles if a["sentiment"] == "positive"]
        elif sentiment_filter == "Negative":
            filtered = [a for a in articles if a["sentiment"] == "negative"]
        elif sentiment_filter == "Neutral":
            filtered = [a for a in articles if a["sentiment"] == "neutral"]

        # Sentiment summary
        pos = sum(1 for a in articles if a["sentiment"] == "positive")
        neg = sum(1 for a in articles if a["sentiment"] == "negative")
        neu = sum(1 for a in articles if a["sentiment"] == "neutral")
        total = len(articles)

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Articles", total)
        with c2: st.metric("🟢 Positive", pos, delta=f"{pos/total*100:.0f}%" if total else "")
        with c3: st.metric("🔴 Negative", neg, delta=f"-{neg/total*100:.0f}%" if total else "")
        with c4:
            overall = "RISK-ON 📈" if pos > neg * 1.3 else ("RISK-OFF 📉" if neg > pos * 1.3 else "MIXED ◆")
            st.metric("Market Tone", overall)

        # Sentiment donut
        fig = go.Figure(go.Pie(
            labels=["Positive", "Negative", "Neutral"],
            values=[pos, neg, neu],
            hole=0.6,
            marker_colors=["#00d4aa", "#ef4444", "#374151"],
            textinfo="label+percent",
            textfont=dict(family="Space Mono, monospace", size=9),
        ))
        fig.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#9ca3af"),
            height=200,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            annotations=[dict(text=overall.split()[0], x=0.5, y=0.5, font_size=11,
                              font_family="Space Mono, monospace", showarrow=False,
                              font_color="#e5e7eb")]
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Article cards
        for article in filtered[:20]:
            sent = article["sentiment"]
            icon, color = SENTIMENT_ICONS[sent]
            pub = article.get("published", "")[:20]
            source = article.get("source", "")

            css_class = f"news-card {'negative' if sent=='negative' else 'neutral' if sent=='neutral' else ''}"

            st.markdown(f"""
            <div class='{css_class}'>
                <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                    <div style='flex:1;'>
                        <a href='{article.get("link","#")}' target='_blank'
                           style='font-family:DM Serif Display,serif;font-size:1rem;color:#e5e7eb;text-decoration:none;'>
                           {article["title"]}
                        </a>
                        <div style='font-family:IBM Plex Sans,sans-serif;font-size:0.75rem;color:#9ca3af;margin-top:0.3rem;'>
                            {article.get("summary","")[:160]}…
                        </div>
                    </div>
                    <span style='font-family:Space Mono,monospace;font-size:0.8rem;color:{color};margin-left:1rem;white-space:nowrap;'>{icon} {sent.upper()}</span>
                </div>
                <div style='font-family:Space Mono,monospace;font-size:0.6rem;color:#374151;margin-top:0.4rem;'>
                    {source} &nbsp;·&nbsp; {pub}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 2: World Events → Trades ─────────────────────────────
    with tab2:
        st.markdown("### Global Events → Investment Implications")
        st.markdown("""
        <div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:0.75rem 1rem;margin-bottom:1.5rem;font-family:Space Mono,monospace;font-size:0.65rem;color:#6b7280;letter-spacing:0.1em;'>
        FRAMEWORK: Identify macro/geopolitical theme → map to affected sectors → find best-positioned equities
        </div>
        """, unsafe_allow_html=True)

        selected_theme = st.selectbox("Select World Event Theme:", list(WORLD_THEMES.keys()))
        theme_data = WORLD_THEMES[selected_theme]

        bias = theme_data["sentiment_bias"]
        bias_color = "#00d4aa" if bias == "bullish" else "#ef4444" if bias == "bearish" else "#f59e0b"

        st.markdown(f"""
        <div style='background:#111827;border:1px solid #1f2937;border-left:3px solid {bias_color};border-radius:6px;padding:1.25rem;margin-bottom:1.5rem;'>
            <div style='font-family:Space Mono,monospace;font-size:0.65rem;color:{bias_color};text-transform:uppercase;letter-spacing:0.1em;'>
                {bias.upper()} BIAS — INVESTMENT THESIS
            </div>
            <div style='font-family:IBM Plex Sans,sans-serif;font-size:0.9rem;color:#d1d5db;margin-top:0.5rem;'>
                {theme_data["thesis"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Related tickers
        st.markdown("**Equity Plays to Watch**")
        from utils.data import get_quote
        tickers = theme_data["related_tickers"]
        cols = st.columns(len(tickers))
        for col, tick in zip(cols, tickers):
            with col:
                q = get_quote(tick)
                if q and not q.get("error"):
                    pct = q.get("change_pct", 0)
                    pcolor = "#00d4aa" if pct >= 0 else "#ef4444"
                    st.markdown(f"""
                    <div class='metric-card' style='text-align:center;padding:0.8rem;'>
                        <div style='font-family:Space Mono,monospace;font-size:0.9rem;font-weight:700;color:#e5e7eb;'>{tick}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.85rem;color:#d1d5db;'>${q.get("price",0):,.2f}</div>
                        <div style='font-family:Space Mono,monospace;font-size:0.75rem;color:{pcolor};'>{pct:+.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Narrative playbook
        playbooks = {
            "AI & Tech Regulation": [
                ("Short-term catalyst", "EU AI Act enforcement creates compliance moat for US hyperscalers and established players."),
                ("Mid-term trade", "Infrastructure buildout continues regardless of regulation — NVDA, AMD, data center REITs (EQIX, DLR)."),
                ("Risk to thesis", "Severe US export controls on chips to China could hurt semiconductor revenue significantly."),
            ],
            "Energy Transition": [
                ("Short-term catalyst", "AI data center power demand is forcing utilities to restart nuclear and sign long-term PPAs."),
                ("Mid-term trade", "Grid modernization plays (Eaton, Quanta Services) are structural beneficiaries regardless of politics."),
                ("Risk to thesis", "Policy reversal on IRA credits could weigh on solar/wind but won't stop nuclear momentum."),
            ],
            "Geopolitical Risk": [
                ("Short-term catalyst", "Defense budget hikes across NATO members create a multi-year revenue ramp for primes."),
                ("Mid-term trade", "Domestic rare earth & critical minerals (MP Materials) benefit from supply chain diversification mandates."),
                ("Risk to thesis", "Diplomatic resolution reduces defense premium; commodity price crashes hurt materials plays."),
            ],
            "Healthcare & GLP-1": [
                ("Short-term catalyst", "Expanded Medicare/Medicaid GLP-1 coverage could be a +30% revenue catalyst for LLY/NVO."),
                ("Mid-term trade", "Second-generation oral GLP-1s (VKTX, Roche pipeline) are the next leg. Biosimilar entrants in 2026-27."),
                ("Risk to thesis", "Side-effect data or safety signals could cause sharp sector-wide pullback."),
            ],
            "Macro / Fed Policy": [
                ("Short-term catalyst", "Rate cut cycle benefits long-duration assets: small-caps (IWM), REITs (XLRE), and unprofitable growth."),
                ("Mid-term trade", "Steepening yield curve benefits regional banks (KRE) and insurance companies."),
                ("Risk to thesis", "Re-acceleration of inflation prevents cuts and keeps pressure on rate-sensitive names."),
            ],
        }

        playbook = playbooks.get(selected_theme, [])
        for label, desc in playbook:
            label_color = "#00d4aa" if "catalyst" in label.lower() else "#f59e0b" if "trade" in label.lower() else "#ef4444"
            st.markdown(f"""
            <div style='background:#111827;border:1px solid #1f2937;border-radius:6px;padding:0.9rem 1rem;margin-bottom:0.5rem;'>
                <span class='tag' style='background:rgba(0,0,0,0.4);color:{label_color};border:1px solid {label_color}33;'>{label}</span>
                <div style='font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;color:#d1d5db;margin-top:0.5rem;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)
