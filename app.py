import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Courier Control Tower", layout="wide")

st.title("🚚 Courier Operations Control Tower")

# =========================
# LOAD DATA (LOCAL FILES ON GITHUB REPO)
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv("deliveries.csv")
    stops = pd.read_csv("stops.csv")
    return df, stops

df, stops = load_data()

st.success("✅ Data Loaded Successfully")

# =========================
# CLEAN COLUMNS
# =========================
df.columns = df.columns.str.strip()
stops.columns = stops.columns.str.strip()

courier_col = "Courier Id"

# =========================
# DATE/TIME HANDLING
# =========================
if "Act Tm" in df.columns:
    df["Act Tm"] = pd.to_datetime(df["Act Tm"], errors="coerce")

# =========================
# KPI FLAGS
# =========================
df["Before_12"] = df["Act Tm"].dt.hour < 12

df["Exception"] = df.get("Act Ckpt Code", "") != "OK"

# =========================
# KPI CALCULATION
# =========================
kpi = df.groupby(courier_col).agg(
    Deliveries=(courier_col, "count"),
    Before_12=("Before_12", "sum"),
    Exceptions=("Exception", "sum")
).reset_index()

kpi["Before 12 %"] = (kpi["Before_12"] / kpi["Deliveries"]) * 100
kpi["Exception %"] = (kpi["Exceptions"] / kpi["Deliveries"]) * 100

# =========================
# PERFORMANCE SCORE (NEW)
# =========================
kpi["Score"] = (kpi["Before 12 %"] * 0.6) - (kpi["Exception %"] * 0.4)

# =========================
# HEADER KPIs
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("Couriers", len(kpi))
c2.metric("Avg Before 12%", f"{kpi['Before 12 %'].mean():.1f}%")
c3.metric("Avg Exception%", f"{kpi['Exception %'].mean():.1f}%")

st.divider()

# =========================
# TOP PERFORMANCE
# =========================
st.subheader("🏆 Top Couriers")

top = kpi.sort_values("Score", ascending=False)

st.dataframe(top, use_container_width=True)

# =========================
# CHART
# =========================
fig = px.bar(
    top,
    x=courier_col,
    y="Score",
    title="Courier Performance Score"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# LOW PERFORMANCE
# =========================
st.subheader("🚨 Low Performance Couriers")

st.dataframe(
    kpi.sort_values("Exception %", ascending=False).head(10),
    use_container_width=True
)

# =========================
# RAW DATA
# =========================
with st.expander("📦 Raw Data"):
    st.dataframe(df, use_container_width=True)
