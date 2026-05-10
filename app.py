import streamlit as st
import pandas as pd
import plotly.express as px
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# ---------------------------------------------------
# 0. ALPHA_SOC CONFIG & SYSTEM CSS
# ---------------------------------------------------
st.set_page_config(
    page_title="Shadow's Trade Ledger",
    layout="wide",
    page_icon="⚡"
)

# Custom Glassmorphism UI
st.markdown("""
<style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    .stMetric { 
        background: rgba(255, 255, 255, 0.03); 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid rgba(0, 255, 204, 0.15);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
    }
    .stButton>button {
        width: 100%;
        background-color: #00ffcc !important;
        color: #000000 !important;
        font-weight: bold;
        border: none;
    }
    [data-testid="stSidebar"] { background-color: #0e1117; border-right: 1px solid #1e2127; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 1. CLOUD DATABASE ENGINE
# ---------------------------------------------------
conn = st.connection("supabase", type=SupabaseConnection)

def load_data():
    try:
        response = conn.client.table("trading_ledger").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception:
        st.error("Uplink Failure: Could not reach Supabase. Check Secrets.")
        return pd.DataFrame()

def save_trade(trade_dict):
    try:
        conn.client.table("trading_ledger").insert(trade_dict).execute()
        return True
    except Exception as e:
        st.error(f"Write Access Denied: {e}")
        return False

def delete_trade(trade_id):
    try:
        conn.client.table("trading_ledger").delete().eq("id", trade_id).execute()
        return True
    except Exception as e:
        st.error(f"Deletion Failed: {e}")
        return False

# ---------------------------------------------------
# 2. OPERATIONAL FILTERS (SIDEBAR)
# ---------------------------------------------------
st.sidebar.title("🕹️ SOC_FILTERS")
raw_df = load_data()

if not raw_df.empty:
    # Asset Filter
    tickers = sorted(raw_df["ticker"].unique().tolist())
    selected_tickers = st.sidebar.multiselect("Asset Focus", tickers, default=tickers)
    
    # Strategy Filter
    strategies = sorted(raw_df["strategy"].unique().tolist())
    selected_strats = st.sidebar.multiselect("Tactical Focus", strategies, default=strategies)
    
    # Filter Logic
    df = raw_df[
        (raw_df["ticker"].isin(selected_tickers)) & 
        (raw_df["strategy"].isin(selected_strats))
    ]
else:
    df = raw_df

# ---------------------------------------------------
# 3. INTERFACE HEADER
# ---------------------------------------------------
st.title("⚡ Shadow's Trade Ledger")
t1, t2, t3, t4 = st.tabs(["📊 Analytics", "📥 Entry", "🧮 Risk", "🛠️ Maintenance"])

# ===================================================
# TAB 1 — ANALYTICS DASHBOARD
# ===================================================
with t1:
    if not df.empty:
        # KPI Calculation
        total_pl = df["net_pl"].sum()
        wins = df[df["status"] == "Win"]["net_pl"].sum()
        losses = abs(df[df["status"] == "Loss"]["net_pl"].sum())
        profit_factor = wins / losses if losses != 0 else wins
        win_rate = (len(df[df["status"] == "Win"]) / len(df)) * 100
        avg_r = df["r_multiple"].mean()

        # Metric Display
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
            fig.add_hline(y=0, line_dash="dash", line_color="#ff4b4b", opacity=0.6)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("AI Performance Review")
            # Discipline Analysis
            discipline_count = len(df[df["followed_plan"] == "Yes"])
            discipline_score = (discipline_count / len(df)) * 100
            
            if discipline_score > 80:
                st.success(f"**Discipline: {discipline_score:.0f}%**\nExecution is optimal. You are trading the plan, not the P/L.")
            elif discipline_score > 50:
                st.warning(f"**Discipline: {discipline_score:.0f}%**\nDeviation detected. Emotional leaks are impacting the edge.")
            else:
                st.error(f"**Discipline: {discipline_score:.0f}%**\nCRITICAL: Gambling behavior detected. Reset required.")

            # Psychological Dominance
            top_emo = df["emotion"].mode()[0]
            st.info(f"**Dominant State:** {top_emo}")

        st.subheader("📜 Detailed Operational Ledger")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("System Standby. No data found for selected filters.")

# ===================================================
# TAB 2 — OPERATION ENTRY
# ===================================================
with t2:
    st.subheader("Log New Operation")
    with st.form("entry_form"):
        c1, c2, c3 = st.columns(3)
        date = c1.date_input("Operation Date")
        ticker = c2.text_input("Ticker", placeholder="SUIUSDT.P")
        platform = c3.selectbox("Source", ["Kraken", "MEXC", "Trading212", "Binance"])

        c4, c5, c6 = st.columns(3)
        strategy = c4.selectbox("Tactical Protocol", ["Scalping", "Breakout", "Trend Following", "ICT/SMC"])
        t_side = c5.radio("Side", ["Long", "Short"], horizontal=True)
        emotion = c6.select_slider("Emotional State", options=["Fear", "Anxious", "Neutral", "Calm", "Greed"])

        c7, c8, c9, c10 = st.columns(4)
        qty = c7.number_input("Quantity (Units)", value=1.0, step=0.1)
        entry = c8.number_input("Entry Price", format="%.4f", step=0.0001)
        stop = c9.number_input("Stop Loss", format="%.4f", step=0.0001)
        exit_p = c10.number_input("Exit Price", format="%.4f", step=0.0001)

        fees = st.number_input("Fees ($)", value=0.10)
        plan = st.selectbox("Protocol Adherence?", ["Yes", "Partially", "No - FOMO", "No - Revenge"])

        if st.form_submit_button("COMMIT TO CLOUD"):
            # Calculation Logic
            if t_side == "Long":
                net_pl = ((exit_p - entry) * qty) - fees
                r_mult = (exit_p - entry) / abs(entry - stop) if entry != stop else 0
            else:
                net_pl = ((entry - exit_p) * qty) - fees
                r_mult = (entry - exit_p) / abs(stop - entry) if entry != stop else 0

            status = "Win" if net_pl > 0 else "Loss" if net_pl < 0 else "Break-even"

            payload = {
                "date": str(date), "ticker": ticker, "platform": platform, "strategy": strategy,
                "type": t_side, "entry_price": entry, "stop_loss": stop, "exit_price": exit_p,
                "quantity": qty, "fees": fees, "net_pl": net_pl, "r_multiple": r_mult,
                "status": status, "followed_plan": plan, "emotion": emotion
            }

            if save_trade(payload):
                st.success("Entry Secured.")
                st.rerun()

# ===================================================
# TAB 3 — RISK CALCULATOR
# ===================================================
with t3:
    st.subheader("🧮 Tactical Position Sizing")
    ca, cb = st.columns(2)
    acc_size = ca.number_input("War Chest ($)", value=100.0)
    risk_pct = ca.slider("Risk Exposure (%)", 0.5, 5.0, 1.0)
    
    e_calc = cb.number_input("Planned Entry Target", value=1.0000, format="%.4f")
    s_calc = cb.number_input("Planned Stop Floor", value=0.9500, format="%.4f")

    risk_usd = acc_size * (risk_pct / 100)
    dist = abs(e_calc - s_calc)
    
    if dist > 0:
        recommended_q = risk_usd / dist
        st.success(f"**Target Quantity:** {recommended_q:.2f} Units")
        st.info(f"**Cash at Risk:** ${risk_usd:.2f}")
    else:
        st.warning("Stop Loss cannot equal entry price.")

# ===================================================
# TAB 4 — MAINTENANCE (PURGE)
# ===================================================
with t4:
    st.subheader("🛠️ Operational Maintenance")
    st.info("Retrieve the entry ID from the Analytics tab to purge.")
    
    # Security Gate
    with st.expander("🔐 Authorize Purge Protocol"):
        auth_pass = st.text_input("Admin Auth Code", type="password")
        if auth_pass == "12911Abc_@#":
            del_id = st.number_input("ID to Purge", step=1, value=0)
            if st.button("EXECUTE PERMANENT WIPE"):
                if del_id > 0:
                    if delete_trade(del_id):
                        st.success(f"Trade {del_id} wiped from Cloud.")
                        st.rerun()
                else:
                    st.error("Invalid ID.")
        elif auth_pass:
            st.error("Authentication Failure.")
