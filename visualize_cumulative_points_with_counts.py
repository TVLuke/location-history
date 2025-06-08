import os
import geopandas as gpd
from datetime import datetime, timedelta
import json
from shapely.geometry import shape

overwrite = True

progress_tracking = True  # Set to True to track progress in a JSON file

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

# Initialize progress tracking data structure if needed
progress_data = {}
progress_file = os.path.join(base_dir, 'progress.json')

# Load existing progress data if file exists and we're not overwriting
if progress_tracking and os.path.exists(progress_file) and not overwrite:
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {progress_file}, starting with empty progress data")
        progress_data = {}

# Dictionary to track all areas that have ever had points
all_areas_with_points = set()

# Delete progress file if progress_tracking is False
if not progress_tracking and os.path.exists(progress_file):
    os.remove(progress_file)
    print(f"Deleted {progress_file} as progress_tracking is False")

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

        # Store previous counts to detect 0->1 transitions
        previous_counts = {}
        if 'NUMPOINTS' in shapefile_gdf.columns:
            for idx, poly in shapefile_gdf.iterrows():
                if onlygermany:
                    area_name = poly.get('GEN', f"Area_{idx}")
                else:
                    area_name = poly.get('LAU_NAME', f"Area_{idx}")
                previous_counts[area_name] = poly['NUMPOINTS']

        # Initialize the 'NUMPOINTS' column
        shapefile_gdf['NUMPOINTS'] = 0

        # Count points within each polygon
        for idx, poly in shapefile_gdf.iterrows():
            count = points_gdf.within(poly.geometry).sum()
            shapefile_gdf.at[idx, 'NUMPOINTS'] = count

        # Track progress if enabled
        if progress_tracking:
            # Create a dictionary to store area names and their counts
            area_counts = {}
            new_areas = []
            
            # Collect area names and counts
            for idx, poly in shapefile_gdf.iterrows():
                if onlygermany:
                    area_name = poly.get('GEN', f"Area_{idx}")
                else:
                    area_name = poly.get('LAU_NAME', f"Area_{idx}")
                    
                count = poly['NUMPOINTS']
                area_counts[area_name] = int(count)  # Convert numpy.int64 to int for JSON serialization
                
                # Check for new areas with points
                if count > 0:
                    # For the first day, all areas with points are new
                    if date == sorted(os.listdir(cumulative_dir))[0].split('_')[0]:
                        if area_name not in all_areas_with_points:
                            new_areas.append(area_name)
                            all_areas_with_points.add(area_name)
                    # For subsequent days, check if the area wasn't in previous days
                    elif area_name not in all_areas_with_points:
                        new_areas.append(area_name)
                        all_areas_with_points.add(area_name)
            
            # Filter out areas with zero count and get top 10 areas by count
            non_zero_areas = {name: count for name, count in area_counts.items() if count > 0}
            top_areas = sorted(non_zero_areas.items(), key=lambda x: x[1], reverse=True)[:10]
            top_areas_dict = {name: count for name, count in top_areas}
            
            # Store in progress data
            progress_data[date] = {
                "new_areas": new_areas,
                "top_areas": top_areas_dict
            }
            
            # Save progress data to file after each day is processed
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            print(f"Progress data for {date} saved to {progress_file}")

        # Save the updated shapefile
        shapefile_gdf.to_file(output_file_path)
        
        print(f'Processed {cumulative_file} and saved to {output_file_path}')

# Final message if progress tracking is enabled
if progress_tracking:
    print(f"All progress data has been saved to {progress_file}")
