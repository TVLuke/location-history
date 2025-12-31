import os
import csv
import math
from datetime import datetime

# Spoofed GPS locations during CCC events - filter these out
# Each entry: (name, latitude, longitude, radius_km)
SPOOF_LOCATIONS = [
    ("'s-Hertogenbosch", 51.6898486, 5.2894054, 100),
    ("Köln Mühlheim", 50.95477, 6.991599, 100),
]

# Event dates: December 26-31 (any year)
EVENT_DAYS = [(12, 26), (12, 27), (12, 28), (12, 29), (12, 30), (12, 31)]


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance in km between two coordinates using the Haversine formula."""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def is_event_date(time_str):
    """Check if the timestamp falls within December 26-31."""
    if not time_str:
        return False
    
    try:
        # Parse the date from ISO format (e.g., "2024-12-27T14:30:00.000Z")
        date_part = time_str.split("T")[0]
        dt = datetime.strptime(date_part, "%Y-%m-%d")
        return (dt.month, dt.day) in EVENT_DAYS
    except (ValueError, IndexError):
        return False


def should_filter_point(lat, lon, time_str):
    """Check if a point should be filtered out."""
    # Only filter during event dates
    if not is_event_date(time_str):
        return False
    
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (ValueError, TypeError):
        return False
    
    # Check if within any spoof location radius
    for name, spoof_lat, spoof_lon, radius_km in SPOOF_LOCATIONS:
        distance = haversine_distance(lat_f, lon_f, spoof_lat, spoof_lon)
        if distance <= radius_km:
            return True
    return False


def filter_csv_file(filepath):
    """Filter a single CSV file, removing points near CCC event during event dates."""
    rows_to_keep = []
    header = None
    filtered_count = 0
    
    with open(filepath, 'r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        header = reader.fieldnames
        
        for row in reader:
            lat = row.get('lat', '')
            lon = row.get('lon', '')
            time_str = row.get('time', '')
            
            if should_filter_point(lat, lon, time_str):
                filtered_count += 1
            else:
                rows_to_keep.append(row)
    
    # Write back the filtered data
    if filtered_count > 0:
        with open(filepath, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows_to_keep)
        print(f"Filtered {filtered_count} points from {os.path.basename(filepath)}")
    
    return filtered_count


def main():
    """Process all CSV files in the csv directory."""
    csv_dir = os.path.join('.', 'csv')
    
    if not os.path.exists(csv_dir):
        print(f"CSV directory '{csv_dir}' does not exist.")
        return False
    
    total_filtered = 0
    files_modified = 0
    
    print(f"CCC Event Filter: Removing spoofed GPS points")
    for name, lat, lon, radius in SPOOF_LOCATIONS:
        print(f"  - {name}: ({lat}, {lon}) within {radius}km")
    print(f"Filter active for dates: December 26-31")
    print("-" * 60)
    
    for filename in sorted(os.listdir(csv_dir)):
        if filename.endswith('.csv'):
            filepath = os.path.join(csv_dir, filename)
            filtered = filter_csv_file(filepath)
            if filtered > 0:
                total_filtered += filtered
                files_modified += 1
    
    print("-" * 60)
    print(f"CCC Event Filter complete: {total_filtered} points removed from {files_modified} files")
    return True


if __name__ == "__main__":
    main()
