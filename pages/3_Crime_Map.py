import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import load_master_data, load_geojson_data

st.set_page_config(page_title="Geospatial Insights", page_icon="🗺️", layout="wide")
st.title("🗺️ Geospatial Insights")
st.write("Use the filters to explore historical crime patterns across NSW suburbs.")

master_df = load_master_data()
nsw_geojson = load_geojson_data()

if master_df.empty or nsw_geojson is None:
    st.error("Could not load necessary data files.")
else:
    st.sidebar.header("🗺️ Map Filters")
    crime_metrics = [col for col in master_df.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]
    years = sorted(master_df['Year'].unique(), reverse=True)

    selected_offence = st.sidebar.selectbox("Select Offence Category:", options=crime_metrics)
    selected_year = st.sidebar.slider("Select Year:", min_value=min(years), max_value=max(years), value=max(years))

    year_df = master_df[master_df['Year'] == selected_year]
    map_data = year_df[['Suburb', selected_offence]].copy()
    map_data.rename(columns={selected_offence: 'Incidents'}, inplace=True)
    map_data['Suburb'] = map_data['Suburb'].str.upper()

    if map_data.empty:
        st.warning("No data found for the selected year and offence category.")
    else:
        st.subheader(f"Hotspots for '{selected_offence}' in {selected_year}")
        fig = px.choropleth_mapbox(
            map_data, geojson=nsw_geojson,
            locations='Suburb', featureidkey="properties.suburb_name",
            color='Incidents', color_continuous_scale="Viridis",
            mapbox_style="carto-positron", zoom=9,
            center={"lat": -33.8688, "lon": 151.2093},
            opacity=0.6, labels={'Incidents': 'Total Incidents'}
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Show Top 10 Suburbs for this selection"):
            st.dataframe(map_data.sort_values('Incidents', ascending=False).head(10))
