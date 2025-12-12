import streamlit as st
import yfinance as yf
import pandas as pd
import math

# --- Configuration ---
st.set_page_config(
    page_title="Theme Tracker Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS (Clean Dark Theme) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0b0c15;
        color: #ffffff;
    }
    
    /* Clean DataFrame styling */
    div[data-testid="stDataFrame"] {
        background-color: #151621;
        border-radius: 8px;
        padding: 10px;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #8b949e;
        font-weight: 600;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: white;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #4CAF50; /* Green highlight */
        border-bottom: 2px solid #4CAF50;
    }

    /* Remove standard padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Constants ---
SECTORS = {
    "Semiconductors": ["NVDA", "AMD", "INTC", "TSM", "AVGO", "QCOM", "MU", "TXN", "ARM"],
    "EV & Mobility": ["TSLA", "RIVN", "LCID", "NIO", "XPEV", "GM", "F", "ON", "LI"],
    "Cloud & SaaS": ["MSFT", "ADBE", "CRM", "SNOW", "DDOG", "NOW", "WDAY", "ZS", "HUBS"],
    "Cybersecurity": ["PANW", "CRWD", "FTNT", "OKTA", "CYBR", "S", "NET", "TENB"],
    "AI & Robotics": ["ISRG", "PATH", "IRBT", "UPST", "PLTR", "AI", "GOOGL", "SYM"],
    "E-Commerce": ["AMZN", "BABA", "JD", "SHOP", "MELI", "EBAY", "ETSY", "CPNG"],
    "Biotech": ["PFE", "MRNA", "BNTX", "LLY", "UNH", "JNJ", "ABBV", "VRTX"],
    "Fintech": ["PYPL", "AXP", "COIN", "AFRM", "V", "MA", "HOOD", "SQ"],
    "Energy": ["XOM", "CVX", "SHEL", "BP", "COP", "SLB", "OXY", "HAL"],
    "Retail": ["WMT", "TGT", "COST", "HD", "LOW", "NKE", "SBUX", "LULU"],
    "Media": ["NFLX", "DIS", "CMCSA", "WBD", "PARA", "SPOT", "ROKU"],
    "Travel": ["BKNG", "ABNB", "MAR", "DAL", "UAL", "CCL", "RCL", "LUV"],
    "Defense": ["RTX", "LMT", "BA", "NOC", "GD", "LHX", "HII"],
    "Gaming": ["TTWO", "EA", "RBLX", "U", "SONY", "NTDOY", "ATVI"]
}

# Flatten list for batch fetching
ALL_TICKERS = list(set([t for s in SECTORS.values() for t in s]))

# --- Data Engine ---
@st.cache_data(ttl=60)
def fetch_data():
    """Fetches 5d data for current price."""
    try:
        data = yf.download(
            ALL_TICKERS, 
            period="5d", 
            group_by='ticker', 
            threads=True,
            progress=False,
            auto_adjust=False
        )
        return data
    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

def get_simple_metrics(ticker, live_df):
    """Extracts just Price and % Change."""
    try:
        if ticker not in live_df.columns.levels[0]: return None
        
        t_data = live_df[ticker]
        closes = t_data['Close'].dropna()
        
        if len(closes) < 2: return None
        
        current_price = float(closes.iloc[-1])
        prev_close = float(closes.iloc[-2]) # Compare to previous day close for simplicity
        
        change = current_price - prev_close
        pct_change = (change / prev_close) # decimal for dataframe formatting
        
        return {
            "price": current_price,
            "pct_change": pct_change
        }
    except Exception:
        return None

# --- Main UI ---

st.title("Theme Tracker")
st.markdown("---")

# Data Loading
live_data = fetch_data()

# Tabs
tab_overview, tab_detail = st.tabs(["Overview", "Sector Detail"])

# --- TAB 1: OVERVIEW ---
with tab_overview:
    sector_summary = []
    
    for sec_name, sec_tickers in SECTORS.items():
        total_change = 0
        count = 0
        
        for t in sec_tickers:
            m = get_simple_metrics(t, live_data)
            if m:
                total_change += m['pct_change']
                count += 1
        
        if count > 0:
            avg_change = total_change / count
            sector_summary.append({
                "Theme / Sector": sec_name,
                "Performance": avg_change
            })
    
    df_overview = pd.DataFrame(sector_summary)
    
    if not df_overview.empty:
        df_overview = df_overview.sort_values("Performance", ascending=False)
        
        st.dataframe(
            df_overview,
            column_config={
                "Theme / Sector": st.column_config.TextColumn("Theme / Sector", width="large"),
                "Performance": st.column_config.ProgressColumn(
                    "Daily Performance",
                    format="%.2f%%",
                    min_value=-0.05,
                    max_value=0.05,
                )
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )
    else:
        st.info("Loading market data...")

# --- TAB 2: SECTOR DETAIL ---
with tab_detail:
    # Clean pill selection
    selected_sector = st.pills(
        "Select Sector", 
        list(SECTORS.keys()), 
        default="Semiconductors",
        selection_mode="single",
        label_visibility="collapsed"
    )

    if selected_sector:
        tickers = SECTORS[selected_sector]
        rows = []
        
        for t in tickers:
            m = get_simple_metrics(t, live_data)
            if m:
                rows.append({
                    "Ticker": t,
                    "Price": m['price'],
                    "Performance": m['pct_change']
                })
        
        df_detail = pd.DataFrame(rows)
        
        if not df_detail.empty:
            df_detail = df_detail.sort_values("Performance", ascending=False)
            
            st.dataframe(
                df_detail,
                column_config={
                    "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Performance": st.column_config.ProgressColumn(
                        "Daily Change",
                        format="%.2f%%",
                        min_value=-0.1, # Wider range for individual stocks
                        max_value=0.1,
                    )
                },
                hide_index=True,
                use_container_width=True,
                height=600
            )
        else:
            st.info("No data available.")
