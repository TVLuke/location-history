import csv
import json
from datetime import datetime
from geopy.distance import geodesic, distance as geopy_distance
import os
import math
import pytz

# Define the root directory
root_dir = os.path.dirname(os.path.abspath(__file__))

# Define directories for storing output files
all_dir = os.path.join(root_dir, 'all')
slow_dir = os.path.join(root_dir, 'slow')
fast_dir = os.path.join(root_dir, 'fast')
csv_dir = os.path.join(root_dir, 'csv')
points_dir = os.path.join(root_dir, 'points')

# Define file naming scheme
all_file_template = '{}_all.geojson'
slow_file_template = '{}_slow.geojson'
fast_file_template = '{}_fast.geojson'
points_file_template = '{}_points.geojson'

# Introduce the overwrite variable
overwrite = True

# Load exclusion timeframes from exclusion.json
exclusion_file_path = os.path.join(root_dir, 'exclusion.json')
excluded_timeframes = []
if os.path.exists(exclusion_file_path):
    with open(exclusion_file_path, 'r') as exclusion_file:
        exclusion_data = json.load(exclusion_file)
        excluded_timeframes = exclusion_data.get('times', [])
    print(f"Loaded {len(excluded_timeframes)} excluded timeframes from exclusion.json")
else:
    print("Warning: exclusion.json not found. No timeframes will be excluded.")

# Function to check if a timestamp falls within excluded timeframes
def is_excluded(timestamp_str):
    # Parse the timestamp string to datetime object
    time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    try:
        timestamp = datetime.strptime(timestamp_str, time_format)
    except ValueError:
        print(f"Warning: Could not parse timestamp: {timestamp_str}")
        return False
    
    # Convert to UTC timezone for proper comparison
    timestamp = timestamp.replace(tzinfo=pytz.UTC)
    
    # Extract date components for comparison
    timestamp_date = timestamp.date()
    
    # Check if the timestamp falls within any excluded timeframe
    for timeframe in excluded_timeframes:
        try:
            # Parse the start and end times from exclusion.json
            start_time = datetime.strptime(timeframe['start'], "%Y-%m-%d %H:%M:%S.000Z").replace(tzinfo=pytz.UTC)
            end_time = datetime.strptime(timeframe['end'], "%Y-%m-%d %H:%M:%S.000Z").replace(tzinfo=pytz.UTC)
            
            # Extract date components for comparison
            start_date = start_time.date()
            
            # Check if the date matches and the time is within range
            if start_date == timestamp_date and start_time <= timestamp <= end_time:
                return True
        except ValueError as e:
            print(f"Warning: Error parsing date in exclusion.json: {e}")
            continue
    
    return False

# Function to calculate speed in km/h
def calculate_speed(point1, point2):
    time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    time1 = datetime.strptime(point1[0], time_format)
    time2 = datetime.strptime(point2[0], time_format)
    
    # Calculate time difference in hours
    time_diff = (time2 - time1).total_seconds() / 3600.0
    
    # Calculate distance in kilometers
    coords_1 = (point1[1], point1[2])
    coords_2 = (point2[1], point2[2])
    distance = geodesic(coords_1, coords_2).kilometers
    
    # Calculate speed
    if time_diff > 0:
        speed = distance / time_diff
    else:
        speed = 0
    return speed

# Function to combine consecutive paths with matching endpoints
def combine_paths(geojson_data):
    combined_features = []
    current_path = None

    for feature in geojson_data['features']:
        if current_path is None:
            current_path = feature
        else:
            current_end = current_path['geometry']['coordinates'][-1]
            next_start = feature['geometry']['coordinates'][0]
            if current_end == next_start:
                # Combine the paths
                current_path['geometry']['coordinates'].extend(feature['geometry']['coordinates'][1:])
            else:
                combined_features.append(current_path)
                current_path = feature

    if current_path is not None:
        combined_features.append(current_path)

    geojson_data['features'] = combined_features
    return geojson_data

