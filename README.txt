NOTE: There is a charge for using the API on this. However, I think it cost me like... 30 cents to do 200 images.

What script does:

Prompts for OpenAI Key: Enter your Open AI key for the API
Directory Selection: Prompts the user to select a directory containing image files.
Image Resizing: Resizes all images in the selected directory to 25% of their original size and saves them in a sub-directory named `resized`.
Image Identification: Sends the resized images to the OpenAI API for analysis to identify the most prominent subject in each image.
File Renaming: Renames the resized images based on the descriptions provided by the OpenAI API.
Libraries Required:
`Pillow`: For image processing and resizing.
`requests`: For making HTTP requests to the OpenAI API.
`tkinter`: For creating GUI dialogs for directory and API key selection.

Usage Instructions
1. Install Required Libraries
Ensure you have Python installed. Then, install the required libraries using pip:

pip install -r requirements.txt

2. Run the Script:

python resize-rename-image.py

When prompted, enter your OpenAI API key. This key is used to authenticate your requests to the OpenAI API.

Select Directory - A file dialog will appear asking you to select the directory containing the images you want to process. Choose the appropriate directory and proceed.

Processing - The script will resize each image in the selected directory to 25% of its original size and save the resized images in a subdirectory named `resized`. It will then send each resized image to the OpenAI API for analysis and receive a description of the most prominent subject in each image. Finally, the script will rename the resized images based on the descriptions provided by the OpenAI API. 
