import os
from PIL import Image, ImageDraw, ImageFont
import subprocess
from datetime import datetime

# Define directories
base_dir = '.'
visualizations_dir = os.path.join(base_dir, 'visualizations_geopandas')
dated_images_dir = os.path.join(base_dir, 'visualizations_with_dates')
square_images_dir = os.path.join(base_dir, 'visualizations_square')
vertical_images_dir = os.path.join(base_dir, 'visualizations_vertical')
square_dated_images_dir = os.path.join(base_dir, 'visualizations_square_with_dates')
vertical_dated_images_dir = os.path.join(base_dir, 'visualizations_vertical_with_dates')

# Get the current date in YYYYMMDD format
current_date = datetime.now().strftime('%Y%m%d')

# Define the video output paths with the current date
video_output_path = os.path.join(base_dir, f'visualization_video_{current_date}.mp4')
video_output_path_square = os.path.join(base_dir, f'visualization_video_square_{current_date}.mp4')
video_output_path_vertical = os.path.join(base_dir, f'visualization_video_vertical_{current_date}.mp4')

# Create new directory for images with date text
os.makedirs(dated_images_dir, exist_ok=True)
os.makedirs(square_dated_images_dir, exist_ok=True)
os.makedirs(vertical_dated_images_dir, exist_ok=True)

# Add a toggle for recreating images
recreate_images = False

# Introduce the overwrite variable
overwrite = False

# Define the path to the JetBrains font
font_path = os.path.join(base_dir, 'static', 'droid', 'droid.ttf')

# Path to the background music file
background_music_path = os.path.join(base_dir, 'static', 'timecode.mp3')

# Function to add date text to images and save them in a new directory
def add_date_to_image(image_path, date_text, output_dir):
    output_path = os.path.join(output_dir, os.path.basename(image_path))
    if not recreate_images and os.path.exists(output_path):
        print(f"Image {output_path} already exists. Skipping creation.")
        return
    # Format date to German preferences (DD.MM.YYYY)
    formatted_date = datetime.strptime(date_text, '%Y%m%d').strftime('%d.%m.%Y')
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        # Calculate font size based on desired text height
        text_height = 150
        # Use a truetype font if available
        try:
            font = ImageFont.truetype(font_path, text_height)
        except IOError:
            print("JetBrains font not found. Using default font.")
            sleep(50)
            font = ImageFont.load_default()

        # Calculate text width and adjust position
        text_bbox = draw.textbbox((0, 0), formatted_date, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_position = (10, img.height - text_height - 10)

        # Draw text on the image
        draw.text(text_position, formatted_date, font=font, fill='black')

        # Save the modified image
        img.save(output_path)

# Function to add date text to images in different formats
def add_date_to_cropped_images(image_dir, output_dir, position):
    for filename in os.listdir(image_dir):
        if filename.endswith('.png'):
            img_path = os.path.join(image_dir, filename)
            output_path = os.path.join(output_dir, filename)
            if not recreate_images and os.path.exists(output_path):
                print(f"Image {output_path} already exists. Skipping creation.")
                continue
            img = Image.open(img_path)
            draw = ImageDraw.Draw(img)

            date_text = filename.split('_')[0]
            formatted_date = datetime.strptime(date_text, '%Y%m%d').strftime('%d.%m.%Y')
            # Calculate font size based on desired text height
            text_height = 150
            # Use a truetype font if available
            try:
                font = ImageFont.truetype(font_path, text_height)
            except IOError:
                print("JetBrains font not found. Using default font.")
                sleep(50)
                font = ImageFont.load_default()

            # Calculate text width and adjust position
            text_bbox = draw.textbbox((0, 0), formatted_date, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            if position == 'center':
                text_position = ((img.width - text_width) / 2, img.height - text_height - 10)
            else:  # 'bottom_left'
                text_position = (10, img.height - text_height - 10)
            draw.text(text_position, formatted_date, font=font, fill='black')
            img.save(output_path)


image_files = sorted(os.listdir(visualizations_dir))
for image_file in image_files:
    if image_file.endswith('_visualization.png'):
        date_text = image_file.split('_')[0]
        image_path = os.path.join(visualizations_dir, image_file)
        add_date_to_image(image_path, date_text, dated_images_dir)
    
add_date_to_cropped_images(square_images_dir, square_dated_images_dir, 'bottom_left')

    # Add date to vertical images
add_date_to_cropped_images(vertical_images_dir, vertical_dated_images_dir, 'center')

# Create video using ffmpeg with all files in order at 30 fps
ffmpeg_command = [
    'ffmpeg', '-y', '-pattern_type', 'glob', '-framerate', '30', '-i', os.path.join(dated_images_dir, '*.png'),
    '-i', background_music_path, '-c:v', 'libx264', '-r', '30', '-pix_fmt', 'yuv420p', '-shortest',
    video_output_path
]

# Check if the video file already exists
if not overwrite and os.path.exists(video_output_path):
    print(f"Video {video_output_path} already exists. Skipping creation.")
else:
    subprocess.run(ffmpeg_command)
    print(f'Video created at {video_output_path}')

# Check if the square video file already exists
if not overwrite and os.path.exists(video_output_path_square):
    print(f"Square video {video_output_path_square} already exists. Skipping creation.")
else:
    # Create square video
    subprocess.run([
        'ffmpeg', '-y', '-pattern_type', 'glob', '-framerate', '30', '-i', os.path.join(square_dated_images_dir, '*.png'),
        '-i', background_music_path, '-vf', 'scale=1080:1080,setsar=1:1', '-c:v', 'libx264', '-r', '30', '-pix_fmt', 'yuv420p', '-shortest',
        video_output_path_square
    ])
    print(f'Square video created at {video_output_path_square}')

# Check if the vertical video file already exists
if not overwrite and os.path.exists(video_output_path_vertical):
    print(f"9:16 video {video_output_path_vertical} already exists. Skipping creation.")
else:
    # Create vertical 9:16 video
    subprocess.run([
        'ffmpeg', '-y', '-pattern_type', 'glob', '-framerate', '30', '-i', os.path.join(vertical_dated_images_dir, '*.png'),
        '-i', background_music_path, '-vf', 'scale=1080:1920,setsar=1:1', '-c:v', 'libx264', '-r', '30', '-pix_fmt', 'yuv420p', '-shortest',
        video_output_path_vertical
    ])
    print(f'9:16 video created at {video_output_path_vertical}')
