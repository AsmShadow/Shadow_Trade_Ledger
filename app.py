import streamlit as st
import pandas as pd
import plotly.express as px
from st_supabase_connection import SupabaseConnection

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="ALPHA_SOC_TRADING",
    layout="wide",
    page_icon="⚡"
)

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------

st.markdown("""
<style>
.main {
    background-color: #0b0e14;
}

.stMetric {
    background: rgba(255, 255, 255, 0.05);
    padding: 15px;
    border-radius: 10px;
    border: 1px solid rgba(0, 255, 204, 0.2);
}

.stButton > button {
    width: 100%;
    background-color: #00ffcc !important;
    color: black !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SUPABASE CONNECTION
# ---------------------------------------------------

conn = st.connection("supabase", type=SupabaseConnection)

# ---------------------------------------------------
# DATABASE FUNCTIONS
# ---------------------------------------------------

def load_data():
    try:
        response = (
            conn.client
            .table("trading_ledger")
            .select("*")
            .execute()
        )

        if response.data:
            df = pd.DataFrame(response.data)
            return df

        return pd.DataFrame()

    except Exception as e:
        st.error("Database connection failed.")
        st.exception(e)
        return pd.DataFrame()


def save_trade(trade_dict):
    try:
        conn.client.table("trading_ledger").insert(trade_dict).execute()
        return True

    except Exception as e:
        st.error("Failed to save trade.")
        st.exception(e)
        return False

# ---------------------------------------------------
# UI HEADER
# ---------------------------------------------------

st.title("⚡ ALPHA_SOC // TRADING OPERATIONS")

tab1, tab2, tab3 = st.tabs([
    "📊 Analytics Dashboard",
    "📥 Log Operation",
    "🧮 Risk Calculator"
])

# ===================================================
# TAB 1 — ANALYTICS
# ===================================================

with tab1:

    df = load_data()

    if not df.empty:

        # -------------------------
        # METRICS
        # -------------------------

        total_pl = df["net_pl"].sum()

        wins = df[df["status"] == "Win"]["net_pl"].sum()

        losses = abs(
            df[df["status"] == "Loss"]["net_pl"].sum()
        )

        profit_factor = (
            wins / losses if losses != 0 else wins
        )

        win_rate = (
            len(df[df["status"] == "Win"]) / len(df)
        ) * 100

        avg_r = df["r_multiple"].mean()

        # -------------------------
        # METRIC CARDS
        # -------------------------

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "TOTAL NET P/L",
            f"${total_pl:.2f}"
        )

        m2.metric(
            "WIN RATE",
            f"{win_rate:.1f}%"
        )

        m3.metric(
            "PROFIT FACTOR",
            f"{profit_factor:.2f}"
        )

        m4.metric(
            "AVG R-MULTIPLE",
            f"{avg_r:.2f}R"
        )

        # -------------------------
        # CHARTS
        # -------------------------

        col_left, col_right = st.columns([2, 1])

        with col_left:

            st.subheader("Equity Curve")

            df["equity"] = df["net_pl"].cumsum()

            fig = px.area(
                df,
                x=df.index,
                y="equity",
                template="plotly_dark"
            )

            fig.update_traces(
                line_color="#00ffcc",
                fillcolor="rgba(0,255,204,0.1)"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with col_right:

            st.subheader("Strategy Performance")

            strat_perf = (
                df.groupby("strategy")["net_pl"]
                .sum()
                .reset_index()
            )

            fig_bar = px.bar(
                strat_perf,
                x="strategy",
                y="net_pl",
                template="plotly_dark",
                color="net_pl"
            )

            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )

        # -------------------------
        # TABLE
        # -------------------------

        st.subheader("📜 Trade History")

        st.dataframe(
            df.sort_index(ascending=False),
            use_container_width=True
        )

    else:
        st.info("No trading data found.")

# ===================================================
# TAB 2 — LOG TRADE
# ===================================================

with tab2:

    st.subheader("Log New Trade")

    with st.form("trade_form"):

        c1, c2, c3 = st.columns(3)

        date = c1.date_input("Trade Date")

        ticker = c2.text_input("Ticker")

        platform = c3.selectbox(
            "Platform",
            ["Kraken", "MEXC", "Trading212", "Binance"]
        )

        c4, c5, c6 = st.columns(3)

        strategy = c4.selectbox(
            "Strategy",
            [
                "Scalping",
                "Breakout",
                "Trend Following",
                "ICT/SMC"
            ]
        )

        t_type = c5.radio(
            "Type",
            ["Long", "Short"],
            horizontal=True
        )

        emotion = c6.select_slider(
            "Emotion",
            options=[
                "Fear",
                "Anxious",
                "Neutral",
                "Calm",
                "Greed"
            ]
        )

        c7, c8, c9, c10 = st.columns(4)

        entry = c7.number_input(
            "Entry Price",
            step=0.0001,
            format="%.4f"
        )

        stop = c8.number_input(
            "Stop Loss",
            step=0.0001,
            format="%.4f"
        )

        exit_price = c9.number_input(
            "Exit Price",
            step=0.0001,
            format="%.4f"
        )

        fees = c10.number_input(
            "Fees",
            value=0.10
        )

        plan = st.selectbox(
            "Followed Plan?",
            [
                "Yes",
                "Partially",
                "No - FOMO",
                "No - Revenge Trade"
            ]
        )

        submitted = st.form_submit_button(
            "COMMIT OPERATION TO LEDGER"
        )

        if submitted:

            # -----------------------------------
            # TRADE CALCULATIONS
            # -----------------------------------

            if t_type == "Long":

                net_pl = (
                    (exit_price - entry) * 100
                ) - fees

                r_multiple = (
                    (exit_price - entry)
                    / (entry - stop)
                    if entry != stop else 0
                )

            else:

                net_pl = (
                    (entry - exit_price) * 100
                ) - fees

                r_multiple = (
                    (entry - exit_price)
                    / (stop - entry)
                    if entry != stop else 0
                )

            # -----------------------------------
            # STATUS
            # -----------------------------------

            if net_pl > 0:
                status = "Win"

            elif net_pl < 0:
                status = "Loss"

            else:
                status = "Break-even"

            # -----------------------------------
            # SAVE TO DATABASE
            # -----------------------------------

            trade_data = {
                "date": str(date),
                "ticker": ticker,
                "platform": platform,
                "strategy": strategy,
                "type": t_type,
                "entry_price": entry,
                "stop_loss": stop,
                "exit_price": exit_price,
                "fees": fees,
                "net_pl": net_pl,
                "r_multiple": r_multiple,
                "status": status,
                "followed_plan": plan,
                "emotion": emotion
            }

            success = save_trade(trade_data)

            if success:
                st.success("Trade logged successfully.")
                st.rerun()

# ===================================================
# TAB 3 — RISK CALCULATOR
# ===================================================

with tab3:

    st.subheader("🧮 Position Size Calculator")

    col_a, col_b = st.columns(2)

    account_size = col_a.number_input(
        "Account Balance ($)",
        value=100.0
    )

    risk_percent = col_a.slider(
        "Risk per Trade (%)",
        0.5,
        5.0,
        1.0
    )

    entry_calc = col_b.number_input(
        "Planned Entry",
        value=1.0000,
        format="%.4f"
    )

    stop_calc = col_b.number_input(
        "Planned Stop",
        value=0.9500,
        format="%.4f"
    )

    risk_amount = (
        account_size * (risk_percent / 100)
    )

    distance = abs(entry_calc - stop_calc)

    if distance > 0:

        position_size = risk_amount / distance

        st.success(
            f"Recommended Position Size: {position_size:.2f} units"
        )

        st.info(
            f"Total Risk Amount: ${risk_amount:.2f}"
        )

    else:
        st.warning(
            "Stop loss must not equal entry price."
        )
