# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

PROCESSED_DATA_FILE = 'crime_data_processed.parquet'

# --- Page Configuration ---
st.set_page_config(page_title="NSW Crime Intelligence Platform", page_icon="🚨", layout="wide")

# --- Data Loading ---
@st.cache_data
# Loads the processed crime incidents dataset for the dossier tool.
def load_processed_crime_data(file_path):
    processed_crime_dataframe = pd.read_parquet(file_path)
    return processed_crime_dataframe

# --- Main Application ---
st.title("🚨 NSW Crime Intelligence Platform")
st.write("An interactive tool to analyze recorded crime incidents across NSW suburbs.")

# Load the data
processed_crime_dataframe = load_processed_crime_data(PROCESSED_DATA_FILE)

# --- Sidebar Filters ---
st.sidebar.header("🔍 Investigation Filters")

# Get lists of unique values for filters
suburbs = sorted(processed_crime_dataframe['Suburb'].unique())
offence_categories = sorted(processed_crime_dataframe['OffenceCategory'].unique())

# Create widgets
selected_suburb = st.sidebar.selectbox("Select a Suburb", options=suburbs, index=suburbs.index('Sydney'))
selected_offences = st.sidebar.multiselect("Select Offence Categories", options=offence_categories, default=['Theft', 'Assault'])

# --- Filtering Logic ---
# Filter data based on user selections
selection_filtered_dataframe = processed_crime_dataframe[
    (processed_crime_dataframe['Suburb'] == selected_suburb) &
    (processed_crime_dataframe['OffenceCategory'].isin(selected_offences))
]

# --- Main Page Display ---
if selection_filtered_dataframe.empty:
    st.warning(f"No data found for the selected criteria in {selected_suburb}.")
else:
    # --- Key Metrics ---
    total_incidents = selection_filtered_dataframe['Incidents'].sum()
    st.metric(label=f"Total Recorded Incidents in {selected_suburb}", value=f"{total_incidents:,}")

    # --- Time Series Analysis ---
    st.subheader("Incidents Over Time")
    
    # Group data by Date and Offence Category for the chart
    incidents_over_time_dataframe = selection_filtered_dataframe.groupby(['Date', 'OffenceCategory'])['Incidents'].sum().reset_index()
    
    crime_timeseries_chart = px.line(
        incidents_over_time_dataframe,
        x='Date',
        y='Incidents',
        color='OffenceCategory',
        title=f"Monthly Incidents in {selected_suburb}",
        labels={'Incidents': 'Number of Incidents', 'Date': 'Month'},
        template='plotly_white'
    )
    crime_timeseries_chart.update_layout(legend_title_text='Offence Category')
    st.plotly_chart(crime_timeseries_chart, use_container_width=True)

    # --- Data Table ---
    with st.expander("Show Raw Data for Selection"):
        st.dataframe(selection_filtered_dataframe)