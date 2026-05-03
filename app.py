import streamlit as st
import pandas as pd

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Courier Control Tower",
    layout="wide"
)

st.title("🚚 Courier Operations Control Tower (Enterprise STABLE)")

# =========================
# SAFE CSV LOADER (FIX ALL ERRORS)
# =========================
def load_csv_safe(file_path):
    try:
        # Try normal read first
        df = pd.read_csv(file_path, encoding="utf-8", low_memory=False)

        # If broken (no columns)
        if df is None or df.empty or len(df.columns) == 0:
            return None

        return df

    except Exception:
        try:
            # fallback encoding
            df = pd.read_csv(file_path, encoding="latin1", low_memory=False)

            if df is None or df.empty or len(df.columns) == 0:
                return None

            return df

        except Exception:
            return None


# =========================
# LOAD DATA
# =========================
deliveries = load_csv_safe("deliveries.csv")
stops = load_csv_safe("stops.csv")

# =========================
# VALIDATION
# =========================
if deliveries is None or stops is None:
    st.error("❌ CSV files are missing, empty, or corrupted.")
    st.stop()

st.success("Data Loaded Successfully ✅")

# =========================
# CLEAN COLUMNS
# =========================
deliveries.columns = deliveries.columns.str.strip()
stops.columns = stops.columns.str.strip()

# =========================
# STANDARDIZE COURIER ID
# =========================
if "Courier ID" in deliveries.columns:
    deliveries["Courier ID"] = deliveries["Courier ID"].astype(str).str.upper().str.strip()

if "Courier id" in stops.columns:
    stops["Courier id"] = stops["Courier id"].astype(str).str.upper().str.strip()

# =========================
# DATETIME FIX
# =========================
if "Act Tm" in deliveries.columns:
    deliveries["Act Tm"] = pd.to_datetime(deliveries["Act Tm"], errors="coerce")

# =========================
# KPI: BEFORE 12
# =========================
if "Act Tm" in deliveries.columns:
    deliveries["Before_12"] = deliveries["Act Tm"].dt.hour < 12
else:
    deliveries["Before_12"] = False

# =========================
# EXCEPTION LOGIC
# =========================
keywords = ["delay", "failed", "exception", "undel", "return", "hold"]

if "PUD Info" in stops.columns:
    stops["Exception"] = stops["PUD Info"].fillna("").astype(str).str.lower().apply(
        lambda x: any(k in x for k in keywords)
    )
else:
    stops["Exception"] = False

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

# =========================
# MERGE
# =========================
final = pd.merge(
    delivery_kpi,
    stops_kpi,
    left_on="Courier ID",
    right_on="Courier id",
    how="outer"
)

final = final.fillna(0)

final["Before12_Rate"] = (final["Before12_Rate"] * 100).round(2)
final["Exception_Rate"] = (final["Exception_Rate"] * 100).round(2)

# =========================
# UI FILTER
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
# TABLE
# =========================
st.subheader("📊 Full Courier Performance")
st.dataframe(final, use_container_width=True)

# =========================
# DEBUG (optional)
# =========================
with st.expander("🔍 Debug Info"):
    st.write("Deliveries shape:", deliveries.shape)
    st.write("Stops shape:", stops.shape)
    st.write("Columns deliveries:", list(deliveries.columns))
    st.write("Columns stops:", list(stops.columns))
