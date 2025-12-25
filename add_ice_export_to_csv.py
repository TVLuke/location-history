#!/usr/bin/env python3
import os
import json
import csv
import glob
import pandas as pd
from datetime import datetime
import re

def get_date_from_csv_filename(filename):
    """Extract date from CSV filename (e.g., 20200303.csv -> 20200303)"""
    base = os.path.basename(filename)
    name = os.path.splitext(base)[0]
    return name

def get_timestamp_from_status_filename(filename):
    """Extract timestamp from status filename (e.g., 1740401339055_status.json -> 1740401339055)"""
    base = os.path.basename(filename)
    timestamp_str = base.split('_')[0]
    return int(timestamp_str)

def timestamp_to_datetime(timestamp_ms):
    """Convert millisecond timestamp to datetime object"""
    return datetime.fromtimestamp(timestamp_ms / 1000)

def add_ice_data_to_csv(csv_file, status_files):
    """Add ICE data from status files to a CSV file"""
    try:
        df = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        print(f"Warning: {csv_file} is empty. Creating new DataFrame.")
        df = pd.DataFrame(columns=['time', 'lat', 'lon'])
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return False
    
    # Check for required columns - adapt to the actual column names in the CSV
    time_col = 'time' if 'time' in df.columns else 'timestamp'
    lat_col = 'lat' if 'lat' in df.columns else 'latitude'
    lon_col = 'lon' if 'lon' in df.columns else 'longitude'
    
    if time_col not in df.columns:
        print(f"Warning: {csv_file} does not have a time/timestamp column. Skipping.")
        return False
    
    # Convert to datetime for processing
    try:
        df[time_col] = pd.to_datetime(df[time_col])
    except Exception as e:
        print(f"Error converting timestamps in {csv_file}: {e}")
        return False
        
    # Convert to timezone-naive if timezone-aware
    if df[time_col].dt.tz is not None:
        df[time_col] = df[time_col].dt.tz_localize(None)
        
    # Convert to the correct string format with Z suffix
    df[time_col] = df[time_col].dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    # Process each status file
    ice_data = []
    for status_file in status_files:
        try:
            timestamp_ms = get_timestamp_from_status_filename(status_file)
            timestamp_dt = timestamp_to_datetime(timestamp_ms)
            # Ensure timestamp is timezone-naive
            if hasattr(timestamp_dt, 'tzinfo') and timestamp_dt.tzinfo is not None:
                timestamp_dt = timestamp_dt.replace(tzinfo=None)
                
            # Format timestamp in the correct ISO format with Z suffix
            formatted_timestamp = timestamp_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                
            with open(status_file, 'r') as f:
                status_data = json.load(f)
            
            if 'latitude' in status_data and 'longitude' in status_data:
                # Create data point with the column names matching the CSV
                data_point = {
                    time_col: formatted_timestamp,
                    lat_col: status_data['latitude'],
                    lon_col: status_data['longitude'],
                    'provider': 'wifionice'
                }
                ice_data.append(data_point)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON in {status_file}. Skipping.")
        except Exception as e:
            print(f"Error processing {status_file}: {e}")
    
    if not ice_data:
        print(f"No valid ICE data found for {csv_file}")
        return False
    
    ice_df = pd.DataFrame(ice_data)
    combined_df = pd.concat([df, ice_df], ignore_index=True)
    combined_df = combined_df.sort_values(time_col)
    
    # Remove duplicates if any
    combined_df = combined_df.drop_duplicates(subset=[time_col])
    
    # Ensure all timestamps have the correct format with Z suffix
    if isinstance(combined_df[time_col].iloc[0], datetime):
        combined_df[time_col] = combined_df[time_col].apply(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.000Z'))
    
    # Save back to CSV
    combined_df.to_csv(csv_file, index=False)
    print(f"Added {len(ice_data)} ICE data points to {csv_file}")
    return True

def process_specific_csv(csv_file, trips_dir):
    """Process a specific CSV file with its matching trips directory"""
    # Get date from CSV filename
    date_str = get_date_from_csv_filename(csv_file)
    
    # Check if corresponding trips directory exists
    date_trips_dir = os.path.join(trips_dir, date_str)
    print(f"Looking for trips directory: {date_trips_dir}")
    print(f"Directory exists: {os.path.exists(date_trips_dir)}")
    
    if not os.path.exists(date_trips_dir):
        print(f"No trips directory found for {date_str}. Skipping.")
        return False
    
    # Get all status files for this date
    status_files = glob.glob(os.path.join(date_trips_dir, '*_status.json'))
    if not status_files:
        print(f"No status files found for {date_str}. Skipping.")
        return False
    
    # Add ICE data to CSV
    return add_ice_data_to_csv(csv_file, status_files)

def process_csv_directory():
    """Process all CSV files in the /csv directory"""
    csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv')
    trips_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trips')
    
    print(f"CSV directory path: {csv_dir}")
    print(f"Trips directory path: {trips_dir}")
    
    # Check if trips directory exists
    if not os.path.exists(trips_dir):
        print("Trips directory does not exist. Skipping ICE data export.")
        return
    
    # Check if csv directory exists
    if not os.path.exists(csv_dir):
        print("CSV directory does not exist. Skipping ICE data export.")
        return
        
    # List trips subdirectories
    trips_subdirs = os.listdir(trips_dir)
    print(f"Trips subdirectories: {trips_subdirs}")
    
    # Get all CSV files
    csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
    
    # Process all CSV files
    processed_count = 0
    for csv_file in csv_files:
        date_str = get_date_from_csv_filename(csv_file)
        if date_str in trips_subdirs:
            if process_specific_csv(csv_file, trips_dir):
                processed_count += 1
        else:
            print(f"No trips directory found for {date_str}. Skipping.")
    
    print(f"Processed {processed_count} CSV files with matching trip directories.")
    
    # Special case for 20250816 if it exists
    specific_csv = os.path.join(csv_dir, '20250816.csv')
    if os.path.exists(specific_csv):
        print("\nSpecifically processing 20250816.csv:")
        process_specific_csv(specific_csv, trips_dir)

if __name__ == "__main__":
    # For testing, you can uncomment this line to process just one specific file
    # process_specific_csv('/Users/tvluke/projects/newlocationtrack/csv/20250816.csv', '/Users/tvluke/projects/newlocationtrack/trips')
    process_csv_directory()
