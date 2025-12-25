import os
import geopandas as gpd
import json

overwrite = True

# Define directories
base_dir = '.'
cumulative_dir = os.path.join(base_dir, 'cumulative')
onlygermany = False #if true, only german "Gemeinden" are used, otherwise a european Local Area Units NUTS file is used from http://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/local-administrative-units
if onlygermany:
    shapefile_path = os.path.join(base_dir, 'basisdaten', 'VG5000_GEM.shp')
    # Load the shapefile
    shapefile_gdf = gpd.read_file(shapefile_path)
    shapefile_gdf.set_crs(epsg=25832, inplace=True)  # Set initial CRS to EPSG:25832
    shapefile_gdf = shapefile_gdf.to_crs(epsg=3857)  # Transform to match the map's CRS
else:
    shapefile_path = os.path.join(base_dir, 'basisdaten', 'LAU_RG_01M_2023_3035.shp')
    # Load the shapefile
    shapefile_gdf = gpd.read_file(shapefile_path)
    shapefile_gdf.set_crs(epsg=3035, inplace=True)  # Set initial CRS to EPSG:3035
    shapefile_gdf = shapefile_gdf.to_crs(epsg=3857)  # Transform to match the map's CRS
output_dir = os.path.join(base_dir, 'shapefile_cumulative')

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)


# Process each cumulative file
for cumulative_file in sorted(os.listdir(cumulative_dir)):
    if cumulative_file.endswith('.geojson'):
        cumulative_path = os.path.join(cumulative_dir, cumulative_file)
        date = cumulative_file.split('_')[0]
        output_file_path = os.path.join(output_dir, f'{date}_VG5000_GEM_with_counts.shp')

        # Check if the output file exists and overwrite is False
        if os.path.exists(output_file_path) and not overwrite:
            continue

        # Load the GeoJSON file
        with open(cumulative_path, 'r') as f:
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

        # Save the updated shapefile
        shapefile_gdf.to_file(output_file_path)
        
        print(f'Processed {cumulative_file} and saved to {output_file_path}')
