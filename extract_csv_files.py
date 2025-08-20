import os
import zipfile
import xml.etree.ElementTree as ET
import csv

# Define the CSV headers
csv_headers = [
    "time", "lat", "lon", "elevation", "accuracy", "bearing", "speed", "satellites", "provider", "hdop", "vdop", "pdop", "geoidheight", "ageofdgpsdata", "dgpsid", "activity", "battery", "annotation", "timestamp_ms", "time_offset", "distance", "starttimestamp_ms", "profile_name", "battery_charging"
]

# Function to parse GPX and create CSV
def parse_gpx_to_csv(gpx_file, csv_file):
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    # Detect namespace
    namespace = root.tag.split('}')[0].strip('{')
    ns = {'default': namespace}

    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()

        for trkpt in root.findall('.//default:trkpt', ns):
            row = {
                "time": trkpt.find('default:time', ns).text if trkpt.find('default:time', ns) is not None else '',
                "lat": trkpt.get('lat'),
                "lon": trkpt.get('lon'),
                "elevation": trkpt.find('default:ele', ns).text if trkpt.find('default:ele', ns) is not None else '',
                "provider": trkpt.find('default:src', ns).text if trkpt.find('default:src', ns) is not None else '',
                "speed": trkpt.find('default:speed', ns).text if trkpt.find('default:speed', ns) is not None else '',
                "hdop": trkpt.find('default:hdop', ns).text if trkpt.find('default:hdop', ns) is not None else '',
                "vdop": trkpt.find('default:vdop', ns).text if trkpt.find('default:vdop', ns) is not None else '',
                "pdop": trkpt.find('default:pdop', ns).text if trkpt.find('default:pdop', ns) is not None else '',
                "geoidheight": trkpt.find('default:geoidheight', ns).text if trkpt.find('default:geoidheight', ns) is not None else '',
            }
            writer.writerow(row)

# Function to parse KML and create CSV
def parse_kml_to_csv(kml_file, csv_file):
    tree = ET.parse(kml_file)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}

    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()

        for placemark in root.findall('.//kml:Placemark', ns):
            # Extract activity from Category
            activity = placemark.find('.//kml:ExtendedData/kml:Data[@name="Category"]/kml:value', ns)
            activity_value = activity.text if activity is not None else ''

            # Filter only 'Walking' activities
            if activity_value != 'Walking':
                continue

            # Extract Point coordinates
            point = placemark.find('.//kml:Point/kml:coordinates', ns)
            if point is not None:
                coords = point.text.strip().split(',')
                row = {
                    "time": placemark.find('.//kml:begin', ns).text if placemark.find('.//kml:begin', ns) is not None else '',
                    "lat": coords[1],
                    "lon": coords[0],
                    "elevation": coords[2] if len(coords) > 2 else '',
                    "activity": activity_value
                }
                writer.writerow(row)

            # Extract LineString coordinates
            linestring = placemark.find('.//kml:LineString/kml:coordinates', ns)
            if linestring is not None:
                for coord in linestring.text.strip().split():
                    coords = coord.split(',')
                    row = {
                        "time": placemark.find('.//kml:begin', ns).text if placemark.find('.//kml:begin', ns) is not None else '',
                        "lat": coords[1],
                        "lon": coords[0],
                        "elevation": coords[2] if len(coords) > 2 else '',
                        "activity": activity_value
                    }
                    writer.writerow(row)

# Main function to process files
def main(overwrite=None):
    # Use provided values or defaults
    overwrite = overwrite if overwrite is not None else False
    
    # Define the directories
    root_dir = '.'
    gps_dir = os.path.join(root_dir, 'gps')
    csv_dir = os.path.join(root_dir, 'csv')
    locations_dir = os.path.join(root_dir, 'locations')
    
    # Create the csv directory if it doesn't exist
    os.makedirs(csv_dir, exist_ok=True)
    
    print(f"Extracting CSV files with overwrite={overwrite}")
    
    # Iterate over all files in the gps directory
    for filename in os.listdir(gps_dir):
        if filename.endswith('.zip'):
            zip_path = os.path.join(gps_dir, filename)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Check for CSV files
                    csv_files = [file for file in zip_ref.namelist() if file.endswith('.csv')]
                    if csv_files:
                        # Extract all CSV files to the csv directory
                        for file in csv_files:
                            csv_file_path = os.path.join(csv_dir, file)
                            if not os.path.exists(csv_file_path) or overwrite:
                                zip_ref.extract(file, csv_dir)
                                print(f"Extracted {file} to {csv_dir}")
                    else:
                        # Check for GPX files
                        gpx_files = [file for file in zip_ref.namelist() if file.endswith('.gpx')]
                        for gpx_file in gpx_files:
                            extracted_gpx_path = zip_ref.extract(gpx_file, gps_dir)
                            csv_filename = os.path.splitext(os.path.basename(gpx_file))[0] + '.csv'
                            csv_file_path = os.path.join(csv_dir, csv_filename)
                            # Check if the file exists and overwrite is False
                            if not os.path.exists(csv_file_path) or overwrite:
                                parse_gpx_to_csv(extracted_gpx_path, csv_file_path)
                                print(f"Converted {gpx_file} to {csv_filename}")
            except zipfile.BadZipFile:
                print(f"Skipping {filename}: not a valid zip file")

    # Process KML files
    if os.path.exists(locations_dir):
        for kml_file in os.listdir(locations_dir):
            if kml_file.endswith('.kml'):
                date_str = kml_file.replace('history', '').replace('-', '').split('.')[0]
                csv_file = os.path.join(csv_dir, f'{date_str}.csv')
                # Check if the file exists and overwrite is False
                if not os.path.exists(csv_file) or overwrite:
                    parse_kml_to_csv(os.path.join(locations_dir, kml_file), csv_file)
                    print(f"Converted {kml_file} to {date_str}.csv")
    
    print("CSV extraction completed")
    return True

if __name__ == "__main__":
    # When run directly, use default values
    main()
