from PIL import Image, PngImagePlugin, JpegImagePlugin, ExifTags
import os
import re
import base64
import requests
import json
from tkinter import Tk, filedialog, simpledialog

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to clean the description to make it valid for metadata and file names
def clean_description(description):
    description = re.sub(r'[^a-zA-Z0-9\s]', '', description)  # Remove special characters
    return '_'.join(description.split()[:3])  # Use the first three words and replace spaces with underscores

# Function to resize the image
def resize_image(image_path, output_path, scale=0.25):
    with Image.open(image_path) as img:
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality downsampling
        img.save(output_path)
        print(f"Resized and saved {image_path} to {output_path}")

# Function to add metadata to an image
def add_metadata(image_path, description, tags):
    with Image.open(image_path) as img:
        if img.format == 'PNG':
            metadata = PngImagePlugin.PngInfo()
            metadata.add_text("Description", description)
            metadata.add_text("Tags", ', '.join(tags))
            img.save(image_path, pnginfo=metadata)
        elif img.format in ['JPEG', 'JPG']:
            exif_data = img.info.get('exif', b'')
            img = img.copy()

            # Add description and tags to EXIF
            exif_dict = {}
            if exif_data:
                exif_dict = img._getexif()
                if exif_dict is None:
                    exif_dict = {}
            
            # Custom tags for description and tags
            exif_dict[0x9286] = description.encode('utf-8')
            exif_dict[0x9287] = ', '.join(tags).encode('utf-8')

            # Convert EXIF dict to bytes
            exif_bytes = Image.Exif()

            for tag, value in exif_dict.items():
                exif_bytes[tag] = value

            img.save(image_path, "JPEG", quality=95, exif=exif_bytes)
        else:
            print(f"Unsupported image format for metadata: {img.format}")

# Function to get directory from user
def get_directory():
    root = Tk()
    root.withdraw()  # Hide the main window
    directory = filedialog.askdirectory(title="Select Directory")
    return directory

# Function to get OpenAI API key from user
def get_api_key():
    root = Tk()
    root.withdraw()  # Hide the main window
    api_key = simpledialog.askstring("API Key", "Enter your OpenAI API key:", show='*')
    return api_key

# Function to view metadata of an image
def view_metadata(image_path):
    with Image.open(image_path) as img:
        print(f"Metadata for {image_path}:")
        if img.format == 'PNG':
            for key, value in img.info.items():
                if isinstance(value, str):
                    print(f"{key}: {value}")
        elif img.format in ['JPEG', 'JPG']:
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag, tag)
                    if tag_name in ['UserComment', 'XPComment']:
                        print(f"{tag_name}: {value.decode('utf-8', 'ignore')}")
            else:
                print("No EXIF metadata found.")

# Function to rename the file based on description
def rename_file(directory, old_name, new_base_name):
    extension = os.path.splitext(old_name)[1]
    new_name = f"{new_base_name}{extension}"
    new_path = os.path.join(directory, new_name)
    os.rename(old_name, new_path)
    return new_path

# Get the OpenAI API key from the user
api_key = get_api_key()
if not api_key:
    print("No API key provided.")
    exit()

# Get the directory from the user
directory_path = get_directory()
if not directory_path:
    print("No directory selected.")
    exit()

# Create output directory if it doesn't exist
resized_directory_path = os.path.join(directory_path, "resized")
if not os.path.exists(resized_directory_path):
    os.makedirs(resized_directory_path)

# Get a list of all image files in the directory
image_paths = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]

# Resize all images and save them to the resized directory
for image_path in image_paths:
    file_name = os.path.basename(image_path)
    output_path = os.path.join(resized_directory_path, file_name)
    resize_image(image_path, output_path)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Send resized images to OpenAI for identification, add metadata, and rename files
for image_path in [os.path.join(resized_directory_path, f) for f in os.listdir(resized_directory_path)]:
    base64_image = encode_image(image_path)
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze the most prominent subject of this photograph, label it in as few words as possible, and provide three relevant tags. Format your response as follows: 'Label: <label>\nTags: <tag1>, <tag2>, <tag3>'."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"  # or "low" depending on your needs
                        }
                    }
                ]
            }
        ],
        "max_tokens": 50  # Limit the number of tokens to get a short response
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_data = response.json()
    
    if 'choices' in response_data and len(response_data['choices']) > 0:
        full_response = response_data['choices'][0]['message']['content'].strip()
        try:
            label_line, tags_line = full_response.split('\n')
            label = label_line.split(': ')[1]
            tags = [tag.strip() for tag in tags_line.split(': ')[1].split(',')]
            cleaned_description = clean_description(label)
            add_metadata(image_path, cleaned_description, tags)
            print(f"Added metadata to {image_path}: {cleaned_description}, Tags: {', '.join(tags)}")
            view_metadata(image_path)
            new_path = rename_file(resized_directory_path, image_path, cleaned_description)
            print(f"Renamed file to {new_path}")
        except ValueError:
            print(f"Unexpected response format for {image_path}: {full_response}")
    else:
        print(f"Failed to get a description for {image_path}")

