import streamlit as st
import pandas as pd

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Courier Control Tower", layout="wide")

st.title("🚚 Courier Operations Control Tower (Live)")

# =========================
# GITHUB RAW LINKS (CHANGE THESE)
# =========================
DELIVERY_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/data/deliveries.csv"
STOPS_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/data/stops.csv"

# =========================
# LOAD DATA (CACHE FOR SPEED)
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv(DELIVERY_URL)
    stops = pd.read_csv(STOPS_URL)
    return df, stops

df, stops = load_data()

st.success("✅ Data Loaded from GitHub")

# =========================
# CLEAN COLUMNS
# =========================
df.columns = df.columns.str.strip()
stops.columns = stops.columns.str.strip()

courier_col = "Courier Id"

# =========================
# DATETIME HANDLING
# =========================
if "Act Tm" in df.columns:
    df["Act Tm"] = pd.to_datetime(df["Act Tm"], errors="coerce")

# =========================
# KPI FLAGS
# =========================
df["Before_12"] = df["Act Tm"].dt.time < pd.to_datetime("12:00").time()

df["Exception"] = ~df.get("Act Ckpt Code", pd.Series([""] * len(df))).isin(["OK"])

# =========================
# DELIVERY KPI
# =========================
delivery_kpi = df.groupby(courier_col).agg(
    Total_Deliveries=(courier_col, "count"),
    Before_12=("Before_12", "sum"),
    Exceptions=("Exception", "sum")
).reset_index()

delivery_kpi["Before 12 %"] = delivery_kpi["Before_12"] / delivery_kpi["Total_Deliveries"] * 100
delivery_kpi["Exception %"] = delivery_kpi["Exceptions"] / delivery_kpi["Total_Deliveries"] * 100

# =========================
# STOP KPI
# =========================
if courier_col in stops.columns:
    stop_kpi = stops.groupby(courier_col).agg(
        Total_Stops=(courier_col, "count")
    ).reset_index()
else:
    stop_kpi = pd.DataFrame(columns=[courier_col, "Total_Stops"])

# =========================
# MERGE TABLES
# =========================
final = pd.merge(delivery_kpi, stop_kpi, on=courier_col, how="left")
final["Total_Stops"] = final["Total_Stops"].fillna(0)

# =========================
# PRODUCTIVITY SCORE
# =========================
final["Stops per Delivery"] = final["Total_Stops"] / final["Total_Deliveries"]

# =========================
# KPI HEADER
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("Couriers", len(final))
col2.metric("Avg Before 12 %", f"{final['Before 12 %'].mean():.2f}%")
col3.metric("Avg Exception %", f"{final['Exception %'].mean():.2f}%")

st.divider()

# =========================
# RANKING
# =========================
st.subheader("🏆 Courier Ranking (Before 12 Performance)")

st.dataframe(
    final.sort_values("Before 12 %", ascending=False),
    use_container_width=True
)

# =========================
# TOP PERFORMERS
# =========================
st.subheader("🔥 Top Couriers")

st.dataframe(
    final.sort_values("Before 12 %", ascending=False).head(10),
    use_container_width=True
)

# =========================
# LOW PERFORMANCE
# =========================
st.subheader("🚨 Low Performance Couriers")

st.dataframe(
    final.sort_values("Exception %", ascending=False).head(10),
    use_container_width=True
)

# =========================
# RAW DATA EXPANDER
# =========================
with st.expander("📦 Raw Data"):
    st.dataframe(df, use_container_width=True)
