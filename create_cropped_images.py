import os
from PIL import Image

# Define directories
base_dir = '.'
visualizations_dir = os.path.join(base_dir, 'visualizations_geopandas')
square_images_dir = os.path.join(base_dir, 'visualizations_square')
vertical_images_dir = os.path.join(base_dir, 'visualizations_vertical')

# Create directories if they don't exist
os.makedirs(square_images_dir, exist_ok=True)
os.makedirs(vertical_images_dir, exist_ok=True)

# Function to crop images
def crop_images():
    for filename in os.listdir(visualizations_dir):
        if filename.endswith('.png'):
            img_path = os.path.join(visualizations_dir, filename)
            img = Image.open(img_path)

            # Crop to square
            min_dimension = min(img.width, img.height)
            square_img = img.crop(((img.width - min_dimension) // 2,
                                   (img.height - min_dimension) // 2,
                                   (img.width + min_dimension) // 2,
                                   (img.height + min_dimension) // 2))
            square_img.save(os.path.join(square_images_dir, filename))

            # Crop to a slightly wider vertical 9:16 area
            vertical_width = int(img.height * 9 / 16 * 1.2)  # 20% wider
            vertical_img = img.crop(((img.width - vertical_width) // 2,
                                     0,
                                     (img.width + vertical_width) // 2,
                                     img.height))

            # Create a new image with a white background
            vertical_final = Image.new('RGB', (vertical_img.width, int(vertical_img.width * 16 / 9)), (255, 255, 255))
            vertical_final.paste(vertical_img, (0, (vertical_final.height - vertical_img.height) // 2))
            vertical_final.save(os.path.join(vertical_images_dir, filename))

if __name__ == "__main__":
    crop_images()
