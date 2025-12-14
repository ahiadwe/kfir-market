import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz
import time

# --- Configuration ---
st.set_page_config(
    page_title="Theme Tracker Live",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed" # Starts closed on mobile (good for focus)
)

# Force Dark Theme & Mobile CSS Optimization
st.markdown("""
<style>
    /* Dark Theme Colors */
    [data-testid="stAppViewContainer"] {
        background-color: #0b0c15;
        color: #ffffff;
    }
    [data-testid="stHeader"] {
        background-color: #0b0c15;
    }
    [data-testid="stSidebar"] {
        background-color: #151621;
        border-right: 1px solid #222335;
    }
    
    /* Metrics Styling */
    div[data-testid="metric-container"] {
        background-color: #151621;
        border: 1px solid #222335;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Mobile Optimizations */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 2rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        h1 {
            font-size: 1.8rem !important;
        }
        /* Make dataframe headers smaller on mobile */
        th {
            font-size: 0.8rem !important;
        }
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Constants & Data ---
SECTORS = {
    "📊 Overview": [], 
    "💾 Semiconductors": ["NVDA", "AMD", "INTC", "TSM", "AVGO", "QCOM", "MU", "TXN"],
    "🚗 EV & Mobility": ["TSLA", "RIVN", "LCID", "NIO", "XPEV", "GM", "F", "ON"],
    "☁️ Cloud & SaaS": ["MSFT", "ADBE", "CRM", "SNOW", "DDOG", "NOW", "WDAY", "ZS"],
    "🛡️ Cybersecurity": ["PANW", "CRWD", "FTNT", "OKTA", "CYBR", "S", "NET"],
    "🤖 AI & Robotics": ["ISRG", "PATH", "IRBT", "UPST", "PLTR", "AI", "GOOGL"],
    "🛒 E-Commerce": ["AMZN", "BABA", "JD", "SHOP", "MELI", "EBAY", "ETSY"],
    "🧬 Biotech": ["PFE", "MRNA", "BNTX", "LLY", "UNH", "JNJ", "ABBV"],
    "💳 Fintech": ["PYPL", "AXP", "COIN", "AFRM", "V", "MA", "HOOD"],
    "⚡ Energy": ["XOM", "CVX", "SHEL", "BP", "COP", "SLB"],
    "🛍️ Retail": ["WMT", "TGT", "COST", "HD", "LOW", "NKE", "SBUX"],
    "📺 Media": ["NFLX", "DIS", "CMCSA", "WBD", "PARA", "SPOT"],
    "✈️ Travel": ["BKNG", "ABNB", "MAR", "DAL", "UAL", "CCL", "RCL"],
    "⚔️ Defense": ["RTX", "LMT", "BA", "NOC", "GD"],
    "🎮 Gaming": ["TTWO", "EA", "RBLX", "U", "SONY", "NTDOY"],
    "🏠 Real Estate": ["PLD", "AMT", "EQIX", "O", "SPG"]
}

# Mapping Tickers to Company Names
COMPANY_NAMES = {
    "NVDA": "NVIDIA", "AMD": "Adv. Micro Devices", "INTC": "Intel", "TSM": "TSMC", "AVGO": "Broadcom", "QCOM": "Qualcomm", "MU": "Micron", "TXN": "Texas Inst.",
    "TSLA": "Tesla", "RIVN": "Rivian", "LCID": "Lucid", "NIO": "NIO Inc", "XPEV": "XPeng", "GM": "GM", "F": "Ford", "ON": "ON Semi",
    "MSFT": "Microsoft", "ADBE": "Adobe", "CRM": "Salesforce", "SNOW": "Snowflake", "DDOG": "Datadog", "NOW": "ServiceNow", "WDAY": "Workday", "ZS": "Zscaler",
    "PANW": "Palo Alto", "CRWD": "CrowdStrike", "FTNT": "Fortinet", "OKTA": "Okta", "CYBR": "CyberArk", "S": "SentinelOne", "NET": "Cloudflare",
    "ISRG": "Intuitive Surg.", "PATH": "UiPath", "IRBT": "iRobot", "UPST": "Upstart", "PLTR": "Palantir", "AI": "C3.ai", "GOOGL": "Google",
    "AMZN": "Amazon", "BABA": "Alibaba", "JD": "JD.com", "SHOP": "Shopify", "MELI": "MercadoLibre", "EBAY": "eBay", "ETSY": "Etsy",
    "PFE": "Pfizer", "MRNA": "Moderna", "BNTX": "BioNTech", "LLY": "Eli Lilly", "UNH": "UnitedHealth", "JNJ": "J&J", "ABBV": "AbbVie",
    "PYPL": "PayPal", "AXP": "Amex", "COIN": "Coinbase", "AFRM": "Affirm", "V": "Visa", "MA": "Mastercard", "HOOD": "Robinhood",
    "XOM": "Exxon", "CVX": "Chevron", "SHEL": "Shell", "BP": "BP", "COP": "ConocoPhillips", "SLB": "Schlumberger",
    "WMT": "Walmart", "TGT": "Target", "COST": "Costco", "HD": "Home Depot", "LOW": "Lowe's", "NKE": "Nike", "SBUX": "Starbucks",
    "NFLX": "Netflix", "DIS": "Disney", "CMCSA": "Comcast", "WBD": "Warner Bros", "PARA": "Paramount", "SPOT": "Spotify",
    "BKNG": "Booking", "ABNB": "Airbnb", "MAR": "Marriott", "DAL": "Delta", "UAL": "United", "CCL": "Carnival", "RCL": "Royal Caribbean",
    "RTX": "Raytheon", "LMT": "Lockheed", "BA": "Boeing", "NOC": "Northrop", "GD": "General Dyn.",
    "TTWO": "Take-Two", "EA": "Electronic Arts", "RBLX": "Roblox", "U": "Unity", "SONY": "Sony", "NTDOY": "Nintendo",
    "PLD": "Prologis", "AMT": "American Tower", "EQIX": "Equinix", "O": "Realty Income", "SPG": "Simon Prop."
}

INDICES_MAP = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "BTC-USD": "Bitcoin"}
INDICES = list(INDICES_MAP.keys())

# Helper to flatten list
def get_all_tickers():
    all_t = []
    for s in SECTORS.values():
        all_t.extend(s)
    return list(set(all_t + INDICES))

# --- Data Fetching ---
@st.cache_data(ttl=300) 
def fetch_market_data():
    tickers = get_all_tickers()
    if not tickers: return pd.DataFrame(), pd.DataFrame()
    
    try:
        # Live Data (5d, 15m)
        live_data = yf.download(tickers, period="5d", interval="15m", prepost=True, group_by='ticker', threads=True, progress=False, auto_adjust=False)
    except Exception:
        live_data = pd.DataFrame()

    time.sleep(1) 

    try:
        # Daily Data (1y)
        daily_data = yf.download(tickers, period="1y", group_by='ticker', threads=True, progress=False, auto_adjust=False)
    except:
        daily_data = pd.DataFrame()
        
    return live_data, daily_data

def calculate_metrics(ticker, live_df, daily_df, timeframe="1D"):
    try:
        t_live = live_data[ticker] if ticker in live_data.columns.levels[0] else pd.DataFrame()
        t_daily = daily_data[ticker] if ticker in daily_data.columns.levels[0] else pd.DataFrame()
    except: return None

    if t_daily.empty: return None

    current_price = 0.0
    is_extended = False
    
    # 1. Try to get latest price from Live data (includes pre/post)
    if not t_live.empty:
        valid_live = t_live['Close'].dropna()
        if not valid_live.empty:
            current_price = float(valid_live.iloc[-1])
            # Check for Extended Hours
            last_dt = valid_live.index[-1]
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=pytz.timezone('US/Eastern'))
            else:
                last_dt = last_dt.astimezone(pytz.timezone('US/Eastern'))
            
            h, m = last_dt.hour, last_dt.minute
            if (h < 9) or (h == 9 and m < 30) or (h >= 16):
                is_extended = True
    
    # 2. Fallback to Daily
    if current_price == 0 and not t_daily.empty:
        current_price = float(t_daily['Close'].iloc[-1])

    # 3. Calculate Reference Price
    start_price = current_price
    closes = t_daily['Close'].dropna()
    
    if timeframe == "1D":
        if len(closes) >= 2: start_price = float(closes.iloc[-2])
    else:
        lb_map = {"1W": 5, "1M": 21, "3M": 63, "1Y": 252}
        lb = lb_map.get(timeframe, 5)
        if len(closes) > lb: start_price = float(closes.iloc[-(lb+1)])
        elif not closes.empty: start_price = float(closes.iloc[0])

    change_pct = ((current_price - start_price) / start_price) * 100 if start_price else 0
    
    vol = 0
    if 'Volume' in t_daily.columns:
        try:
            v = t_daily['Volume'].iloc[-1]
            if pd.notna(v): vol = int(v)
        except: vol = 0

    return {
        "Ticker": ticker,
        "Price": current_price,
        "Change": change_pct,
        "Volume": vol,
        "Extended": is_extended,
        "History": closes.tolist()[-30:]
    }

def format_volume(num):
    if num > 1_000_000_000: return f"{num/1_000_000_000:.1f}B"
    if num > 1_000_000: return f"{num/1_000_000:.1f}M"
    if num > 1_000: return f"{num/1_000:.1f}K"
    return str(num)

# --- UI Layout ---

# Sidebar Navigation (Mobile Drawer)
with st.sidebar:
    st.title("⚙️ Controls")
    st.markdown("---")
    
    # Controls moved here for mobile space efficiency
    if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("### Navigation")
    selected_sector = st.pills("Select Sector", list(SECTORS.keys()), default="📊 Overview")
    if not selected_sector: selected_sector = "📊 Overview"
    
    st.markdown("### Settings")
    timeframe = st.segmented_control("Timeframe", ["1D", "1W", "1M", "3M", "1Y"], default="1D")
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

# Main Content Area
st.title("⚡ Theme Tracker")

# 1. Market Pulse Ticker (Top Row)
with st.spinner("Loading Market Pulse..."):
    live_data, daily_data = fetch_market_data()

# Calculate Indices Metrics
idx_cols = st.columns(3)
for i, idx in enumerate(INDICES):
    m = calculate_metrics(idx, live_data, daily_data, "1D") # Always 1D for pulse
    if m:
        name = INDICES_MAP[idx]
        with idx_cols[i]:
            st.metric(label=name, value=f"${m['Price']:,.2f}", delta=f"{m['Change']:.2f}%")

st.markdown("---")

# 2. Main Content Logic
if selected_sector == "📊 Overview":
    st.subheader("Market Heatmap")
    
    sector_stats = []
    for sec_name, tickers in SECTORS.items():
        if sec_name == "📊 Overview": continue
        
        total_change = 0
        count = 0
        for t in tickers:
            m = calculate_metrics(t, live_data, daily_data, timeframe)
            if m:
                total_change += m['Change']
                count += 1
        
        avg = total_change / count if count > 0 else 0
        sector_stats.append({"Sector": sec_name, "Avg Change": avg})
    
    df_overview = pd.DataFrame(sector_stats).sort_values("Avg Change", ascending=False)
    
    st.dataframe(
        df_overview,
        column_config={
            "Sector": st.column_config.TextColumn("Sector"),
            "Avg Change": st.column_config.ProgressColumn(
                "Performance",
                format="%.2f%%",
                min_value=-5,
                max_value=5,
            ),
        },
        hide_index=True,
        width="stretch"
    )

else:
    # Sector Detail View
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader(f"{selected_sector}")
    with c2:
        search_term = st.text_input("Filter", placeholder="Symbol", label_visibility="collapsed")
    
    rows = []
    tickers = SECTORS[selected_sector]
    
    for t in tickers:
        if search_term and search_term.upper() not in t: continue
        
        m = calculate_metrics(t, live_data, daily_data, timeframe)
        if m:
            icon = "☾" if m['Extended'] else ""
            comp_name = COMPANY_NAMES.get(t, t)
            # Shorten name for mobile
            if len(comp_name) > 15: comp_name = comp_name[:15] + "..."
            
            rows.append({
                "Symbol": f"{t} {icon}",
                "Name": comp_name,
                "Price": m['Price'],
                "Change": m['Change']/100,
                "Trend": m['History']
            })
            
    df_sector = pd.DataFrame(rows)
    
    if not df_sector.empty:
        df_sector = df_sector.sort_values("Change", ascending=False)
        
        st.dataframe(
            df_sector,
            column_config={
                "Symbol": st.column_config.TextColumn("Ticker", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Price": st.column_config.NumberColumn("Price", format="$%.2f", width="small"),
                "Change": st.column_config.NumberColumn("Change", format="%.2f%%", width="small"),
                "Trend": st.column_config.LineChartColumn("Trend", y_min=0, width="small"),
            },
            hide_index=True,
            width="stretch"
        )
    else:
        st.info("No data available.")
