import streamlit as st
import pandas as pd
import pdfplumber
import plotly.express as px


def extract_sbi_pdf(file):
    transactions = []

    with pdfplumber.open(file,password=password) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and len(row) >= 5:
                        transactions.append(row)

    df = pd.DataFrame(transactions)
    df = df.dropna(how='all')


    df.columns = df.iloc[0]
    df = df[1:]

    # Clean column names
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Rename to standard names
    rename_map = {
        'txn_date': 'Txn Date',
        'date': 'Txn Date',
        'description': 'Description',
        'debit': 'Debit',
        'credit': 'Credit',
        'balance': 'Balance'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    for col in ['Debit', 'Credit', 'Balance']:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(",", "")
                .str.replace("DR", "", case=False)
                .str.replace("CR", "", case=False)
                .str.extract(r"([\d.]+)")
                .astype(float)
            )

    return df


st.set_page_config(page_title="📊 Finance Manager", layout="wide")
st.title("📄 Personal Finance Manager")
st.markdown("Upload your **SBI Bank PDF statement** or **CSV file** to analyze your transactions.")

file = st.file_uploader("Upload SBI PDF or CSV", type=["pdf", "csv"])

if file is not None:
    if file.name.endswith(".pdf"):
        password = st.text_input("🔐 Enter PDF password (if required)", type="password")
        try:
            df = extract_sbi_pdf(file)
            st.success("✅ PDF parsed successfully!")
        except Exception as e:
            st.error(f"❌ Error parsing PDF: {e}")
            st.stop()
    else:
        df = pd.read_csv(file)
        st.success("✅ CSV loaded successfully!")

    df.columns = df.columns.str.strip()
    if 'Txn Date' not in df.columns:
        st.error("❌ Missing 'Txn Date' column. Please upload a valid file.")
        st.stop()

    df["Txn Date"] = pd.to_datetime(df["Txn Date"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=["Txn Date"])

    df["Debit"] = pd.to_numeric(df.get("Debit", 0).fillna(0), errors='coerce').fillna(0)
    df["Credit"] = pd.to_numeric(df.get("Credit", 0).fillna(0), errors='coerce').fillna(0)
    df["Balance"] = pd.to_numeric(df.get("Balance", 0).fillna(0), errors='coerce')

    df["Type"] = df["Debit"].apply(lambda x: "Credit" if x == 0 else "Debit")
    df["Net Amount"] = df["Credit"] - df["Debit"]
    df["Month"] = df["Txn Date"].dt.month_name()
    df["Year"] = df["Txn Date"].dt.year
    df = df.sort_values(by="Txn Date")

    total_credit = df["Credit"].sum()
    total_debit = df["Debit"].sum()
    closing_balance = df["Balance"].iloc[-1] if "Balance" in df.columns else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Credit", f"₹{total_credit:,.2f}")
    col2.metric("💸 Total Debit", f"₹{total_debit:,.2f}")
    col3.metric("🏦 Closing Balance", f"₹{closing_balance:,.2f}")

    st.markdown("### 📅 Transaction Timeline")
    fig = px.line(df, x="Txn Date", y="Balance", title="Balance Over Time")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📊 Monthly Spending & Income")
    monthly_summary = df.groupby(["Year", "Month"]).agg({
        "Debit": "sum",
        "Credit": "sum"
    }).reset_index()

    fig2 = px.bar(
        monthly_summary,
        x="Month",
        y=["Debit", "Credit"],
        barmode="group",
        title="Monthly Debit vs Credit",
        color_discrete_map={"Debit": "red", "Credit": "green"},
        facet_col="Year"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ---- Filterable Table ----
    st.markdown("### 🔍 Filtered Transactions")
    search = st.text_input("Search Description", "")
    filtered_df = df[df["Description"].str.contains(search, case=False, na=False)] if search else df
    st.dataframe(filtered_df, use_container_width=True)

    # ---- CSV Download ----
    st.download_button("📥 Download Cleaned CSV", data=filtered_df.to_csv(index=False), file_name="cleaned_transactions.csv", mime="text/csv")

else:
    st.info("⬆️ Please upload a file to begin.")
