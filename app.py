import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Courier Control Tower AI v2", layout="wide")

st.title("🚚 Courier Operations Control Tower - AI v2")

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv("deliveries.csv", encoding="utf-8", low_memory=False)
    stops = pd.read_csv("stops.csv", encoding="utf-8", low_memory=False)

    df.columns = df.columns.str.strip()
    stops.columns = stops.columns.str.strip()

    return df, stops

df, stops = load_data()

st.success("✅ Data Loaded & Cleaned")

# =========================
# SMART COLUMN DETECTOR (AI STYLE)
# =========================
def find_col(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None

courier_col = find_col(df, ["courier id", "courier"])
time_col = find_col(df, ["act tm", "actual", "time"])
status_col = find_col(df, ["ckpt", "status", "code"])

if courier_col is None or time_col is None:
    st.error("❌ Required columns not found")
    st.stop()

# =========================
# CLEAN TIME
# =========================
df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

# =========================
# AI FEATURES ENGINE
# =========================
df["hour"] = df[time_col].dt.hour
df["Before_12"] = df["hour"] < 12

# Exception detection (smart)
df["Exception"] = df.get(status_col, "OK").astype(str).str.upper().ne("OK")

# =========================
# AI SCORING MODEL (Weighted)
# =========================
courier_kpi = df.groupby(courier_col).agg(
    Total_Stops=(courier_col, "count"),
    Before_12_Count=("Before_12", "sum"),
    Exceptions=("Exception", "sum"),
    Avg_Hour=("hour", "mean")
).reset_index()

courier_kpi["Before_12_%"] = (courier_kpi["Before_12_Count"] / courier_kpi["Total_Stops"]) * 100
courier_kpi["Exception_%"] = (courier_kpi["Exceptions"] / courier_kpi["Total_Stops"]) * 100

# AI Score (weighted model)
courier_kpi["AI_Score"] = (
    courier_kpi["Before_12_%"] * 0.65
    - courier_kpi["Exception_%"] * 0.35
    + (10 - courier_kpi["Avg_Hour"].fillna(10))
)

# Normalize score
courier_kpi["AI_Score"] = np.round(courier_kpi["AI_Score"], 2)

# =========================
# KPI HEADER
# =========================
c1, c2, c3, c4 = st.columns(4)

c1.metric("Couriers", len(courier_kpi))
c2.metric("Avg Before 12%", f"{courier_kpi['Before_12_%'].mean():.1f}%")
c3.metric("Avg Exception%", f"{courier_kpi['Exception_%'].mean():.1f}%")
c4.metric("AI Score Avg", f"{courier_kpi['AI_Score'].mean():.1f}")

st.divider()

# =========================
# FILTER
# =========================
selected = st.selectbox("Select Courier", ["All"] + list(courier_kpi[courier_col]))

if selected != "All":
    courier_kpi = courier_kpi[courier_kpi[courier_col] == selected]

# =========================
# TOP PERFORMANCE
# =========================
st.subheader("🏆 AI Performance Ranking")

st.dataframe(
    courier_kpi.sort_values("AI_Score", ascending=False),
    use_container_width=True
)

# =========================
# CHARTS
# =========================
fig1 = px.bar(
    courier_kpi.sort_values("AI_Score", ascending=False),
    x=courier_col,
    y="AI_Score",
    title="AI Courier Score"
)

st.plotly_chart(fig1, use_container_width=True)

fig2 = px.scatter(
    courier_kpi,
    x="Before_12_%",
    y="Exception_%",
    size="Total_Stops",
    color="AI_Score",
    title="Performance Matrix (Before 12 vs Exceptions)"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# EXCEPTION HEAT VIEW
# =========================
st.subheader("🚨 Risk Analysis")

st.dataframe(
    courier_kpi.sort_values("Exception_%", ascending=False),
    use_container_width=True
)

# =========================
# RAW DATA
# =========================
with st.expander("📦 Raw Data View"):
    st.dataframe(df, use_container_width=True)
