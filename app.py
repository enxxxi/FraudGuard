import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random


# ============================================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================================
st.set_page_config(page_title="FraudGuard — Fraud Detection Dashboard", layout="wide")

# Custom CSS for dark blue theme
st.markdown("""
<style>
    /* Main background */
    .main { background-color: #0f1419; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #1a2234; }
    
    /* Text colors */
    body { color: #ffffff; }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 { color: #ffffff; }
    
    /* Input fields */
    .stTextInput input, .stSelectbox select, .stMultiSelect { 
        background-color: #2a3d52; 
        color: #ffffff;
    }
    
    /* Cards and containers */
    [data-testid="column"] { background-color: #1a2234; }
    
    /* Dataframe */
    .stDataFrame { background-color: #1a2234; }
</style>
""", unsafe_allow_html=True)

# Sidebar branding
st.sidebar.markdown(
    "<div style='text-align: center; padding: 20px 0;'>"
    "<h2 style='margin: 0; color: #fff; font-size: 24px;'>🛡️ FraudGuard</h2>"
    "<p style='margin: 8px 0; color: #888; font-size: 12px;'>ML FRAUD DETECTION</p>"
    "</div>",
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

# Sidebar navigation with custom styling
st.sidebar.markdown(
    "<p style='color: #888; font-size: 12px; font-weight: bold; margin-left: 15px; margin-bottom: 15px;'>Monitoring</p>", 
    unsafe_allow_html=True
)

# Menu items with icons
menu_items = [
    ("📊 Dashboard", "Dashboard"),
    ("📧 Email Inbox", "Email Inbox"),
    ("📋 Transactions", "Transactions"),
    ("📈 Analytics", "Analytics"),
]

# Create custom radio buttons with styling
page = st.sidebar.radio(
    "Navigate",
    [item[0] for item in menu_items],
    format_func=lambda x: x,
    label_visibility="collapsed",
    key="nav_radio"
)

# Map back to page name
page = [item[1] for item in menu_items if item[0] == page][0]

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; color: #666; font-size: 11px; padding: 10px;'>"
    "v1.0 · rule-based engine"
    "</div>",
    unsafe_allow_html=True
)

# Main content title
st.markdown("<h1 style='color: #ff6b6b;'>🛡️ FraudGuard</h1>", unsafe_allow_html=True)


# ============================================================================
# GENERATE SAMPLE TRANSACTION DATA
# ============================================================================
@st.cache_data
def generate_sample_transactions():
    """Generate simulated bank transactions with fraud indicators."""
    np.random.seed(42)
    transactions = []
    
    # Suspicious transaction patterns
    suspicious_amounts = [850, 2500, 5000, 12000, 3200, 6700]
    suspicious_times = [2, 3, 4, 23, 22, 21]  # late-night hours
    transaction_types = ["Transfer", "Withdrawal", "Purchase", "Wire", "Card Payment", "Cash Advance"]
    locations = ["Downtown ATM", "Online Store", "International", "Local Branch", "ATM Network", "Web Transfer"]
    
    for i in range(25):
        is_suspicious = random.random() < 0.4  # 40% fraud rate in demo
        
        if is_suspicious:
            amount = random.choice(suspicious_amounts)
            hour = random.choice(suspicious_times)
            fraud_label = "HIGH"
        else:
            amount = round(random.uniform(10, 500), 2)
            hour = random.randint(6, 20)
            fraud_label = "LOW"
        
        date = datetime.now() - timedelta(days=random.randint(0, 10))
        date = date.replace(hour=hour, minute=random.randint(0, 59))
        
        fraud_score = np.random.uniform(0.85, 0.99) if is_suspicious else np.random.uniform(0.05, 0.3)
        
        transactions.append({
            "Transaction_ID": f"TXN{1000+i}",
            "Amount": amount,
            "Type": random.choice(transaction_types),
            "Time": date.strftime("%Y-%m-%d %H:%M"),
            "Location": random.choice(locations),
            "Fraud_Score": round(fraud_score, 3),
            "Risk_Level": fraud_label if fraud_score > 0.5 else ("MEDIUM" if fraud_score > 0.3 else "LOW"),
            "Timestamp": date
        })
    
    return pd.DataFrame(transactions).sort_values("Timestamp", ascending=False)


