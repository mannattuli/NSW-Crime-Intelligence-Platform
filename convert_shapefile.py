# convert_shapefile.py
import geopandas as gpd

# --- CONFIGURATION ---
SHAPEFILE_PATH = "shapefile_source/SAL_2021_AUST_GDA2020.shp"
OUTPUT_GEOJSON_PATH = "nsw_suburbs.json"

# Converts the national shapefile to a simplified NSW-only GeoJSON for web use.
def convert_and_filter_shapefile():
    print(f"Loading shapefile from {SHAPEFILE_PATH}...")
    national_suburb_geodataframe = gpd.read_file(SHAPEFILE_PATH)
    print(f"Loaded {len(national_suburb_geodataframe)} total suburbs for Australia.")

    # --- Filter for NSW only ---
    # CORRECTED to use the actual column name 'STE_NAME21'
    print("Filtering for New South Wales...")
    nsw_suburb_geodataframe = national_suburb_geodataframe[national_suburb_geodataframe['STE_NAME21'] == 'New South Wales'].copy()
    print(f"Found {len(nsw_suburb_geodataframe)} suburbs in NSW.")

    # --- Simplify Geometry ---
    print("Simplifying geometries for web performance...")
    nsw_suburb_geodataframe['geometry'] = nsw_suburb_geodataframe['geometry'].simplify(tolerance=0.001)

    # --- Prepare for merging ---
    # CORRECTED to use the actual column name 'SAL_NAME21'
    nsw_suburb_geodataframe.rename(columns={'SAL_NAME21': 'suburb_name'}, inplace=True)
    nsw_suburb_geodataframe['suburb_name'] = nsw_suburb_geodataframe['suburb_name'].str.upper()

    # --- Save to GeoJSON ---
    print(f"Saving filtered data to {OUTPUT_GEOJSON_PATH}...")
    output_geojson_geodataframe = nsw_suburb_geodataframe[['suburb_name', 'geometry']]
    output_geojson_geodataframe.to_file(OUTPUT_GEOJSON_PATH, driver='GeoJSON')
    
    print("\n✅ Success! Your custom GeoJSON file is ready.")

if __name__ == "__main__":
    convert_and_filter_shapefile()