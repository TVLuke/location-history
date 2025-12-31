import os
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from matplotlib.colors import ListedColormap
from PIL import Image, ImageDraw, ImageFont

# Set overwrite flag
overwrite = False

def setup_directories(base_dir):
    """Set up required directories."""
    shapefile_dir = os.path.join(base_dir, 'shapefile_yearly')
    visualizations_dir = os.path.join(base_dir, 'visualizations_yearly_geopandas')
    visualizations_nolines_dir = os.path.join(base_dir, 'visualizations_yearly_geopandas_nolines')
    cumulative_visualizations_dir = os.path.join(base_dir, 'visualizations_cumulative_geopandas')
    cumulative_visualizations_nolines_dir = os.path.join(base_dir, 'visualizations_cumulative_geopandas_nolines')
    all_dir = os.path.join(base_dir, 'all')
    os.makedirs(visualizations_dir, exist_ok=True)
    os.makedirs(visualizations_nolines_dir, exist_ok=True)
    os.makedirs(cumulative_visualizations_dir, exist_ok=True)
    os.makedirs(cumulative_visualizations_nolines_dir, exist_ok=True)
    return shapefile_dir, visualizations_dir, visualizations_nolines_dir, cumulative_visualizations_dir, cumulative_visualizations_nolines_dir, all_dir


def get_year_geojson_files(year, all_dir):
    """Retrieve all GeoJSON files for a specific year from the all directory."""
    geojson_files = []
    for filename in sorted(os.listdir(all_dir)):
        if filename.startswith(year) and filename.endswith('_all.geojson'):
            geojson_path = os.path.join(all_dir, filename)
            if os.path.exists(geojson_path):
                geojson_files.append(geojson_path)
    return geojson_files


def get_cumulative_geojson_files(year, all_dir):
    """Retrieve all GeoJSON files from the beginning up to and including the specified year."""
    geojson_files = []
    target_year = int(year)
    for filename in sorted(os.listdir(all_dir)):
        if filename.endswith('_all.geojson'):
            # Extract year from filename (format: YYYY-MM-DD_all.geojson)
            file_year = int(filename[:4])
            if file_year <= target_year:
                geojson_path = os.path.join(all_dir, filename)
                if os.path.exists(geojson_path):
                    geojson_files.append(geojson_path)
    return geojson_files


def get_cumulative_shapefile_data(year, shapefile_dir, first_year):
    """Load and combine NUMPOINTS from all shapefiles up to and including the specified year."""
    target_year = int(year)
    start_year = int(first_year)
    
    # Load the first shapefile to get the base structure
    first_shapefile = os.path.join(shapefile_dir, f'{first_year}_VG5000_GEM_with_counts.shp')
    cumulative_gdf = gpd.read_file(first_shapefile)
    cumulative_gdf.set_crs(epsg=3857, inplace=True, allow_override=True)
    cumulative_gdf = cumulative_gdf.to_crs(epsg=3857)
    
    # Initialize cumulative NUMPOINTS
    cumulative_gdf['NUMPOINTS'] = cumulative_gdf['NUMPOINTS'].fillna(0)
    
    # Add NUMPOINTS from subsequent years
    for year_val in range(start_year + 1, target_year + 1):
        year_str = str(year_val)
        shapefile_path = os.path.join(shapefile_dir, f'{year_str}_VG5000_GEM_with_counts.shp')
        if os.path.exists(shapefile_path):
            year_gdf = gpd.read_file(shapefile_path)
            year_gdf.set_crs(epsg=3857, inplace=True, allow_override=True)
            year_gdf = year_gdf.to_crs(epsg=3857)
            year_gdf['NUMPOINTS'] = year_gdf['NUMPOINTS'].fillna(0)
            
            # Add the NUMPOINTS from this year to the cumulative total
            cumulative_gdf['NUMPOINTS'] = cumulative_gdf['NUMPOINTS'] + year_gdf['NUMPOINTS']
    
    return cumulative_gdf


