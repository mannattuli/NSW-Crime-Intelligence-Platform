import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import load_master_data, load_geojson_data

# --- Page Config ---
st.set_page_config(page_title="Suburb Dossier", page_icon="📑", layout="wide")

# --- Main App ---
st.title("📑 Suburb Intelligence Dossier")
st.write("Select a suburb to generate a complete analytical report.")

master_df = load_master_data()
suburb_geometries = load_geojson_data()

if master_df.empty or suburb_geometries is None:
    st.error("Master data files not found. Please ensure all data processing scripts have run successfully.")
else:
    # --- Sidebar Selector ---
    suburbs = sorted(master_df['Suburb'].unique())
    selected_suburb = st.selectbox("Select a Suburb for In-Depth Analysis:", options=suburbs)

    # --- Filter all data for the selected suburb ---
    suburb_df = master_df[master_df['Suburb'] == selected_suburb].copy()
    
    st.header(f"Dossier for: {selected_suburb}")

    # --- Part 1: Key Socio-Economic Metrics ---
    st.subheader("Socio-Economic Profile")
    latest_year_data = suburb_df[suburb_df['Year'] == suburb_df['Year'].max()]
    if not latest_year_data.empty:
        col1, col2, col3 = st.columns(3)
        ier_col, ieo_col = 'Index of Economic Resources', 'Index of Education and Occupation'
        with col1:
            st.metric("Venue Count", f"{latest_year_data['VenueCount'].iloc[0]}")
        with col2:
            if ier_col in latest_year_data.columns:
                st.metric(ier_col, f"{latest_year_data[ier_col].iloc[0]:.0f}")
        with col3:
            if ieo_col in latest_year_data.columns:
                st.metric(ieo_col, f"{latest_year_data[ieo_col].iloc[0]:.0f}")
    
    # --- Part 2: Geographic View ---
    st.subheader("Geographic Location")
    suburb_geometry = suburb_geometries[suburb_geometries['suburb_name'] == selected_suburb.upper()]
    
    if not suburb_geometry.empty:
        centroid = suburb_geometry.geometry.centroid.iloc[0]
        center_lat, center_lon = centroid.y, centroid.x

        fig_map = px.choropleth_mapbox(
            pd.DataFrame([{'Suburb': selected_suburb}]),
            geojson=suburb_geometry.geometry,
            locations='Suburb',
            featureidkey="properties.suburb_name",
            mapbox_style="carto-positron", zoom=12,
            center={"lat": center_lat, "lon": center_lon},
            opacity=0.3
        )
        fig_map.update_traces(showlegend=False, marker_line_width=2)
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, coloraxis_showscale=False)
        st.plotly_chart(fig_map, use_container_width=True)
    
    # --- Part 3: Crime Signature Analysis ---
    st.subheader("Crime Signature Over Time")
    crime_cols = [col for col in master_df.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]
    top_crimes = suburb_df[crime_cols].sum().nlargest(3).index.tolist()
    
    if top_crimes:
        st.write(f"Analyzing trends for the top 3 crimes: **{', '.join(top_crimes)}**")
        fig_trend = px.line(suburb_df, x='Year', y=top_crimes, title=f"Annual Trends for Top Crimes in {selected_suburb}", markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)