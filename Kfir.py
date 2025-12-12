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
    initial_sidebar_state="collapsed"
)

# Force Dark Theme via CSS injection
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #0b0c15;
        color: #ffffff;
    }
    [data-testid="stHeader"] {
        background-color: #0b0c15;
    }
    .stMetric {
        background-color: #151621;
        padding: 10px;
        border-radius: 10px;
    }
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Constants & Data ---
SECTORS = {
    "📊 Overview": [], # Special case
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

INDICES = ["^GSPC", "^IXIC", "BTC-USD"]

# Helper to flatten list
def get_all_tickers():
    all_t = []
    for s in SECTORS.values():
        all_t.extend(s)
    return list(set(all_t + INDICES))

# --- Data Fetching ---
@st.cache_data(ttl=60) # Cache for 60 seconds to prevent spamming Yahoo
def fetch_market_data():
    tickers = get_all_tickers()
    if not tickers: return pd.DataFrame(), pd.DataFrame()
    
    # 1. Fetch 5d intraday with prepost for accurate current price
    try:
        live_data = yf.download(
            tickers, 
            period="5d", 
            interval="15m", 
            prepost=True, 
            group_by='ticker', 
            threads=False, # Safe mode for web servers
            progress=False,
            auto_adjust=False # Fix FutureWarning
        )
    except Exception as e:
        st.error(f"Error fetching live data: {e}")
        live_data = pd.DataFrame()

    # 2. Fetch Daily data for % change calculation reference
    try:
        daily_data = yf.download(
            tickers, 
            period="1y", 
            group_by='ticker', 
            threads=False, 
            progress=False,
            auto_adjust=False # Fix FutureWarning
        )
    except:
        daily_data = pd.DataFrame()
        
    return live_data, daily_data

def calculate_metrics(ticker, live_df, daily_df, timeframe="1D"):
    # Extract specific ticker data
    try:
        t_live = live_data[ticker] if ticker in live_data.columns.levels[0] else pd.DataFrame()
        t_daily = daily_data[ticker] if ticker in daily_data.columns.levels[0] else pd.DataFrame()
    except:
        return None

    if t_daily.empty: return None

    # Get Current Price (latest from live, or fallback to daily)
    current_price = 0.0
    is_extended = False
    
    if not t_live.empty:
        valid_live = t_live['Close'].dropna()
        if not valid_live.empty:
            current_price = float(valid_live.iloc[-1])
            # Check time for Extended Hours icon
            last_dt = valid_live.index[-1]
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=pytz.timezone('US/Eastern'))
            else:
                last_dt = last_dt.astimezone(pytz.timezone('US/Eastern'))
            
            h, m = last_dt.hour, last_dt.minute
            if (h < 9) or (h == 9 and m < 30) or (h >= 16):
                is_extended = True
    
    if current_price == 0 and not t_daily.empty:
        current_price = float(t_daily['Close'].iloc[-1])

    # Calculate Change based on Timeframe
    start_price = current_price
    closes = t_daily['Close'].dropna()
    
    if timeframe == "1D":
        # Compare to previous Close
        if len(closes) >= 2:
            start_price = float(closes.iloc[-2])
    else:
        # Multi-day lookback
        lookback_map = {"1W": 5, "1M": 21, "3M": 63, "1Y": 252}
        lb = lookback_map.get(timeframe, 5)
        if len(closes) > lb:
            start_price = float(closes.iloc[-(lb+1)])
        elif not closes.empty:
            start_price = float(closes.iloc[0])

    change_pct = ((current_price - start_price) / start_price) * 100 if start_price else 0
    
    # Volume (Approx from daily) - FIXED: Handle NaN values safely
    vol = 0
    if 'Volume' in t_daily.columns:
        try:
            v = t_daily['Volume'].iloc[-1]
            if pd.notna(v):
                vol = int(v)
        except (ValueError, TypeError):
            vol = 0

    return {
        "Ticker": ticker,
        "Price": current_price,
        "Change": change_pct,
        "Volume": vol,
        "Extended": is_extended,
        "History": closes.tolist()[-30:] # For Sparkline
    }

def format_volume(num):
    if num > 1_000_000_000: return f"{num/1_000_000_000:.1f}B"
    if num > 1_000_000: return f"{num/1_000_000:.1f}M"
    if num > 1_000: return f"{num/1_000:.1f}K"
    return str(num)

# --- UI Layout ---

# 1. Header & Controls
col1, col2 = st.columns([3, 1])
with col1:
    st.title("⚡ Theme Tracker Live")
with col2:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# 2. Controls Row
c1, c2 = st.columns([4, 2])
with c1:
    # Chips for Sectors (Using radio looking like pills)
    selected_sector = st.pills("Select Sector", list(SECTORS.keys()), default="📊 Overview")
    # Fix for KeyError: Ensure selected_sector is never None
    if not selected_sector:
        selected_sector = "📊 Overview"
        
with c2:
    timeframe = st.segmented_control("Timeframe", ["1D", "1W", "1M", "3M", "1Y"], default="1D")

# Fetch Data
with st.spinner("Fetching global market data..."):
    live_data, daily_data = fetch_market_data()

# Process Data
if selected_sector == "📊 Overview":
    # --- OVERVIEW DASHBOARD ---
    st.subheader("Sector Performance")
    
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
        width="stretch", # Replaced use_container_width based on warning
        height=600
    )

else:
    # --- SECTOR DETAIL ---
    tickers = SECTORS[selected_sector]
    
    # Filter/Search
    search_term = st.text_input("Search Ticker", placeholder="e.g. NVDA", label_visibility="collapsed")
    
    rows = []
    for t in tickers:
        if search_term and search_term.upper() not in t: continue
        
        m = calculate_metrics(t, live_data, daily_data, timeframe)
        if m:
            # Add Icons
            icon = "☾" if m['Extended'] else ""
            
            rows.append({
                "Ticker": f"{t} {icon}",
                "Price": m['Price'],
                "Change": m['Change']/100, # Divide by 100 for percentage formatting in dataframe
                "Volume": m['Volume'], # Keep raw for sorting
                "Vol Str": format_volume(m['Volume']), # Display string
                "Trend": m['History']
            })
            
    df_sector = pd.DataFrame(rows)
    
    if not df_sector.empty:
        # Sort by Performance Descending
        df_sector = df_sector.sort_values("Change", ascending=False)
        
        # Display Table
        st.dataframe(
            df_sector,
            column_config={
                "Ticker": st.column_config.TextColumn("Symbol", help="☾ = Extended Hours"),
                "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "Change": st.column_config.NumberColumn(
                    "Change", 
                    format="%.2f%%"
                ),
                "Trend": st.column_config.LineChartColumn(
                    "30-Day Trend",
                    y_min=0,
                    width="medium"
                ),
                "Volume": None, # Hide raw number
                "Vol Str": st.column_config.TextColumn("Volume")
            },
            hide_index=True,
            width="stretch", # Replaced use_container_width based on warning
            height=700
        )
    else:
        st.info("No data available for this sector.")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')} | Data provider: Yahoo Finance")
