import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Courier Control Tower", layout="wide")

st.title("🚚 Courier Operations Control Tower (Enterprise)")

# =========================
# LOAD DATA (LOCAL FILES ONLY)
# =========================
@st.cache_data
def load_data():
    deliveries = pd.read_csv("deliveries.csv", encoding="utf-8")
    stops = pd.read_csv("stops.csv", encoding="utf-8")
    return deliveries, stops

df, stops = load_data()

st.success("✅ Data Loaded Successfully")

# =========================
# CLEAN COLUMNS
# =========================
df.columns = df.columns.str.strip()

# =========================
# SAFE COLUMN HANDLING
# =========================
courier_col = "Courier Id" if "Courier Id" in df.columns else df.columns[0]

# =========================
# TIME PROCESSING
# =========================
if "Act Tm" in df.columns:
    df["Act Tm"] = pd.to_datetime(df["Act Tm"], errors="coerce")

# =========================
# KPI LOGIC
# =========================
df["Before_12"] = df["Act Tm"].dt.hour < 12

df["Exception"] = df.get("Act Ckpt Code", "OK") != "OK"

kpi = df.groupby(courier_col).agg(
    Total_Deliveries=(courier_col, "count"),
    Before_12=("Before_12", "sum"),
    Exceptions=("Exception", "sum")
).reset_index()

kpi["Before_12_%"] = (kpi["Before_12"] / kpi["Total_Deliveries"]) * 100
kpi["Exception_%"] = (kpi["Exceptions"] / kpi["Total_Deliveries"]) * 100

# =========================
# PERFORMANCE SCORE
# =========================
kpi["Score"] = (kpi["Before_12_%"] * 0.7) - (kpi["Exception_%"] * 0.3)

# =========================
# FILTERS
# =========================
st.sidebar.header("🔎 Filters")

selected_courier = st.sidebar.selectbox(
    "Select Courier",
    ["All"] + list(kpi[courier_col].unique())
)

if selected_courier != "All":
    kpi = kpi[kpi[courier_col] == selected_courier]

# =========================
# KPI CARDS
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("Couriers", len(kpi))
c2.metric("Avg Before 12%", f"{kpi['Before_12_%'].mean():.1f}%")
c3.metric("Avg Exception%", f"{kpi['Exception_%'].mean():.1f}%")

st.divider()

# =========================
# TOP PERFORMANCE TABLE
# =========================
st.subheader("🏆 Courier Performance")

st.dataframe(
    kpi.sort_values("Score", ascending=False),
    use_container_width=True
)

# =========================
# BAR CHART
# =========================
fig = px.bar(
    kpi.sort_values("Score", ascending=False),
    x=courier_col,
    y="Score",
    title="Courier Performance Score"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# EXCEPTION ANALYSIS
# =========================
st.subheader("🚨 High Exception Couriers")

st.dataframe(
    kpi.sort_values("Exception_%", ascending=False),
    use_container_width=True
)

# =========================
# RAW DATA VIEW
# =========================
with st.expander("📦 Raw Deliveries Data"):
    st.dataframe(df, use_container_width=True)

with st.expander("📦 Stops Data"):
    st.dataframe(stops, use_container_width=True)
