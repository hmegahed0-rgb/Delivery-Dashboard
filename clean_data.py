import pandas as pd
import numpy as np

# =========================
# 1. LOAD DATA
# =========================
deliveries = pd.read_csv("deliveries.csv", encoding="utf-8", low_memory=False)
stops = pd.read_csv("stops.csv", encoding="utf-8", low_memory=False)

# =========================
# 2. CLEAN COLUMN NAMES
# =========================
deliveries.columns = deliveries.columns.str.strip()
stops.columns = stops.columns.str.strip()

# =========================
# 3. SAFE DATETIME PARSING
# =========================
if "Act Tm" in deliveries.columns:
    deliveries["Act Tm"] = pd.to_datetime(deliveries["Act Tm"], errors="coerce")

if "Act Dt Tm" in stops.columns:
    stops["Act Dt Tm"] = pd.to_datetime(stops["Act Dt Tm"], errors="coerce")

# =========================
# 4. KPI: BEFORE 12 PM
# =========================
if "Act Tm" in deliveries.columns:
    deliveries["Before_12"] = deliveries["Act Tm"].dt.hour < 12

# =========================
# 5. EXCEPTION FLAG (BASIC LOGIC)
# =========================
exception_keywords = [
    "delay", "failed", "exception", "undel", "return", "hold"
]

if "PUD Info" in stops.columns:
    stops["Exception"] = stops["PUD Info"].astype(str).str.lower().apply(
        lambda x: any(k in x for k in exception_keywords)
    )
else:
    stops["Exception"] = False

# =========================
# 6. STANDARDIZE COURIER ID
# =========================
if "Courier id" in stops.columns:
    stops["Courier id"] = stops["Courier id"].astype(str).str.lower().str.strip()

if "Courier ID" in deliveries.columns:
    deliveries["Courier ID"] = deliveries["Courier ID"].astype(str).str.lower().str.strip()

# =========================
# 7. AGGREGATIONS
# =========================

# Deliveries KPI per courier
delivery_kpi = deliveries.groupby("Courier ID").agg(
    Total_Deliveries=("Courier ID", "count"),
    Before12_Rate=("Before_12", "mean")
).reset_index()

# Stops KPI per courier
stops_kpi = stops.groupby("Courier id").agg(
    Total_Stops=("Courier id", "count"),
    Exception_Rate=("Exception", "mean")
).reset_index()

# =========================
# 8. MERGE KPI TABLE
# =========================
final = pd.merge(delivery_kpi, stops_kpi, left_on="Courier ID", right_on="Courier id", how="outer")

# =========================
# 9. CLEAN FINAL VALUES
# =========================
final["Before12_Rate"] = (final["Before12_Rate"] * 100).round(2)
final["Exception_Rate"] = (final["Exception_Rate"] * 100).round(2)

final = final.fillna(0)

# =========================
# 10. SAVE OUTPUT FILES
# =========================
final.to_csv("clean_courier_kpi.csv", index=False, encoding="utf-8")
deliveries.to_csv("clean_deliveries.csv", index=False, encoding="utf-8")
stops.to_csv("clean_stops.csv", index=False, encoding="utf-8")

print("✅ CLEANING DONE - ENTERPRISE DATA READY")
