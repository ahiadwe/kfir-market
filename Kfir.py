import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import altair as alt

# --- Configuration ---
st.set_page_config(
    page_title="Theme Tracker Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
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
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #ffffff;
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e;
    }

    /* Remove standard padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Constants: Fallback Data ---
# Used if live scraping fails (e.g., missing lxml dependency)
FALLBACK_SECTORS = {
    "Magnificent 7 & Big Tech": ["MSFT", "AAPL", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "ORCL", "IBM", "CSCO"],
    "Semiconductors": ["TSM", "AVGO", "AMD", "QCOM", "TXN", "MU", "INTC", "ARM", "AMAT", "LRCX", "ADI"],
    "Software (SaaS) & Cloud": ["CRM", "NOW", "ADBE", "SNOW", "DDOG", "PLTR", "MDB", "ZS", "NET", "WDAY", "HUBS", "TEAM"],
    "Cybersecurity": ["PANW", "CRWD", "FTNT", "OKTA", "CYBR", "GEN", "TENB", "S", "CHKP"],
    "Fintech & Payments": ["V", "MA", "PYPL", "SQ", "COIN", "HOOD", "AFRM", "FI", "FIS", "GPN", "TOST"],
    "Banking & Finance": ["JPM", "BAC", "WFC", "C", "MS", "GS", "SCHW", "BLK", "AXP", "USB", "PNC"],
    "Healthcare & Pharma": ["LLY", "JNJ", "ABBV", "MRK", "PFE", "AMGN", "BMY", "GILD", "VRTX", "REGN", "NVO"],
    "MedTech & Devices": ["TMO", "ABT", "MDT", "ISRG", "SYK", "BSX", "EW", "DXCM", "ZBH", "BDX", "GEHC"],
    "Consumer Discretionary": ["HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "TJX", "LULU", "CMG", "YUM", "EBAY"],
    "Consumer Staples": ["WMT", "COST", "PG", "KO", "PEP", "PM", "MO", "CL", "EL", "K", "GIS", "MNST"],
    "Automotive & EV": ["TM", "F", "GM", "HMC", "STLA", "RIVN", "LCID", "LI", "NIO", "XPEV"],
    "Aerospace & Defense": ["RTX", "LMT", "BA", "NOC", "GD", "LHX", "GE", "TDG", "AXON", "HII"],
    "Industrials & Logistics": ["CAT", "DE", "UNP", "UPS", "HON", "ETN", "ITW", "WM", "MMM", "FDX", "CSX"],
    "Energy (Oil & Gas)": ["XOM", "CVX", "SHEL", "TTE", "COP", "BP", "SLB", "EOG", "OXY", "MPC", "VLO"],
    "Clean Tech & Utilities": ["NEE", "DU", "SO", "AEP", "SRE", "D", "PEG", "FSLR", "ENPH", "SEDG", "PLUG"],
    "Materials & Mining": ["LIN", "SCCO", "FCX", "NEM", "SHW", "APD", "DD", "CTVA", "ALB", "NUE", "DOW"],
    "Real Estate (REITs)": ["PLD", "AMT", "EQIX", "CCI", "O", "SPG", "PSA", "WELL", "DLR", "VICI"],
    "Media & Telecom": ["NFLX", "DIS", "TMUS", "VZ", "T", "CMCSA", "CHTR", "WBD", "SPOT", "LYV", "PARA"],
    "Travel & Leisure": ["BKNG", "ABNB", "MAR", "HLT", "DAL", "UAL", "RCL", "CCL", "LUV", "EXPE", "LVS"]
}

# --- Data Engine: Dynamic Fetching ---

@st.cache_data(ttl=86400) # Cache S&P 500 list for 24 hours
def get_sp500_components():
    """Fetches S&P 500 constituents. Falls back to curated list if scraping fails."""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        # Try reading HTML. If lxml is missing, pandas might fail or try bs4 if available.
        # We catch the error to ensure the app doesn't crash.
        tables = pd.read_html(url)
        df = tables[0]
        # Clean up column names
        df = df.rename(columns={'Symbol': 'Ticker', 'GICS Sector': 'Sector', 'Security': 'Name'})
        return df[['Ticker', 'Name', 'Sector']]
    except Exception as e:
        # Fallback logic
        rows = []
        for sector, tickers in FALLBACK_SECTORS.items():
            for t in tickers:
                rows.append({"Ticker": t, "Name": t, "Sector": sector})
        
        return pd.DataFrame(rows)

@st.cache_data(ttl=900)  # Cache market data for 15 minutes
def fetch_market_data(tickers):
    """Fetches 1y data for a list of tickers to calculate multiple timeframes."""
    if not tickers:
        return pd.DataFrame()
    try:
        # Download 1 year of data
        data = yf.download(
            tickers, 
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
    idx = max(0, len(closes) - 1 - days_back)
    prev = float(closes.iloc[idx])
    
    if prev == 0: return 0.0
    return (current - prev) / prev

def get_detailed_metrics(ticker, live_df):
    """Extracts Price, 1D, 1W, 1M, YTD."""
    try:
        # Handle MultiIndex columns
        if ticker not in live_df.columns.levels[0]: 
            return None
        
        t_data = live_df[ticker]
        closes = t_data['Close'].dropna()
        
        if len(closes) < 2: 
            return None
        
        current_price = float(closes.iloc[-1])
        
        # Calculate periods
        change_1d = calculate_change(closes, 1)
        change_1w = calculate_change(closes, 5)
        change_1m = calculate_change(closes, 21)
        
        # YTD calculation
        current_year = datetime.datetime.now().year
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

# --- App Initialization ---

# 1. Fetch S&P 500 Components (Dynamic Source with Fallback)
with st.spinner("Fetching Market Constituents..."):
    sp500_df = get_sp500_components()

if sp500_df.empty:
    st.error("Failed to load market data. Please try again later.")
    st.stop()

# 2. Organize by Sector
SECTORS = sp500_df['Sector'].unique().tolist()
SECTORS.sort()

# Initialize Session State
if 'selected_sector' not in st.session_state:
    st.session_state.selected_sector = SECTORS[0]
if 'page' not in st.session_state:
    st.session_state.page = "Overview"

# --- Sidebar Navigation ---
with st.sidebar:
    st.title("Theme Tracker Pro")
    st.write(f"Tracking **{len(sp500_df)}** stocks across **{len(SECTORS)}** sectors.")
    
    # Navigation Mode
    nav_selection = st.radio(
        "Navigation", 
        ["Overview", "Sector Detail"], 
        index=0 if st.session_state.page == "Overview" else 1
    )
    
    # Update state based on radio selection
    if nav_selection != st.session_state.page:
        st.session_state.page = nav_selection
        st.rerun()
    
    st.markdown("---")
    
    # Refresh Button
    if st.button("🔄 Refresh Market Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.caption(f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

# --- Logic for Data Fetching ---
# We need to fetch data for the relevant stocks.
# To avoid fetching 500 stocks at once (slow), we fetch based on the view.

if st.session_state.page == "Overview":
    # Strategy: Fetch ALL data once (cached) to enable fast switching.
    target_tickers = sp500_df['Ticker'].tolist()
else:
    # Fetch only selected sector
    target_tickers = sp500_df[sp500_df['Sector'] == st.session_state.selected_sector]['Ticker'].tolist()

with st.spinner(f"Fetching market data for {len(target_tickers)} stocks..."):
    live_data = fetch_market_data(target_tickers)

# --- VIEW: OVERVIEW ---
if st.session_state.page == "Overview":
    st.subheader("Market Sectors Overview")
    
    # Grid Layout for more compact display (3 columns)
    cols = st.columns(3)
    
    for i, sec in enumerate(SECTORS):
        sec_tickers = sp500_df[sp500_df['Sector'] == sec]['Ticker'].tolist()
        
        # Calculate average performance for the sector (using available data)
        total_1d = 0
        count = 0
        for t in sec_tickers:
            m = get_detailed_metrics(t, live_data)
            if m:
                total_1d += m['1d']
                count += 1
        
        avg_1d = total_1d / count if count > 0 else 0.0
        color_hex = "#4CAF50" if avg_1d >= 0 else "#FF4B4B"
        
        # Select current column in the grid
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1E1E24; padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid {color_hex};">
                    <h4 style="margin: 0; font-size: 1.0rem;">{sec}</h4>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px;">
                        <span style="color: #8b949e; font-size: 0.8rem;">{count} Stocks</span>
                        <span style="font-weight: bold; color: {color_hex}; font-size: 1.1rem;">{avg_1d:+.2%}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Compact button
                if st.button(f"Details ➔", key=f"nav_{sec}", use_container_width=True):
                    st.session_state.selected_sector = sec
                    st.session_state.page = "Sector Detail"
                    st.rerun()
                
                st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# --- VIEW: SECTOR DETAIL ---
elif st.session_state.page == "Sector Detail":
    
    # Controls Area
    c_sel, c_tf, c_top = st.columns([2, 1, 1])
    with c_sel:
        # Ensure selected_sector is in the current list
        if st.session_state.selected_sector not in SECTORS:
            st.session_state.selected_sector = SECTORS[0]
            
        selected_sector = st.selectbox("Select Sector", SECTORS, index=SECTORS.index(st.session_state.selected_sector))
        st.session_state.selected_sector = selected_sector
        
    with c_tf:
        timeframe_map = {"1 Day": "1d", "1 Week": "1w", "1 Month": "1m", "YTD": "ytd"}
        tf_label = st.selectbox("Ranking Timeframe", list(timeframe_map.keys()))
        tf_key = timeframe_map[tf_label]
        
    with c_top:
        st.write("")
        st.write("")
        show_top = st.checkbox("Show Top 10 Only", value=True)

    # Process Data for Table
    sec_tickers = sp500_df[sp500_df['Sector'] == selected_sector]['Ticker'].tolist()
    rows = []
    
    for t in sec_tickers:
        m = get_detailed_metrics(t, live_data)
        # Handle cases where Name might not be available in live fetch
        name_series = sp500_df[sp500_df['Ticker'] == t]['Name']
        name = name_series.values[0] if not name_series.empty else t
        
        if m:
            clean_ticker = t.replace(".", "-")
            logo_url = f"https://assets.parqet.com/logos/symbol/{clean_ticker}?format=png"
            
            rows.append({
                "Logo": logo_url,
                "Symbol": t,
                "Name": name,
                "Price": m['price'],
                "1d": m['1d'],
                "1w": m['1w'],
                "1m": m['1m'],
                "ytd": m['ytd']
            })
            
    df_detail = pd.DataFrame(rows)
    
    if not df_detail.empty:
        # Sort
        df_detail = df_detail.sort_values(tf_key, ascending=False)
        
        # Filter Top 10
        if show_top:
            df_detail = df_detail.head(10)
            
        # --- VISUALIZATION: Diverging Bar Chart (Altair) ---
        # This is the most reliable way to show Green/Red bars in Streamlit
        st.subheader(f"Top Movers ({tf_label})")
        
        chart_data = df_detail.copy()
        chart_data['Color'] = chart_data[tf_key].apply(lambda x: 'Positive' if x >= 0 else 'Negative')
        
        # Base Chart
        bar_chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X(f"{tf_key}:Q", axis=alt.Axis(format='%'), title="Performance"),
            y=alt.Y("Symbol:N", sort="-x", title=None),
            color=alt.Color("Color:N", scale=alt.Scale(domain=['Positive', 'Negative'], range=['#4CAF50', '#FF4B4B']), legend=None),
            tooltip=["Name", "Price", alt.Tooltip(f"{tf_key}:Q", format=".2%")]
        ).properties(height=max(400, len(df_detail) * 30))
        
        st.altair_chart(bar_chart, use_container_width=True)
        
        # --- DATA TABLE: Custom Coloring (No Matplotlib) ---
        st.subheader("Detailed Data")
        
        # Format columns for display (keeping raw numbers for styling)
        display_df = df_detail.copy()
        
        # Custom styling function
        def style_positive_negative(val):
            try:
                v = float(val)
                if v > 0:
                    return 'color: #4CAF50; font-weight: bold'
                elif v < 0:
                    return 'color: #FF4B4B; font-weight: bold'
                return ''
            except:
                return ''

        # Apply Pandas Styling without matplotlib dependency
        styler = display_df.style.format({
            "Price": "${:.2f}",
            "1d": "{:+.2%}",
            "1w": "{:+.2%}",
            "1m": "{:+.2%}",
            "ytd": "{:+.2%}"
        }).map(style_positive_negative, subset=["1d", "1w", "1m", "ytd"])
        
        st.dataframe(
            styler,
            column_config={
                "Logo": st.column_config.ImageColumn("Logo", width="small"),
                "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                "Name": st.column_config.TextColumn("Name", width="large"),
                "Price": st.column_config.NumberColumn("Price"),
                # We let the Styler handle the colors for % columns
                "1d": st.column_config.Column("1 Day"),
                "1w": st.column_config.Column("1 Week"),
                "1m": st.column_config.Column("1 Month"),
                "ytd": st.column_config.Column("YTD"),
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )
    else:
        st.info("No data available.")
