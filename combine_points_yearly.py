import os
import json
from collections import defaultdict

# Define directories
base_dir = '.'
points_dir = os.path.join(base_dir, 'points')
yearly_dir = os.path.join(base_dir, 'points_yearly')
os.makedirs(yearly_dir, exist_ok=True)

# Introduce the overwrite variable
overwrite = True

# Collect points by year
yearly_points = defaultdict(list)

for filename in os.listdir(points_dir):
    if filename.endswith('_points.geojson'):
        # Extract year from the filename
        year = filename[:4]
        if int(year) >= 2020:
            with open(os.path.join(points_dir, filename), 'r') as file:
                data = json.load(file)
                yearly_points[year].extend(data.get('features', []))

# Write combined points for each year
for year, features in yearly_points.items():
    yearly_geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    # Check if the yearly file exists and overwrite is False
    yearly_file_path = os.path.join(yearly_dir, f'{year}_points.geojson')
    if os.path.exists(yearly_file_path) and not overwrite:
        continue
    with open(yearly_file_path, 'w') as outfile:
        json.dump(yearly_geojson, outfile, indent=2)
