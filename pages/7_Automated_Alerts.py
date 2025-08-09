# pages/6_Automated_Alerts.py

import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Automated Alerts", page_icon="🚨", layout="wide")

# --- Data Loading ---
@st.cache_data
# Loads the master analytics dataset used for anomaly detection.
def load_master_analytics_dataset(file_path='../master_analytics_data.parquet'):
    master_analytics_dataframe = pd.read_parquet(file_path)
    return master_analytics_dataframe

# --- Anomaly Detection Logic ---
def generate_yearly_anomaly_alerts(analytics_dataframe, target_year, baseline_year_window, zscore_threshold):
    # Flags suburbs where a crime metric significantly exceeds its recent baseline.
    anomaly_alert_messages = []
    
    # --- THIS IS THE UPGRADED LOGIC ---
    # Define the historical baseline period
    baseline_start_year = target_year - baseline_year_window
    baseline_end_year = target_year - 1
    
    historical_baseline_dataframe = analytics_dataframe[
        (analytics_dataframe['Year'] >= baseline_start_year) & 
        (analytics_dataframe['Year'] <= baseline_end_year)
    ]
    # --- END OF UPGRADE ---

    current_year_dataframe = analytics_dataframe[analytics_dataframe['Year'] == target_year].copy()
    
    if historical_baseline_dataframe.empty:
        return ["Not enough historical data for the selected baseline period."]

    crime_metric_columns = [column_name for column_name in analytics_dataframe.columns if column_name not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]

    suburb_baseline_statistics_dataframe = historical_baseline_dataframe.groupby('Suburb')[crime_metric_columns].agg(['mean', 'std']).reset_index()
    suburb_baseline_statistics_dataframe.columns = ['_'.join(column_tuple).strip() for column_tuple in suburb_baseline_statistics_dataframe.columns.values]
    
    baseline_comparison_dataframe = pd.merge(current_year_dataframe, suburb_baseline_statistics_dataframe, left_on='Suburb', right_on='Suburb_', how='left')
    # Fill std dev of 0 with a small number to avoid division by zero
    for crime_metric in crime_metric_columns:
        if f'{crime_metric}_std' in baseline_comparison_dataframe.columns:
            baseline_comparison_dataframe[f'{crime_metric}_std'].fillna(0, inplace=True)

    for crime_metric in crime_metric_columns:
        mean_column_name = f'{crime_metric}_mean'
        std_column_name = f'{crime_metric}_std'
        
        baseline_comparison_dataframe['z_score'] = (baseline_comparison_dataframe[crime_metric] - baseline_comparison_dataframe[mean_column_name]).divide(baseline_comparison_dataframe[std_column_name].replace(0, pd.NA)).fillna(0)
        
        anomaly_rows_dataframe = baseline_comparison_dataframe[(baseline_comparison_dataframe['z_score'] > zscore_threshold) & (baseline_comparison_dataframe[crime_metric] > baseline_comparison_dataframe[mean_column_name])]
        
        for _, suburb_row in anomaly_rows_dataframe.iterrows():
            alert_text = f"**{crime_metric}** in **{suburb_row['Suburb']}** was significantly high in {target_year}. ({int(suburb_row[crime_metric])} incidents vs. a recent {baseline_year_window}-year average of {suburb_row[mean_column_name]:.1f})"
            anomaly_alert_messages.append(alert_text)
            
    return anomaly_alert_messages

# --- Main App ---
st.title("🚨 Automated Anomaly Report")
st.write("This page flags suburbs where crime in a selected year was statistically higher than its recent historical average.")

master_analytics_dataframe = load_master_analytics_dataset()

if master_analytics_dataframe.empty:
    st.error("Master data file is empty or not found.")
else:
    available_years = sorted(master_analytics_dataframe['Year'].unique(), reverse=True)
    
    year_column, baseline_column = st.columns(2)
    with year_column:
        selected_year = st.selectbox("Select Year to Analyze:", options=available_years)
    with baseline_column:
        baseline_years = st.slider("Select Baseline Period (Years):", 1, 10, 3, help="Compare the selected year against the average of the previous X years.")

    anomaly_sensitivity_threshold = st.sidebar.slider("Anomaly Sensitivity (Standard Deviations):", min_value=1.0, max_value=5.0, value=2.0, step=0.5, help="Lower numbers will generate more alerts.")

    with st.spinner("Analyzing data to find anomalies..."):
        alerts = generate_yearly_anomaly_alerts(master_analytics_dataframe, selected_year, baseline_years, anomaly_sensitivity_threshold)

    st.subheader(f"Found {len(alerts)} Significant Anomalies for {selected_year}")
    st.caption(f"Comparing {selected_year} against the average from {selected_year - baseline_years}–{selected_year - 1}.")

    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No significant anomalies found for the selected criteria.")