# Function to generate points along a path
def generate_points_along_path(path, interval_meters=500):
    points = []
    coords = path['geometry']['coordinates']
    remaining_distance = 0

    for i in range(len(coords) - 1):
        start = coords[i]
        end = coords[i + 1]
        start_point = (start[1], start[0])  # (latitude, longitude)
        end_point = (end[1], end[0])
        segment_distance = geodesic(start_point, end_point).meters
        total_distance = remaining_distance + segment_distance

        while total_distance >= interval_meters:
            fraction = (interval_meters - remaining_distance) / segment_distance
            intermediate_lat = start_point[0] + fraction * (end_point[0] - start_point[0])
            intermediate_lon = start_point[1] + fraction * (end_point[1] - start_point[1])
            points.append([intermediate_lon, intermediate_lat])
            total_distance -= interval_meters
            remaining_distance = 0
            start_point = (intermediate_lat, intermediate_lon)

        remaining_distance = total_distance

    return points

# Iterate over all CSV files in the csv directory
for csv_filename in os.listdir(csv_dir):
    if csv_filename.endswith('.csv'):
        file_date = os.path.splitext(csv_filename)[0]  # Extract date from filename
        csv_path = os.path.join(csv_dir, csv_filename)

        # Check if all four files exist
        all_file_exists = os.path.exists(os.path.join(all_dir, all_file_template.format(file_date)))
        slow_file_exists = os.path.exists(os.path.join(slow_dir, slow_file_template.format(file_date)))
        fast_file_exists = os.path.exists(os.path.join(fast_dir, fast_file_template.format(file_date)))
        points_file_exists = os.path.exists(os.path.join(points_dir, points_file_template.format(file_date)))

        # If all four files exist and overwrite is False, skip processing
        if all_file_exists and slow_file_exists and fast_file_exists and points_file_exists and not overwrite:
            continue

        # Read CSV and process data
        with open(csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)

        # Skip the header row
        data = data[1:]
        
        # Print the excluded timeframes for debugging
        print(f"Processing file {file_date} with {len(data)} points")
        print(f"Excluded timeframes: {excluded_timeframes}")
        
        # Check if this date has exclusion timeframes
        should_check_exclusion = False
        for timeframe in excluded_timeframes:
            try:
                exclusion_date = datetime.strptime(timeframe['start'], "%Y-%m-%d %H:%M:%S.000Z").date()
                file_date_obj = datetime.strptime(file_date, "%Y%m%d").date()
                if exclusion_date == file_date_obj:
                    should_check_exclusion = True
                    print(f"File date {file_date} matches exclusion date {exclusion_date}")
                    break
            except ValueError as e:
                print(f"Error parsing exclusion date: {e}")
        
        # Create filtered data for slow paths (used for point counting)
        # ALL data is used for all_paths (used for drawing lines)
        if should_check_exclusion:
            filtered_data = [point for point in data if not is_excluded(point[0])]
            excluded_count = len(data) - len(filtered_data)
            if excluded_count > 0:
                print(f"Will exclude {excluded_count} points from slow paths (for region counting), but include in all_paths (for line drawing)")
        else:
            filtered_data = data
            print(f"File date {file_date} does not match any exclusion dates")
        
        # Create empty GeoJSON files if no points in original data
        if not data:
            print(f"No points in {file_date}. Creating empty GeoJSON files.")
            # Prepare empty GeoJSON structures
            slow_paths_geojson = {
                "type": "FeatureCollection",
                "features": []
            }
            fast_paths_geojson = {
                "type": "FeatureCollection",
                "features": []
            }
            all_paths_geojson = {
                "type": "FeatureCollection",
                "features": []
            }
            date_points_geojson = {
                "type": "FeatureCollection",
                "features": []
            }
            
            # Write empty GeoJSON files
            with open(os.path.join(all_dir, all_file_template.format(file_date)), 'w') as all_geojson_file:
                json.dump(all_paths_geojson, all_geojson_file, indent=2)
            
            with open(os.path.join(slow_dir, slow_file_template.format(file_date)), 'w') as slow_geojson_file:
                json.dump(slow_paths_geojson, slow_geojson_file, indent=2)
            
            with open(os.path.join(fast_dir, fast_file_template.format(file_date)), 'w') as fast_geojson_file:
                json.dump(fast_paths_geojson, fast_geojson_file, indent=2)
            
            with open(os.path.join(points_dir, points_file_template.format(file_date)), 'w') as points_geojson_file:
                json.dump(date_points_geojson, points_geojson_file, indent=2)
                
            continue

        # Prepare GeoJSON structures
        slow_paths_geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        fast_paths_geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        all_paths_geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        # Iterate over ALL points for all_paths (used for drawing lines)
        for i in range(len(data) - 1):
            point1 = data[i]
            point2 = data[i + 1]

            # Convert latitude and longitude to float
            point1[1] = float(point1[1])
            point1[2] = float(point1[2])
            point2[1] = float(point2[1])
            point2[2] = float(point2[2])

            speed = calculate_speed(point1, point2)

            # Create a feature for all paths (includes ALL data for line drawing)
            all_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [point1[2], point1[1]],  # GeoJSON uses [longitude, latitude]
                        [point2[2], point2[1]]
                    ]
                },
                "properties": {
                    "speed": speed
                }
            }
            all_paths_geojson["features"].append(all_feature)

            # fast_paths uses all data too
            if speed > 15:
                fast_paths_geojson["features"].append(all_feature)
        
        # Iterate over FILTERED points for slow_paths (used for region point counting)
        for i in range(len(filtered_data) - 1):
            point1 = filtered_data[i]
            point2 = filtered_data[i + 1]

            # Convert latitude and longitude to float
            try:
                p1_lat = float(point1[1])
                p1_lon = float(point1[2])
                p2_lat = float(point2[1])
                p2_lon = float(point2[2])
            except (ValueError, IndexError):
                continue

            speed = calculate_speed([point1[0], p1_lat, p1_lon], [point2[0], p2_lat, p2_lon])

            if speed <= 15:
                slow_feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [p1_lon, p1_lat],
                            [p2_lon, p2_lat]
                        ]
                    },
                    "properties": {
                        "speed": speed
                    }
                }
                slow_paths_geojson["features"].append(slow_feature)

        # Combine paths in each GeoJSON file
        slow_paths_geojson = combine_paths(slow_paths_geojson)
        fast_paths_geojson = combine_paths(fast_paths_geojson)
        all_paths_geojson = combine_paths(all_paths_geojson)

        # Write to GeoJSON files in respective subfolders
        with open(os.path.join(all_dir, all_file_template.format(file_date)), 'w') as all_geojson_file:
            json.dump(all_paths_geojson, all_geojson_file, indent=2)

        with open(os.path.join(slow_dir, slow_file_template.format(file_date)), 'w') as slow_geojson_file:
            json.dump(slow_paths_geojson, slow_geojson_file, indent=2)

        with open(os.path.join(fast_dir, fast_file_template.format(file_date)), 'w') as fast_geojson_file:
            json.dump(fast_paths_geojson, fast_geojson_file, indent=2)

        # Prepare GeoJSON structure for points
        date_points_geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        # Generate points along each path in the slow paths file
        for feature in slow_paths_geojson['features']:
            points = generate_points_along_path(feature)
            for point in points:
                point_feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": point
                    },
                    "properties": {}
                }
                date_points_geojson["features"].append(point_feature)

        # Write points to GeoJSON file
        with open(os.path.join(points_dir, points_file_template.format(file_date)), 'w') as points_geojson_file:
            json.dump(date_points_geojson, points_geojson_file, indent=2)
