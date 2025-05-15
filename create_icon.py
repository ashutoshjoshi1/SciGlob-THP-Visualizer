# Simple script to create a basic icon file if it doesn't exist
import os
from PIL import Image, ImageDraw

def create_icon():
    if os.path.exists('icon.ico'):
        print("Icon file already exists.")
        return
    
    try:
        # Create a simple 64x64 icon
        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a simple THP icon (a circle with T, H, P letters)
        draw.ellipse((4, 4, 60, 60), fill=(0, 120, 212))
        draw.text((20, 20), "THP", fill=(255, 255, 255))
        
        # Save as .ico
        img.save('icon.ico')
        print("Created icon.ico file.")
    except Exception as e:
        print(f"Error creating icon: {e}")
        print("You can continue without an icon or create one manually.")

if __name__ == "__main__":
    create_icon()