# ============================================================================
# FRAUD DETECTION LOGIC
# ============================================================================
def get_risk_level_color(risk):
    """Return color code for risk level."""
    if risk == "HIGH":
        return "#ff6b6b"
    elif risk == "MEDIUM":
        return "#ffd93d"
    else:
        return "#51cf66"


def get_fraud_reasons(amount, hour, transaction_type):
    """Generate explainable fraud reasons."""
    reasons = []
    
    if amount > 5000:
        reasons.append("⚠️ Unusually high transaction amount")
    if hour in [2, 3, 4, 23, 22, 21]:
        reasons.append("⚠️ Suspicious late-night transfer")
    if transaction_type in ["Wire", "International"]:
        reasons.append("⚠️ High-risk transaction type")
    if hour < 6:
        reasons.append("⚠️ Abnormal spending behavior")
    
    if not reasons:
        reasons.append("✓ Transaction appears normal")
    
    return reasons


# ============================================================================
# LOAD DATA
# ============================================================================
df_transactions = generate_sample_transactions()

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================
if page == "Dashboard":
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    high_risk_count = len(df_transactions[df_transactions["Risk_Level"] == "HIGH"])
    total_transactions = len(df_transactions)
    avg_fraud_score = df_transactions["Fraud_Score"].mean()
    flagged_today = df_transactions[
        df_transactions["Timestamp"] >= datetime.now() - timedelta(days=1)
    ].shape[0]
    
    with col1:
        st.metric("🚨 High-Risk Alerts", high_risk_count, f"{(high_risk_count/total_transactions*100):.1f}%")
    with col2:
        st.metric("📊 Total Monitored", total_transactions, "transactions")
    with col3:
        st.metric("📉 Avg. Fraud Score", f"{avg_fraud_score:.2%}", "probability")
    with col4:
        st.metric("📅 Flagged Today", flagged_today, "alerts")
    
    st.markdown("---")
    st.subheader("⚠️ Critical Alerts (Last 5)")
    
    high_risk_txns = df_transactions[df_transactions["Risk_Level"] == "HIGH"].head(5)
    for idx, row in high_risk_txns.iterrows():
        with st.container(border=True):
            col_alert1, col_alert2, col_alert3 = st.columns([2, 2, 1])
            with col_alert1:
                st.write(f"**{row['Transaction_ID']}** • {row['Type']}")
                st.write(f"Amount: **₹{row['Amount']:,.2f}** at {row['Time']}")
            with col_alert2:
                st.write(f"📍 {row['Location']}")
                reasons = get_fraud_reasons(row['Amount'], int(row['Time'].split()[1].split(":")[0]), row['Type'])
                for reason in reasons[:2]:
                    st.write(reason)
            with col_alert3:
                st.metric("Risk", row["Risk_Level"], f"{row['Fraud_Score']:.1%}")


# ============================================================================
# PAGE: EMAIL INBOX
# ============================================================================
elif page == "Email Inbox":
    st.markdown("---")
    st.subheader("📨 Bank Email Notifications")
    
    # Filter options
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        risk_filter = st.multiselect(
            "Filter by Risk Level",
            ["HIGH", "MEDIUM", "LOW"],
            default=["HIGH", "MEDIUM", "LOW"]
        )
    with col_filter2:
        hours_back = st.slider("Hours back", 1, 240, 24)
    
    filtered_df = df_transactions[
        (df_transactions["Risk_Level"].isin(risk_filter)) &
        (df_transactions["Timestamp"] >= datetime.now() - timedelta(hours=hours_back))
    ]
    
    st.write(f"**Showing {len(filtered_df)} transactions**")
    
    for idx, row in filtered_df.iterrows():
        risk_color = get_risk_level_color(row["Risk_Level"])
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"### 📧 Email Notification")
                st.write(f"**Transaction ID:** {row['Transaction_ID']}")
                st.write(f"**Message:** ₹{row['Amount']:,.2f} transferred via {row['Type']} at {row['Time']}")
            
            with col2:
                st.markdown("### 📊 Risk Analysis")
                for reason in get_fraud_reasons(row['Amount'], int(row['Time'].split()[1].split(":")[0]), row['Type']):
                    st.write(reason)
            
            with col3:
                st.markdown("### 🎯 Prediction")
                st.metric("Risk Level", row["Risk_Level"], f"{row['Fraud_Score']:.1%}")
                if row["Risk_Level"] == "HIGH":
                    st.warning("⚠️ Needs Review")
                elif row["Risk_Level"] == "MEDIUM":
                    st.info("ℹ️ Monitor")


