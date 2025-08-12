
import streamlit as st
import pandas as pd
from src.utils import load_master_data

st.set_page_config(page_title="Automated Alerts", page_icon="🚨", layout="wide")

# Finds suburbs where a crime metric significantly exceeds its recent baseline.
def find_anomalies(dataframe, target_year, baseline_period_years, std_dev_threshold):
    alerts = []
    
    baseline_start_year = target_year - baseline_period_years
    baseline_end_year = target_year - 1
    
    historical_df = dataframe[(dataframe['Year'] >= baseline_start_year) & (dataframe['Year'] <= baseline_end_year)]
    current_year_df = dataframe[dataframe['Year'] == target_year].copy()
    
    if historical_df.empty:
        return ["Not enough historical data for the selected baseline period."]

    crime_cols = [col for col in dataframe.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]

    stats = historical_df.groupby('Suburb')[crime_cols].agg(['mean', 'std']).reset_index()
    stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
    
    merged_df = pd.merge(current_year_df, stats, left_on='Suburb', right_on='Suburb_', how='left')
    
    for crime in crime_cols:
        if f'{crime}_std' in merged_df.columns:
            merged_df[f'{crime}_std'].fillna(0, inplace=True)

    for crime in crime_cols:
        mean_col, std_col = f'{crime}_mean', f'{crime}_std'
        merged_df['z_score'] = (merged_df[crime] - merged_df[mean_col]).divide(merged_df[std_col].replace(0, pd.NA)).fillna(0)
        anomalies = merged_df[(merged_df['z_score'] > std_dev_threshold) & (merged_df[crime] > merged_df[mean_col])]
        
        for _, row in anomalies.iterrows():
            alert_text = f"**{crime}** in **{row['Suburb']}** was significantly high in {target_year}. ({int(row[crime])} incidents vs. a recent {baseline_period_years}-year average of {row[mean_col]:.1f})"
            alerts.append(alert_text)
            
    return alerts

st.title("🚨 Automated Anomaly Report")
st.write("This page flags suburbs where crime in a selected year was statistically higher than its recent historical average.")

master_df = load_master_data()

if master_df.empty:
    st.error("Master data file is empty or not found.")
else:
    years = sorted(master_df['Year'].unique(), reverse=True)
    
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Select Year to Analyze:", options=years)
    with col2:
        baseline_years = st.slider("Select Baseline Period (Years):", 1, 10, 3, help="Compare the selected year against the average of the previous X years.")

    threshold = st.sidebar.slider("Anomaly Sensitivity (Standard Deviations):", 1.0, 5.0, 2.0, 0.5, help="Lower numbers will generate more alerts.")

    with st.spinner("Analyzing data to find anomalies..."):
        alerts = find_anomalies(master_df, selected_year, baseline_years, threshold)

    st.subheader(f"Found {len(alerts)} Significant Anomalies for {selected_year}")
    st.caption(f"Comparing {selected_year} against the average from {selected_year - baseline_years}–{selected_year - 1}.")

    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No significant anomalies found for the selected criteria.")
