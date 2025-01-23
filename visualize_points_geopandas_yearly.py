import os
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
import fiona
import pandas as pd
from datetime import timedelta
from matplotlib.colors import ListedColormap
from PIL import Image, ImageDraw, ImageFont

# Introduce the overwrite variable
overwrite = True


def setup_directories(base_dir):
    """Set up required directories."""
    shapefile_dir = os.path.join(base_dir, 'shapefile_yearly')
    visualizations_dir = os.path.join(base_dir, 'visualizations_yearly_geopandas')
    all_dir = os.path.join(base_dir, 'all')
    os.makedirs(visualizations_dir, exist_ok=True)
    return shapefile_dir, visualizations_dir, all_dir

def get_year_geojson(date, dir):
    # get all file paths from the dir where the date 
    # in the filename says, they are from that year.
    files = [os.path.join(dir, f) for f in os.listdir(dir) if f.startswith(date) and f.endswith('.geojson')]
    return files


def plot_geojson_files(ax, geojson_files):
    for idx, geojson_file in enumerate(geojson_files):
        gdf = gpd.read_file(geojson_file)
        gdf.set_crs(epsg=4326, inplace=True)
        gdf = gdf.to_crs(epsg=3857)
        gdf.plot(ax=ax, color='#abc9e5', zorder=3)


def plot_shapefile(ax, shapefile_path):
    """Plot the shapefile with a defined colormap."""
    shapefile_gdf = gpd.read_file(shapefile_path)
    shapefile_gdf.set_crs(epsg=3857, inplace=True, allow_override=True)
    shapefile_gdf = shapefile_gdf.to_crs(epsg=3857)
    shapefile_gdf.plot(ax=ax, color='#dcd798', edgecolor='none', zorder=2)

    # Set transparency for elements where NUMPOINTS is below 5
    shapefile_gdf['color'] = shapefile_gdf['NUMPOINTS'].apply(lambda x: (0, 0, 0, 0) if x < 5 else '#dcd798')

    # Define a new colormap for NUMPOINTS >= 5
    colors = ['#dcd798']
    steps = 60
    for i in range(1, steps + 1):
        r = int(220 + (134 - 220) * (i / steps))
        g = int(215 + (22 - 215) * (i / steps))
        b = int(152 + (226 - 152) * (i / steps))
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    colors.extend(['#8616e2' for _ in range(7501, 10001)])  # Extend to cover potential higher values
    defined_cmap = ListedColormap(colors)

    shapefile_gdf[shapefile_gdf['NUMPOINTS'] >= 5].plot(ax=ax, column='NUMPOINTS', cmap=defined_cmap, legend=False, zorder=3)

    # Set limits in Web Mercator
    bounds = gpd.GeoSeries(shapefile_gdf.geometry).to_crs(epsg=3857).total_bounds
    zoom_out_factor = 1.1
    x_center = (bounds[0] + bounds[2]) / 2
    y_center = (bounds[1] + bounds[3]) / 2
    x_range = (bounds[2] - bounds[0]) * zoom_out_factor / 2
    y_range = (bounds[3] - bounds[1]) * zoom_out_factor / 2
    ax.set_xlim(x_center - x_range, x_center + x_range)
    ax.set_ylim(y_center - y_range, y_center + y_range)

# Function to add year text to images and save them in a new directory
def add_year_to_image(image_path, year_text, output_dir):
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        # Calculate font size based on desired text height
        text_height = 150
        # Use a truetype font if available
        try:
            font = ImageFont.truetype("black.ttf", text_height)
        except IOError:
            font = ImageFont.load_default()

        # Calculate text width and adjust position
        text_bbox = draw.textbbox((0, 0), year_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_position = ((img.width - text_width) / 2, img.height - text_height - 30)

        # Draw text on the image
        draw.text(text_position, year_text, font=font, fill='black')

        # Save the modified image
        output_path = os.path.join(output_dir, os.path.basename(image_path))
        img.save(output_path)

# Main execution
base_dir = '.'
shapefile_dir, visualizations_dir, all_dir = setup_directories(base_dir)

# Directory for images with year text
dated_images_dir = os.path.join(base_dir, 'visualizations_with_years')
os.makedirs(dated_images_dir, exist_ok=True)

# Iterate over each shapefile in shapefile_yearly
date_files = [f for f in os.listdir(shapefile_dir) if f.endswith('_VG5000_GEM_with_counts.shp')]

for shapefile_file in date_files:
    date = shapefile_file.split('_')[0]
    shapefile_path = os.path.join(shapefile_dir, shapefile_file)

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

    europecoastline_gdf.plot(ax=ax, color='#e9e6be', edgecolor='none', zorder=1)
    secondbackground_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none', zorder=1)
    germany_gdf.plot(ax=ax, color='#dcd798', edgecolor='none', zorder=1)

    # Plot GeoJSON files and shapefile
    geojson_files = get_year_geojson(date, all_dir)
    print(geojson_files)
    plot_geojson_files(ax, geojson_files)
    plot_shapefile(ax, shapefile_path)

    # Remove axis labels and ticks
    ax.set_axis_off()
    ax.set_aspect('equal', adjustable='datalim')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save the figure
    plt.savefig(output_png_path, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)

    # Add year to each generated image
    add_year_to_image(output_png_path, date, dated_images_dir)

    print(f'Visualization for {date} saved to {output_png_path}')
