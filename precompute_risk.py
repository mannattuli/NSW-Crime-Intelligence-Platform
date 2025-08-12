import pandas as pd
import geopandas as gpd
import numpy as np
import gc # Garbage Collector interface

TARGET_AREA = 'Greater Sydney' # Options: 'Greater Sydney' or 'NSW'

# Bounding box for Greater Sydney (approximate)
GREATER_SYDNEY_BOUNDS = {
    "min_lon": 150.5, 
    "min_lat": -34.2, 
    "max_lon": 151.4, 
    "max_lat": -33.5
}

# File paths
SHAPEFILE_PATH = "shapefile_source/SAL_2021_AUST_GDA2020.shp"
PREMISES_FILE = 'premises-list-as-at-8-february-2021.csv'
PROCESSED_CRIME_FILE = 'crime_data_processed.parquet'
OUTPUT_FILE = 'risk_grid.parquet'

GRID_SIZE = 0.002 # The size of each grid square in degrees (~200m)

def create_risk_grid():
    """
    Performs a heavy, one-time calculation to create a risk grid.
    This optimized version focuses on a smaller area and manages memory better.
    """
    print("--- Starting Risk Grid Pre-computation (Optimized) ---")

    # 1. Define the analysis area
    if TARGET_AREA == 'Greater Sydney':
        print("Focusing analysis on Greater Sydney for performance.")
        min_lon, min_lat, max_lon, max_lat = GREATER_SYDNEY_BOUNDS.values()
    else:
        print("Loading suburb shapefile to define NSW boundaries...")
        suburbs_gdf = gpd.read_file(SHAPEFILE_PATH)
        suburbs_gdf_nsw = suburbs_gdf[suburbs_gdf['STE_NAME21'] == 'New South Wales'].copy()
        min_lon, min_lat, max_lon, max_lat = suburbs_gdf_nsw.total_bounds
        del suburbs_gdf, suburbs_gdf_nsw # Free up memory
        gc.collect()

    # 2. Create the Grid
    print("Creating analysis grid...")
    lons = np.arange(min_lon, max_lon, GRID_SIZE)
    lats = np.arange(min_lat, max_lat, GRID_SIZE)
    
    grid_cells = []
    from shapely.geometry import Polygon
    for lon in lons:
        for lat in lats:
            grid_cells.append(Polygon([
                (lon, lat), (lon + GRID_SIZE, lat),
                (lon + GRID_SIZE, lat + GRID_SIZE), (lon, lat + GRID_SIZE)
            ]))
            
    grid_gdf = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:4326")
    grid_gdf['grid_id'] = range(len(grid_gdf))
    print(f"Created a grid with {len(grid_gdf)} cells.")

    # 3. Calculate Venue Density (Optimized)
    print("Calculating venue density...")
    premises_df = pd.read_csv(PREMISES_FILE, encoding='latin1', low_memory=False)
    
    premises_df.dropna(subset=['Postcode'], inplace=True)
    premises_df = premises_df[premises_df['Postcode'].between(1000, 2999)]
    print(f"Filtered to {len(premises_df)} venues within NSW postcodes.")
    
    premises_df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
    premises_df['Latitude'] = pd.to_numeric(premises_df['Latitude'].astype(str).str.replace(',', ''), errors='coerce')
    premises_df['Longitude'] = pd.to_numeric(premises_df['Longitude'].astype(str).str.replace(',', ''), errors='coerce')
    premises_df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
    
    premises_gdf = gpd.GeoDataFrame(
        premises_df, 
        geometry=gpd.points_from_xy(premises_df.Longitude, premises_df.Latitude),
        crs="EPSG:4326"
    )

    joined_venues = gpd.sjoin(grid_gdf, premises_gdf, how="left", predicate='contains')
    venue_counts = joined_venues.groupby('grid_id').size().reset_index(name='VenueCount')
    grid_gdf = pd.merge(grid_gdf, venue_counts, on='grid_id', how='left')
    grid_gdf['VenueCount'] = grid_gdf['VenueCount'].fillna(0)


    del premises_df, premises_gdf, joined_venues, venue_counts
    gc.collect()

    # 4. Calculate Crime Density
    print("Calculating crime density...")
    crime_df = pd.read_parquet(PROCESSED_CRIME_FILE)
    crime_summary = crime_df.groupby('Suburb')['Incidents'].sum().reset_index()
    crime_summary['Suburb_Clean'] = crime_summary['Suburb'].str.upper().str.strip()

    suburbs_gdf = gpd.read_file(SHAPEFILE_PATH)
    suburbs_gdf_nsw = suburbs_gdf[suburbs_gdf['STE_NAME21'] == 'New South Wales'].copy()
    suburbs_gdf_nsw.rename(columns={'SAL_NAME21': 'Suburb'}, inplace=True)
    suburbs_gdf_nsw['Suburb_Clean'] = suburbs_gdf_nsw['Suburb'].str.upper().str.strip()
    
    suburbs_with_crime = pd.merge(suburbs_gdf_nsw, crime_summary, on='Suburb_Clean', how='left')
    suburbs_with_crime['Incidents'] = suburbs_with_crime['Incidents'].fillna(0)
    
    joined_crime = gpd.sjoin(grid_gdf, suburbs_with_crime, how="left", predicate='intersects')
    crime_density = joined_crime.groupby('grid_id')['Incidents'].mean().reset_index()
    grid_gdf = pd.merge(grid_gdf, crime_density, on='grid_id', how='left')
    grid_gdf['Incidents'] = grid_gdf['Incidents'].fillna(0)

    del crime_df, crime_summary, suburbs_gdf, suburbs_gdf_nsw, suburbs_with_crime, joined_crime, crime_density
    gc.collect()

    # 5. Normalize and Save
    print("Normalizing scores and saving final grid...")
    grid_gdf['VenueRisk'] = (grid_gdf['VenueCount'] / grid_gdf['VenueCount'].max()) * 10
    grid_gdf['CrimeRisk'] = (grid_gdf['Incidents'] / grid_gdf['Incidents'].max()) * 10
    
    grid_gdf['min_lon'] = grid_gdf.geometry.bounds['minx']
    grid_gdf['min_lat'] = grid_gdf.geometry.bounds['miny']
    grid_gdf['max_lon'] = grid_gdf.geometry.bounds['maxx']
    grid_gdf['max_lat'] = grid_gdf.geometry.bounds['maxy']

    final_df = grid_gdf[['grid_id', 'VenueRisk', 'CrimeRisk', 'min_lon', 'min_lat', 'max_lon', 'max_lat']]
    final_df.to_parquet(OUTPUT_FILE)

    print(f"\n✅ Success! Optimized risk grid created and saved to {OUTPUT_FILE}.")

if __name__ == "__main__":
    create_risk_grid()
