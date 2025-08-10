import streamlit as st
import pandas as pd
from src.utils import load_master_data

# --- Page Config ---
st.set_page_config(page_title="Automated Alerts", page_icon="🚨", layout="wide")

# --- Anomaly Detection Logic ---
# Finds suburbs where a crime metric significantly exceeds its recent baseline.
def find_anomalies(analytics_dataframe, target_year, baseline_year_window, zscore_threshold):
    anomaly_alert_messages = []
    
    baseline_start_year = target_year - baseline_year_window
    baseline_end_year = target_year - 1
    
    historical_baseline_dataframe = analytics_dataframe[
        (analytics_dataframe['Year'] >= baseline_start_year) & 
        (analytics_dataframe['Year'] <= baseline_end_year)
    ]

    current_year_dataframe = analytics_dataframe[analytics_dataframe['Year'] == target_year].copy()
    
    if historical_baseline_dataframe.empty:
        return ["Not enough historical data for the selected baseline period."]

    crime_metric_columns = [col for col in analytics_dataframe.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]

    suburb_baseline_stats = historical_baseline_dataframe.groupby('Suburb')[crime_metric_columns].agg(['mean', 'std']).reset_index()
    suburb_baseline_stats.columns = ['_'.join(col).strip() for col in suburb_baseline_stats.columns.values]
    
    comparison_df = pd.merge(current_year_dataframe, suburb_baseline_stats, left_on='Suburb', right_on='Suburb_', how='left')
    
    for crime_metric in crime_metric_columns:
        if f'{crime_metric}_std' in comparison_df.columns:
            comparison_df[f'{crime_metric}_std'].fillna(0, inplace=True)

    for crime_metric in crime_metric_columns:
        mean_col = f'{crime_metric}_mean'
        std_col = f'{crime_metric}_std'
        
        comparison_df['z_score'] = (comparison_df[crime_metric] - comparison_df[mean_col]).divide(comparison_df[std_col].replace(0, pd.NA)).fillna(0)
        
        anomaly_rows = comparison_df[(comparison_df['z_score'] > zscore_threshold) & (comparison_df[crime_metric] > comparison_df[mean_col])]
        
        for _, row in anomaly_rows.iterrows():
            alert_text = f"**{crime_metric}** in **{row['Suburb']}** was significantly high in {target_year}. ({int(row[crime_metric])} incidents vs. a recent {baseline_year_window}-year average of {row[mean_col]:.1f})"
            anomaly_alert_messages.append(alert_text)
            
    return anomaly_alert_messages

# --- Main App ---
st.title("🚨 Automated Anomaly Report")
st.write("This page flags suburbs where crime in a selected year was statistically higher than its recent historical average.")

master_df = load_master_data()

if master_df.empty:
    st.error("Master data file is empty or not found.")
else:
    available_years = sorted(master_df['Year'].unique(), reverse=True)
    
    year_col, baseline_col = st.columns(2)
    with year_col:
        selected_year = st.selectbox("Select Year to Analyze:", options=available_years)
    with baseline_col:
        baseline_years = st.slider("Select Baseline Period (Years):", 1, 10, 3, help="Compare the selected year against the average of the previous X years.")

    anomaly_sensitivity = st.sidebar.slider("Anomaly Sensitivity (Standard Deviations):", 1.0, 5.0, 2.0, 0.5, help="Lower numbers will generate more alerts.")

    with st.spinner("Analyzing data to find anomalies..."):
        alerts = find_anomalies(master_df, selected_year, baseline_years, anomaly_sensitivity)

    st.subheader(f"Found {len(alerts)} Significant Anomalies for {selected_year}")
    st.caption(f"Comparing {selected_year} against the average from {selected_year - baseline_years}–{selected_year - 1}.")

    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No significant anomalies found for the selected criteria.")