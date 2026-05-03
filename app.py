import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Ops Control Tower V2", layout="wide")

st.title("🚚 Ops Control Tower Dashboard V2")
st.markdown("### Advanced Delivery Performance Analytics")

# ---------------------------
# UPLOAD
# ---------------------------
file = st.file_uploader("Upload File", type=["xlsx", "csv"])

if file:

    if file.name.endswith("csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.success("Data Loaded Successfully")

    # ---------------------------
    # CLEAN DATETIME
    # ---------------------------
    df["Delivery DateTime"] = pd.to_datetime(
        df["Last Physical Ckpt Date"].astype(str) + " " +
        df["Last Physical Ckpt Time"].astype(str),
        errors="coerce"
    )

    df = df.dropna(subset=["Delivery DateTime"])

    # ---------------------------
    # FEATURES
    # ---------------------------
    df["Hour"] = df["Delivery DateTime"].dt.hour
    df["Date"] = df["Delivery DateTime"].dt.date
    df["Week"] = df["Delivery DateTime"].dt.isocalendar().week
    df["Month"] = df["Delivery DateTime"].dt.to_period("M").astype(str)

    df["Before_12"] = df["Delivery DateTime"].dt.time < pd.to_datetime("12:00").time()

    df["After_12"] = ~df["Before_12"]

    # ---------------------------
    # SIDEBAR FILTERS
    # ---------------------------
    st.sidebar.header("Filters")

    route_col = st.sidebar.selectbox(
        "Route Type",
        ["Dest Route", "Origin Route", "Arrival Route"]
    )

    time_view = st.sidebar.selectbox(
        "Time View",
        ["Daily", "Weekly", "Monthly"]
    )

    routes = st.sidebar.multiselect(
        "Select Routes",
        df[route_col].dropna().unique(),
        default=df[route_col].dropna().unique()
    )

    df = df[df[route_col].isin(routes)]

    # ---------------------------
    # GROUPING
    # ---------------------------
    if time_view == "Daily":
        group_col = "Date"
    elif time_view == "Weekly":
        group_col = "Week"
    else:
        group_col = "Month"

    # ---------------------------
    # KPIs
    # ---------------------------
    total = len(df)
    before12 = df["Before_12"].sum()
    after12 = df["After_12"].sum()

    otd = (before12 / total * 100) if total > 0 else 0

    sla_target = 85
    sla_gap = otd - sla_target

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📦 Total", total)
    col2.metric("⏰ Before 12", int(before12))
    col3.metric("🚨 After 12", int(after12))
    col4.metric("📊 SLA %", f"{otd:.2f}%")

    st.divider()

    # ---------------------------
    # ROUTE PERFORMANCE
    # ---------------------------
    route_perf = df.groupby(route_col).agg(
        Total=("Waybill Number", "count"),
        Before_12=("Before_12", "sum")
    ).reset_index()

    route_perf["OTD %"] = (route_perf["Before_12"] / route_perf["Total"] * 100).round(2)

    route_perf = route_perf.sort_values("OTD %", ascending=False)

    st.subheader("🏆 Route Performance Ranking")

    st.dataframe(route_perf, use_container_width=True)

    # ---------------------------
    # SUMMARY TREND
    # ---------------------------
    trend = df.groupby(group_col).agg(
        Total=("Waybill Number", "count"),
        Before_12=("Before_12", "sum")
    ).reset_index()

    trend["OTD %"] = (trend["Before_12"] / trend["Total"] * 100).round(2)

    st.subheader("📈 Performance Trend")

    st.dataframe(trend, use_container_width=True)

    # ---------------------------
    # HOURLY HEATMAP DATA
    # ---------------------------
    st.subheader("⏱️ Hourly Delivery Pattern")

    heatmap = df.groupby(["Hour", route_col]).size().reset_index(name="Deliveries")

    st.dataframe(heatmap, use_container_width=True)

    # ---------------------------
    # SLA INSIGHT
    # ---------------------------
    st.subheader("💡 Insights")

    if otd >= sla_target:
        st.success(f"✔ SLA Achieved: {otd:.2f}% ≥ {sla_target}%")
    else:
        st.error(f"⚠ SLA Missed: {otd:.2f}% < {sla_target}%")

    worst_routes = route_perf.tail(3)[route_col].tolist()

    st.warning(f"🚨 Weak Routes: {', '.join(map(str, worst_routes))}")

    # ---------------------------
    # RAW DATA
    # ---------------------------
    with st.expander("📄 Raw Data"):
        st.dataframe(df, use_container_width=True)

else:
    st.info("Upload file to start analytics")
