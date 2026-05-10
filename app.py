import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import numpy as np
from st_supabase_connection import SupabaseConnection

# --- 1. SETTINGS & MODERN CSS ---
st.set_page_config(page_title="ALPHA_SOC_TRADING", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .stMetric { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid rgba(0, 255, 204, 0.2);
    }
    .stButton>button {
        width: 100%;
        background-color: #00ffcc !important;
        color: black !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "trading_data_v2.csv"


# Initialize secure connection to Cloud Database
conn = st.connection("supabase", type=SupabaseConnection)

# --- 2. DATA ENGINE ---
from st_supabase_connection import SupabaseConnection

# Initialize secure connection to Cloud Database
conn = st.connection("supabase", type=SupabaseConnection)

def load_data():
    # Fetch all rows directly using the native Supabase client
    response = conn.client.table("trading_ledger").select("*").execute()
    
    # Check if there is data
    if response.data:
        return pd.DataFrame(response.data)
        
    # Return empty template if database is empty/new
    return pd.DataFrame(columns=[
        "date", "ticker", "platform", "strategy", "type", "entry_price", 
        "stop_loss", "exit_price", "fees", "net_pl", "r_multiple", 
        "status", "followed_plan", "emotion"
    ])

def save_trade(trade_dict):
    # Push new trade directly to Supabase cloud
    conn.client.table("trading_ledger").insert(trade_dict).execute()

# --- 3. THE INTERFACE ---
st.title("⚡ ALPHA_SOC // TRADING OPERATIONS")

tab1, tab2, tab3 = st.tabs(["📊 Analytics Dashboard", "📥 Log Operation", "🧮 Risk Calculator"])

# --- TAB 1: ANALYTICS ---
with tab1:
    df = load_data()
    if not df.empty:
        # Advanced Math
        total_pl = df['Net_PL'].sum()
        wins = df[df['Status'] == 'Win']['Net_PL'].sum()
        losses = abs(df[df['Status'] == 'Loss']['Net_PL'].sum())
        profit_factor = wins / losses if losses != 0 else wins
        win_rate = (len(df[df['Status'] == 'Win']) / len(df)) * 100

        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TOTAL NET P/L", f"${total_pl:.2f}", delta=f"{total_pl:.2f}")
        m2.metric("WIN RATE", f"{win_rate:.1f}%")
        m3.metric("PROFIT FACTOR", f"{profit_factor:.2f}")
        m4.metric("AVG R-MULTIPLE", f"{df['R_Multiple'].mean():.2f}R")

        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Equity Curve (Accumulated Alpha)")
            df['Equity'] = df['Net_PL'].cumsum()
            fig = px.area(df, x=df.index, y='Equity', template="plotly_dark")
            fig.update_traces(line_color='#00ffcc', fillcolor='rgba(0, 255, 204, 0.1)')
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Strategy Efficiency")
            strat_perf = df.groupby('Strategy')['Net_PL'].sum().reset_index()
            fig_bar = px.bar(strat_perf, x='Strategy', y='Net_PL', template="plotly_dark", color='Net_PL')
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("📜 Operation History")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("System Standby. No operation data detected.")

# --- TAB 2: LOGGING ---
with tab2:
    st.subheader("Log New High-Volatility Operation")
    with st.form("advanced_form"):
        c1, c2, c3 = st.columns(3)
        date = c1.date_input("Operation Date")
        ticker = c2.text_input("Ticker (e.g. SUIUSDT.P)")
        platform = c3.selectbox("Platform", ["Kraken", "MEXC", "Trading212", "Binance"])

        c4, c5, c6 = st.columns(3)
        strategy = c4.selectbox("Strategy", ["Scalping", "Breakout", "Trend Following", "ICT/SMC"])
        t_type = c5.radio("Type", ["Long", "Short"], horizontal=True)
        emotion = c6.select_slider("Entry Emotion", options=["Fear", "Anxious", "Neutral", "Calm", "Greed"])

        c7, c8, c9, c10 = st.columns(4)
        entry = c7.number_input("Entry Price", step=0.0001, format="%.4f")
        stop = c8.number_input("Stop Loss", step=0.0001, format="%.4f")
        exit_p = c9.number_input("Exit Price", step=0.0001, format="%.4f")
        fees = c10.number_input("Fees ($)", value=0.10)

        plan = st.selectbox("Did you follow the plan?", ["Yes", "Partially", "No - FOMO", "No - Revenge Trade"])

        if st.form_submit_button("COMMIT OPERATION TO LEDGER"):
            # Logic
            if t_type == "Long":
                net_pl = (exit_p - entry) * 100 - fees  # Example unit multiplier
                r_mult = (exit_p - entry) / (entry - stop) if entry != stop else 0
            else:
                net_pl = (entry - exit_p) * 100 - fees
                r_mult = (entry - exit_p) / (stop - entry) if entry != stop else 0

            status = "Win" if net_pl > 0 else "Loss" if net_pl < 0 else "Break-even"

            save_trade({
                "Date": date, "Ticker": ticker, "Platform": platform, "Strategy": strategy,
                "Type": t_type, "Entry": entry, "StopLoss": stop, "Exit": exit_p,
                "Fees": fees, "Net_PL": net_pl, "R_Multiple": r_mult, "Status": status,
                "Followed_Plan": plan, "Emotion": emotion
            })
            st.rerun()

# --- TAB 3: RISK CALCULATOR ---
with tab3:
    st.subheader("🧮 Position Sizing (Pre-Trade)")
    col_a, col_b = st.columns(2)

    account_size = col_a.number_input("Account Balance ($)", value=100.0)
    risk_percent = col_a.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

    entry_calc = col_b.number_input("Planned Entry", value=1.0000, format="%.4f")
    stop_calc = col_b.number_input("Planned Stop", value=0.9500, format="%.4f")

    risk_amount = account_size * (risk_percent / 100)
    distance = abs(entry_calc - stop_calc)

    if distance > 0:
        pos_size = risk_amount / distance
        st.success(f"**Recommended Position Size:** {pos_size:.2f} units")
        st.info(f"**Total Risk Amount:** ${risk_amount:.2f}")
    else:
        st.warning("Set a Stop Loss to calculate position size.")
