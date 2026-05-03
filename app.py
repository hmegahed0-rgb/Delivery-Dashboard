import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Courier Profile Dashboard", layout="wide")

st.title("👤 Courier Profile Dashboard (Enterprise v3)")

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

st.success("Data Loaded Successfully ✅")

# =========================
# SMART DETECTION
# =========================
def find_col(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None

courier_col = find_col(df, ["courier id", "courier"])
time_col = find_col(df, ["act tm", "time"])
status_col = find_col(df, ["ckpt", "status", "code"])

# =========================
# VALIDATION
# =========================
if courier_col is None or time_col is None:
    st.error("Missing required columns")
    st.stop()

# =========================
# CLEAN DATA
# =========================
df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
df = df.dropna(subset=[courier_col, time_col])
df = df.drop_duplicates()

df["hour"] = df[time_col].dt.hour
df["Before_12"] = df["hour"] < 12

df["Exception"] = df.get(status_col, "OK").astype(str).str.upper().ne("OK")

# =========================
# KPI TABLE
# =========================
kpi = df.groupby(courier_col).agg(
    Total_Stops=(courier_col, "size"),
    Before_12=("Before_12", "sum"),
    Exceptions=("Exception", "sum"),
    Avg_Hour=("hour", "mean")
).reset_index()

kpi["Before_12_%"] = (kpi["Before_12"] / kpi["Total_Stops"]) * 100
kpi["Exception_%"] = (kpi["Exceptions"] / kpi["Total_Stops"]) * 100

kpi["Score"] = (
    kpi["Before_12_%"] * 0.65
    - kpi["Exception_%"] * 0.35
    + (10 - kpi["Avg_Hour"].fillna(10))
)

# =========================
# SIDEBAR PROFILE SELECTOR
# =========================
st.sidebar.header("👤 Courier Profile")

selected = st.sidebar.selectbox(
    "Select Courier",
    sorted(kpi[courier_col].unique())
)

profile = kpi[kpi[courier_col] == selected].iloc[0]

# =========================
# PROFILE HEADER
# =========================
st.subheader(f"📊 Profile: {selected}")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Stops", int(profile["Total_Stops"]))
c2.metric("Before 12 %", f"{profile['Before_12_%']:.1f}%")
c3.metric("Exception %", f"{profile['Exception_%']:.1f}%")
c4.metric("AI Score", f"{profile['Score']:.2f}")

st.divider()

# =========================
# FILTER DATA FOR COURIER
# =========================
courier_df = df[df[courier_col] == selected]

# =========================
# DAILY PERFORMANCE
# =========================
st.subheader("📅 Daily Activity")

daily = courier_df.copy()
daily["Date"] = daily[time_col].dt.date

daily_kpi = daily.groupby("Date").agg(
    Stops=(courier_col, "count"),
    Before_12=("Before_12", "sum"),
    Exceptions=("Exception", "sum")
).reset_index()

st.dataframe(daily_kpi, use_container_width=True)

fig1 = px.line(daily_kpi, x="Date", y="Stops", title="Daily Stops Trend")
st.plotly_chart(fig1, use_container_width=True)

# =========================
# BEFORE 12 BREAKDOWN
# =========================
st.subheader("⏰ Before 12 Performance")

fig2 = px.histogram(
    courier_df,
    x="hour",
    title="Hourly Distribution"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# EXCEPTIONS DETAIL
# =========================
st.subheader("🚨 Exceptions Breakdown")

exceptions = courier_df[courier_df["Exception"] == True]

st.write(f"Total Exceptions: {len(exceptions)}")

st.dataframe(exceptions, use_container_width=True)

# =========================
# COMPARISON VS COMPANY
# =========================
st.subheader("📊 vs Company Average")

avg_before = kpi["Before_12_%"].mean()
avg_exc = kpi["Exception_%"].mean()

comp = pd.DataFrame({
    "Metric": ["Before 12 %", "Exception %"],
    "Courier": [profile["Before_12_%"], profile["Exception_%"]],
    "Company Avg": [avg_before, avg_exc]
})

fig3 = px.bar(comp, x="Metric", y=["Courier", "Company Avg"], barmode="group")
st.plotly_chart(fig3, use_container_width=True)

# =========================
# RAW DATA
# =========================
with st.expander("📦 Raw Courier Data"):
    st.dataframe(courier_df, use_container_width=True)
