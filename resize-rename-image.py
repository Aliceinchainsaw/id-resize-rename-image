from PIL import Image
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

# Function to clean the description to make it a valid file name
def clean_description(description):
    description = re.sub(r'[^a-zA-Z0-9\s]', '', description)  # Remove special characters
    description = '_'.join(description.split()[:3])  # Use the first three words and replace spaces with underscores
    return description

# Function to generate a new file name with a sequence number if needed
def generate_new_file_name(directory, base_name, extension):
    new_file_name = f"{base_name}{extension}"
    new_file_path = os.path.join(directory, new_file_name)
    sequence = 1
    while os.path.exists(new_file_path):
        new_file_name = f"{base_name}_{sequence}{extension}"
        new_file_path = os.path.join(directory, new_file_name)
        sequence += 1
    return new_file_path

# Function to resize the image
def resize_image(image_path, output_path, scale=0.25):
    with Image.open(image_path) as img:
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality downsampling
        img.save(output_path)
        print(f"Resized and saved {image_path} to {output_path}")

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

# Send resized images to OpenAI for identification and rename them
for image_path in [os.path.join(resized_directory_path, f) for f in os.listdir(resized_directory_path)]:
    base64_image = encode_image(image_path)
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze the most prominent subject of this photograph and label it in as few words as possible. If the photograph shows multiple items as the main subject, simply label it as the category of what those items fall under."},
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
        "max_tokens": 15  # Limit the number of tokens to keep the response short
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_data = response.json()
    
    if 'choices' in response_data and len(response_data['choices']) > 0:
        description = response_data['choices'][0]['message']['content'].strip()
        cleaned_description = clean_description(description)
        base_name = cleaned_description
        extension = os.path.splitext(image_path)[1]
        new_file_path = generate_new_file_name(resized_directory_path, base_name, extension)
        
        # Rename the file
        os.rename(image_path, new_file_path)
        print(f"Renamed {image_path} to {new_file_path}")

    else:
        print(f"Failed to get a description for {image_path}")
