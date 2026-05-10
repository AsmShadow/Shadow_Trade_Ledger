import streamlit as st
import pandas as pd
import plotly.express as px
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# ---------------------------------------------------
# PAGE CONFIG & THEME
# ---------------------------------------------------
st.set_page_config(page_title="ALPHA_SOC_V4", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .main { background-color: #0b0e14; }
    .stMetric { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; border-radius: 10px; 
        border: 1px solid rgba(0, 255, 204, 0.2); 
    }
    .stButton>button {
        width: 100%; background-color: #00ffcc !important;
        color: black !important; font-weight: bold;
    }
    [data-testid="stSidebar"] { background-color: #0e1117; border-right: 1px solid #1e2127; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------
conn = st.connection("supabase", type=SupabaseConnection)

def load_data():
    try:
        response = conn.client.table("trading_ledger").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error("Terminal Connection Lost. Check Supabase Link.")
        return pd.DataFrame()

def save_trade(trade_dict):
    try:
        conn.client.table("trading_ledger").insert(trade_dict).execute()
        return True
    except Exception as e:
        st.error(f"Write Access Denied: {e}")
        return False

# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------
st.sidebar.title("🕹️ SOC_FILTERS")
raw_df = load_data()

if not raw_df.empty:
    all_tickers = raw_df["ticker"].unique().tolist()
    selected_tickers = st.sidebar.multiselect("Asset Focus", all_tickers, default=all_tickers)
    df = raw_df[raw_df["ticker"].isin(selected_tickers)]
else:
    df = raw_df

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.title("⚡ ALPHA_SOC // OPERATIONAL COMMAND")
tab1, tab2, tab3 = st.tabs(["📊 Analytics", "📥 Entry", "🧮 Risk"])

# ===================================================
# TAB 1 — ANALYTICS
# ===================================================
with tab1:
    if not df.empty:
        # Calculations
        total_pl = df["net_pl"].sum()
        wins = df[df["status"] == "Win"]["net_pl"].sum()
        losses = abs(df[df["status"] == "Loss"]["net_pl"].sum())
        profit_factor = wins / losses if losses != 0 else wins
        win_rate = (len(df[df["status"] == "Win"]) / len(df)) * 100
        avg_r = df["r_multiple"].mean()

        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("NET ALPHA", f"${total_pl:.2f}", delta=f"{total_pl:.2f}")
        m2.metric("WIN RATE", f"{win_rate:.1f}%", delta=f"{win_rate-50:.1f}%" if win_rate != 50 else None)
        m3.metric("PROFIT FACTOR", f"{profit_factor:.2f}")
        m4.metric("AVG RISK_REWARD", f"{avg_r:.2f}R")

        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Equity Trajectory")
            df["equity"] = df["net_pl"].cumsum()
            fig = px.area(df, x=df.index, y="equity", template="plotly_dark")
            fig.update_traces(line_color="#00ffcc", fillcolor="rgba(0,255,204,0.1)")
            fig.add_hline(y=0, line_dash="dash", line_color="#ff4b4b", opacity=0.5)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("AI Operational Review")
            # Logic-based analysis of your discipline
            discipline_score = (len(df[df["followed_plan"] == "Yes"]) / len(df)) * 100
            
            if discipline_score > 80:
                st.success(f"**Discipline: {discipline_score:.0f}%**\nExecution is optimal. You are trading the plan, not the P/L.")
            elif discipline_score > 50:
                st.warning(f"**Discipline: {discipline_score:.0f}%**\nDeviation detected. Emotional leaks (FOMO/Revenge) are impacting the edge.")
            else:
                st.error(f"**Discipline: {discipline_score:.0f}%**\nCRITICAL: You are gambling. Stop trading until discipline is restored.")

            # Top Emotion Analysis
            top_emotion = df["emotion"].mode()[0]
            st.info(f"**Dominant State:** {top_emotion}")

        st.subheader("📜 Detailed Ledger")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("System Standby. Awaiting first operational input.")

# ===================================================
# TAB 2 — LOG TRADE
# ===================================================
with tab2:
    st.subheader("Manual Data Uplink")
    with st.form("trade_form"):
        c1, c2, c3 = st.columns(3)
        date = c1.date_input("Date")
        ticker = c2.text_input("Ticker (e.g. SUIUSDT.P)")
        platform = c3.selectbox("Source Platform", ["Kraken", "MEXC", "Trading212", "Binance"])

        c4, c5, c6 = st.columns(3)
        strategy = c4.selectbox("Tactical Strategy", ["Scalping", "Breakout", "Trend Following", "ICT/SMC"])
        t_type = c5.radio("Side", ["Long", "Short"], horizontal=True)
        emotion = c6.select_slider("State of Mind", options=["Fear", "Anxious", "Neutral", "Calm", "Greed"])

        c7, c8, c9, c10 = st.columns(4)
        quantity = c7.number_input("Units/Quantity", value=1.0, step=0.1)
        entry = c8.number_input("Entry", step=0.0001, format="%.4f")
        stop = c9.number_input("Stop Loss", step=0.0001, format="%.4f")
        exit_price = c10.number_input("Exit Price", step=0.0001, format="%.4f")

        fees = st.number_input("Operational Fees", value=0.10)
        plan = st.selectbox("Protocol Adherence?", ["Yes", "Partially", "No - FOMO", "No - Revenge Trade"])

        if st.form_submit_button("COMMIT TO CLOUD"):
            # Math Logic
            if t_type == "Long":
                net_pl = ((exit_price - entry) * quantity) - fees
                r_multiple = (exit_price - entry) / abs(entry - stop) if entry != stop else 0
            else:
                net_pl = ((entry - exit_price) * quantity) - fees
                r_multiple = (entry - exit_price) / abs(stop - entry) if entry != stop else 0

            status = "Win" if net_pl > 0 else "Loss" if net_pl < 0 else "Break-even"

            trade_data = {
                "date": str(date), "ticker": ticker, "platform": platform, "strategy": strategy,
                "type": t_type, "entry_price": entry, "stop_loss": stop, "exit_price": exit_price,
                "quantity": quantity, "fees": fees, "net_pl": net_pl, "r_multiple": r_multiple,
                "status": status, "followed_plan": plan, "emotion": emotion
            }

            if save_trade(trade_data):
                st.success("Operation Logged.")
                st.rerun()

# ===================================================
# TAB 3 — RISK CALCULATOR
# ===================================================
with tab3:
    st.subheader("🧮 Tactical Planning")
    ca, cb = st.columns(2)
    acc_size = ca.number_input("War Chest ($)", value=100.0)
    risk_pct = ca.slider("Risk Exposure (%)", 0.5, 5.0, 1.0)
    e_calc = cb.number_input("Planned Entry ", value=1.0000, format="%.4f")
    s_calc = cb.number_input("Planned Stop ", value=0.9500, format="%.4f")

    risk_usd = acc_size * (risk_pct / 100)
    dist = abs(e_calc - s_calc)
    
    if dist > 0:
        recommended_q = risk_usd / dist
        st.success(f"**Loadout:** {recommended_q:.2f} Units")
        st.info(f"**Exposure:** ${risk_usd:.2f}")
    else:
        st.warning("Define operational floor (Stop Loss).")
