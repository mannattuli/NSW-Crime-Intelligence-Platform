# fuse_data.py

import pandas as pd
import geopandas as gpd

# --- CONFIGURATION ---
PROCESSED_CRIME_FILE = 'crime_data_processed.parquet'
PREMISES_FILE = 'premises-list-as-at-8-february-2021.csv'
SHAPEFILE_PATH = "shapefile_source/SAL_2021_AUST_GDA2020.shp"
OUTPUT_FILE = 'master_analytics_data.parquet'

# Builds the master analytics dataset by merging crime data with geospatially derived venue counts.
def create_master_dataset():
    print("--- Creating Master Analytics Dataset with Geospatial Join ---")

    # --- Part 1: Load and Aggregate Crime Data ---
    print(f"Loading crime data from {PROCESSED_CRIME_FILE}...")
    raw_crime_dataframe = pd.read_parquet(PROCESSED_CRIME_FILE)
    raw_crime_dataframe['Year'] = raw_crime_dataframe['Date'].dt.year
    crime_summary_pivot_dataframe = raw_crime_dataframe.pivot_table(
        index=['Suburb', 'Year'], columns='OffenceCategory', 
        values='Incidents', aggfunc='sum'
    ).fillna(0).reset_index()
    crime_summary_pivot_dataframe['Suburb_Clean'] = crime_summary_pivot_dataframe['Suburb'].str.upper().str.strip()

    # --- Part 2: Prepare Geospatial Data ---
    print("Loading suburb shapefile for geospatial analysis...")
    suburb_boundaries_geodataframe = gpd.read_file(SHAPEFILE_PATH)
    suburb_boundaries_geodataframe = suburb_boundaries_geodataframe[suburb_boundaries_geodataframe['STE_NAME21'] == 'New South Wales'].copy()
    suburb_boundaries_geodataframe.rename(columns={'SAL_NAME21': 'Suburb'}, inplace=True)
    suburb_boundaries_geodataframe['Suburb_Clean'] = suburb_boundaries_geodataframe['Suburb'].str.upper().str.strip()
    suburb_boundaries_geodataframe = suburb_boundaries_geodataframe[['Suburb_Clean', 'geometry']]

    # --- Part 3: Load and Prepare Premises Data as Geographic Points ---
    print(f"Loading Premises data from {PREMISES_FILE}...")
    raw_premises_dataframe = pd.read_csv(PREMISES_FILE, encoding='latin1', low_memory=False)
    raw_premises_dataframe.dropna(subset=['Latitude', 'Longitude'], inplace=True)

    # --- THIS IS THE FIX ---
    # The Latitude/Longitude columns have commas and are not clean numbers.
    # We must clean them and convert them to a numeric type before using them.
    print("Cleaning Latitude and Longitude columns to ensure numeric types...")
    raw_premises_dataframe['Latitude'] = raw_premises_dataframe['Latitude'].astype(str).str.replace(',', '').str.strip()
    raw_premises_dataframe['Longitude'] = raw_premises_dataframe['Longitude'].astype(str).str.replace(',', '').str.strip()
    
    raw_premises_dataframe['Latitude'] = pd.to_numeric(raw_premises_dataframe['Latitude'], errors='coerce')
    raw_premises_dataframe['Longitude'] = pd.to_numeric(raw_premises_dataframe['Longitude'], errors='coerce')
    raw_premises_dataframe.dropna(subset=['Latitude', 'Longitude'], inplace=True)
    # --- END OF FIX ---

    premises_points_geodataframe = gpd.GeoDataFrame(
        raw_premises_dataframe, 
        geometry=gpd.points_from_xy(raw_premises_dataframe.Longitude, raw_premises_dataframe.Latitude),
        crs="EPSG:4326"
    )
    premises_points_geodataframe = premises_points_geodataframe.to_crs(suburb_boundaries_geodataframe.crs)

    # --- Part 4: The Geospatial Join ---
    print("Performing geospatial join...")
    premises_within_suburb_geodataframe = gpd.sjoin(premises_points_geodataframe, suburb_boundaries_geodataframe, how="inner", predicate='within')
    venue_counts_per_suburb_dataframe = premises_within_suburb_geodataframe.groupby('Suburb_Clean').size().reset_index(name='VenueCount')
    print(f"Spatially joined and counted venues for {len(venue_counts_per_suburb_dataframe)} suburbs.")

    # --- Part 5: Final Merge ---
    print("Merging crime data with geospatially-derived venue counts...")
    master_analytics_dataframe = pd.merge(crime_summary_pivot_dataframe, venue_counts_per_suburb_dataframe, on='Suburb_Clean', how='left')
    master_analytics_dataframe['VenueCount'] = master_analytics_dataframe['VenueCount'].fillna(0).astype(int)
    
    print(f"✅ Merge successful! Master dataset created with {len(master_analytics_dataframe['Suburb'].unique())} suburbs.")
    print(f"Saving master dataset to {OUTPUT_FILE}...")
    master_analytics_dataframe.to_parquet(OUTPUT_FILE)

    print("\n✅ --- Master Analytics File Created Successfully! ---")
    print("Final Fused Data Head:\n", master_analytics_dataframe.head())

if __name__ == "__main__":
    create_master_dataset()