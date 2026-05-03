import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Courier Control Tower", layout="wide")
st.title("🤖🚚 AI Smart Courier Pipeline (Enterprise V6)")

# =========================
# SAFE CSV LOADER (AI ROBUST)
# =========================
def load_csv(file):
    try:
        df = pd.read_csv(file, encoding="utf-8", low_memory=False)
        if df is None or df.empty:
            return None
        return df
    except:
        try:
            df = pd.read_csv(file, encoding="latin1", low_memory=False)
            if df is None or df.empty:
                return None
            return df
        except:
            return None


# =========================
# AI COLUMN DETECTOR
# =========================
def detect_column(df, keywords):
    for col in df.columns:
        col_clean = col.strip().lower()
        for k in keywords:
            if k.lower() in col_clean:
                return col
    return None


# =========================
# LOAD DATA
# =========================
deliveries = load_csv("deliveries.csv")
stops = load_csv("stops.csv")

if deliveries is None or stops is None:
    st.error("❌ Data not found or corrupted")
    st.stop()

st.success("AI Engine Loaded Data Successfully ✅")

# =========================
# CLEAN COLUMNS
# =========================
deliveries.columns = deliveries.columns.str.strip()
stops.columns = stops.columns.str.strip()

# =========================
# AI COLUMN MAPPING
# =========================
delivery_courier = detect_column(deliveries, ["courier"])
stop_courier = detect_column(stops, ["courier"])

act_time_col = detect_column(deliveries, ["act tm", "act time"])
pud_info_col = detect_column(stops, ["pud info", "info", "status"])

if delivery_courier is None or stop_courier is None:
    st.error("❌ Cannot detect Courier column automatically")
    st.stop()

# =========================
# STANDARDIZE
# =========================
deliveries[delivery_courier] = deliveries[delivery_courier].astype(str).str.upper()
stops[stop_courier] = stops[stop_courier].astype(str).str.upper()

# =========================
# DATETIME SAFE
# =========================
if act_time_col:
    deliveries[act_time_col] = pd.to_datetime(deliveries[act_time_col], errors="coerce")
    deliveries["Before_12"] = deliveries[act_time_col].dt.hour < 12
else:
    deliveries["Before_12"] = False

# =========================
# EXCEPTION AI DETECTION
# =========================
keywords = ["delay", "failed", "exception", "undel", "return", "hold"]

if pud_info_col:
    stops["Exception"] = stops[pud_info_col].fillna("").astype(str).str.lower().apply(
        lambda x: any(k in x for k in keywords)
    )
else:
    stops["Exception"] = False

# =========================
# KPI ENGINE (AI SAFE)
# =========================
delivery_kpi = deliveries.groupby(delivery_courier).agg(
    Total_Deliveries=(delivery_courier, "count"),
    Before12_Rate=("Before_12", lambda x: x.mean() if len(x) > 0 else 0)
).reset_index()

stop_kpi = stops.groupby(stop_courier).agg(
    Total_Stops=(stop_courier, "count"),
    Exception_Rate=("Exception", lambda x: x.mean() if len(x) > 0 else 0)
).reset_index()

# =========================
# MERGE AI VIEW
# =========================
final = pd.merge(
    delivery_kpi,
    stop_kpi,
    left_on=delivery_courier,
    right_on=stop_courier,
    how="outer"
).fillna(0)

final["Before12_Rate"] = (final["Before12_Rate"] * 100).round(2)
final["Exception_Rate"] = (final["Exception_Rate"] * 100).round(2)

final.rename(columns={delivery_courier: "Courier"}, inplace=True)

# =========================
# AI COURIER SELECTOR
# =========================
courier = st.selectbox("🤖 Select Courier (AI Detected)", final["Courier"].unique())

profile = final[final["Courier"] == courier]

# =========================
# DASHBOARD KPIs
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("🚚 Total Stops", int(profile["Total_Stops"].values[0]))
col2.metric("⏰ Before 12%", f"{profile['Before12_Rate'].values[0]}%")
col3.metric("⚠️ Exception%", f"{profile['Exception_Rate'].values[0]}%")

# =========================
# AI SCORE ENGINE
# =========================
score = (
    profile["Before12_Rate"].values[0] * 0.5
    + (100 - profile["Exception_Rate"].values[0]) * 0.5
)

st.subheader("🧠 AI Performance Score")
st.progress(int(score))
st.write(f"AI Score: {round(score,2)} / 100")

# =========================
# TABLE
# =========================
st.subheader("📊 AI Full Analytics View")
st.dataframe(final, use_container_width=True)

# =========================
# DEBUG PANEL
# =========================
with st.expander("🔍 AI Debug Engine"):
    st.write("Detected Columns:")
    st.write({
        "Courier (Deliveries)": delivery_courier,
        "Courier (Stops)": stop_courier,
        "Time Column": act_time_col,
        "Info Column": pud_info_col
    })
