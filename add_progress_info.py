import os
import json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Configuration variables
overwrite = False
add_progress_info = True
show_top_10 = True      # Controls whether the top 10 list is added to the image
show_new_location = True  # Controls whether new locations are displayed in the top left corner

# Variables for tracking new location display
last_new_location = None  # The most recent new location to display
last_new_location_frames = 0  # Number of frames the current new location has been displayed
box_visible = False      # Whether the notification box is currently visible
animation_state = None   # Can be 'slide_in', 'slide_out', or None

# Define directories
base_dir = '.'
progress_file = os.path.join(base_dir, 'progress.json')

# Input image directories
visualizations_dir = os.path.join(base_dir, 'visualizations_geopandas')
square_images_dir = os.path.join(base_dir, 'visualizations_square')
vertical_images_dir = os.path.join(base_dir, 'visualizations_vertical')

# Output image directories with progress info
visualizations_progress_dir = os.path.join(base_dir, 'visualizations_geopandas_progress_info')
square_progress_dir = os.path.join(base_dir, 'visualizations_square_progress_info')
vertical_progress_dir = os.path.join(base_dir, 'visualizations_vertical_progress_info')

# Create output directories if they don't exist
os.makedirs(visualizations_progress_dir, exist_ok=True)
os.makedirs(square_progress_dir, exist_ok=True)
os.makedirs(vertical_progress_dir, exist_ok=True)

# Define the path to the font (same as in create_video_from_images.py)
font_path = os.path.join(base_dir, 'static', 'droid', 'droid.ttf')

def load_progress_data():
    """Load progress data from JSON file"""
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading progress data: {e}")
        return {}

def format_progress_data(date, progress_data):
    """Format progress data for display on image."""
    if date not in progress_data:
        return None
    
    # Get top areas for the date
    top_areas = progress_data[date].get('top_areas', {})
    if not top_areas:
        return None
    
    # Format the top areas as lines of text
    formatted_lines = []
    
    # Only add top 10 list if show_top_10 is True
    if show_top_10:
        formatted_lines.append("TOP 10")  # Add TOP 10 header
        
        for area, count in top_areas.items():
            # Simplify city name by removing everything after a comma
            simple_area = area.split(',')[0]
            # Convert count to kilometers (divide by 2) and format with one decimal place
            km_value = count / 2
            formatted_lines.append(f"{simple_area}: {km_value:.1f} km")
    
    return formatted_lines if formatted_lines else None

