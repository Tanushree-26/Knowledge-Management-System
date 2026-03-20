import os
from dotenv import load_dotenv
load_dotenv()

Google_API_KEY = os.getenv('GOOGLE_API_KEY')
Google_DRIVE = os.getenv('GOOGLE_DRIVE_FOLDER_ID')