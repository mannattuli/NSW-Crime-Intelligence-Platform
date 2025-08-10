import pandas as pd
import streamlit as st
from pathlib import Path
import json

@st.cache_data
def load_master_data():
    """
    Finds and loads the master analytics Parquet file using a reliable path.
    Caches the result for performance.
    """
    # This creates a reliable path to the file from anywhere in the project
    project_root = Path(__file__).parent.parent
    data_file_path = project_root / "master_analytics_data.parquet"
    
    try:
        master_df = pd.read_parquet(data_file_path)
        return master_df
    except Exception as e:
        st.exception(e)
        return pd.DataFrame()

@st.cache_data
def load_geojson_data():
    """Loads the GeoJSON file needed for mapping using the standard json library."""
    project_root = Path(__file__).parent.parent
    geojson_path = project_root / "nsw_suburbs.json"
    
    try:
        with open(geojson_path) as f:
            geojson_data = json.load(f)
        return geojson_data
    except Exception as e:
        st.exception(e)
        return None
    
@st.cache_data
def load_processed_crime_data():
    """
    Finds and loads the processed crime Parquet file which has monthly data.
    This is required for the Temporal Analysis page.
    """
    project_root = Path(__file__).parent.parent
    data_file_path = project_root / "crime_data_processed.parquet"
    
    try:
        df = pd.read_parquet(data_file_path)
        return df
    except Exception as e:
        st.exception(e)
        return pd.DataFrame()