import streamlit as st
import pandas as pd
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Courier Control Tower", layout="wide")
st.title("🚚🤖 AI Smart Courier Pipeline (Enterprise Stable)")

# =========================
# BASE PATH (GITHUB SAFE)
# =========================
BASE_DIR = os.path.dirname(__file__)

# =========================
# SAFE LOAD FUNCTION
# =========================
def load_csv(file_name):
    path = os.path.join(BASE_DIR, file_name)

    if not os.path.exists(path):
        st.error(f"❌ File missing: {file_name}")
        return None

    try:
        return pd.read_csv(path, encoding="utf-8", low_memory=False)
    except:
        try:
            return pd.read_csv(path, encoding="latin1", low_memory=False)
        except:
            st.error(f"❌ Cannot read file: {file_name}")
            return None


# =========================
# LOAD DATA
# =========================
deliveries = load_csv("deliveries.csv")
stops = load_csv("stops.csv")

if deliveries is None or stops is None:
    st.stop()

st.success("Data Loaded Successfully ✅")

# =========================
# CLEAN COLUMNS
# =========================
deliveries.columns = deliveries.columns.str.strip()
stops.columns = stops.columns.str.strip()

# =========================
# AI COLUMN DETECTION
# =========================
def detect_column(df, keywords):
    for col in df.columns:
        col_clean = col.strip().lower()
        for k in keywords:
            if k.lower() in col_clean:
                return col
    return None


delivery_courier_col = detect_column(deliveries, ["courier"])
stop_courier_col = detect_column(stops, ["courier"])

time_col = detect_column(deliveries, ["act tm", "time", "date"])
info_col = detect_column(stops, ["pud info", "info", "status"])

if delivery_courier_col is None or stop_courier_col is None:
    st.error("❌ Courier column not found in dataset")
    st.stop()

# =========================
# STANDARDIZE COURIER
# =========================
deliveries[delivery_courier_col] = deliveries[delivery_courier_col].astype(str).str.upper().str.strip()
stops[stop_courier_col] = stops[stop_courier_col].astype(str).str.upper().str.strip()

# =========================
# TIME PROCESSING
# =========================
if time_col:
    deliveries[time_col] = pd.to_datetime(deliveries[time_col], errors="coerce")
    deliveries["Before_12"] = deliveries[time_col].dt.hour < 12
else:
    deliveries["Before_12"] = False

# =========================
# EXCEPTION DETECTION
# =========================
keywords = ["delay", "failed", "exception", "return", "hold", "undel"]

if info_col:
    stops["Exception"] = stops[info_col].fillna("").astype(str).str.lower().apply(
        lambda x: any(k in x for k in keywords)
    )
else:
    stops["Exception"] = False

# =========================
# KPI ENGINE
# =========================
delivery_kpi = deliveries.groupby(delivery_courier_col).agg(
    Total_Deliveries=(delivery_courier_col, "count"),
    Before12_Rate=("Before_12", lambda x: x.mean() if len(x) > 0 else 0)
).reset_index()

stop_kpi = stops.groupby(stop_courier_col).agg(
    Total_Stops=(stop_courier_col, "count"),
    Exception_Rate=("Exception", lambda x: x.mean() if len(x) > 0 else 0)
).reset_index()

# =========================
# MERGE
# =========================
final = pd.merge(
    delivery_kpi,
    stop_kpi,
    left_on=delivery_courier_col,
    right_on=stop_courier_col,
    how="outer"
).fillna(0)

final.rename(columns={delivery_courier_col: "Courier"}, inplace=True)

final["Before12_Rate"] = (final["Before12_Rate"] * 100).round(2)
final["Exception_Rate"] = (final["Exception_Rate"] * 100).round(2)

# =========================
# UI SELECTOR
# =========================
courier = st.selectbox("👤 Select Courier", final["Courier"].astype(str).unique())

profile = final[final["Courier"] == courier]

# =========================
# METRICS
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("🚚 Total Stops", int(profile["Total_Stops"].values[0]))
col2.metric("⏰ Before 12%", f"{profile['Before12_Rate'].values[0]}%")
col3.metric("⚠️ Exception%", f"{profile['Exception_Rate'].values[0]}%")

# =========================
# AI SCORE
# =========================
score = (
    profile["Before12_Rate"].values[0] * 0.5 +
    (100 - profile["Exception_Rate"].values[0]) * 0.5
)

st.subheader("🧠 AI Performance Score")
st.progress(int(score))
st.write(f"Score: {round(score,2)} / 100")

# =========================
# FULL TABLE
# =========================
st.subheader("📊 Full KPI Table")
st.dataframe(final, use_container_width=True)

# =========================
# DEBUG PANEL
# =========================
with st.expander("🔍 Debug Info"):
    st.write("Detected Columns:")
    st.json({
        "deliveries_courier": delivery_courier_col,
        "stops_courier": stop_courier_col,
        "time_column": time_col,
        "info_column": info_col
    })
