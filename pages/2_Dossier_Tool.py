import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import load_master_data

# --- Page Config ---
st.set_page_config(page_title="Dossier Tool", page_icon="🔎", layout="wide")

# --- Main App ---
st.title("🔎 Crime Dossier Tool")
st.write("Select a suburb and crime categories to investigate long-term trends.")

master_df = load_master_data()

if master_df.empty:
    st.error("Master data file is empty or not found.")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("🔍 Investigation Filters")
    suburbs = sorted(master_df['Suburb'].unique())
    crime_metrics = [col for col in master_df.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]

    selected_suburb = st.sidebar.selectbox("Select a Suburb", options=suburbs)
    # Allow selecting multiple crime types for comparison
    selected_offences = st.sidebar.multiselect("Select Offence Categories to Compare", options=crime_metrics, default=crime_metrics[:2])

    # --- Filtering Logic ---
    filtered_df = master_df[master_df['Suburb'] == selected_suburb]

    # --- Main Page Display ---
    if filtered_df.empty or not selected_offences:
        st.warning(f"No data found for the selected criteria in {selected_suburb}.")
    else:
        # --- Key Metrics ---
        total_incidents = filtered_df[selected_offences].sum().sum()
        st.metric(label=f"Total Selected Incidents in {selected_suburb} (All Years)", value=f"{total_incidents:,.0f}")

        # --- Time Series Analysis ---
        st.subheader(f"Annual Trends in {selected_suburb}")
        
        # Plot the long-term trend for the selected crimes
        trend_chart = px.line(
            filtered_df,
            x='Year',
            y=selected_offences,
            title=f"Annual Incidents in {selected_suburb}",
            labels={'value': 'Number of Incidents', 'Year': 'Year'},
            template='plotly_white',
            markers=True
        )
        st.plotly_chart(trend_chart, use_container_width=True)

        # --- Data Table ---
        with st.expander("Show Annual Data for Selection"):
            st.dataframe(filtered_df[['Year', 'Suburb'] + selected_offences])