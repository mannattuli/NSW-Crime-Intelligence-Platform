import geopandas as gpd

SHAPEFILE_PATH = "shapefile_source/SAL_2021_AUST_GDA2020.shp"
OUTPUT_GEOJSON_PATH = "nsw_suburbs.json"

def create_geojson_with_centroids():
    """
    Reads the shapefile, filters for NSW, and saves a GeoJSON file
    that includes pre-calculated centroid coordinates for each suburb.
    """
    print(f"Loading shapefile from {SHAPEFILE_PATH}...")
    gdf = gpd.read_file(SHAPEFILE_PATH)
    
    print("Filtering for New South Wales...")
    gdf_nsw = gdf[gdf['STE_NAME21'] == 'New South Wales'].copy()

    print("Simplifying geometries for web performance...")
    gdf_nsw['geometry'] = gdf_nsw['geometry'].simplify(tolerance=0.001)
    
    # --- NEW: Pre-calculate centroids ---
    print("Calculating and adding centroids to the data...")
    gdf_nsw['centroid_lon'] = gdf_nsw.geometry.centroid.x
    gdf_nsw['centroid_lat'] = gdf_nsw.geometry.centroid.y
    # --- END NEW ---

    gdf_nsw.rename(columns={'SAL_NAME21': 'suburb_name'}, inplace=True)
    gdf_nsw['suburb_name'] = gdf_nsw['suburb_name'].str.upper()

    print(f"Saving final data to {OUTPUT_GEOJSON_PATH}...")
    # Save the geometry and the new centroid columns
    final_gdf = gdf_nsw[['suburb_name', 'geometry', 'centroid_lon', 'centroid_lat']]
    final_gdf.to_file(OUTPUT_GEOJSON_PATH, driver='GeoJSON')
    
    print("\n✅ Success! Your final GeoJSON file with centroids is ready.")

if __name__ == "__main__":
    create_geojson_with_centroids()