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
# Curated list of high-impact stocks per sector (Comprehensive Expansion)
SECTORS = {
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

# Mapping for nicer display names (Expanded)
COMPANY_NAMES = {
    # Tech & Semi
    "NVDA": "NVIDIA", "TSM": "TSMC", "AVGO": "Broadcom", "AMD": "Adv. Micro Devices", "QCOM": "Qualcomm", "TXN": "Texas Instruments", 
    "MU": "Micron", "INTC": "Intel", "ARM": "Arm Holdings", "AMAT": "Applied Materials", "LRCX": "Lam Research", "ADI": "Analog Devices",
    "MSFT": "Microsoft", "AAPL": "Apple", "GOOGL": "Alphabet", "META": "Meta", "AMZN": "Amazon", "TSLA": "Tesla", 
    "ORCL": "Oracle", "IBM": "IBM", "CSCO": "Cisco", "CRM": "Salesforce", "NOW": "ServiceNow", "ADBE": "Adobe", 
    "SNOW": "Snowflake", "DDOG": "Datadog", "PLTR": "Palantir", "MDB": "MongoDB", "ZS": "Zscaler", "NET": "Cloudflare", 
    "WDAY": "Workday", "HUBS": "HubSpot", "TEAM": "Atlassian",
    # Cyber
    "PANW": "Palo Alto Net", "CRWD": "CrowdStrike", "FTNT": "Fortinet", "OKTA": "Okta", "CYBR": "CyberArk", "GEN": "Gen Digital", 
    "TENB": "Tenable", "S": "SentinelOne", "CHKP": "Check Point",
    # Finance
    "V": "Visa", "MA": "Mastercard", "PYPL": "PayPal", "SQ": "Block", "COIN": "Coinbase", "HOOD": "Robinhood", "AFRM": "Affirm", 
    "FI": "Fiserv", "FIS": "Fidelity National", "GPN": "Global Payments", "TOST": "Toast",
    "JPM": "JPMorgan", "BAC": "Bank of America", "WFC": "Wells Fargo", "C": "Citigroup", "MS": "Morgan Stanley", "GS": "Goldman Sachs", 
    "SCHW": "Charles Schwab", "BLK": "BlackRock", "AXP": "Amex", "USB": "US Bancorp", "PNC": "PNC Financial",
    # Health
    "LLY": "Eli Lilly", "JNJ": "Johnson & Johnson", "ABBV": "AbbVie", "MRK": "Merck", "PFE": "Pfizer", "AMGN": "Amgen", 
    "BMY": "Bristol-Myers", "GILD": "Gilead", "VRTX": "Vertex", "REGN": "Regeneron", "NVO": "Novo Nordisk",
    "TMO": "Thermo Fisher", "ABT": "Abbott", "MDT": "Medtronic", "ISRG": "Intuitive Surgical", "SYK": "Stryker", "BSX": "Boston Scientific", 
    "EW": "Edwards Lifesciences", "DXCM": "Dexcom", "ZBH": "Zimmer Biomet", "BDX": "Becton Dickinson", "GEHC": "GE HealthCare",
    # Consumer
    "HD": "Home Depot", "MCD": "McDonald's", "NKE": "Nike", "SBUX": "Starbucks", "TGT": "Target", "LOW": "Lowe's", 
    "TJX": "TJX Companies", "LULU": "Lululemon", "CMG": "Chipotle", "YUM": "Yum! Brands", "EBAY": "eBay",
    "WMT": "Walmart", "COST": "Costco", "PG": "Procter & Gamble", "KO": "Coca-Cola", "PEP": "PepsiCo", "PM": "Philip Morris", 
    "MO": "Altria", "CL": "Colgate-Palmolive", "EL": "Estee Lauder", "K": "Kellanova", "GIS": "General Mills", "MNST": "Monster Bev",
    # Auto
    "TM": "Toyota", "F": "Ford", "GM": "General Motors", "HMC": "Honda", "STLA": "Stellantis", "RIVN": "Rivian", 
    "LCID": "Lucid", "LI": "Li Auto", "NIO": "NIO", "XPEV": "XPeng",
    # Industrial & Defense
    "RTX": "RTX Corp", "LMT": "Lockheed Martin", "BA": "Boeing", "NOC": "Northrop Grumman", "GD": "General Dynamics", 
    "LHX": "L3Harris", "GE": "GE Aerospace", "TDG": "TransDigm", "AXON": "Axon", "HII": "Huntington Ingalls",
    "CAT": "Caterpillar", "DE": "Deere", "UNP": "Union Pacific", "UPS": "UPS", "HON": "Honeywell", "ETN": "Eaton", 
    "ITW": "Illinois Tool Works", "WM": "Waste Management", "MMM": "3M", "FDX": "FedEx", "CSX": "CSX Corp",
    # Energy & Materials
    "XOM": "ExxonMobil", "CVX": "Chevron", "SHEL": "Shell", "TTE": "TotalEnergies", "COP": "ConocoPhillips", "BP": "BP plc", 
    "SLB": "Schlumberger", "EOG": "EOG Resources", "OXY": "Occidental", "MPC": "Marathon Petroleum", "VLO": "Valero",
    "NEE": "NextEra Energy", "DU": "Duke Energy", "SO": "Southern Co", "AEP": "American Elec", "SRE": "Sempra", "D": "Dominion", 
    "PEG": "PSEG", "FSLR": "First Solar", "ENPH": "Enphase", "SEDG": "SolarEdge", "PLUG": "Plug Power",
    "LIN": "Linde", "SCCO": "Southern Copper", "FCX": "Freeport-McMoRan", "NEM": "Newmont", "SHW": "Sherwin-Williams", 
    "APD": "Air Products", "DD": "DuPont", "CTVA": "Corteva", "ALB": "Albemarle", "NUE": "Nucor", "DOW": "Dow Inc",
    # Real Estate
    "PLD": "Prologis", "AMT": "American Tower", "EQIX": "Equinix", "CCI": "Crown Castle", "O": "Realty Income", 
    "SPG": "Simon Property", "PSA": "Public Storage", "WELL": "Welltower", "DLR": "Digital Realty", "VICI": "VICI Properties",
    # Media & Leisure
    "NFLX": "Netflix", "DIS": "Disney", "TMUS": "T-Mobile", "VZ": "Verizon", "T": "AT&T", "CMCSA": "Comcast", "CHTR": "Charter", 
    "WBD": "Warner Bros", "SPOT": "Spotify", "LYV": "Live Nation", "PARA": "Paramount",
    "BKNG": "Booking Holdings", "ABNB": "Airbnb", "MAR": "Marriott", "HLT": "Hilton", "DAL": "Delta Air", "UAL": "United Airlines", 
    "RCL": "Royal Caribbean", "CCL": "Carnival", "LUV": "Southwest", "EXPE": "Expedia", "LVS": "Las Vegas Sands"
}

# Flatten list for batch fetching
ALL_TICKERS = list(set([t for s in SECTORS.values() for t in s]))

# --- Data Engine ---
@st.cache_data(ttl=900)  # Cache for 15 minutes
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

# Initialize Session State
if 'selected_sector' not in st.session_state:
    st.session_state.selected_sector = list(SECTORS.keys())[0]
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Overview"

# Header
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
        
        # --- SELECTION & NAVIGATION ---
        # Display clickable button for navigation
        c1, c2 = st.columns([3, 1])
        with c1:
            st.info("👇 Select a sector below to see the 'Go to Detail' button.")
        
        # Apply Pandas Styling
        styler_overview = df_overview.style.format({
            "Daily": "{:+.2%}",
            "YTD": "{:+.2%}"
        }).bar(
            subset=["Daily"],
            align=0,
            color=['#FF4B4B', '#4CAF50'],
            vmin=-0.05,
            vmax=0.05
        )

        # Interactive Dataframe
        event = st.dataframe(
            styler_overview,
            column_config={
                "Theme / Sector": st.column_config.TextColumn("Theme / Sector", width="large"),
                "Daily": st.column_config.Column("Daily Performance"), # Use generic Column to avoid overriding Styler
                "YTD": st.column_config.NumberColumn("YTD Return"),
                "Count": st.column_config.NumberColumn("Tickers", format="%d")
            },
            hide_index=True,
            width="stretch",
            height=600,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Handle Selection Button
        if len(event.selection.rows) > 0:
            selected_row_idx = event.selection.rows[0]
            new_sector = df_overview.iloc[selected_row_idx]["Theme / Sector"]
            
            # Update state immediately
            st.session_state.selected_sector = new_sector
            
            # Show a prominent button to jump
            with c2:
                if st.button(f"🔍 View Top 10 for {new_sector}", type="primary"):
                    # Switch tab is tricky in Streamlit purely programmatically without extra components,
                    # so we instruct user or use a visual cue.
                    st.toast(f"Switched to {new_sector} details! Please click the 'Sector Detail' tab.", icon="🚀")

# --- TAB 2: SECTOR DETAIL ---
with tab_detail:
    # Determine index based on session state
    try:
        current_sector_idx = list(SECTORS.keys()).index(st.session_state.selected_sector)
    except ValueError:
        current_sector_idx = 0

    # Controls
    col_sel, col_tf, col_limit, col_blank = st.columns([2, 1, 1, 1])
    with col_sel:
        selected_sector = st.selectbox(
            "Select Sector", 
            list(SECTORS.keys()), 
            index=current_sector_idx
        )
        st.session_state.selected_sector = selected_sector

    with col_tf:
        timeframe_options = {
            "1 Day": "1D %",
            "1 Week": "1W %",
            "1 Month": "1M %",
            "YTD": "YTD %"
        }
        selected_tf_label = st.selectbox("Ranking Timeframe", list(timeframe_options.keys()))
        selected_tf_col = timeframe_options[selected_tf_label]

    with col_limit:
        show_top_10 = st.checkbox("Show Top 10 Only", value=True)

    if selected_sector:
        tickers = SECTORS[selected_sector]
        rows = []
        
        # Sector Aggregate Metrics
        sec_1d, sec_1w, sec_1m, sec_ytd = 0, 0, 0, 0
        valid_count = 0

        for t in tickers:
            m = get_detailed_metrics(t, live_data)
            if m:
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
            # Sort by the selected timeframe column
            df_detail = df_detail.sort_values(selected_tf_col, ascending=False)
            
            # Apply Top 10 Filter
            if show_top_10:
                df_detail = df_detail.head(10)
            
            # Apply styling to detail view
            styler_detail = df_detail.style.format({
                "1D %": "{:+.2%}",
                "1W %": "{:+.2%}",
                "1M %": "{:+.2%}",
                "YTD %": "{:+.2%}",
                "Price": "${:.2f}"
            }).bar(
                subset=[selected_tf_col], # Dynamic column based on user selection
                align=0,
                color=['#FF4B4B', '#4CAF50'],
                vmin=-0.05,
                vmax=0.05
            )

            st.dataframe(
                styler_detail,
                column_config={
                    "Logo": st.column_config.ImageColumn("Logo", width="small"),
                    "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                    "Name": st.column_config.TextColumn("Company Name", width="medium"),
                    "Price": st.column_config.NumberColumn("Price"),
                    # Generic Column config avoids overriding the Pandas Styler colors
                    "1D %": st.column_config.Column("1 Day"),
                    "1W %": st.column_config.Column("1 Week"),
                    "1M %": st.column_config.Column("1 Month"),
                    "YTD %": st.column_config.Column("YTD"),
                },
                hide_index=True,
                width="stretch",
                height=600
            )
        else:
            st.info("No data available for this sector.")
