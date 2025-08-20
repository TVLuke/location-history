import os
import sys
from PIL import Image

# Define directories
base_dir = '.'
visualizations_dir = os.path.join(base_dir, 'visualizations_geopandas')
square_images_dir = os.path.join(base_dir, 'visualizations_square')
vertical_images_dir = os.path.join(base_dir, 'visualizations_vertical')

# Create directories if they don't exist
os.makedirs(square_images_dir, exist_ok=True)
os.makedirs(vertical_images_dir, exist_ok=True)

# Default overwrite setting
overwrite = False

# Function to crop images
def crop_images(overwrite=False):
    png_files = [f for f in os.listdir(visualizations_dir) if f.endswith('.png')]
    total_files = len(png_files)
    print(f"Found {total_files} PNG files to process.")

    for i, filename in enumerate(png_files):
        square_output_path = os.path.join(square_images_dir, filename)
        vertical_output_path = os.path.join(vertical_images_dir, filename)
        
        # Skip if files exist and overwrite is False
        if not overwrite and os.path.exists(square_output_path) and os.path.exists(vertical_output_path):
            print(f"Skipping {filename} (files already exist and overwrite=False)")
            continue
            
        print(f"\nProcessing image {i+1} of {total_files}: {filename}")
        img_path = os.path.join(visualizations_dir, filename)
        img = Image.open(img_path)

        # Crop to square
        min_dimension = min(img.width, img.height)
        square_img = img.crop(((img.width - min_dimension) // 2,
                               (img.height - min_dimension) // 2,
                               (img.width + min_dimension) // 2,
                               (img.height + min_dimension) // 2))
        square_img.save(square_output_path)
        print(f"  Saved square image to {square_output_path}")

        # Crop to a slightly wider vertical 9:16 area
        vertical_width = int(img.height * 9 / 16 * 1.2)  # 20% wider
        vertical_img = img.crop(((img.width - vertical_width) // 2,
                                 0,
                                 (img.width + vertical_width) // 2,
                                 img.height))

        # Create a new image with a white background
        vertical_final = Image.new('RGB', (vertical_img.width, int(vertical_img.width * 16 / 9)), (255, 255, 255))
        vertical_final.paste(vertical_img, (0, (vertical_final.height - vertical_img.height) // 2))
        vertical_final.save(vertical_output_path)
        print(f"  Saved vertical image to {vertical_output_path}")

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'true':
        overwrite = True
    print(f"Running with overwrite={overwrite}")
    crop_images(overwrite=overwrite)
