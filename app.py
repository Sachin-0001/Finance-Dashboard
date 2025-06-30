import streamlit as st
import pandas as pd

st.set_page_config(page_title="Finance Manager", page_icon=":money_with_wings:", layout="wide")
st.title("Finance Manager App")
file= st.file_uploader("Upload your CSV file", type=["csv"])
if file is not None:
    df= pd.read_csv(file)
    df.columns = df.columns.str.strip()
    df["Txn Date"] = pd.to_datetime(df["Txn Date"], dayfirst=True)
    df["Debit"] = df["Debit"].fillna(0)
    df["Credit"] = df["Credit"].fillna(0)
    df["Debit"] = df["Debit"].astype(float)
    df["Credit"] = df["Credit"].astype(float)
    df["Type"] = df["Debit"].apply(lambda x: "Credit" if x == 0 else "Debit")
    df["Balance"] = df["Balance"].astype(float)
    df["Net Amount"] = (df["Credit"] - df["Debit"])
    df["Month"] = df["Txn Date"].dt.month_name()
    df["Year"] = df["Txn Date"].dt.year
    df = df.sort_values(by="Txn Date")
    # df.drop(columns=["Balance", "Debit/Credit",], inplace=True, errors='ignore')
    total_debit = df["Debit"].sum()
    total_credit = df["Credit"].sum()
    st.metric("Total Spent", f"₹{total_debit:,.2f}")
    st.metric("Total Received", f"₹{total_credit:,.2f}")
    st.line_chart(df.set_index("Txn Date")[["Debit", "Credit"]])
    daily_summary = df.groupby("Txn Date")[["Debit", "Credit"]].sum()

    st.subheader("Daily Debit vs Credit")
    st.line_chart(daily_summary)

    df["Month-Year"] = df["Txn Date"].dt.to_period("M").astype(str)
    monthly_summary = df.groupby("Month-Year")[["Debit", "Credit"]].sum()

    st.subheader("Monthly Cash Flow")
    st.bar_chart(monthly_summary)

    df["Cumulative"] = df["Net Amount"].cumsum()

    st.subheader("Running Balance Over Time")
    st.line_chart(df.set_index("Txn Date")["Cumulative"])
    # df.drop(columns=["Balance", "Debit/Credit","Debit","Credit"], inplace=True, errors='ignore')

    st.subheader("Raw Transaction Data")
    st.write(df)