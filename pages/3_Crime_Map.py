import streamlit as st
import pandas as pd
import plotly.express as px
import json

# --- Page Config ---
st.set_page_config(page_title="Crime Hotspot Map", page_icon="🗺️", layout="wide")

# --- Data Loading ---
# In pages/2_Crime_Map.py

# ... (imports and other code) ...

@st.cache_data
# Loads processed crime data and NSW GeoJSON for choropleth mapping.
def load_crime_and_geojson_data():
    crime_dataframe = pd.read_parquet('../crime_data_processed.parquet')
    crime_dataframe['Year'] = crime_dataframe['Date'].dt.year
    crime_dataframe['Suburb'] = crime_dataframe['Suburb'].str.upper()

    with open('nsw_suburbs.json') as geojson_file:
        nsw_suburbs_geojson = json.load(geojson_file)
        
    return crime_dataframe, nsw_suburbs_geojson



# --- Main App ---
st.title("🗺️ NSW Crime Hotspot Map")
st.write("Select a crime category and a year to visualize incident hotspots across Sydney suburbs.")

crime_dataframe, nsw_suburbs_geojson = load_crime_and_geojson_data()

# --- Sidebar Filters ---
st.sidebar.header("🗺️ Map Filters")
offence_categories = sorted(crime_dataframe['OffenceCategory'].unique())

selected_offence = st.sidebar.selectbox(
    "Select Offence Category:",
    options=offence_categories,
    index=offence_categories.index('Theft')
)

years = sorted(crime_dataframe['Year'].unique(), reverse=True)
selected_year = st.sidebar.slider(
    "Select Year:",
    min_value=min(years),
    max_value=max(years),
    value=max(years)
)

# --- Filtering and Aggregation ---
# Filter data based on user selections
selected_offence_year_dataframe = crime_dataframe[
    (crime_dataframe['OffenceCategory'] == selected_offence) &
    (crime_dataframe['Year'] == selected_year)
]

# Aggregate the data by suburb to get a total incident count
suburb_incident_totals_dataframe = selected_offence_year_dataframe.groupby('Suburb')['Incidents'].sum().reset_index()

# --- Map Visualization ---
if suburb_incident_totals_dataframe.empty:
    st.warning("No data found for the selected year and offence category.")
else:
    st.subheader(f"Hotspots for '{selected_offence}' in {selected_year}")

    crime_hotspot_map = px.choropleth_mapbox(
        suburb_incident_totals_dataframe,
        geojson=nsw_suburbs_geojson,
        locations='Suburb',         # Column in your data that matches the GeoJSON key
        featureidkey="properties.suburb_name", # Path to the key in the GeoJSON file
        color='Incidents',          # The column to use for the color scale
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=9,
        center={"lat": -33.8688, "lon": 151.2093},
        opacity=0.6,
        labels={'Incidents': 'Total Incidents'}
    )
    crime_hotspot_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(crime_hotspot_map, use_container_width=True)

    with st.expander("Show Top 10 Suburbs for this selection"):
        st.dataframe(suburb_incident_totals_dataframe.sort_values('Incidents', ascending=False).head(10))