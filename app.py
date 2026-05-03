import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Courier AI Ranking", layout="wide")
st.title("🏆🚚 Courier AI Ranking System (Enterprise V7)")

BASE_DIR = os.path.dirname(__file__)

def load_csv(name):
    path = os.path.join(BASE_DIR, name)
    return pd.read_csv(path, encoding="utf-8", low_memory=False)

# =========================
# LOAD DATA
# =========================
deliveries = load_csv("deliveries.csv")
stops = load_csv("stops.csv")

st.success("Data Loaded ✅")

# =========================
# CLEAN
# =========================
deliveries.columns = deliveries.columns.str.strip()
stops.columns = stops.columns.str.strip()

# FORCE COURIER COLUMN
COURIER = "Couier ID"

# =========================
# TIME FEATURE
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
# EXCEPTION DETECTION
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
# KPI BUILD
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
# MERGE
# =========================
df = pd.merge(delivery_kpi, stop_kpi, on=COURIER, how="outer").fillna(0)

# =========================
# AI SCORING ENGINE
# =========================
df["Before12_Rate"] = df["Before12_Rate"] * 100
df["Exception_Rate"] = df["Exception_Rate"] * 100

df["AI_Score"] = (
    df["Before12_Rate"] * 0.4 +
    (100 - df["Exception_Rate"]) * 0.4 +
    (df["Total_Deliveries"] / (df["Total_Deliveries"].max() + 1)) * 20
)

# =========================
# RANKING
# =========================
df["Rank"] = df["AI_Score"].rank(ascending=False)

df = df.sort_values("AI_Score", ascending=False)

# =========================
# UI
# =========================
st.subheader("🏆 Courier Ranking Table")

st.dataframe(
    df[[COURIER, "Total_Deliveries", "Total_Stops",
        "Before12_Rate", "Exception_Rate", "AI_Score", "Rank"]],
    use_container_width=True
)

# =========================
# TOP PERFORMER
# =========================
top = df.iloc[0]

st.success(f"🥇 Top Courier: {top[COURIER]} | Score: {round(top['AI_Score'],2)}")

# =========================
# SELECT COURIER PROFILE
# =========================
courier = st.selectbox("👤 Select Courier", df[COURIER].astype(str).unique())

profile = df[df[COURIER] == courier].iloc[0]

st.subheader("📊 Courier Profile")

col1, col2, col3 = st.columns(3)

col1.metric("🚚 Deliveries", int(profile["Total_Deliveries"]))
col2.metric("⏰ Before 12%", f"{round(profile['Before12_Rate'],2)}%")
col3.metric("⚠️ Exception%", f"{round(profile['Exception_Rate'],2)}%")

st.metric("🏆 AI Score", round(profile["AI_Score"], 2))
