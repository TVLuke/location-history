#!/usr/bin/env python3
"""
Script to clean up CSV files by removing non-ICE data points where the speed between
consecutive points exceeds 400 km/h.
"""

import os
import glob
import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def calculate_speed(row1, row2, time_col, lat_col, lon_col):
    """
    Calculate speed in km/h between two points
    """
    # Calculate distance in kilometers
    distance = haversine_distance(row1[lat_col], row1[lon_col], row2[lat_col], row2[lon_col])
    
    # Calculate time difference in hours
    time_diff = (row2[time_col] - row1[time_col]).total_seconds() / 3600
    
    # Avoid division by zero
    if time_diff == 0:
        return 0
    
    # Calculate speed in km/h
    speed = distance / time_diff
    
    return speed

def is_ice_data_point(row):
    """
    Check if a data point is from ICE data based on provider column
    ICE data points have provider='wifionice'
    """
    # Check if the provider column is set to 'wifionice'
    if 'provider' in row and row['provider'] == 'wifionice':
        return True
    
    return False

def cleanup_csv_file(csv_file, max_speed=400):
    """
    Clean up a CSV file by removing non-ICE data points where the speed between
    consecutive points exceeds max_speed km/h
    """
    try:
        df = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        print(f"Warning: {csv_file} is empty. Skipping.")
        return False
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return False
    
    # Determine column names
    time_col = 'time' if 'time' in df.columns else 'timestamp'
    lat_col = 'lat' if 'lat' in df.columns else 'latitude'
    lon_col = 'lon' if 'lon' in df.columns else 'longitude'
    
    # Check if required columns exist
    if time_col not in df.columns or lat_col not in df.columns or lon_col not in df.columns:
        print(f"Warning: {csv_file} does not have required columns. Skipping.")
        return False
    
    # Convert time column to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except Exception as e:
            print(f"Error converting timestamps in {csv_file}: {e}")
            return False
    
    # Convert to timezone-naive if timezone-aware
    if df[time_col].dt.tz is not None:
        df[time_col] = df[time_col].dt.tz_localize(None)
    
    # Sort by timestamp
    df = df.sort_values(by=time_col)
    
    # Skip files that don't have any ICE data (provider column with wifionice)
    if 'provider' not in df.columns or not (df['provider'] == 'wifionice').any():
        print(f"No ICE data found in {csv_file}. Skipping.")
        return False
    
    # Add a column to mark ICE data points
    df['is_ice_data'] = df.apply(is_ice_data_point, axis=1)
    
    # Print some stats about ICE data points
    ice_count = df['is_ice_data'].sum()
    print(f"Identified {ice_count} ICE data points out of {len(df)} total points in {csv_file}")
    
    # Reset index for easier iteration
    df = df.reset_index(drop=True)
    
    # Add progress reporting
    print(f"Processing {len(df)} points for speed filtering...")
    
    # Vectorized approach for speed calculation
    # Create arrays for lat, lon, and time
    lats = df[lat_col].values
    lons = df[lon_col].values
    times = df[time_col].values
    is_ice = df['is_ice_data'].values
    
    # Iterate through the dataframe and mark points to remove
    points_to_remove = []
    i = 0
    progress_interval = max(1, len(df) // 10)  # Report progress every 10%
    
    while i < len(df) - 1:
        # Report progress
        if i % progress_interval == 0:
            print(f"  Progress: {i}/{len(df)} points processed ({i/len(df)*100:.1f}%)")
            
        # Calculate speed between current point and next point
        speed = calculate_speed(df.iloc[i], df.iloc[i+1], time_col, lat_col, lon_col)
        
        if speed > max_speed:
            # If speed exceeds max_speed, remove the non-ICE point
            if is_ice[i]:
                # Current point is ICE data, remove next point
                points_to_remove.append(i+1)
                # Skip the next point since we're removing it
                i += 2
            elif i+1 < len(df) and is_ice[i+1]:
                # Next point is ICE data, remove current point
                points_to_remove.append(i)
                # Move to the point after next
                i += 1
            else:
                # Neither point is ICE data, remove the current point
                points_to_remove.append(i)
                i += 1  # Always increment to avoid infinite loop
            
            # If we've reached the end of the dataframe, break
            if i >= len(df) - 1:
                break
        else:
            # Speed is acceptable, move to next point
            i += 1
            
    print(f"  Progress: {len(df)}/{len(df)} points processed (100%)")
    print(f"Speed filtering complete. Found {len(points_to_remove)} points to remove.")
    
    # Remove the marked points
    if points_to_remove:
        df = df.drop(points_to_remove)
        print(f"Removed {len(points_to_remove)} points from {csv_file}")
    else:
        print(f"No points removed from {csv_file}")
    
    # Reset index and ensure time format is correct
    df = df.reset_index(drop=True)
    
    # Ensure all timestamps have the correct format with Z suffix
    if isinstance(df[time_col].iloc[0], datetime):
        df[time_col] = df[time_col].apply(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.000Z'))
    
    # Save back to CSV
    df.to_csv(csv_file, index=False)
    
    return True

def process_csv_directory():
    """Process all CSV files in the /csv directory"""
    csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv')
    
    # Check if csv directory exists
    if not os.path.exists(csv_dir):
        print("CSV directory does not exist. Skipping speed cleanup.")
        return
    
    # Get all CSV files
    csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
    
    # Process each CSV file
    processed_count = 0
    for csv_file in csv_files:
        print(f"Processing {csv_file}...")
        if cleanup_csv_file(csv_file):
            processed_count += 1
    
    print(f"Processed {processed_count} CSV files for speed cleanup.")

if __name__ == "__main__":
    process_csv_directory()
