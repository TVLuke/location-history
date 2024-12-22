import os
from PIL import Image, ImageDraw, ImageFont
import subprocess
from datetime import datetime

# Define directories
base_dir = '/Users/tvluke/projects/newlocationtrack'
visualizations_dir = os.path.join(base_dir, 'visualizations_geopandas')
dated_images_dir = os.path.join(base_dir, 'visualizations_with_dates')

# Get the current date in YYYYMMDD format
current_date = datetime.now().strftime('%Y%m%d')

# Define the video output path with the current date
video_output_path = os.path.join(base_dir, f'visualization_video_{current_date}.mp4')

# Create new directory for images with date text
os.makedirs(dated_images_dir, exist_ok=True)

# Add a toggle for recreating images
recreate_images = False

# Introduce the overwrite variable
overwrite = False

# Function to add date text to images and save them in a new directory
def add_date_to_image(image_path, date_text, output_dir):
    # Format date to German preferences (DD.MM.YYYY)
    formatted_date = datetime.strptime(date_text, '%Y%m%d').strftime('%d.%m.%Y')
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        # Calculate font size based on desired text height
        text_height = 150
        # Use a truetype font if available
        try:
            font = ImageFont.truetype("arial.ttf", text_height)
        except IOError:
            font = ImageFont.load_default()

        # Calculate text width and adjust position
        text_bbox = draw.textbbox((0, 0), formatted_date, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_position = (10, img.height - text_height - 10)

        # Draw text on the image
        draw.text(text_position, formatted_date, font=font, fill='black')

        # Save the modified image
        output_path = os.path.join(output_dir, os.path.basename(image_path))
        img.save(output_path)


# Process images and add date text
if recreate_images:
    image_files = sorted(os.listdir(visualizations_dir))
    for image_file in image_files:
        if image_file.endswith('_visualization.png'):
            date_text = image_file.split('_')[0]
            image_path = os.path.join(visualizations_dir, image_file)
            add_date_to_image(image_path, date_text, dated_images_dir)
else:
    print("Skipping image creation as per configuration.")

# Create video using ffmpeg with all files in order at 30 fps
ffmpeg_command = [
    'ffmpeg', '-y', '-pattern_type', 'glob', '-framerate', '30', '-i', os.path.join(dated_images_dir, '*.png'),
    '-c:v', 'libx264', '-r', '30', '-pix_fmt', 'yuv420p',
    video_output_path
]

# Check if the video file already exists
if not overwrite and os.path.exists(video_output_path):
    print(f"Video {video_output_path} already exists. Skipping creation.")
else:
    subprocess.run(ffmpeg_command)
    print(f'Video created at {video_output_path}')
