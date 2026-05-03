import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Courier Control Tower", layout="wide")

# =========================
# LOAD RAW DATA
# =========================
@st.cache_data
def load_data():
    deliveries = pd.read_csv("deliveries.csv", encoding="utf-8", low_memory=False)
    stops = pd.read_csv("stops.csv", encoding="utf-8", low_memory=False)

    deliveries.columns = deliveries.columns.str.strip()
    stops.columns = stops.columns.str.strip()

    # Courier normalization
    if "Courier ID" in deliveries.columns:
        deliveries["Courier ID"] = deliveries["Courier ID"].astype(str).str.upper().str.strip()

    if "Courier id" in stops.columns:
        stops["Courier id"] = stops["Courier id"].astype(str).str.upper().str.strip()

    # datetime
    if "Act Tm" in deliveries.columns:
        deliveries["Act Tm"] = pd.to_datetime(deliveries["Act Tm"], errors="coerce")

    # KPI before 12
    deliveries["Before_12"] = deliveries["Act Tm"].dt.hour < 12

    # exception
    keywords = ["delay", "failed", "exception", "undel", "return", "hold"]

    if "PUD Info" in stops.columns:
        stops["Exception"] = stops["PUD Info"].fillna("").astype(str).str.lower().apply(
            lambda x: any(k in x for k in keywords)
        )
    else:
        stops["Exception"] = False

    return deliveries, stops


deliveries, stops = load_data()

# =========================
# KPI CALCULATION
# =========================
delivery_kpi = deliveries.groupby("Courier ID").agg(
    Total_Deliveries=("Courier ID", "count"),
    Before12_Rate=("Before_12", "mean")
).reset_index()

stops_kpi = stops.groupby("Courier id").agg(
    Total_Stops=("Courier id", "count"),
    Exception_Rate=("Exception", "mean")
).reset_index()

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
# UI
# =========================
st.title("🚚 Courier Operations Control Tower (Enterprise v4)")

courier = st.selectbox("Select Courier", final["Courier ID"].unique())

profile = final[final["Courier ID"] == courier]

st.metric("Total Stops", int(profile["Total_Stops"].values[0]))
st.metric("Before 12 %", float(profile["Before12_Rate"].values[0]))
st.metric("Exception %", float(profile["Exception_Rate"].values[0]))

st.dataframe(final)
