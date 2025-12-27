import os
from dotenv import load_dotenv

load_dotenv()

# API Keys & Secrets
FINMIND_API_TOKEN = os.getenv("FINMIND_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # Targeted user ID or Group ID

# Google Sheets
# Path to the json key file or the content itself
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL")
