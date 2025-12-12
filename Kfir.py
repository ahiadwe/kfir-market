import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import pytz

# --- Configuration ---
st.set_page_config(
    page_title="Theme Tracker Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS (Cyber/Glass Theme) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #050505 70%);
        color: #e0e0e0;
    }
    
    /* Metrics/Cards styling */
    div[data-testid="metric-container"] {
        background-color: rgba(30, 30, 40, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        border-color: rgba(100, 200, 255, 0.3);
    }
    
    /* Custom Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    
    /* DataFrame styling */
    div[data-testid="stDataFrame"] {
        background-color: rgba(20, 20, 25, 0.5);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 10px;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 4px;
        color: #8b949e;
        border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: white;
        background-color: rgba(255,255,255,0.1);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #238636;
        color: white;
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Remove standard padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Custom divider */
    hr {
        border-color: rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Constants (Real Names) ---
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

INDICES = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Bitcoin": "BTC-USD"}

# Flatten list for batch fetching
ALL_TICKERS = list(set([t for s in SECTORS.values() for t in s] + list(INDICES.values())))

# --- Data Engine ---

@st.cache_data(ttl=60)
def fetch_data():
    """Fetches 5d/15m data for sparklines and current price."""
    try:
        data = yf.download(
            ALL_TICKERS, 
            period="5d", 
            interval="15m", 
            group_by='ticker', 
            threads=True,
            progress=False,
            auto_adjust=False
        )
        return data
    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_daily_history():
    """Fetches 1y daily data for context and % calculations."""
    try:
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
        st.error(f"History API Error: {e}")
        return pd.DataFrame()

def get_ticker_metrics(ticker, live_df, daily_df):
    """Extracts clean metrics for a specific ticker."""
    try:
        # Access MultiIndex data safely
        if ticker not in live_df.columns.levels[0]:
            return None
        
        t_live = live_df[ticker]
        
        # Get latest price
        valid_closes = t_live['Close'].dropna()
        if valid_closes.empty:
            return None
        
        current_price = float(valid_closes.iloc[-1])
        
        # Calculate change (vs yesterday's close from daily data if available)
        if ticker in daily_df.columns.levels[0]:
            t_daily = daily_df[ticker]
            daily_closes = t_daily['Close'].dropna()
            if len(daily_closes) > 1:
                prev_close = float(daily_closes.iloc[-2])
            else:
                prev_close = float(valid_closes.iloc[0]) # Fallback to start of 5d
        else:
            prev_close = float(valid_closes.iloc[0])

        change = current_price - prev_close
        pct_change = (change / prev_close) * 100
        
        # Get simple sparkline data (last 20 points of 15m data)
        sparkline = valid_closes.tail(24).tolist() # last 6 hours approx
        
        return {
            "price": current_price,
            "change": change,
            "pct_change": pct_change,
            "history": sparkline,
            "volume": float(t_live['Volume'].iloc[-1]) if 'Volume' in t_live else 0
        }
    except Exception:
        return None

# --- Charts ---

def plot_candle_chart(ticker, data):
    """Interactive Candlestick chart using Altair (No Plotly dependency)."""
    if ticker not in data.columns.levels[0]:
        return None
    
    df = data[ticker].dropna().reset_index()
    # Ensure columns are lower case for consistency
    df.columns = [c.lower() for c in df.columns] 
    
    # Rename 'Datetime' or 'Date' to a standard 'date' column for Altair
    if 'datetime' in df.columns:
        df = df.rename(columns={'datetime': 'date'})
    elif 'date' not in df.columns: # fallback if index name was lost
        df['date'] = df.index

    # Base chart
    base = alt.Chart(df).encode(
        x=alt.X('date:T', axis=alt.Axis(
            title=None, 
            format='%m-%d %H:%M', 
            labelColor='#888',
            gridColor='#333'
        ))
    )

    # Candlestick Rule (Low to High)
    rule = base.mark_rule().encode(
        y=alt.Y('low:Q', scale=alt.Scale(zero=False), axis=alt.Axis(title='Price', labelColor='#888', gridColor='#333')),
        y2='high:Q',
        color=alt.value('#555')
    )

    # Candlestick Bar (Open to Close)
    bar = base.mark_bar(size=4).encode(
        y='open:Q',
        y2='close:Q',
        color=alt.condition(
            "datum.open <= datum.close",
            alt.value("#00ff88"),  # Green/Bullish
            alt.value("#ff0055")   # Red/Bearish
        ),
        tooltip=['date:T', 'open', 'high', 'low', 'close', 'volume']
    )

    chart = (rule + bar).properties(
        height=350, 
        title=alt.TitleParams(text=f"{ticker} • 5-Day Intraday", color='white')
    ).configure_view(
        strokeWidth=0
    ).configure(
        background='transparent'
    )
    
    return chart

# --- Main UI ---

# 1. Header & Pulse
col_title, col_time = st.columns([2, 1])
with col_title:
    st.title("⚡ Theme Tracker Pro")
with col_time:
    if st.button("Refresh Market Data", icon="🔄"):
        st.cache_data.clear()
        st.rerun()

# 2. Market Pulse Row (Indices)
live_data = fetch_data()
daily_data = fetch_daily_history()

pulse_cols = st.columns(len(INDICES))
for idx, (name, ticker) in enumerate(INDICES.items()):
    metrics = get_ticker_metrics(ticker, live_data, daily_data)
    with pulse_cols[idx]:
        if metrics:
            color = "normal" if metrics['pct_change'] >= 0 else "inverse"
            st.metric(
                label=name,
                value=f"{metrics['price']:,.2f}",
                delta=f"{metrics['pct_change']:.2f}%",
                delta_color=color
            )

st.markdown("---")

# 3. Main Navigation (Tabs)
tab_overview, tab_analysis = st.tabs(["📊 Market Overview", "🔍 Sector Deep Dive"])

# --- TAB 1: MARKET OVERVIEW (The new "Something like this" view) ---
with tab_overview:
    st.caption("Real-time performance by sector")
    
    sector_summary = []
    
    # Aggregate data for each sector
    for sec_name, sec_tickers in SECTORS.items():
        total_change = 0
        valid_count = 0
        trend_agg = []
        
        # We need to average the trend lines to show a "Sector Trend"
        # This is a bit complex, so we will pick the 'leader' (first ticker) for the sparkline 
        # to keep performance high, or average the scalar change.
        
        first_ticker_history = []
        
        for t in sec_tickers:
            m = get_ticker_metrics(t, live_data, daily_data)
            if m:
                total_change += m['pct_change']
                valid_count += 1
                if not first_ticker_history:
                    first_ticker_history = m['history']

        if valid_count > 0:
            avg_change = total_change / valid_count
            sector_summary.append({
                "Theme / Sector": sec_name,
                "Daily Performance": avg_change / 100, # Divide by 100 for column config %
                "Trend": first_ticker_history # Using leader trend for sparkline visual
            })
    
    df_overview = pd.DataFrame(sector_summary)
    
    if not df_overview.empty:
        # Sort by performance
        df_overview = df_overview.sort_values("Daily Performance", ascending=False)
        
        st.dataframe(
            df_overview,
            column_config={
                "Theme / Sector": st.column_config.TextColumn("Theme / Sector", width="medium"),
                "Trend": st.column_config.LineChartColumn(
                    "Trend (Leader)",
                    y_min=None, 
                    y_max=None,
                    width="small"
                ),
                "Daily Performance": st.column_config.ProgressColumn(
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
        st.info("Market data unavailable. Please refresh.")

# --- TAB 2: SECTOR DEEP DIVE (Detailed view) ---
with tab_analysis:
    # Sector Selection within the tab
    selected_sector = st.pills(
        "Choose Sector", 
        list(SECTORS.keys()), 
        default="Semiconductors",
        selection_mode="single",
        label_visibility="collapsed"
    )

    if selected_sector:
        tickers = SECTORS[selected_sector]
        
        # Process data for table
        table_data = []
        for t in tickers:
            m = get_ticker_metrics(t, live_data, daily_data)
            if m:
                table_data.append({
                    "Ticker": t,
                    "Price": m['price'],
                    "Change %": m['pct_change'],
                    "Volume": m['volume'],
                    "Trend Data": m['history'] # Hidden column for logic
                })
        
        df_table = pd.DataFrame(table_data)
        
        if not df_table.empty:
            # Layout: Master (Table) - Detail (Chart)
            col_list, col_detail = st.columns([1.5, 1])
            
            with col_list:
                st.subheader(f"{selected_sector} Components")
                
                # Interactive DataFrame
                event = st.dataframe(
                    df_table,
                    column_config={
                        "Ticker": st.column_config.TextColumn("Symbol", width="small"),
                        "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                        "Change %": st.column_config.NumberColumn(
                            "Change", 
                            format="%.2f%%",
                            help="Daily percent change"
                        ),
                        "Volume": st.column_config.ProgressColumn(
                            "Vol Intensity",
                            min_value=0,
                            max_value=df_table['Volume'].max(),
                            format="%d",
                        ),
                        "Trend Data": None 
                    },
                    hide_index=True,
                    selection_mode="single-row",
                    on_select="rerun",
                    use_container_width=True,
                    height=500
                )

            with col_detail:
                # Determine which ticker to show
                selected_ticker = tickers[0] # Default to first
                
                # Check if user selected a row
                if len(event.selection.rows) > 0:
                    row_idx = event.selection.rows[0]
                    selected_ticker = df_table.iloc[row_idx]["Ticker"]
                
                # Get details for selected ticker
                m_sel = get_ticker_metrics(selected_ticker, live_data, daily_data)
                
                if m_sel:
                    # Top Stats Card
                    st.markdown(f"""
                    <div style="padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; margin-bottom: 20px; border-left: 4px solid {'#00ff88' if m_sel['pct_change'] > 0 else '#ff0055'}">
                        <h2 style="margin:0; color:white;">{selected_ticker}</h2>
                        <h1 style="margin:0; font-size: 3em;">${m_sel['price']:.2f}</h1>
                        <span style="color: {'#00ff88' if m_sel['pct_change'] > 0 else '#ff0055'}; font-size: 1.2em; font-weight: bold;">
                            {m_sel['pct_change']:+.2f}%
                        </span>
                        <span style="color: #888; margin-left: 10px;">Today's Move</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Chart
                    chart = plot_candle_chart(selected_ticker, live_data)
                    if chart:
                        st.altair_chart(chart, use_container_width=True)
                    
                    # Additional Stats
                    t_daily = daily_data[selected_ticker] if selected_ticker in daily_data else pd.DataFrame()
                    
                    high_52 = t_daily['High'].max() if not t_daily.empty else 0
                    low_52 = t_daily['Low'].min() if not t_daily.empty else 0
                    avg_vol = t_daily['Volume'].mean() if not t_daily.empty else 0
                    
                    # Grid for stats
                    s1, s2, s3 = st.columns(3)
                    s1.metric("52W High", f"${high_52:.0f}")
                    s2.metric("52W Low", f"${low_52:.0f}")
                    s3.metric("Avg Vol", f"{avg_vol/1e6:.1f}M")
                
        else:
            st.info("No data available for this sector.")

# Footer
st.markdown("---")
st.caption("Theme Tracker Pro v2.1 | Built with Streamlit & Altair")
