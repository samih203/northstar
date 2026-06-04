# 📡 Northstar — Market Intelligence Platform

A full-featured stock market analysis platform built with Streamlit. Features real-time data, ML-powered predictions, undervalued stock screening, sentiment-tagged news, and curated investment theses based on world events.

---

## ✨ Features

| Module | What it does |
|--------|-------------|
| **Market Overview** | Live index prices, sector heatmaps, YTD comparison charts |
| **Stock Scanner** | Multi-factor scoring (value + growth + quality) across a 60+ stock universe; thematic/niche screens |
| **News Intelligence** | RSS-aggregated market news with keyword sentiment analysis; World Events → Trade Ideas |
| **AI Picks** | Random Forest ML model predicting 5-day directional movement; curated portfolios by risk profile |
| **Deep Analysis** | Full technical analysis (RSI, MACD, Bollinger Bands, candlestick), fundamental metrics, multi-ticker comparison |

---

## 🚀 Deploy to Streamlit Cloud (Recommended)

### 1. Fork / Push to GitHub

```bash
# Initialize a new repo
git init
git add .
git commit -m "Initial Northstar deploy"

# Create a new GitHub repo at github.com/new, then:
git remote add origin https://github.com/YOUR_USERNAME/northstar.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your GitHub repo and branch (`main`)
4. Set **Main file path** to `app.py`
5. Click **Deploy**

Your app will be live at `https://northstar.streamlit.app`

---

## 💻 Local Development

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/northstar.git
cd northstar

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 📁 Project Structure

```
northstar/
├── app.py                   # Entry point, routing, global CSS/theme
├── requirements.txt
├── .streamlit/
│   └── config.toml          # Dark theme config
├── pages/
│   ├── overview.py          # Market Overview page
│   ├── scanner.py           # Stock Scanner page
│   ├── news.py              # News Intelligence page
│   ├── ai_picks.py          # AI Picks page
│   └── analysis.py          # Deep Analysis page
├── utils/
│   └── data.py              # Data fetching (yfinance, RSS), screening logic
└── models/
    └── ml.py                # ML model (Random Forest), technical feature engineering
```

---

## 🧠 ML Model Details

The prediction engine uses a **Random Forest Classifier** (200 trees) trained on historical OHLCV data with 18 engineered features:

- **Momentum**: 1/3/5/10-day returns
- **Trend**: SMA 5/20/50, EMA 12/26, golden cross detection
- **Oscillators**: RSI (14), MACD, MACD signal & histogram
- **Volatility**: Bollinger Band width & position, ATR (14)
- **Volume**: Volume ratio vs 20-day average

**Target**: Binary classification — will price be higher 5 trading days from now?

Training uses a **time-series split** (80/20) to prevent lookahead bias. Model accuracy is reported on the out-of-sample test set.

> ⚠️ **Disclaimer**: This is for educational purposes only. Not financial advice. Past ML performance does not predict future returns.

---

## 📊 Data Sources

- **Price data**: Yahoo Finance via `yfinance` (free, no API key)
- **News**: Yahoo Finance RSS + MarketWatch RSS (free, no API key)
- **Fundamentals**: Yahoo Finance Info endpoint

All data is cached with TTLs (5 min for quotes, 15 min for screens, 30 min for news).

---

## 🎨 Theming

Dark terminal aesthetic with:
- **Fonts**: DM Serif Display (headings) + IBM Plex Sans (body) + Space Mono (numbers/code)
- **Colors**: `#00d4aa` (teal accent), `#f59e0b` (amber), `#ef4444` (red)
- **Background**: `#0a0e1a` (deep navy)

---

## 🔧 Extending the App

### Add more stocks to the screener universe
Edit `utils/data.py` → `screen_undervalued()` → `universe` list.

### Add a new thematic basket
Edit `utils/data.py` → `THEMATIC_STOCKS` dict.

### Upgrade to paid news API
Replace `get_news()` in `utils/data.py` with a [NewsAPI](https://newsapi.org) call using your key stored in Streamlit secrets:
```toml
# .streamlit/secrets.toml
NEWS_API_KEY = "your_key_here"
```
Then access via `st.secrets["NEWS_API_KEY"]`.

### Add more ML models
Edit `models/ml.py` — the `predict_direction()` function can be extended with LSTM, XGBoost, or ensemble voting.

---

## ⚙️ Streamlit Cloud Secrets (Optional)

For future API key integrations, add secrets at `share.streamlit.io → App Settings → Secrets`:

```toml
NEWS_API_KEY = "..."
ALPHA_VANTAGE_KEY = "..."
```

---

## 📄 License

MIT — free to use, modify, and deploy.
