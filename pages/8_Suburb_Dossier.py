# pages/7_Suburb_Dossier.py

import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd

# --- Page Config ---
st.set_page_config(page_title="Suburb Dossier", page_icon="📑", layout="wide")

# --- Data Loading ---
@st.cache_data
# Loads the master analytics Parquet and NSW GeoJSON as a GeoDataFrame.
def load_all_data():
    try:
        master_analytics_dataframe = pd.read_parquet('master_analytics_data.parquet')
        suburb_geodataframe = gpd.read_file('nsw_suburbs.json')
        return master_analytics_dataframe, suburb_geodataframe
    except FileNotFoundError:
        return pd.DataFrame(), None

# --- Main App ---
st.title("📑 Suburb Intelligence Dossier")
st.write("Select a suburb to generate a complete analytical report.")

master_analytics_dataframe, suburb_geometries = load_all_data()

if master_analytics_dataframe.empty or suburb_geometries is None:
    st.error("Master data files not found. Please ensure `fuse_data.py` has been run successfully.")
else:
    # --- Sidebar Selector ---
    suburbs = sorted(master_analytics_dataframe['Suburb'].unique())
    selected_suburb = st.selectbox(
        "Select a Suburb for In-Depth Analysis:", 
        options=suburbs
    )

    # --- Filter all data for the selected suburb ---
    selected_suburb_dataframe = master_analytics_dataframe[master_analytics_dataframe['Suburb'] == selected_suburb].copy()
    
    st.header(f"Dossier for: {selected_suburb}")

    # --- Part 1: Key Socio-Economic Metrics ---
    # ... (This section remains the same)
    st.subheader("Socio-Economic Profile")
    latest_year_suburb_dataframe = selected_suburb_dataframe[selected_suburb_dataframe['Year'] == selected_suburb_dataframe['Year'].max()]
    if not latest_year_suburb_dataframe.empty:
        metric_column_venue, metric_column_ier, metric_column_ieo = st.columns(3)
        ier_col = 'Index of Economic Resources'
        ieo_col = 'Index of Education and Occupation'
        with metric_column_venue:
            st.metric("Venue Count", f"{latest_year_suburb_dataframe['VenueCount'].iloc[0]}")
        with metric_column_ier:
            if ier_col in latest_year_suburb_dataframe.columns:
                st.metric(ier_col, f"{latest_year_suburb_dataframe[ier_col].iloc[0]:.0f}")
        with metric_column_ieo:
            if ieo_col in latest_year_suburb_dataframe.columns:
                st.metric(ieo_col, f"{latest_year_suburb_dataframe[ieo_col].iloc[0]:.0f}")
    
    # --- Part 2: Geographic View (Corrected) ---
    st.subheader("Geographic Location")
    
    # Filter the GeoDataFrame for the selected suburb
    suburb_geometry = suburb_geometries[suburb_geometries['suburb_name'] == selected_suburb.upper()]
    
    if not suburb_geometry.empty:
        # --- THIS IS THE FIX ---
        # Use the robust .centroid method to get the center point
        centroid = suburb_geometry.geometry.centroid.iloc[0]
        center_lat, center_lon = centroid.y, centroid.x

        suburb_geometry_map = px.choropleth_mapbox(
            pd.DataFrame([{'Suburb': selected_suburb}]),
            geojson=suburb_geometry.geometry,
            locations='Suburb',
            featureidkey="properties.suburb_name",
            mapbox_style="carto-positron",
            zoom=12,
            center={"lat": center_lat, "lon": center_lon},
            opacity=0.3
        )
        suburb_geometry_map.update_traces(showlegend=False, marker_line_width=2)
        suburb_geometry_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_showscale=False)
        st.plotly_chart(suburb_geometry_map, use_container_width=True)
    
    # --- Part 3: Crime Signature Analysis ---
    # ... (This section remains the same)
    st.subheader("Crime Signature Over Time")
    crime_metric_columns = [column_name for column_name in master_analytics_dataframe.columns if column_name not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]
    top_three_crime_categories = selected_suburb_dataframe[crime_metric_columns].sum().nlargest(3).index.tolist()
    if top_three_crime_categories:
        st.write(f"Analyzing trends for the top 3 crimes: **{', '.join(top_three_crime_categories)}**")
        top_crimes_by_year_chart = px.line(selected_suburb_dataframe, x='Year', y=top_three_crime_categories, title=f"Annual Trends for Top Crimes in {selected_suburb}", markers=True)
        st.plotly_chart(top_crimes_by_year_chart, use_container_width=True)