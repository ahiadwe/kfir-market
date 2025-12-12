import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

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
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #ffffff;
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e;
    }

    /* Refresh Button Styling */
    div.stButton > button {
        background-color: #262730;
        color: white;
        border: 1px solid #4CAF50;
    }
    div.stButton > button:hover {
        background-color: #4CAF50;
        color: white;
        border-color: #4CAF50;
    }

    /* Remove standard padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Constants & High Impact Stocks ---
# Curated list of high-impact stocks per sector
SECTORS = {
    "Semiconductors": ["NVDA", "TSM", "AVGO", "AMD", "QCOM", "TXN", "MU", "INTC", "ARM", "AMAT"],
    "Tech Giants & SaaS": ["MSFT", "AAPL", "ADBE", "CRM", "ORCL", "NOW", "UBER", "CSCO", "IBM", "INTU"],
    "EV & Mobility": ["TSLA", "TM", "RIVN", "ON", "LCID", "F", "GM", "HMC", "STLA", "LI"],
    "Cybersecurity": ["PANW", "CRWD", "FTNT", "PLTR", "OKTA", "NET", "ZS", "CYBR", "GEN", "TENB"],
    "E-Commerce & Retail": ["AMZN", "WMT", "HD", "COST", "BABA", "PDD", "JD", "SHOP", "TGT", "LOW"],
    "Biotech & Pharma": ["LLY", "JNJ", "ABBV", "MRK", "NVO", "PFE", "AMGN", "VRTX", "GILD", "BMY"],
    "Fintech & Finance": ["JPM", "V", "MA", "BRK-B", "BAC", "WFC", "MS", "GS", "AXP", "PYPL"],
    "Energy & Clean Tech": ["XOM", "CVX", "SHEL", "TTE", "COP", "BP", "SLB", "EOG", "OXY", "FSLR"],
    "Media & Streaming": ["NFLX", "DIS", "GOOGL", "META", "CMCSA", "TMUS", "VZ", "T", "SPOT", "WBD"],
    "Travel & Leisure": ["BKNG", "ABNB", "MAR", "HLT", "DAL", "UAL", "RCL", "CCL", "LUV", "EXPE"]
}

# Mapping for nicer display names
COMPANY_NAMES = {
    "NVDA": "NVIDIA", "TSM": "TSMC", "AVGO": "Broadcom", "AMD": "Adv. Micro Devices", 
    "QCOM": "Qualcomm", "TXN": "Texas Instruments", "MU": "Micron", "INTC": "Intel",
    "ARM": "Arm Holdings", "AMAT": "Applied Materials", "MSFT": "Microsoft", "AAPL": "Apple",
    "ADBE": "Adobe", "CRM": "Salesforce", "ORCL": "Oracle", "NOW": "ServiceNow",
    "UBER": "Uber", "CSCO": "Cisco", "IBM": "IBM", "INTU": "Intuit",
    "TSLA": "Tesla", "TM": "Toyota", "RIVN": "Rivian", "ON": "ON Semi",
    "LCID": "Lucid", "F": "Ford", "GM": "General Motors", "HMC": "Honda",
    "STLA": "Stellantis", "LI": "Li Auto", "PANW": "Palo Alto Net", "CRWD": "CrowdStrike",
    "FTNT": "Fortinet", "PLTR": "Palantir", "OKTA": "Okta", "NET": "Cloudflare",
    "ZS": "Zscaler", "CYBR": "CyberArk", "GEN": "Gen Digital", "TENB": "Tenable",
    "AMZN": "Amazon", "WMT": "Walmart", "HD": "Home Depot", "COST": "Costco",
    "BABA": "Alibaba", "PDD": "PDD Holdings", "JD": "JD.com", "SHOP": "Shopify",
    "TGT": "Target", "LOW": "Lowe's", "LLY": "Eli Lilly", "JNJ": "Johnson & Johnson",
    "ABBV": "AbbVie", "MRK": "Merck", "NVO": "Novo Nordisk", "PFE": "Pfizer",
    "AMGN": "Amgen", "VRTX": "Vertex", "GILD": "Gilead", "BMY": "Bristol-Myers",
    "JPM": "JPMorgan", "V": "Visa", "MA": "Mastercard", "BRK-B": "Berkshire Hathaway",
    "BAC": "Bank of America", "WFC": "Wells Fargo", "MS": "Morgan Stanley", "GS": "Goldman Sachs",
    "AXP": "Amex", "PYPL": "PayPal", "XOM": "ExxonMobil", "CVX": "Chevron",
    "SHEL": "Shell", "TTE": "TotalEnergies", "COP": "ConocoPhillips", "BP": "BP plc",
    "SLB": "Schlumberger", "EOG": "EOG Resources", "OXY": "Occidental", "FSLR": "First Solar",
    "NFLX": "Netflix", "DIS": "Disney", "GOOGL": "Alphabet (Google)", "META": "Meta",
    "CMCSA": "Comcast", "TMUS": "T-Mobile", "VZ": "Verizon", "T": "AT&T",
    "SPOT": "Spotify", "WBD": "Warner Bros", "BKNG": "Booking Holdings", "ABNB": "Airbnb",
    "MAR": "Marriott", "HLT": "Hilton", "DAL": "Delta Air", "UAL": "United Airlines",
    "RCL": "Royal Caribbean", "CCL": "Carnival", "LUV": "Southwest", "EXPE": "Expedia"
}

# Flatten list for batch fetching
ALL_TICKERS = list(set([t for s in SECTORS.values() for t in s]))

# --- Data Engine ---
@st.cache_data(ttl=900)  # Cache for 15 minutes (900s) to avoid rate limits
def fetch_data():
    """Fetches 1y data to calculate multiple timeframes."""
    try:
        # Download 1 year of data to calculate YTD, 1M, 1W
        data = yf.download(
            ALL_TICKERS, 
            period="1y", 
            group_by='ticker', 
            threads=True,
            progress=False,
            auto_adjust=False
        )
        return data
    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

def calculate_change(closes, days_back):
    """Helper to calculate % change given a series and days back."""
    if len(closes) < days_back + 1:
        return 0.0
    
    current = float(closes.iloc[-1])
    # Use -days_back (e.g., -5 for 1 week)
    # Ensure we don't go out of bounds
    idx = max(0, len(closes) - 1 - days_back)
    prev = float(closes.iloc[idx])
    
    if prev == 0: return 0.0
    return (current - prev) / prev

def get_detailed_metrics(ticker, live_df):
    """Extracts Price, 1D, 1W, 1M, YTD."""
    try:
        # Handle MultiIndex columns (Ticker -> Open/High/Low/Close)
        if ticker not in live_df.columns.levels[0]: 
            return None
        
        t_data = live_df[ticker]
        closes = t_data['Close'].dropna()
        
        if len(closes) < 2: 
            return None
        
        current_price = float(closes.iloc[-1])
        
        # 1 Day (approx 1 trading day)
        change_1d = calculate_change(closes, 1)
        
        # 1 Week (approx 5 trading days)
        change_1w = calculate_change(closes, 5)
        
        # 1 Month (approx 21 trading days)
        change_1m = calculate_change(closes, 21)
        
        # YTD calculation
        current_year = datetime.datetime.now().year
        # Filter closes for current year
        ytd_closes = closes[closes.index.year == current_year]
        if not ytd_closes.empty:
            start_price = float(ytd_closes.iloc[0])
            change_ytd = (current_price - start_price) / start_price if start_price != 0 else 0.0
        else:
            change_ytd = 0.0

        return {
            "price": current_price,
            "1d": change_1d,
            "1w": change_1w,
            "1m": change_1m,
            "ytd": change_ytd
        }
    except Exception:
        return None

# --- Main UI ---

# Header with Refresh Button
col_header, col_btn = st.columns([6, 1])
with col_header:
    st.title("Theme Tracker Pro")
    st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col_btn:
    st.write("") # Spacer
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Data Loading
with st.spinner("Fetching market data (1Y history)..."):
    live_data = fetch_data()

if live_data.empty:
    st.error("Failed to load data. Please refresh.")
    st.stop()

# Tabs
tab_overview, tab_detail = st.tabs(["Overview", "Sector Detail"])

# --- TAB 1: OVERVIEW ---
with tab_overview:
    sector_summary = []
    
    for sec_name, sec_tickers in SECTORS.items():
        total_change_1d = 0
        total_change_ytd = 0
        count = 0
        
        for t in sec_tickers:
            m = get_detailed_metrics(t, live_data)
            if m:
                total_change_1d += m['1d']
                total_change_ytd += m['ytd']
                count += 1
        
        if count > 0:
            avg_1d = total_change_1d / count
            avg_ytd = total_change_ytd / count
            sector_summary.append({
                "Theme / Sector": sec_name,
                "Daily": avg_1d,
                "YTD": avg_ytd,
                "Count": count
            })
    
    df_overview = pd.DataFrame(sector_summary)
    
    if not df_overview.empty:
        df_overview = df_overview.sort_values("Daily", ascending=False)
        
        st.dataframe(
            df_overview,
            column_config={
                "Theme / Sector": st.column_config.TextColumn("Theme / Sector", width="large"),
                "Daily": st.column_config.ProgressColumn(
                    "Daily Performance",
                    format="%.2f%%",
                    min_value=-0.05,
                    max_value=0.05,
                ),
                "YTD": st.column_config.NumberColumn(
                    "YTD Return",
                    format="%.2f%%"
                ),
                "Count": st.column_config.NumberColumn("Tickers", format="%d")
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )

# --- TAB 2: SECTOR DETAIL ---
with tab_detail:
    col_sel, col_blank = st.columns([1, 2])
    with col_sel:
        selected_sector = st.selectbox(
            "Select Sector", 
            list(SECTORS.keys()), 
            index=0
        )

    if selected_sector:
        tickers = SECTORS[selected_sector]
        rows = []
        
        # Sector Aggregate Metrics
        sec_1d, sec_1w, sec_1m, sec_ytd = 0, 0, 0, 0
        valid_count = 0

        for t in tickers:
            m = get_detailed_metrics(t, live_data)
            if m:
                # Construct Logo URL (using parqet as a public source)
                # Clean ticker for potential URL issues (though most standard tickers work)
                clean_ticker = t.replace(".", "-") if "." in t else t
                logo_url = f"https://assets.parqet.com/logos/symbol/{clean_ticker}?format=png"

                rows.append({
                    "Logo": logo_url,
                    "Symbol": t,
                    "Name": COMPANY_NAMES.get(t, t),
                    "Price": m['price'],
                    "1D %": m['1d'],
                    "1W %": m['1w'],
                    "1M %": m['1m'],
                    "YTD %": m['ytd']
                })
                # Accumulate for averages
                sec_1d += m['1d']
                sec_1w += m['1w']
                sec_1m += m['1m']
                sec_ytd += m['ytd']
                valid_count += 1
        
        # Display Sector Aggregates
        if valid_count > 0:
            st.markdown(f"### {selected_sector} Performance")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("1 Day", f"{sec_1d/valid_count:.2%}", delta_color="normal")
            m2.metric("1 Week", f"{sec_1w/valid_count:.2%}", delta_color="normal")
            m3.metric("1 Month", f"{sec_1m/valid_count:.2%}", delta_color="normal")
            m4.metric("YTD", f"{sec_ytd/valid_count:.2%}", delta_color="normal")
            st.markdown("---")

        df_detail = pd.DataFrame(rows)
        
        if not df_detail.empty:
            # User can sort by any column, default to 1D perf
            df_detail = df_detail.sort_values("1D %", ascending=False)
            
            st.dataframe(
                df_detail,
                column_config={
                    "Logo": st.column_config.ImageColumn("Logo", width="small"),
                    "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                    "Name": st.column_config.TextColumn("Company Name", width="medium"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "1D %": st.column_config.NumberColumn("1 Day", format="%.2f%%"),
                    "1W %": st.column_config.NumberColumn("1 Week", format="%.2f%%"),
                    "1M %": st.column_config.NumberColumn("1 Month", format="%.2f%%"),
                    "YTD %": st.column_config.NumberColumn("YTD", format="%.2f%%"),
                },
                hide_index=True,
                use_container_width=True,
                height=600
            )
        else:
            st.info("No data available for this sector.")
