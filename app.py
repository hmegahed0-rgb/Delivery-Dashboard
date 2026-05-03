import streamlit as st
import pandas as pd
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Courier Control Tower", layout="wide")
st.title("🚚🤖 AI Courier Control Tower (Stable Edition)")

BASE_DIR = os.path.dirname(__file__)

# =========================
# SAFE CSV LOADER (NO CRASH)
# =========================
def load_csv(file_name):
    path = os.path.join(BASE_DIR, file_name)

    st.write(f"📂 Loading: {file_name}")

    # File not found
    if not os.path.exists(path):
        st.error(f"❌ File not found: {file_name}")
        return None

    # File size check
    size = os.path.getsize(path)
    st.write(f"📏 File size: {size} bytes")

    if size < 10:
        st.error(f"❌ File is empty or corrupted: {file_name}")
        return None

    # Try reading CSV safely
    try:
        df = pd.read_csv(path, encoding="utf-8", low_memory=False)
    except:
        try:
            df = pd.read_csv(path, encoding="latin1", low_memory=False)
        except Exception as e:
            st.error(f"❌ Cannot parse CSV: {file_name}")
            st.code(str(e))
            return None

    # Final validation
    if df is None or df.empty:
        st.error(f"❌ No data inside file: {file_name}")
        return None

    return df


# =========================
# LOAD FILES
# =========================
deliveries = load_csv("deliveries.csv")
stops = load_csv("stops.csv")

if deliveries is None or stops is None:
    st.warning("⚠️ Fix CSV files and re-upload to GitHub")
    st.stop()

st.success("Data Loaded Successfully ✅")

# =========================
# CLEAN COLUMNS
# =========================
deliveries.columns = deliveries.columns.str.strip()
stops.columns = stops.columns.str.strip()

# =========================
# FORCE COURIER COLUMN
# =========================
COURIER = "Couier ID"

if COURIER not in deliveries.columns or COURIER not in stops.columns:
    st.error("❌ 'Couier ID' column not found in one of the files")
    st.write("Deliveries columns:", deliveries.columns)
    st.write("Stops columns:", stops.columns)
    st.stop()

# =========================
# TIME HANDLING
# =========================
time_col = None
for c in deliveries.columns:
    if "act" in c.lower() and "tm" in c.lower():
        time_col = c
        break

if time_col:
    deliveries[time_col] = pd.to_datetime(deliveries[time_col], errors="coerce")
    deliveries["Before12"] = deliveries[time_col].dt.hour < 12
else:
    deliveries["Before12"] = False

# =========================
# EXCEPTION LOGIC
# =========================
info_col = None
for c in stops.columns:
    if "info" in c.lower():
        info_col = c
        break

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
delivery_kpi = deliveries.groupby(COURIER).agg(
    Total_Deliveries=(COURIER, "count"),
    Before12_Rate=("Before12", "mean")
).reset_index()

stop_kpi = stops.groupby(COURIER).agg(
    Total_Stops=(COURIER, "count"),
    Exception_Rate=("Exception", "mean")
).reset_index()

# =========================
# MERGE DATA
# =========================
df = pd.merge(delivery_kpi, stop_kpi, on=COURIER, how="outer").fillna(0)

# =========================
# AI SCORE
# =========================
df["Before12_Rate"] *= 100
df["Exception_Rate"] *= 100

df["AI_Score"] = (
    df["Before12_Rate"] * 0.5 +
    (100 - df["Exception_Rate"]) * 0.5
)

df = df.sort_values("AI_Score", ascending=False)
df["Rank"] = df["AI_Score"].rank(ascending=False)

# =========================
# UI
# =========================
st.subheader("🏆 Courier Ranking")

st.dataframe(
    df[[COURIER, "Total_Deliveries", "Total_Stops",
        "Before12_Rate", "Exception_Rate", "AI_Score", "Rank"]],
    use_container_width=True
)

# =========================
# TOP COURIER
# =========================
top = df.iloc[0]
st.success(f"🥇 Top Courier: {top[COURIER]} | Score: {round(top['AI_Score'],2)}")

# =========================
# PROFILE VIEW
# =========================
courier = st.selectbox("👤 Select Courier", df[COURIER].astype(str).unique())

profile = df[df[COURIER] == courier].iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric("🚚 Deliveries", int(profile["Total_Deliveries"]))
col2.metric("⏰ Before 12%", f"{round(profile['Before12_Rate'],2)}%")
col3.metric("⚠️ Exceptions%", f"{round(profile['Exception_Rate'],2)}%")

st.metric("🏆 AI Score", round(profile["AI_Score"], 2))
