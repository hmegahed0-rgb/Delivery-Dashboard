import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Enterprise Ops Control Tower", layout="wide")

st.title("🏢 Enterprise Control Tower V4")
st.markdown("### Advanced Logistics Intelligence Dashboard")

# ---------------------------
# UPLOAD
# ---------------------------
file = st.file_uploader("Upload Data", type=["xlsx", "csv"])

if file:

    df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)

    st.success("Data Loaded Successfully")

    # ---------------------------
    # DATETIME ENGINE
    # ---------------------------
    df["Delivery DateTime"] = pd.to_datetime(
        df["Last Physical Ckpt Date"].astype(str) + " " +
        df["Last Physical Ckpt Time"].astype(str),
        errors="coerce"
    )

    df = df.dropna(subset=["Delivery DateTime"])

    df["Hour"] = df["Delivery DateTime"].dt.hour
    df["Date"] = df["Delivery DateTime"].dt.date

    df["Before_12"] = df["Delivery DateTime"].dt.time < pd.to_datetime("12:00").time()
    df["After_12"] = ~df["Before_12"]

    route_col = "Dest Route"
    station_col = "Arrival Stn"

    # ---------------------------
    # KPIs
    # ---------------------------
    total = len(df)
    before12 = df["Before_12"].sum()
    otd = (before12 / total * 100) if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📦 Total Shipments", total)
    col2.metric("⏰ Before 12", int(before12))
    col3.metric("🚨 After 12", int(df["After_12"].sum()))
    col4.metric("📊 SLA %", f"{otd:.2f}%")

    st.divider()

    # ---------------------------
    # SLA BANDS
    # ---------------------------
    st.subheader("📊 SLA Performance Bands")

    df["SLA Category"] = np.where(
        df["Before_12"] == True, "On Time", "Late"
    )

    sla = df["SLA Category"].value_counts().reset_index()
    sla.columns = ["Category", "Count"]

    fig1 = px.pie(sla, names="Category", values="Count", title="SLA Split")
    st.plotly_chart(fig1, use_container_width=True)

    # ---------------------------
    # ROUTE PERFORMANCE
    # ---------------------------
    st.subheader("🏆 Route Performance Ranking")

    route_perf = df.groupby(route_col).agg(
        Total=("Waybill Number", "count"),
        Before_12=("Before_12", "sum")
    ).reset_index()

    route_perf["OTD %"] = (route_perf["Before_12"] / route_perf["Total"] * 100)

    route_perf = route_perf.sort_values("OTD %", ascending=False)

    fig2 = px.bar(
        route_perf,
        x=route_col,
        y="OTD %",
        color="OTD %",
        title="Route Performance (OTD %)"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # ---------------------------
    # HEATMAP (Route x Hour)
    # ---------------------------
    st.subheader("🔥 Heatmap: Route vs Hour Activity")

    heatmap = df.groupby([route_col, "Hour"]).size().reset_index(name="Shipments")

    fig3 = px.density_heatmap(
        heatmap,
        x="Hour",
        y=route_col,
        z="Shipments",
        color_continuous_scale="Blues",
        title="Operational Activity Heatmap"
    )

    st.plotly_chart(fig3, use_container_width=True)

    # ---------------------------
    # TREND ANALYSIS
    # ---------------------------
    st.subheader("📈 Performance Trend")

    trend = df.groupby("Date").agg(
        Total=("Waybill Number", "count"),
        Before_12=("Before_12", "sum")
    ).reset_index()

    trend["OTD %"] = trend["Before_12"] / trend["Total"] * 100

    fig4 = px.line(
        trend,
        x="Date",
        y="OTD %",
        markers=True,
        title="Daily OTD Trend"
    )

    st.plotly_chart(fig4, use_container_width=True)

    # ---------------------------
    # STATION PERFORMANCE
    # ---------------------------
    st.subheader("📍 Station Performance")

    station_perf = df.groupby(station_col).agg(
        Total=("Waybill Number", "count"),
        Before_12=("Before_12", "sum")
    ).reset_index()

    station_perf["OTD %"] = station_perf["Before_12"] / station_perf["Total"] * 100

    st.dataframe(station_perf.sort_values("OTD %", ascending=False), use_container_width=True)

    # ---------------------------
    # INSIGHTS ENGINE (Simple AI Logic)
    # ---------------------------
    st.subheader("🧠 Auto Insights")

    worst_route = route_perf.tail(1)[route_col].values[0]
    best_route = route_perf.head(1)[route_col].values[0]

    peak_hour = df["Hour"].value_counts().idxmax()

    st.warning(f"🚨 Weakest Route: {worst_route}")
    st.success(f"🏆 Best Route: {best_route}")
    st.info(f"⏰ Peak Operational Hour: {peak_hour}:00")

    # ---------------------------
    # EXPORT
    # ---------------------------
    st.subheader("📤 Export Data")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Processed Data",
        data=csv,
        file_name="processed_ops_data.csv",
        mime="text/csv"
    )

else:
    st.info("Upload file to start Enterprise Analytics")
