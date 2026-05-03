import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Courier Control Tower", layout="wide")

st.title("🚚 Courier Operations Control Tower")

@st.cache_data
def load_data():
    df = pd.read_csv("deliveries.csv", encoding="utf-8")
    stops = pd.read_csv("stops.csv", encoding="utf-8")

    # تنظيف أسماء الأعمدة (VERY IMPORTANT)
    df.columns = df.columns.str.strip()
    stops.columns = stops.columns.str.strip()

    return df, stops

df, stops = load_data()

st.success("Data Loaded Successfully ✅")

# =========================
# 🔥 SAFE COLUMN DETECTION
# =========================

def find_col(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None

act_tm_col = find_col(df, ["act tm", "act time", "actual time"])
courier_col = find_col(df, ["courier id", "courier"])

# =========================
# VALIDATION
# =========================
if act_tm_col is None:
    st.error("❌ Act Time column not found in file")
    st.stop()

if courier_col is None:
    st.error("❌ Courier column not found in file")
    st.stop()

# =========================
# CONVERT TIME
# =========================
df[act_tm_col] = pd.to_datetime(df[act_tm_col], errors="coerce")

# =========================
# KPI LOGIC
# =========================
df["Before_12"] = df[act_tm_col].dt.hour < 12

df["Exception"] = df.get("Act Ckpt Code", "OK") != "OK"

kpi = df.groupby(courier_col).agg(
    Total=(courier_col, "count"),
    Before_12=("Before_12", "sum"),
    Exceptions=("Exception", "sum")
).reset_index()

kpi["Before_12_%"] = (kpi["Before_12"] / kpi["Total"]) * 100
kpi["Exception_%"] = (kpi["Exceptions"] / kpi["Total"]) * 100

kpi["Score"] = (kpi["Before_12_%"] * 0.7) - (kpi["Exception_%"] * 0.3)

# =========================
# DASHBOARD
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("Couriers", len(kpi))
c2.metric("Avg Before 12%", f"{kpi['Before_12_%'].mean():.1f}%")
c3.metric("Avg Exception%", f"{kpi['Exception_%'].mean():.1f}%")

st.divider()

st.subheader("🏆 Performance Ranking")

st.dataframe(
    kpi.sort_values("Score", ascending=False),
    use_container_width=True
)

fig = px.bar(
    kpi.sort_values("Score", ascending=False),
    x=courier_col,
    y="Score",
    title="Courier Performance Score"
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("📦 Raw Data"):
    st.dataframe(df, use_container_width=True)