# ============================================================================
# PAGE: TRANSACTIONS
# ============================================================================
elif page == "Transactions":
    st.markdown("---")
    st.subheader("🔍 Detailed Transaction Analysis")
    
    # Display transaction table
    display_df = df_transactions[[
        "Transaction_ID", "Amount", "Type", "Time", "Location", "Fraud_Score", "Risk_Level"
    ]].copy()
    
    display_df["Fraud_Score"] = display_df["Fraud_Score"].apply(lambda x: f"{x:.1%}")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Risk distribution
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        risk_counts = df_transactions["Risk_Level"].value_counts()
        fig_risk = go.Figure(data=[go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            marker=dict(colors=["#ff6b6b", "#ffd93d", "#51cf66"])
        )])
        fig_risk.update_layout(title="Risk Level Distribution")
        st.plotly_chart(fig_risk, use_container_width=True)
    
    with col2:
        # Amount distribution by risk
        fig_amount = px.box(
            df_transactions,
            y="Amount",
            color="Risk_Level",
            title="Transaction Amount by Risk Level",
            color_discrete_map={"HIGH": "#ff6b6b", "MEDIUM": "#ffd93d", "LOW": "#51cf66"}
        )
        st.plotly_chart(fig_amount, use_container_width=True)


# ============================================================================
# PAGE: ANALYTICS
# ============================================================================
elif page == "📈 Analytics":
    st.markdown("---")
    st.subheader("📊 Fraud Detection Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Fraud score distribution
        fig_score_dist = px.histogram(
            df_transactions,
            x="Fraud_Score",
            nbins=20,
            title="Fraud Score Distribution",
            labels={"Fraud_Score": "Fraud Probability Score"}
        )
        fig_score_dist.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Threshold")
        st.plotly_chart(fig_score_dist, use_container_width=True)
    
    with col2:
        # Transaction type risk heatmap
        type_risk = df_transactions.groupby("Type")["Fraud_Score"].mean().sort_values(ascending=False)
        fig_type = px.bar(
            x=type_risk.values,
            y=type_risk.index,
            orientation="h",
            title="Average Fraud Score by Transaction Type",
            labels={"x": "Avg Fraud Score", "y": "Transaction Type"}
        )
        st.plotly_chart(fig_type, use_container_width=True)
    
    # Fraud score trends over time
    st.markdown("---")
    df_sorted = df_transactions.sort_values("Timestamp")
    fig_trend = px.scatter(
        df_sorted,
        x="Timestamp",
        y="Fraud_Score",
        color="Risk_Level",
        size="Amount",
        hover_data=["Amount", "Type"],
        title="Fraud Score Trends Over Time",
        color_discrete_map={"HIGH": "#ff6b6b", "MEDIUM": "#ffd93d", "LOW": "#51cf66"}
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Summary statistics
    st.markdown("---")
    st.subheader("📉 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "High-Risk %",
            f"{(len(df_transactions[df_transactions['Risk_Level'] == 'HIGH']) / len(df_transactions) * 100):.1f}%"
        )
    with col2:
        st.metric("Avg. Amount (High-Risk)", f"₹{df_transactions[df_transactions['Risk_Level'] == 'HIGH']['Amount'].mean():,.2f}")
    with col3:
        st.metric("Max Fraud Score", f"{df_transactions['Fraud_Score'].max():.1%}")
    with col4:
        st.metric("Total Amount Monitored", f"₹{df_transactions['Amount'].sum():,.2f}")


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 12px;'>"
    "FraudGuard v1.0 — ML-Powered Fraud Detection | Data as of today's simulation"
    "</div>",
    unsafe_allow_html=True
)
