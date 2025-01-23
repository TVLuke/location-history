import os
import json
import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta

# Set your start date here!
start_date = datetime(2020, 1, 1)

# Define directories
points_dir = 'points'
cumulative_dir = 'cumulative'

# Create cumulative directory if it doesn't exist
os.makedirs(cumulative_dir, exist_ok=True)

# Load all points files
points_files = sorted([f for f in os.listdir(points_dir) if f.endswith('.geojson')])

# Process each day
overwrite = False
current_date = start_date

while current_date <= datetime.now():
    # Format date
    date_str = current_date.strftime('%Y%m%d')
    
    # Save cumulative points
    cumulative_file_path = os.path.join(cumulative_dir, f'{date_str}_cumulative.geojson')
    
    # Check if the cumulative file exists and overwrite is False
    if os.path.exists(cumulative_file_path) and not overwrite:
        current_date += timedelta(days=1)
        continue

    # Determine the previous date
    previous_date = current_date - timedelta(days=1)
    previous_date_str = previous_date.strftime('%Y%m%d')
    previous_cumulative_file_path = os.path.join(cumulative_dir, f'{previous_date_str}_cumulative.geojson')

    # Load cumulative points from the previous date if the file exists
    if os.path.exists(previous_cumulative_file_path):
        cumulative_gdf = gpd.read_file(previous_cumulative_file_path)
    else:
        cumulative_gdf = gpd.GeoDataFrame()

    # Find points file for the current day
    points_file = next((f for f in points_files if date_str in f), None)
    
    # Load points for the current day if available
    if points_file:
        points_gdf = gpd.read_file(os.path.join(points_dir, points_file))
        cumulative_gdf = gpd.GeoDataFrame(pd.concat([cumulative_gdf, points_gdf], ignore_index=True))
    
    cumulative_gdf.to_file(cumulative_file_path, driver='GeoJSON')
    
    # Move to the next day
    current_date += timedelta(days=1)
