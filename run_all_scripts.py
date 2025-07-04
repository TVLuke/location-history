import subprocess

prepare_data = [
    # Script to extract CSV files
    'extract_csv_files.py',
    #Script to split CSV by day
    'split_csv_by_day.py'
]

# Define the scripts to run. This assumes, that csv files are in the folder `csv` (and named yyyymmdd.csv)
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
    'visualize_points_geopandas_yearly.py',
    # create cropped images (square and vertical)
    'create_cropped_images.py',
    # add progress info to images (TOP 10 and new Locations)
    'add_progress_info.py',
    # Script to create videos from images
    'create_video_from_images.py'
]

# Execute each script in sequence
for script in scripts:
    print(f"Running {script}...")
    subprocess.run(['python3', script], check=True)
    print(f"Finished running {script}.")

print("All scripts executed successfully.")
