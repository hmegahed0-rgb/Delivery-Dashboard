import streamlit as st
import pandas as pd
import numpy as np

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Courier Control Tower",
    layout="wide"
)

st.title("🚚 Courier Operations Control Tower (Enterprise FIX)")

# =========================
# LOAD DATA (SAFE + FAST)
# =========================
@st.cache_data
def load_data():
    try:
        deliveries = pd.read_csv(
            "deliveries.csv",
            encoding="utf-8",
            low_memory=False,
            dtype=str
        )

        stops = pd.read_csv(
            "stops.csv",
            encoding="utf-8",
            low_memory=False,
            dtype=str
        )

        # Clean columns
        deliveries.columns = deliveries.columns.str.strip()
        stops.columns = stops.columns.str.strip()

        # Standardize Courier ID
        if "Courier ID" in deliveries.columns:
            deliveries["Courier ID"] = deliveries["Courier ID"].str.upper().str.strip()

        if "Courier id" in stops.columns:
            stops["Courier id"] = stops["Courier id"].str.upper().str.strip()

        # Convert datetime safely
        if "Act Tm" in deliveries.columns:
            deliveries["Act Tm"] = pd.to_datetime(deliveries["Act Tm"], errors="coerce")

        # KPI Before 12
        if "Act Tm" in deliveries.columns:
            deliveries["Before_12"] = deliveries["Act Tm"].dt.hour < 12
        else:
            deliveries["Before_12"] = False

        # Exception logic
        exception_keywords = ["delay", "failed", "exception", "undel", "return", "hold"]

        if "PUD Info" in stops.columns:
            stops["Exception"] = (
                stops["PUD Info"]
                .fillna("")
                .astype(str)
                .str.lower()
                .apply(lambda x: any(k in x for k in exception_keywords))
            )
        else:
            stops["Exception"] = False

        return deliveries, stops

    except Exception as e:
        st.error(f"Data loading failed: {e}")
        return pd.DataFrame(), pd.DataFrame()


deliveries, stops = load_data()

# =========================
# CHECK DATA
# =========================
if deliveries.empty or stops.empty:
    st.warning("No data loaded. Check CSV files in repo.")
    st.stop()

st.success("Data Loaded Successfully ✅")

# =========================
# KPI CALCULATION
# =========================
delivery_kpi = deliveries.groupby("Courier ID").agg(
    Total_Deliveries=("Courier ID", "count"),
    Before12_Rate=("Before_12", lambda x: x.mean() if len(x) > 0 else 0)
).reset_index()

stops_kpi = stops.groupby("Courier id").agg(
    Total_Stops=("Courier id", "count"),
    Exception_Rate=("Exception", lambda x: x.mean() if len(x) > 0 else 0)
).reset_index()

# Merge
final = pd.merge(
    delivery_kpi,
    stops_kpi,
    left_on="Courier ID",
    right_on="Courier id",
    how="outer"
)

final = final.fillna(0)

# Convert to %
final["Before12_Rate"] = (final["Before12_Rate"] * 100).round(2)
final["Exception_Rate"] = (final["Exception_Rate"] * 100).round(2)

# =========================
# UI - FILTER
# =========================
courier = st.selectbox("Select Courier", final["Courier ID"].astype(str).unique())

profile = final[final["Courier ID"] == courier]

# =========================
# METRICS
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("Total Stops", int(profile["Total_Stops"].values[0]))
col2.metric("Before 12 %", f"{profile['Before12_Rate'].values[0]}%")
col3.metric("Exception %", f"{profile['Exception_Rate'].values[0]}%")

# =========================
# FULL TABLE
# =========================
st.subheader("📊 Courier Performance Table")
st.dataframe(final, use_container_width=True)
def safe_read(file):
    try:
        df = pd.read_csv(file, encoding="utf-8", engine="python")
        if df.empty or len(df.columns) == 0:
            return None
        return df
    except:
        return None


deliveries = safe_read("deliveries.csv")
stops = safe_read("stops.csv")

if deliveries is None or stops is None:
    st.error("❌ CSV files are corrupted or empty. Please re-upload them correctly.")
    st.stop()
