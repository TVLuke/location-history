import geopandas as gpd
import os
import json
from shapely.geometry import shape

# Define file paths
base_dir = '.'
shapefile_path = os.path.join(base_dir, 'basisdaten', 'VG5000_GEM.shp')
output_shapefile_dir = os.path.join(base_dir, 'shapefile_yearly')
os.makedirs(output_shapefile_dir, exist_ok=True)

# Load the shapefile
shapefile_gdf = gpd.read_file(shapefile_path)
shapefile_gdf.set_crs(epsg=25832, inplace=True)  # Set initial CRS to EPSG:25832
shapefile_gdf = shapefile_gdf.to_crs(epsg=3857)  # Transform to match the map's CRS

# Introduce the overwrite variable
overwrite = False

# Iterate over each GeoJSON file in points_yearly
points_yearly_dir = os.path.join(base_dir, 'points_yearly')
for geojson_file in os.listdir(points_yearly_dir):
    if geojson_file.endswith('.geojson'):
        geojson_path = os.path.join(points_yearly_dir, geojson_file)
        year = geojson_file.split('_')[0]
        output_shapefile_path = os.path.join(output_shapefile_dir, f'{year}_VG5000_GEM_with_counts.shp')

        # Check if the output file exists and overwrite is False
        if os.path.exists(output_shapefile_path) and not overwrite:
            continue

        # Load the GeoJSON file
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)

        # Create a GeoDataFrame for the GeoJSON points
        points_gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        points_gdf.set_crs(epsg=4326, inplace=True)
        points_gdf = points_gdf.to_crs(epsg=3857)

        # Initialize the 'NUMPOINTS' column
        shapefile_gdf['NUMPOINTS'] = 0

        # Count points within each polygon
        for idx, poly in shapefile_gdf.iterrows():
            count = points_gdf.within(poly.geometry).sum()
            shapefile_gdf.at[idx, 'NUMPOINTS'] = count

        # Save the updated shapefile with the 'NUMPOINTS' attribute
        shapefile_gdf.to_file(output_shapefile_path, driver='ESRI Shapefile')