def plot_geojson_files(ax, geojson_files, skip_plot=False):
    """Plot GeoJSON files with varying alpha values."""
    if skip_plot:
        return  # Skip plotting if requested
    
    if len(geojson_files) >= 2:
        for idx, geojson_file in enumerate(geojson_files):
            gdf = gpd.read_file(geojson_file)
            if gdf.empty:
                continue  # Skip empty GeoDataFrames
            gdf.set_crs(epsg=4326, inplace=True)
            gdf = gdf.to_crs(epsg=3857)
            alpha_value = 0.1 + (0.9 * idx / (len(geojson_files) - 1))  # Gradually increase alpha
            alpha_value = min(alpha_value, 1.0)  # Clamp to 1.0 to avoid floating-point precision issues
            gdf.plot(ax=ax, color='blue', alpha=alpha_value)
    elif len(geojson_files) == 1:
        # If only one file, plot with full opacity
        gdf = gpd.read_file(geojson_files[0])
        if not gdf.empty:  # Only plot if not empty
            gdf.set_crs(epsg=4326, inplace=True)
            gdf = gdf.to_crs(epsg=3857)
            gdf.plot(ax=ax, color='blue', alpha=1.0)


def plot_shapefile(ax, shapefile_path, country_gdf, cumulative_gdf=None):
    """Plot the shapefile with a defined colormap and set map limits based on country_gdf."""
    if cumulative_gdf is not None:
        # Use the provided cumulative data
        shapefile_gdf = cumulative_gdf
    else:
        # Load the shapefile normally
        shapefile_gdf = gpd.read_file(shapefile_path)
        shapefile_gdf.set_crs(epsg=3857, inplace=True, allow_override=True)
        shapefile_gdf = shapefile_gdf.to_crs(epsg=3857)

    # Define a new colormap for NUMPOINTS >= 3
    colors = ['#caaea8']  # First color in the colormap list
    steps = 60

    # Define start and end RGB for the ramp
    r_start, g_start, b_start = 202, 174, 168  # RGB for #caaea8
    r_end, g_end, b_end = 134, 22, 226          # RGB for #8616e2

    # Generate `steps` colors for the ramp, these will be appended to the initial '#caaea8'
    for i in range(1, steps + 1):
        fraction = i / steps
        r = int(r_start + (r_end - r_start) * fraction)
        g = int(g_start + (g_end - g_start) * fraction)
        b = int(b_start + (b_end - b_start) * fraction)
        
        # Clamp values to 0-255 range to be safe
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    colors.extend(['#8616e2' for _ in range(7501, 10001)])  # Extend to cover potential higher values
    defined_cmap = ListedColormap(colors)

    # Filter data to plot only areas with NUMPOINTS >= 3
    shapefile_gdf_to_plot = shapefile_gdf[shapefile_gdf['NUMPOINTS'] >= 3]
    if not shapefile_gdf_to_plot.empty:
        shapefile_gdf_to_plot.plot(ax=ax, column='NUMPOINTS', cmap=defined_cmap, legend=False)

    # Calculate and set fixed map bounds from the country_gdf (ensure it's in EPSG:3857)
    bounds = country_gdf.total_bounds
    zoom_out_factor = 1.2
    x_center = (bounds[0] + bounds[2]) / 2
    y_center = (bounds[1] + bounds[3]) / 2
    x_range = (bounds[2] - bounds[0]) * zoom_out_factor / 2
    y_range = (bounds[3] - bounds[1]) * zoom_out_factor / 2
    ax.set_xlim(x_center - x_range, x_center + x_range)
    ax.set_ylim(y_center - y_range, y_center + y_range)


