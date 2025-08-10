import pandas as pd
import streamlit as st
from pathlib import Path
import geopandas as gpd

@st.cache_data
def load_master_data():
    """Loads the master analytics Parquet file."""
    project_root = Path(__file__).parent.parent
    data_file_path = project_root / "master_analytics_data.parquet"
    try:
        return pd.read_parquet(data_file_path)
    except Exception as e:
        st.exception(e)
        return pd.DataFrame()

@st.cache_data
def load_geojson_data():
    """Loads the GeoJSON file as a GeoDataFrame."""
    project_root = Path(__file__).parent.parent
    geojson_path = project_root / "nsw_suburbs.json"
    try:
        return gpd.read_file(geojson_path)
    except Exception as e:
        st.exception(e)
        return None

@st.cache_data
def load_processed_crime_data():
    """Loads the processed crime Parquet file (monthly data)."""
    project_root = Path(__file__).parent.parent
    data_file_path = project_root / "crime_data_processed.parquet"
    try:
        return pd.read_parquet(data_file_path)
    except Exception as e:
        st.exception(e)
        return pd.DataFrame()