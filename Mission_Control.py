# Mission_Control.py

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="Mission Control - NSW Crime Intelligence", page_icon="📡", layout="wide")

# --- Data Loading ---
@st.cache_data
# Loads the master analytics data for the Mission Control dashboard.
def load_master_analytics_data():
    try:
        master_analytics_dataframe = pd.read_parquet('master_analytics_data.parquet')
        return master_analytics_dataframe
    except FileNotFoundError:
        st.error("Master data file not found. Please ensure `fuse_data.py` has run successfully.")
        return None

# --- Main App ---
st.title("📡 Mission Control: NSW Crime Intelligence")
st.caption(f"Dashboard generated on: {pd.to_datetime('now', utc=True).strftime('%Y-%m-%d %H:%M:%S AEST')}")

master_analytics_dataframe = load_master_analytics_data()

if master_analytics_dataframe is not None and not master_analytics_dataframe.empty:
    # --- Main Layout ---
    alerts_column, hotspots_column = st.columns(2)

    with alerts_column:
        # --- Module 1: Automated Anomaly Ticker ---
        st.subheader("🚨 Key Anomaly Alerts")
        with st.container(border=True):
            latest_year = master_analytics_dataframe['Year'].max()
            baseline_year_start = latest_year - 3
            
            historical_baseline_dataframe = master_analytics_dataframe[(master_analytics_dataframe['Year'] >= baseline_year_start) & (master_analytics_dataframe['Year'] < latest_year)]
            current_year_dataframe = master_analytics_dataframe[master_analytics_dataframe['Year'] == latest_year]
            
            crime_metric_columns = [column_name for column_name in master_analytics_dataframe.columns if column_name not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]
            
            baseline_statistics_dataframe = historical_baseline_dataframe.groupby('Suburb')[crime_metric_columns].agg(['mean', 'std']).reset_index()
            baseline_statistics_dataframe.columns = ['_'.join(column_tuple).strip() for column_tuple in baseline_statistics_dataframe.columns.values]
            
            baseline_comparison_dataframe = pd.merge(current_year_dataframe, baseline_statistics_dataframe, left_on='Suburb', right_on='Suburb_', how='left')

            anomaly_alerts = []
            for crime_metric in crime_metric_columns:
                mean_column_name, std_column_name = f'{crime_metric}_mean', f'{crime_metric}_std'
                baseline_comparison_dataframe['z_score'] = (baseline_comparison_dataframe[crime_metric] - baseline_comparison_dataframe[mean_column_name]).divide(baseline_comparison_dataframe[std_column_name].replace(0, pd.NA)).fillna(0)
                significant_anomalies_dataframe = baseline_comparison_dataframe[(baseline_comparison_dataframe['z_score'] > 2.5) & (baseline_comparison_dataframe[crime_metric] > 5)]
                for _, suburb_record in significant_anomalies_dataframe.iterrows():
                    anomaly_alerts.append((suburb_record['z_score'], f"**{crime_metric}** in **{suburb_record['Suburb']}** ({int(suburb_record[crime_metric])} incidents vs. avg of {suburb_record[mean_column_name]:.1f})"))
            
            anomaly_alerts.sort(key=lambda x: x[0], reverse=True)
            for _, alert_text in anomaly_alerts[:5]:
                st.warning(alert_text)
            st.caption(f"Showing top 5 of {len(anomaly_alerts)} anomalies found for {latest_year} vs. {baseline_year_start}-{latest_year-1} average.")

    with hotspots_column:
        # --- Module 2: Top Hotspots ---
        st.subheader("🔥 Top 5 Crime Hotspots")
        with st.container(border=True):
            latest_year_dataframe = master_analytics_dataframe[master_analytics_dataframe['Year'] == master_analytics_dataframe['Year'].max()]
            most_common_crime = latest_year_dataframe[crime_metric_columns].sum().idxmax()
            
            top_5_suburbs = latest_year_dataframe.nlargest(5, most_common_crime)
            
            st.info(f"Displaying top 5 hotspots for **{most_common_crime}** in {latest_year}.")
            st.dataframe(top_5_suburbs[['Suburb', most_common_crime]].rename(columns={most_common_crime: 'Incidents'}), hide_index=True)
            st.caption("Go to the 'Crime Map' page for a full interactive version.")


    trends_column, correlation_column = st.columns(2)
    
    with trends_column:
        # --- Module 3: Biggest Trends ---
        st.subheader("📈 Major Crime Trends (NSW)")
        with st.container(border=True):
            top_3_crimes = master_analytics_dataframe[crime_metric_columns].sum().nlargest(3).index.tolist()
            top_crime_trends_dataframe = master_analytics_dataframe.groupby('Year')[top_3_crimes].sum().reset_index()
            
            top_crimes_trend_chart = px.line(top_crime_trends_dataframe, x='Year', y=top_3_crimes, title=f"Annual Trend for Top 3 Crimes", markers=True)
            top_crimes_trend_chart.update_layout(margin={"r":10,"t":40,"l":10,"b":10}, height=350)
            st.plotly_chart(top_crimes_trend_chart, use_container_width=True)
            st.caption("Go to the 'Temporal Analysis' page for more detail.")

    with correlation_column:
        # --- Module 4: Strongest Correlation ---
        st.subheader("🔗 Strongest Insight")
        with st.container(border=True):
            latest_year_dataframe = master_analytics_dataframe[master_analytics_dataframe['Year'] == master_analytics_dataframe['Year'].max()]
            socio_metrics = [column_name for column_name in ['Index of Economic Resources', 'VenueCount'] if column_name in latest_year_dataframe.columns]
            
            strongest_corr = 0
            best_pair = (None, None)
            
            for s_metric in socio_metrics:
                for c_metric in crime_metric_columns:
                    corr = latest_year_dataframe[s_metric].corr(latest_year_dataframe[c_metric])
                    if abs(corr) > abs(strongest_corr):
                        strongest_corr = corr
                        best_pair = (s_metric, c_metric)

            if best_pair[0]:
                st.metric(label=f"Strongest Correlation in {latest_year}", value=f"{strongest_corr:.3f}")
                st.info(f"The strongest relationship found was between **{best_pair[0]}** and **{best_pair[1]}**.")
                st.caption("Go to the 'Correlation Lab' page to investigate further.")
            else:
                st.info("No strong correlations found in the latest data.")