def add_year_to_image(image_path, year_text, output_dir, is_cumulative=False, first_year=None):
    """Add year text to images and save them in a new directory."""
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        # Calculate font size based on desired text height
        text_height = 150
        # Use a truetype font if available
        try:
            font = ImageFont.truetype("static/black.ttf", text_height)
        except IOError:
            font = ImageFont.load_default()

        # Create year range text for cumulative visualizations
        if is_cumulative and first_year:
            display_text = f"{first_year} - {year_text}"
        else:
            display_text = year_text

        # Calculate text width and adjust position
        text_bbox = draw.textbbox((0, 0), display_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_position = ((img.width - text_width) / 2, img.height - text_height - 30)

        # Draw text on the image
        draw.text(text_position, display_text, font=font, fill='black')

        # Save the modified image
        output_path = os.path.join(output_dir, os.path.basename(image_path))
        img.save(output_path)


# Main execution
base_dir = '.'
shapefile_dir, visualizations_dir, visualizations_nolines_dir, cumulative_visualizations_dir, cumulative_visualizations_nolines_dir, all_dir = setup_directories(base_dir)

# Directory for images with year text
dated_images_dir = os.path.join(base_dir, 'visualizations_with_years')
dated_images_nolines_dir = os.path.join(base_dir, 'visualizations_with_years_nolines')
dated_cumulative_images_dir = os.path.join(base_dir, 'visualizations_cumulative_with_years')
dated_cumulative_images_nolines_dir = os.path.join(base_dir, 'visualizations_cumulative_with_years_nolines')
os.makedirs(dated_images_dir, exist_ok=True)
os.makedirs(dated_images_nolines_dir, exist_ok=True)
os.makedirs(dated_cumulative_images_dir, exist_ok=True)
os.makedirs(dated_cumulative_images_nolines_dir, exist_ok=True)

# Iterate over each shapefile in shapefile_yearly
shapefile_files = [f for f in os.listdir(shapefile_dir) if f.endswith('_VG5000_GEM_with_counts.shp')]

# Determine the first year for cumulative visualizations
first_year = None
if shapefile_files:
    first_year = sorted(shapefile_files)[0].split('_')[0]

for shapefile_file in sorted(shapefile_files):
    year = shapefile_file.split('_')[0]
    shapefile_path = os.path.join(shapefile_dir, shapefile_file)

    output_png_path = os.path.join(visualizations_dir, f'{year}_visualization.png')

    # Check if the output PNG file exists and overwrite is False
    if os.path.exists(output_png_path) and not overwrite:
        print(f'Visualization for {year} already exists, skipping.')
        continue

    fig, ax = plt.subplots(figsize=(38.4, 21.6))
    fig.patch.set_facecolor('#4a79a5')
    ax.set_facecolor('#4a79a5')

    # Load and plot additional layers
    europecoastline_path = os.path.join(base_dir, 'basisdaten', 'europecoastline.shp')
    secondbackground_path = os.path.join(base_dir, 'basisdaten', 'secondbackground.shp')
    germany_path = os.path.join(base_dir, 'basisdaten', 'germanyshape.shp')
    lakes_path = os.path.join(base_dir, 'basisdaten', 'lakes.shp')

    europecoastline_gdf = gpd.read_file(europecoastline_path)
    secondbackground_gdf = gpd.read_file(secondbackground_path)
    germany_gdf = gpd.read_file(germany_path)
    lakes_gdf = gpd.read_file(lakes_path)

    europecoastline_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    europecoastline_gdf = europecoastline_gdf.to_crs(epsg=3857)

    secondbackground_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    secondbackground_gdf = secondbackground_gdf.to_crs(epsg=3857)

    germany_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    germany_gdf = germany_gdf.to_crs(epsg=3857)
    
    lakes_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
    lakes_gdf = lakes_gdf.to_crs(epsg=3857)

    europecoastline_gdf.plot(ax=ax, color='#e9e6be', edgecolor='none') #light background europe
    secondbackground_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #water
    germany_gdf.plot(ax=ax, color='#dcd798', edgecolor='none') #darker background for germany shape

    # Plot GeoJSON files and shapefile (passing germany_gdf to set extents)
    geojson_files = get_year_geojson_files(year, all_dir)
    print(f'Processing {year}: found {len(geojson_files)} GeoJSON files')
    plot_geojson_files(ax, geojson_files)
    plot_shapefile(ax, shapefile_path, germany_gdf)

    lakes_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #lakes
    
    # Remove axis labels and ticks
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='datalim') # Ensure aspect ratio is equal, adjust data limits to fit figure
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save the figure
    plt.savefig(output_png_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    print(f'Visualization for {year} saved to {output_png_path}')

    # Add year to each generated image
    add_year_to_image(output_png_path, year, dated_images_dir)
    print(f'Year-labeled visualization saved to {dated_images_dir}')

print('\n--- Starting yearly visualizations (no lines) ---\n')

# Create yearly visualizations without blue lines
for shapefile_file in sorted(shapefile_files):
    year = shapefile_file.split('_')[0]
    shapefile_path = os.path.join(shapefile_dir, shapefile_file)

    output_png_path = os.path.join(visualizations_nolines_dir, f'{year}_visualization_nolines.png')

    # Check if the output PNG file exists and overwrite is False
    if os.path.exists(output_png_path) and not overwrite:
        print(f'Visualization (no lines) for {year} already exists, skipping.')
        continue

    fig, ax = plt.subplots(figsize=(38.4, 21.6))
    fig.patch.set_facecolor('#4a79a5')
    ax.set_facecolor('#4a79a5')

    # Load and plot additional layers
    europecoastline_path = os.path.join(base_dir, 'basisdaten', 'europecoastline.shp')
    secondbackground_path = os.path.join(base_dir, 'basisdaten', 'secondbackground.shp')
    germany_path = os.path.join(base_dir, 'basisdaten', 'germanyshape.shp')
    lakes_path = os.path.join(base_dir, 'basisdaten', 'lakes.shp')

    europecoastline_gdf = gpd.read_file(europecoastline_path)
    secondbackground_gdf = gpd.read_file(secondbackground_path)
    germany_gdf = gpd.read_file(germany_path)
    lakes_gdf = gpd.read_file(lakes_path)

    europecoastline_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    europecoastline_gdf = europecoastline_gdf.to_crs(epsg=3857)

    secondbackground_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    secondbackground_gdf = secondbackground_gdf.to_crs(epsg=3857)

    germany_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    germany_gdf = germany_gdf.to_crs(epsg=3857)
    
    lakes_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
    lakes_gdf = lakes_gdf.to_crs(epsg=3857)

    europecoastline_gdf.plot(ax=ax, color='#e9e6be', edgecolor='none') #light background europe
    secondbackground_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #water
    germany_gdf.plot(ax=ax, color='#dcd798', edgecolor='none') #darker background for germany shape

    # Skip plotting GeoJSON files (no blue lines)
    geojson_files = get_year_geojson_files(year, all_dir)
    print(f'Processing {year} (no lines): found {len(geojson_files)} GeoJSON files (not plotted)')
    plot_geojson_files(ax, geojson_files, skip_plot=True)
    plot_shapefile(ax, shapefile_path, germany_gdf)

    lakes_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #lakes
    
    # Remove axis labels and ticks
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='datalim') # Ensure aspect ratio is equal, adjust data limits to fit figure
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save the figure
    plt.savefig(output_png_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    print(f'Visualization (no lines) for {year} saved to {output_png_path}')

    # Add year to each generated image
    add_year_to_image(output_png_path, year, dated_images_nolines_dir)
    print(f'Year-labeled visualization (no lines) saved to {dated_images_nolines_dir}')

print('\n--- Starting cumulative visualizations ---\n')

# Create cumulative visualizations
for shapefile_file in sorted(shapefile_files):
    year = shapefile_file.split('_')[0]
    shapefile_path = os.path.join(shapefile_dir, shapefile_file)

    output_png_path = os.path.join(cumulative_visualizations_dir, f'{year}_cumulative_visualization.png')

    # Check if the output PNG file exists and overwrite is False
    if os.path.exists(output_png_path) and not overwrite:
        print(f'Cumulative visualization for {year} already exists, skipping.')
        continue

    fig, ax = plt.subplots(figsize=(38.4, 21.6))
    fig.patch.set_facecolor('#4a79a5')
    ax.set_facecolor('#4a79a5')

    # Load and plot additional layers
    europecoastline_path = os.path.join(base_dir, 'basisdaten', 'europecoastline.shp')
    secondbackground_path = os.path.join(base_dir, 'basisdaten', 'secondbackground.shp')
    germany_path = os.path.join(base_dir, 'basisdaten', 'germanyshape.shp')
    lakes_path = os.path.join(base_dir, 'basisdaten', 'lakes.shp')

    europecoastline_gdf = gpd.read_file(europecoastline_path)
    secondbackground_gdf = gpd.read_file(secondbackground_path)
    germany_gdf = gpd.read_file(germany_path)
    lakes_gdf = gpd.read_file(lakes_path)

    europecoastline_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    europecoastline_gdf = europecoastline_gdf.to_crs(epsg=3857)

    secondbackground_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    secondbackground_gdf = secondbackground_gdf.to_crs(epsg=3857)

    germany_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    germany_gdf = germany_gdf.to_crs(epsg=3857)
    
    lakes_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
    lakes_gdf = lakes_gdf.to_crs(epsg=3857)

    europecoastline_gdf.plot(ax=ax, color='#e9e6be', edgecolor='none') #light background europe
    secondbackground_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #water
    germany_gdf.plot(ax=ax, color='#dcd798', edgecolor='none') #darker background for germany shape

    # Plot cumulative GeoJSON files and shapefile (passing germany_gdf to set extents)
    cumulative_geojson_files = get_cumulative_geojson_files(year, all_dir)
    print(f'Processing cumulative {year}: found {len(cumulative_geojson_files)} GeoJSON files')
    plot_geojson_files(ax, cumulative_geojson_files)
    
    # Get cumulative shapefile data
    cumulative_shapefile_gdf = get_cumulative_shapefile_data(year, shapefile_dir, first_year)
    plot_shapefile(ax, shapefile_path, germany_gdf, cumulative_gdf=cumulative_shapefile_gdf)

    lakes_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #lakes
    
    # Remove axis labels and ticks
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='datalim') # Ensure aspect ratio is equal, adjust data limits to fit figure
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save the figure
    plt.savefig(output_png_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    print(f'Cumulative visualization for {year} saved to {output_png_path}')

    # Add year range to each generated image
    add_year_to_image(output_png_path, year, dated_cumulative_images_dir, is_cumulative=True, first_year=first_year)
    print(f'Year-labeled cumulative visualization saved to {dated_cumulative_images_dir}')

print('\n--- Starting cumulative visualizations (no lines) ---\n')

# Create cumulative visualizations without blue lines
for shapefile_file in sorted(shapefile_files):
    year = shapefile_file.split('_')[0]
    shapefile_path = os.path.join(shapefile_dir, shapefile_file)

    output_png_path = os.path.join(cumulative_visualizations_nolines_dir, f'{year}_cumulative_visualization_nolines.png')

    # Check if the output PNG file exists and overwrite is False
    if os.path.exists(output_png_path) and not overwrite:
        print(f'Cumulative visualization (no lines) for {year} already exists, skipping.')
        continue

    fig, ax = plt.subplots(figsize=(38.4, 21.6))
    fig.patch.set_facecolor('#4a79a5')
    ax.set_facecolor('#4a79a5')

    # Load and plot additional layers
    europecoastline_path = os.path.join(base_dir, 'basisdaten', 'europecoastline.shp')
    secondbackground_path = os.path.join(base_dir, 'basisdaten', 'secondbackground.shp')
    germany_path = os.path.join(base_dir, 'basisdaten', 'germanyshape.shp')
    lakes_path = os.path.join(base_dir, 'basisdaten', 'lakes.shp')

    europecoastline_gdf = gpd.read_file(europecoastline_path)
    secondbackground_gdf = gpd.read_file(secondbackground_path)
    germany_gdf = gpd.read_file(germany_path)
    lakes_gdf = gpd.read_file(lakes_path)

    europecoastline_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    europecoastline_gdf = europecoastline_gdf.to_crs(epsg=3857)

    secondbackground_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    secondbackground_gdf = secondbackground_gdf.to_crs(epsg=3857)

    germany_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
    germany_gdf = germany_gdf.to_crs(epsg=3857)
    
    lakes_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
    lakes_gdf = lakes_gdf.to_crs(epsg=3857)

    europecoastline_gdf.plot(ax=ax, color='#e9e6be', edgecolor='none') #light background europe
    secondbackground_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #water
    germany_gdf.plot(ax=ax, color='#dcd798', edgecolor='none') #darker background for germany shape

    # Skip plotting cumulative GeoJSON files (no blue lines)
    cumulative_geojson_files = get_cumulative_geojson_files(year, all_dir)
    print(f'Processing cumulative {year} (no lines): found {len(cumulative_geojson_files)} GeoJSON files (not plotted)')
    plot_geojson_files(ax, cumulative_geojson_files, skip_plot=True)
    
    # Get cumulative shapefile data
    cumulative_shapefile_gdf = get_cumulative_shapefile_data(year, shapefile_dir, first_year)
    plot_shapefile(ax, shapefile_path, germany_gdf, cumulative_gdf=cumulative_shapefile_gdf)

    lakes_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none') #lakes
    
    # Remove axis labels and ticks
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='datalim') # Ensure aspect ratio is equal, adjust data limits to fit figure
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save the figure
    plt.savefig(output_png_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    print(f'Cumulative visualization (no lines) for {year} saved to {output_png_path}')

    # Add year range to each generated image
    add_year_to_image(output_png_path, year, dated_cumulative_images_nolines_dir, is_cumulative=True, first_year=first_year)
    print(f'Year-labeled cumulative visualization (no lines) saved to {dated_cumulative_images_nolines_dir}')
