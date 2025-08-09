# pages/3_Temporal_Analysis.py

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="Temporal Analysis", page_icon="📈", layout="wide")

# --- Data Loading ---
@st.cache_data
# Loads the processed crime data and adds temporal features for analysis.
def load_temporal_crime_data(file_path='crime_data_processed.parquet'):
    temporal_crime_dataframe = pd.read_parquet(file_path)
    temporal_crime_dataframe['Year'] = temporal_crime_dataframe['Date'].dt.year
    temporal_crime_dataframe['Month'] = temporal_crime_dataframe['Date'].dt.month_name()
    temporal_crime_dataframe['DayOfWeek'] = temporal_crime_dataframe['Date'].dt.day_name()
    return temporal_crime_dataframe

# --- Main Application ---
st.title("📈 Temporal Crime Pattern Analysis")
st.write("Analyze crime trends over time. Select criteria from the sidebar to begin.")

temporal_crime_dataframe = load_temporal_crime_data()

# --- Sidebar Filters ---
st.sidebar.header("🗓️ Temporal Filters")
suburbs = sorted(temporal_crime_dataframe['Suburb'].unique())
offence_categories = sorted(temporal_crime_dataframe['OffenceCategory'].unique())

selected_suburb = st.sidebar.selectbox("Select a Suburb", options=suburbs, index=suburbs.index('Sydney'))
selected_offence = st.sidebar.selectbox("Select an Offence Category", options=offence_categories, index=offence_categories.index('Theft'))

# --- Filtering Logic ---
selected_suburb_offence_dataframe = temporal_crime_dataframe[
    (temporal_crime_dataframe['Suburb'] == selected_suburb) &
    (temporal_crime_dataframe['OffenceCategory'] == selected_offence)
]

# --- Main Page Display ---
if selected_suburb_offence_dataframe.empty:
    st.warning(f"No '{selected_offence}' data found for {selected_suburb}.")
else:
    st.success(f"Displaying analysis for **{selected_offence}** in **{selected_suburb}**.")
    
    weekday_column, month_column = st.columns(2)
    
    with weekday_column:
        st.subheader("Incidents by Day of the Week")
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        incidents_by_weekday_dataframe = selected_suburb_offence_dataframe.groupby('DayOfWeek')['Incidents'].sum().reindex(day_order).reset_index()
        weekday_incidents_chart = px.bar(incidents_by_weekday_dataframe, x='DayOfWeek', y='Incidents', title="Weekly Crime Rhythm")
        st.plotly_chart(weekday_incidents_chart, use_container_width=True)

    with month_column:
        st.subheader("Incidents by Month")
        month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        incidents_by_month_dataframe = selected_suburb_offence_dataframe.groupby('Month')['Incidents'].sum().reindex(month_order).reset_index()
        monthly_incidents_chart = px.bar(incidents_by_month_dataframe, x='Month', y='Incidents', title="Seasonal Crime Variation")
        st.plotly_chart(monthly_incidents_chart, use_container_width=True)

    # --- Analysis 3: Long-Term Trend ---
    st.subheader("Long-Term Trend by Year")
    incidents_by_year_dataframe = selected_suburb_offence_dataframe.groupby('Year')['Incidents'].sum().reset_index()
    annual_trend_chart = px.line(incidents_by_year_dataframe, x='Year', y='Incidents', title="Annual Trend", markers=True)
    st.plotly_chart(annual_trend_chart, use_container_width=True)