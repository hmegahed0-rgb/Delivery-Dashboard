import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Courier Control Tower",
    layout="wide"
)

st.title("🚚 Courier Operations Control Tower (Enterprise v4)")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv("clean_courier_kpi.csv")
    return df

df = load_data()

st.success("Data Loaded Successfully ✅")

# =========================
# SIDEBAR FILTER
# =========================
courier = st.sidebar.selectbox(
    "👤 Select Courier",
    df["Courier ID"].unique()
)

user_data = df[df["Courier ID"] == courier]

# =========================
# KPI CARDS
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.metric("📦 Total Deliveries", int(user_data["Total_Deliveries"].sum()))
col2.metric("⏰ Before 12 %", f'{user_data["Before12_Rate"].values[0]:.2f}%')
col3.metric("🔴 Exception %", f'{user_data["Exception_Rate"].values[0]:.2f}%')

# AI SCORE (simple model)
score = (
    user_data["Before12_Rate"].values[0] * 0.6
    + (100 - user_data["Exception_Rate"].values[0]) * 0.4
)

col4.metric("🏆 AI Score", f"{score:.1f}")

# =========================
# RANKING TABLE
# =========================
st.subheader("🏆 Courier Ranking")

df["Score"] = (
    df["Before12_Rate"] * 0.6 +
    (100 - df["Exception_Rate"]) * 0.4
)

ranking = df.sort_values("Score", ascending=False)

st.dataframe(ranking[[
    "Courier ID",
    "Total_Deliveries",
    "Before12_Rate",
    "Exception_Rate",
    "Score"
]])

# =========================
# CHART 1 - BEFORE 12
# =========================
st.subheader("⏰ Before 12 Performance")

fig1 = px.bar(
    df,
    x="Courier ID",
    y="Before12_Rate",
    text="Before12_Rate"
)
st.plotly_chart(fig1, use_container_width=True)

# =========================
# CHART 2 - EXCEPTIONS
# =========================
st.subheader("🔴 Exception Rate")

fig2 = px.bar(
    df,
    x="Courier ID",
    y="Exception_Rate",
    text="Exception_Rate"
)
st.plotly_chart(fig2, use_container_width=True)

# =========================
# CHART 3 - SCORE
# =========================
st.subheader("🏆 Performance Score")

fig3 = px.bar(
    df,
    x="Courier ID",
    y="Score",
    text="Score"
)
st.plotly_chart(fig3, use_container_width=True)
