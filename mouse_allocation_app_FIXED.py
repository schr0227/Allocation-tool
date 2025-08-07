
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Mouse Allocation Tool", layout="wide")
st.title("🐭 Experimental Mouse Allocation Tool")

st.markdown("""
This tool assigns mice to experimental groups based on:
- **Sex** (M/F)
- **Genotype** (Cre+/Cre−)
- **Von Frey baseline** (primary behavior to balance)
- **Batch** (aiming for all 4 groups per batch)

Each of the four groups will end with **16 mice (8M/8F)**:
1. Cre− + Vehicle  
2. Cre+ + Vehicle  
3. Cre− + Drug A  
4. Cre+ + Drug A
""")

uploaded_file = st.file_uploader("Upload CSV with columns: ID, Sex, Genotype, VonFrey, Grimace, Hotplate, Batch", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith("csv") else pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()

    # Rename columns for consistency
    df.rename(columns={
        'id': 'MouseID',
        'sex': 'Sex',
        'genotype': 'Genotype',
        'vonfrey': 'VonFrey',
        'grimace': 'Grimace',
        'hotplate': 'Hotplate',
        'batch': 'Batch'
    }, inplace=True)

    df['Sex'] = df['Sex'].replace({'Male': 'M', 'Female': 'F'})
    df['AssignedGroup'] = None
    df['Treatment'] = None

    group_map = {
        ("Cre-", "Vehicle"): 1,
        ("Cre+", "Vehicle"): 2,
        ("Cre-", "Drug A"): 3,
        ("Cre+", "Drug A"): 4
    }

    group_counts = {}
    for group in [1, 2, 3, 4]:
        for sex in ["M", "F"]:
            group_counts[(group, sex)] = 0

    group_vonfrey = {(g, s): [] for g in range(1, 5) for s in ['M', 'F']}

    def assign_group(row):
        geno = row['Genotype']
        sex = row['Sex']
        vf = row['VonFrey']

        eligible_treatments = ["Vehicle", "Drug A"]
        global_mean = df[df['Sex'] == sex]['VonFrey'].mean()

        min_dev = float('inf')
        best_group = None
        best_treatment = None

        for treatment in eligible_treatments:
            group = group_map.get((geno, treatment))
            if group is None or group_counts.get((group, sex), 8) >= 8:
                continue

            current = group_vonfrey[(group, sex)]
            new_mean = (sum(current) + vf) / (len(current) + 1)
            deviation = abs(new_mean - global_mean)

            if deviation < min_dev:
                min_dev = deviation
                best_group = group
                best_treatment = treatment

        return best_group, best_treatment

    # Sort by batch to simulate batch-wise processing
    df = df.sort_values(by='Batch')

    for i, row in df.iterrows():
        group, treatment = assign_group(row)
        if group:
            df.at[i, 'AssignedGroup'] = group
            df.at[i, 'Treatment'] = treatment
            group_counts[(group, row['Sex'])] += 1
            group_vonfrey[(group, row['Sex'])].append(row['VonFrey'])

    st.success("✅ Allocation completed.")

    st.subheader("📋 Assigned Table")
    st.dataframe(df)

    st.download_button("Download Assigned CSV", data=df.to_csv(index=False), file_name="assigned_mice.csv")

    st.subheader("📊 Group Summary")
    summary = df.groupby(['AssignedGroup', 'Sex']).agg(
        Count=('MouseID', 'count'),
        MeanVonFrey=('VonFrey', 'mean')
    ).reset_index()
    st.dataframe(summary)

    st.subheader("📈 Von Frey Mean per Group")
    fig, ax = plt.subplots()
    sns.barplot(data=summary, x='AssignedGroup', y='MeanVonFrey', hue='Sex', ax=ax)
    ax.set_ylabel("Mean Von Frey")
    ax.set_xlabel("Group")
    ax.set_title("Von Frey Mean by Group and Sex")
    st.pyplot(fig)

else:
    st.info("👆 Upload a CSV or Excel file to begin.")