def add_progress_to_image(image_path, date, progress_data, output_path, image_type):
    """Add progress information to an image"""
    global last_new_location, last_new_location_frames, box_visible, animation_state
    
    # Skip if output file exists and overwrite is False
    if os.path.exists(output_path) and not overwrite:
        print(f"Image {output_path} already exists. Skipping.")
        return
    
    # Skip if no progress data for this date
    if date not in progress_data:
        print(f"No progress data for {date}. Skipping.")
        return
    
    # If both show_top_10 and show_new_location are False, just copy the image
    if not show_top_10 and not show_new_location:
        with Image.open(image_path) as img:
            img.save(output_path)
        return
        
    # Get data for this date
    top_areas = progress_data[date].get('top_areas', {})
    new_areas = progress_data[date].get('new_areas', [])
    
    # Check for new areas and update tracking variables
    if new_areas:
        # We have a new area for this date
        if last_new_location != new_areas[0]:  # If it's a different location than before
            last_new_location = new_areas[0]  # Update to the new location
            last_new_location_frames = 0  # Reset the frame counter
            
            # If box wasn't visible, start slide-in animation
            if not box_visible:
                animation_state = 'slide_in'
                box_visible = True
            # Otherwise just replace the text (no animation)
    elif last_new_location and last_new_location_frames >= 22 and box_visible:  # Near the end of display time
        # Start slide-out animation if we're at exactly frame 22
        if last_new_location_frames == 22:
            animation_state = 'slide_out'
    
    # Increment frame counter
    if last_new_location is not None:
        last_new_location_frames += 1
        
        # Check if we need to hide the box after 24 frames
        if last_new_location_frames >= 24:
            box_visible = False
            last_new_location = None
            animation_state = None
    
    # Reset animation state after 2 frames
    if animation_state == 'slide_in' and last_new_location_frames > 2:
        animation_state = None
    
    # Skip if no data to display
    if not show_top_10 and not show_new_location:
        with Image.open(image_path) as img:
            img.save(output_path)
        return
    
    if show_top_10 and not top_areas:
        print(f"No top areas data for {date}. Skipping top 10 display.")
        # Continue processing for new_location if needed
    
    # Format top areas text
    formatted_lines = format_progress_data(date, progress_data)
    
    # Open and process image
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        
        # Use a smaller font size for the progress info
        font_size = 30  # Much smaller than the date font (150)
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print("Font not found. Using default font.")
            font = ImageFont.load_default()
            
        # Function to draw a notification box with animation effects
        def draw_notification_box():
            # Skip if no location to display
            if not last_new_location:
                return
                
            # Get the area to display
            area = last_new_location
            
            # Simplify area name by removing everything after a comma
            area = area.split(',')[0]
            
            # Truncate if longer than 30 characters
            if len(area) > 30:
                area = area[:27] + "..."
                
            # Create the notification text with star symbol
            notification_text = f"NEW: {area}"
            
            # Create slightly larger font for the notification
            try:
                notification_font = ImageFont.truetype(font_path, 36)
            except IOError:
                notification_font = font
                
            # Calculate text dimensions for height only
            text_bbox = draw.textbbox((0, 0), notification_text, font=notification_font)
            text_height = text_bbox[3] - text_bbox[1]
            
            # Add padding for rounded rectangle
            padding = 20
            
            # Fixed width for 35 characters regardless of actual text length
            # Calculate the width of a 35-character string to ensure consistency
            max_text = "X" * 35  # Using X as a wide character for measurement
            max_text_bbox = draw.textbbox((0, 0), max_text, font=notification_font)
            fixed_text_width = max_text_bbox[2] - max_text_bbox[0]
            
            rect_width = fixed_text_width + padding * 2
            rect_height = text_height + padding * 2
            
            # Base position based on image type
            base_x = 30  # Default horizontal margin
            
            if image_type == 'vertical':
                base_y = 250  # Much lower position for vertical images
            else:
                base_y = 30  # Default position for standard and square images
                
            # Apply animation effects based on state
            offset_x = 0
            if animation_state == 'slide_in':
                # Sliding in from left
                if last_new_location_frames == 0:
                    offset_x = -rect_width  # Fully off-screen
                elif last_new_location_frames == 1:
                    offset_x = -rect_width // 2  # Half visible
            elif animation_state == 'slide_out':
                # Sliding out to left
                if last_new_location_frames == 23:
                    offset_x = -rect_width // 2  # Half off-screen
                elif last_new_location_frames >= 24:
                    offset_x = -rect_width  # Fully off-screen
                    return  # Don't draw if fully off-screen
                
            # Calculate final position
            rect_x = base_x + offset_x
            rect_y = base_y
                
            # Draw rounded rectangle background
            # Using multiple rectangles and circles for rounded corners
            corner_radius = 15
            purple_color = (134, 22, 226)  # #8616e2
            
            # Draw the main rectangle
            draw.rectangle(
                [(rect_x + corner_radius, rect_y), 
                 (rect_x + rect_width - corner_radius, rect_y + rect_height)],
                fill=purple_color
            )
            draw.rectangle(
                [(rect_x, rect_y + corner_radius), 
                 (rect_x + rect_width, rect_y + rect_height - corner_radius)],
                fill=purple_color
            )
            
            # Draw the four corner circles
            draw.ellipse([rect_x, rect_y, rect_x + 2 * corner_radius, rect_y + 2 * corner_radius], fill=purple_color)
            draw.ellipse([rect_x + rect_width - 2 * corner_radius, rect_y, rect_x + rect_width, rect_y + 2 * corner_radius], fill=purple_color)
            draw.ellipse([rect_x, rect_y + rect_height - 2 * corner_radius, rect_x + 2 * corner_radius, rect_y + rect_height], fill=purple_color)
            draw.ellipse([rect_x + rect_width - 2 * corner_radius, rect_y + rect_height - 2 * corner_radius, rect_x + rect_width, rect_y + rect_height], fill=purple_color)
            
            # Draw the text centered in the rectangle
            text_x = rect_x + padding
            text_y = rect_y + padding
            draw.text((text_x, text_y), notification_text, font=notification_font, fill="white")
        
        # Add new location notification if enabled
        if show_new_location and box_visible:
            draw_notification_box()
            

        
        # Calculate position based on image type
        if image_type == '16:9':
            # Lower right corner for 16:9 images
            total_height = len(formatted_lines) * (font_size + 5)
            
            # Fixed position for text area in the lower right corner
            # Use a fixed width for the text area to ensure consistent positioning
            text_area_width = 300  # Fixed width for text area
            start_x = img.width - text_area_width - 20
            start_y = img.height - total_height - 220  # Position higher up to fit all 10 lines
            
            # Draw each line with right alignment
            for i, line in enumerate(formatted_lines):
                text_bbox = draw.textbbox((0, 0), line, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                # Right align the text within the fixed width area
                x_pos = start_x + (text_area_width - text_width)
                y_pos = start_y + i * (font_size + 5)
                draw.text((x_pos, y_pos), line, font=font, fill='black')
                
        elif image_type == 'square':
            # Bottom middle for square images
            line_height = font_size + 5
            total_height = len(formatted_lines) * line_height
            
            # Fixed width for text area to ensure consistent positioning
            text_area_width = 300
            start_x = (img.width - text_area_width) / 2
            start_y = img.height - total_height - 220  # Position higher up to fit all 10 lines
            
            # Draw each line centered within the fixed width area
            for i, line in enumerate(formatted_lines):
                text_bbox = draw.textbbox((0, 0), line, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                # Center align the text within the fixed width area
                x_pos = start_x + (text_area_width - text_width) / 2
                y_pos = start_y + (i * line_height)
                draw.text((x_pos, y_pos), line, font=font, fill='black')
                
        elif image_type == 'vertical':
            # Bottom middle for vertical images
            line_height = font_size + 5
            total_height = len(formatted_lines) * line_height
            
            # Fixed width for text area to ensure consistent positioning
            text_area_width = 300
            start_x = (img.width - text_area_width) / 2
            start_y = img.height - total_height - 280  # Position higher up for vertical images
            
            # Draw each line centered within the fixed width area
            for i, line in enumerate(formatted_lines):
                text_bbox = draw.textbbox((0, 0), line, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                # Center align the text within the fixed width area
                x_pos = start_x + (text_area_width - text_width) / 2
                y_pos = start_y + (i * line_height)
                draw.text((x_pos, y_pos), line, font=font, fill='black')
        
        # Save the modified image
        img.save(output_path)
        print(f"Added progress info to {output_path}")

def process_images():
    """Process all images and add progress information"""
    global last_new_location, last_new_location_frames, box_visible, animation_state
    
    # Skip processing if add_progress_info is False
    if not add_progress_info:
        print("add_progress_info is set to False. Skipping processing.")
        return
        
    # Print status of display features
    if not show_top_10:
        print("show_top_10 is set to False. No top 10 list will be added to images.")
        
    if not show_new_location:
        print("show_new_location is set to False. No new location notifications will be added to images.")
        
    if not show_top_10 and not show_new_location:
        print("Both show_top_10 and show_new_location are False. Images will be copied without modifications.")
        if not overwrite:
            print("Since overwrite is also False, existing images will be skipped entirely.")
    
    # Reset tracking variables
    last_new_location = None
    last_new_location_frames = 0
    box_visible = False
    animation_state = None
    
    # Load progress data
    progress_data = load_progress_data()
    if not progress_data:
        print("No progress data available. Exiting.")
        return
    
    # Process 16:9 images
    for filename in sorted(os.listdir(visualizations_dir)):
        if filename.endswith('_visualization.png'):
            date = filename.split('_')[0]
            input_path = os.path.join(visualizations_dir, filename)
            output_path = os.path.join(visualizations_progress_dir, filename)
            add_progress_to_image(input_path, date, progress_data, output_path, '16:9')
    
    # Process square images
    for filename in sorted(os.listdir(square_images_dir)):
        if filename.endswith('.png'):
            date = filename.split('_')[0]
            input_path = os.path.join(square_images_dir, filename)
            output_path = os.path.join(square_progress_dir, filename)
            add_progress_to_image(input_path, date, progress_data, output_path, 'square')
    
    # Process vertical images
    for filename in sorted(os.listdir(vertical_images_dir)):
        if filename.endswith('.png'):
            date = filename.split('_')[0]
            input_path = os.path.join(vertical_images_dir, filename)
            output_path = os.path.join(vertical_progress_dir, filename)
            add_progress_to_image(input_path, date, progress_data, output_path, 'vertical')

if __name__ == "__main__":
    process_images()
