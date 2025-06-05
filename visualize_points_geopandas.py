import os
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import fiona
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, BoundaryNorm
import matplotlib as mpl
import pandas as pd
from datetime import timedelta

# Set your start date here!
startdate = '2020-01-01'

overwrite = True

def setup_directories(base_dir):
    """Set up required directories."""
    shapefile_dir = os.path.join(base_dir, 'shapefile_cumulative')
    visualizations_dir = os.path.join(base_dir, 'visualizations_geopandas')
    all_dir = os.path.join(base_dir, 'all')
    fast_dir = os.path.join(base_dir, 'fast')
    os.makedirs(visualizations_dir, exist_ok=True)
    return shapefile_dir, visualizations_dir, all_dir, fast_dir


def get_dates_to_process(start_date):
    """Generate a list of dates from the start date to today."""
    return [d.strftime('%Y%m%d') for d in pd.date_range(start=start_date, end=pd.Timestamp.today())]


def get_last_10_days_geojson(date_str, all_dir):
    """Retrieve GeoJSON files for the last 10 days from the specified directory."""
    date = pd.to_datetime(date_str, format='%Y%m%d')
    geojson_files = []
    for i in range(10):
        day = date - timedelta(days=9-i)
        if day < pd.to_datetime('2020-01-01'):
            continue  # Skip days before the start date
        geojson_path = os.path.join(all_dir, f'{day.strftime("%Y%m%d")}_all.geojson')
        if os.path.exists(geojson_path):
            geojson_files.append(geojson_path)
    return geojson_files


def plot_geojson_files(ax, geojson_files):
    """Plot GeoJSON files with varying alpha values."""
    if len(geojson_files) >= 2:
        for idx, geojson_file in enumerate(geojson_files):
            gdf = gpd.read_file(geojson_file)
            gdf.set_crs(epsg=4326, inplace=True)
            gdf = gdf.to_crs(epsg=3857)
            alpha_value = 0.1 + (0.9 * idx / (len(geojson_files) - 1))  # Gradually increase alpha
            gdf.plot(ax=ax, color='blue', alpha=alpha_value)


def plot_shapefile(ax, shapefile_path, country_gdf):
    """Plot the shapefile with a defined colormap and set map limits based on country_gdf."""
    shapefile_gdf = gpd.read_file(shapefile_path)
    shapefile_gdf.set_crs(epsg=3857, inplace=True, allow_override=True)
    shapefile_gdf = shapefile_gdf.to_crs(epsg=3857)
    # Removed initial base plot: shapefile_gdf.plot(ax=ax, color='#e9e6be', edgecolor='none')

    # Define a new colormap for NUMPOINTS >= 5
    colors = ['#caaea8']
    steps = 60
    for i in range(1, steps + 1):
        r = int(220 + (134 - 220) * (i / steps))
        g = int(215 + (22 - 215) * (i / steps))
        b = int(152 + (226 - 152) * (i / steps))
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    colors.extend(['#8616e2' for _ in range(7501, 10001)])  # Extend to cover potential higher values
    defined_cmap = ListedColormap(colors)

    # Filter data to plot only areas with NUMPOINTS >= 5
    shapefile_gdf_to_plot = shapefile_gdf[shapefile_gdf['NUMPOINTS'] >= 5]
    if not shapefile_gdf_to_plot.empty:
        shapefile_gdf_to_plot.plot(ax=ax, column='NUMPOINTS', cmap=defined_cmap, legend=False)
    # Note: missing_kwds is not used here as we filter out low/NaN values explicitly. 
    # If NUMPOINTS could be NaN for rows where it's also >= 5 (unlikely), further handling for NaN might be needed before filtering.

    # Calculate and set fixed map bounds from the country_outline_gdf (ensure it's in EPSG:3857)
    # Assuming country_outline_gdf is already in EPSG:3857 when passed
    bounds = country_gdf.total_bounds
    zoom_out_factor = 1.1
    x_center = (bounds[0] + bounds[2]) / 2
    y_center = (bounds[1] + bounds[3]) / 2
    x_range = (bounds[2] - bounds[0]) * zoom_out_factor / 2
    y_range = (bounds[3] - bounds[1]) * zoom_out_factor / 2
    ax.set_xlim(x_center - x_range, x_center + x_range)
    ax.set_ylim(y_center - y_range, y_center + y_range)

# Main execution
base_dir = '.'
shapefile_dir, visualizations_dir, all_dir, fast_dir = setup_directories(base_dir)
dates_to_process = get_dates_to_process(startdate)

for date in dates_to_process:
    shapefile_path = os.path.join(shapefile_dir, f'{date}_VG5000_GEM_with_counts.shp')
    if not os.path.exists(shapefile_path):
        print(f'Shapefile for {date} not found, skipping.')
        continue

    output_png_path = os.path.join(visualizations_dir, f'{date}_visualization.png')

    # Check if the output PNG file exists and overwrite is False
    if os.path.exists(output_png_path) and not overwrite:
        print(f'Visualization for {date} already exists, skipping.')
        continue

    fig, ax = plt.subplots(figsize=(38.4, 21.6))
    fig.patch.set_facecolor('#4a79a5')
    ax.set_facecolor('#4a79a5')

    # Load and plot additional layers
    europecoastline_path = os.path.join(base_dir, 'basisdaten', 'europecoastline.shp')
    secondbackground_path = os.path.join(base_dir, 'basisdaten', 'secondbackground.shp')
    germany_path = os.path.join(base_dir, 'basisdaten', 'germanyshape.shp')

    europecoastline_gdf = gpd.read_file(europecoastline_path)
    secondbackground_gdf = gpd.read_file(secondbackground_path)
    germany_gdf = gpd.read_file(germany_path)

    europecoastline_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    europecoastline_gdf = europecoastline_gdf.to_crs(epsg=3857)

    secondbackground_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    secondbackground_gdf = secondbackground_gdf.to_crs(epsg=3857)

    germany_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    germany_gdf = germany_gdf.to_crs(epsg=3857)

    europecoastline_gdf.plot(ax=ax, color='#e9e6be', edgecolor='none') #light background europe
    secondbackground_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #water
    germany_gdf.plot(ax=ax, color='#dcd798', edgecolor='none') #darker background for germany shape

    # Plot GeoJSON files and shapefile (passing germany_gdf to set extents)
    geojson_files = get_last_10_days_geojson(date, all_dir)
    plot_geojson_files(ax, geojson_files)
    # germany_gdf is already loaded and in EPSG:3857 at this point in the main loop
    plot_shapefile(ax, shapefile_path, germany_gdf)

    # Remove axis labels and ticks
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='datalim') # Ensure aspect ratio is equal, adjust data limits to fit figure
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save the figure
    plt.savefig(output_png_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    print(f'Visualization for {date} saved to {output_png_path}')
