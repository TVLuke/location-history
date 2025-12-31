import subprocess
import extract_csv_files
import split_csv_by_day
import add_ice_export_to_csv
import cleanup_for_speed
import ccc_event_filter

# Configuration variables that will be passed to scripts
config = {
    # Script-specific configuration
    'extract_csv_files': {
        'run': True,       # Whether to run this script
        'overwrite': True  # Whether to overwrite existing CSV files
    },
    'split_csv_by_day': {
        'run': False        # Whether to run this script
    },
    'add_ice_export_to_csv': {
        'run': True        # Whether to run this script
    },
    'cleanup_for_speed': {
        'run': True        # Whether to run this script
    },
    'ccc_event_filter': {
        'run': True        # Whether to run this script
    },
    'calculate_speed_and_filter': {
        'run': True,       # Whether to run this script
        'overwrite': False  # Whether to overwrite existing filtered data
    },
    'cumulative_points': {
        'run': True,       # Whether to run this script
        'overwrite': False,  # Whether to overwrite existing cumulative points
        'start_date': '20200101'  # Start date for processing
    },
    'combine_points_yearly': {
        'run': True,       # Whether to run this script
        'overwrite': False  # Whether to overwrite existing yearly combinations
    },
    'visualize_points_with_counts': {
        'run': True,       # Whether to run this script
        'overwrite': False  # Whether to overwrite existing visualizations
    },
    'visualize_cumulative_points_with_counts': {
        'run': True,       # Whether to run this script
        'overwrite': False,  # Whether to overwrite existing visualizations
        'progress_tracking': False  # Whether to track progress
    },
    'visualize_points_geopandas': {
        'run': True,       # Whether to run this script
        'overwrite': False  # Whether to overwrite existing visualizations
    },
    'visualize_points_geopandas_yearly_new': {
        'run': True,       # Whether to run this script
        'overwrite': False  # Whether to overwrite existing visualizations
    },
    'create_cropped_images': {
        'run': True,       # Whether to run this script
        'overwrite': False  # Whether to overwrite existing cropped images
    },
    'create_video_from_images': {
        'run': True,       # Whether to run this script
        'overwrite': False,  # Whether to overwrite existing videos
        'add_music': True  # Whether to add music to videos
    }
}

# Define the preparation scripts
prepare_data = [
    # No scripts here as we're now calling split_csv_by_day as a module
]

# Define the scripts to run. This assumes that csv files are in the folder `csv` (and named yyyymmdd.csv)
scripts = [
    # Script to calculate speed and filter data
    'calculate_speed_and_filter.py',
    # Script to create cumulative points files
    'cumulative_points.py',
    # Combine the points
    'combine_points_yearly.py',
    # Script to visualize counts to cumulative points
    'visualize_points_with_counts.py',
    # Script to visualize counts to cumulative points
    'visualize_cumulative_points_with_counts.py',
    # Script to visualize points with geopandas
    'visualize_points_geopandas.py',
    # and yearly
    'visualize_points_geopandas_yearly_new.py',
    # create cropped images (square and vertical)
    'create_cropped_images.py',
    # Script to create videos from images
    'create_video_from_images.py'
]

# Run extract_csv_files as a module if enabled
if config['extract_csv_files']['run']:
    print("Running extract_csv_files as a module...")
    extract_csv_files.main(overwrite=config['extract_csv_files']['overwrite'])
    print("Finished running extract_csv_files.")
else:
    print("Skipping extract_csv_files (disabled in config)")

# Run split_csv_by_day as a module if enabled
if config['split_csv_by_day']['run']:
    print("Running split_csv_by_day as a module...")
    split_csv_by_day.main()
    print("Finished running split_csv_by_day.")
else:
    print("Skipping split_csv_by_day (disabled in config)")

# Run add_ice_export_to_csv as a module if enabled
if config['add_ice_export_to_csv']['run']:
    print("Running add_ice_export_to_csv as a module...")
    add_ice_export_to_csv.process_csv_directory()
    print("Finished running add_ice_export_to_csv.")
else:
    print("Skipping add_ice_export_to_csv (disabled in config)")

# Run cleanup_for_speed as a module if enabled
if config['cleanup_for_speed']['run']:
    print("Running cleanup_for_speed as a module...")
    cleanup_for_speed.process_csv_directory()
    print("Finished running cleanup_for_speed.")
else:
    print("Skipping cleanup_for_speed (disabled in config)")

# Run ccc_event_filter as a module if enabled
if config['ccc_event_filter']['run']:
    print("Running ccc_event_filter as a module...")
    ccc_event_filter.main()
    print("Finished running ccc_event_filter.")
else:
    print("Skipping ccc_event_filter (disabled in config)")

# Execute each main script in sequence if enabled
for script_name in scripts:
    script_base_name = script_name.replace('.py', '')
    if script_base_name in config and config[script_base_name]['run']:
        print(f"Running {script_name}...")
        
        # Pass overwrite parameter to scripts that support it
        if script_base_name == 'create_cropped_images' and 'overwrite' in config[script_base_name]:
            overwrite_value = str(config[script_base_name]['overwrite']).lower()
            subprocess.run(['python3', script_name, overwrite_value], check=True)
        else:
            subprocess.run(['python3', script_name], check=True)
            
        print(f"Finished running {script_name}.")
    else:
        print(f"Skipping {script_name} (disabled in config)")

print("All scripts executed successfully.")
