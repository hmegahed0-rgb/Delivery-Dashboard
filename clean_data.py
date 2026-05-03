import pandas as pd

# =========================
# LOAD DATA
# =========================
deliveries = pd.read_csv("deliveries.csv", encoding="utf-8", low_memory=False)
stops = pd.read_csv("stops.csv", encoding="utf-8", low_memory=False)

# =========================
# CLEAN COLUMN NAMES
# =========================
deliveries.columns = deliveries.columns.str.strip()
stops.columns = stops.columns.str.strip()

# =========================
# REMOVE EMPTY ROWS
# =========================
deliveries = deliveries.dropna(how="all")
stops = stops.dropna(how="all")

# =========================
# REMOVE SYSTEM / FAKE COURIERS
# =========================
bad_keywords = [
    "NON_GCA", "TRANSFER", "SYSTEM", "TEST", "nan", "EMPTY"
]

def clean_courier(df, col):
    return df[~df[col].astype(str).str.contains("|".join(bad_keywords), case=False, na=False)]

# detect courier column
courier_col = [c for c in deliveries.columns if "courier" in c.lower()][0]

deliveries = clean_courier(deliveries, courier_col)

# =========================
# CLEAN DATETIME COLUMNS
# =========================
time_cols = [c for c in deliveries.columns if "dt" in c.lower() or "time" in c.lower()]

for col in time_cols:
    deliveries[col] = pd.to_datetime(deliveries[col], errors="coerce")

# drop rows with no real timestamps
deliveries = deliveries.dropna(subset=time_cols, how="all")

# =========================
# REMOVE DUPLICATES
# =========================
deliveries = deliveries.drop_duplicates()

stops = stops.drop_duplicates()

# =========================
# FIX NUMERIC COLUMNS
# =========================
for col in deliveries.columns:
    deliveries[col] = pd.to_numeric(deliveries[col], errors="ignore")

# =========================
# SAVE CLEAN FILES
# =========================
deliveries.to_csv("clean_deliveries.csv", index=False, encoding="utf-8")
stops.to_csv("clean_stops.csv", index=False, encoding="utf-8")

print("✅ Data cleaned successfully!")
