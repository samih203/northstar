import streamlit as st

st.set_page_config(
    page_title="Northstar — Market Intelligence",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #0a0e1a;
    --surface: #111827;
    --border: #1f2937;
    --accent: #00d4aa;
    --accent2: #f59e0b;
    --accent3: #ef4444;
    --text: #e5e7eb;
    --muted: #6b7280;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Sans', sans-serif;
}

[data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

h1, h2, h3 {
    font-family: 'DM Serif Display', serif !important;
    color: var(--text) !important;
}

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    margin-bottom: 0.75rem;
}

.tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.tag-green { background: rgba(0,212,170,0.15); color: #00d4aa; border: 1px solid rgba(0,212,170,0.3); }
.tag-amber { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.tag-red   { background: rgba(239,68,68,0.15);  color: #ef4444;  border: 1px solid rgba(239,68,68,0.3); }

.stMetric { background: var(--surface); padding: 1rem; border-radius: 8px; border: 1px solid var(--border); }
.stMetric label { color: var(--muted) !important; font-family: 'Space Mono', monospace !important; font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
.stMetric [data-testid="stMetricValue"] { font-family: 'Space Mono', monospace !important; color: var(--accent) !important; }

div[data-testid="stHorizontalBlock"] > div { gap: 1rem; }

.stButton > button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(0,212,170,0.1) !important;
}

.stSelectbox > div, .stTextInput > div { background: var(--surface) !important; }

.news-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
}

.news-card.negative { border-left-color: var(--accent3); }
.news-card.neutral  { border-left-color: var(--muted); }

.stock-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 0.5rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
}

.terminal-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

[data-testid="stPlotlyChart"] { border-radius: 8px; overflow: hidden; }

.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-bottom: 1px solid var(--border);
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}

.streamlit-expanderHeader {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    color: var(--text) !important;
}

hr { border-color: var(--border) !important; }

.block-container { padding-top: 1.5rem !important; max-width: 1400px; }

/* Sidebar nav */
[data-testid="stSidebarNav"] a span {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

div[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# Sidebar branding
with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0 1.5rem 0;'>
        <div style='font-family: Space Mono, monospace; font-size: 0.6rem; color: #6b7280; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 0.3rem;'>SYSTEM ONLINE</div>
        <div style='font-family: DM Serif Display, serif; font-size: 1.8rem; color: #e5e7eb; line-height: 1;'>North<span style="color:#00d4aa;">star</span></div>
        <div style='font-family: Space Mono, monospace; font-size: 0.6rem; color: #6b7280; letter-spacing: 0.1em; margin-top: 0.3rem;'>Guiding Your Market Edge</div>
    </div>
    <hr style='border-color:#1f2937; margin: 0 0 1.5rem 0;'/>
    """, unsafe_allow_html=True)
    
    st.markdown("**NAVIGATION**")
    page = st.radio(
        "",
        ["📡  Market Overview", "🔍  Stock Scanner", "📰  News Intelligence", "💡  AI Picks", "📊  Deep Analysis"],
        label_visibility="collapsed"
    )
    
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='font-family: Space Mono, monospace; font-size: 0.6rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em;'>
        Data Sources<br/>
        <span style='color:#374151;'>──────────────</span><br/>
        Yahoo Finance API<br/>
        NewsAPI / RSS Feeds<br/>
        FRED Economic Data<br/>
        SEC EDGAR Filings<br/>
        ML: Random Forest + LSTM
    </div>
    """, unsafe_allow_html=True)

# Route pages
if "Market Overview" in page:
    import pages.overview as p; p.render()
elif "Stock Scanner" in page:
    import pages.scanner as p; p.render()
elif "News Intelligence" in page:
    import pages.news as p; p.render()
elif "AI Picks" in page:
    import pages.ai_picks as p; p.render()
elif "Deep Analysis" in page:
    import pages.analysis as p; p.render()
