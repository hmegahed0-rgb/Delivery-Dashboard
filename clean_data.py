import pandas as pd
import numpy as np

# =========================
# 1. LOAD DATA (SAFE MODE)
# =========================
deliveries = pd.read_csv("deliveries.csv", encoding="utf-8", low_memory=False)
stops = pd.read_csv("stops.csv", encoding="utf-8", low_memory=False)

# =========================
# 2. CLEAN COLUMN NAMES
# =========================
deliveries.columns = deliveries.columns.str.strip()
stops.columns = stops.columns.str.strip()

# =========================
# 3. NORMALIZE COURIER IDS (CRITICAL FIX)
# =========================
def clean_id(x):
    return str(x).upper().strip() if pd.notnull(x) else "UNKNOWN"

if "Courier ID" in deliveries.columns:
    deliveries["Courier ID"] = deliveries["Courier ID"].apply(clean_id)

if "Courier id" in stops.columns:
    stops["Courier id"] = stops["Courier id"].apply(clean_id)

# =========================
# 4. DATETIME PARSING (SAFE)
# =========================
if "Act Tm" in deliveries.columns:
    deliveries["Act Tm"] = pd.to_datetime(deliveries["Act Tm"], errors="coerce")

# =========================
# 5. BEFORE 12 KPI (ACCURATE)
# =========================
def before_12(x):
    return x.hour < 12 if pd.notnull(x) else np.nan

if "Act Tm" in deliveries.columns:
    deliveries["Before_12"] = deliveries["Act Tm"].apply(before_12)

# =========================
# 6. EXCEPTION LOGIC (ROBUST)
# =========================
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

# =========================
# 7. DELIVERY KPI
# =========================
delivery_kpi = deliveries.groupby("Courier ID").agg(
    Total_Deliveries=("Courier ID", "count"),
    Before12_Rate=("Before_12", lambda x: x.mean() if x.notna().sum() > 0 else 0)
).reset_index()

# =========================
# 8. STOP KPI
# =========================
stops_kpi = stops.groupby("Courier id").agg(
    Total_Stops=("Courier id", "count"),
    Exception_Rate=("Exception", lambda x: x.mean() if len(x) > 0 else 0)
).reset_index()

# =========================
# 9. MERGE (CLEAN JOIN)
# =========================
final = pd.merge(
    delivery_kpi,
    stops_kpi,
    left_on="Courier ID",
    right_on="Courier id",
    how="outer"
)

# =========================
# 10. FINAL CLEANING
# =========================
final["Before12_Rate"] = (final["Before12_Rate"] * 100).round(2)
final["Exception_Rate"] = (final["Exception_Rate"] * 100).round(2)

final = final.fillna(0)

# =========================
# 11. SAVE OUTPUTS (PRODUCTION FILES)
# =========================
final.to_csv("clean_courier_kpi.csv", index=False, encoding="utf-8")
deliveries.to_csv("clean_deliveries.csv", index=False, encoding="utf-8")
stops.to_csv("clean_stops.csv", index=False, encoding="utf-8")

print("✅ PRODUCTION CLEANING DONE SUCCESSFULLY")
