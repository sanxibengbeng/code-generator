"""
Utility functions for image handling
"""
import os
import base64
from PIL import Image
import io

def encode_image(image_path):
    """
    Encode an image to base64
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64-encoded image
    """
    # Check if the file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Open and optimize the image if needed
    with Image.open(image_path) as img:
        # Convert to RGB if the image has an alpha channel
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Resize if the image is too large
        max_size = 2000  # Maximum dimension
        if img.width > max_size or img.height > max_size:
            # Calculate new dimensions while preserving aspect ratio
            if img.width > img.height:
                new_width = max_size
                new_height = int(img.height * (max_size / img.width))
            else:
                new_height = max_size
                new_width = int(img.width * (max_size / img.height))
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Save to a buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        
        # Encode to base64
        base64_image = base64.b64encode(buffer.read()).decode('utf-8')
    
    return base64_image

def get_image_dimensions(image_path):
    """
    Get the dimensions of an image
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        tuple: (width, height)
    """
    with Image.open(image_path) as img:
        return img.size
