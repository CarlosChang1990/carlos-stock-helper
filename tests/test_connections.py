import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from config import FINMIND_API_TOKEN, GEMINI_API_KEY, GOOGLE_SHEET_URL
from core.sheets import get_service, get_watchlist
from core.data import DataLoader
from google import genai

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_google_sheets():
    logger.info("Testing Google Sheets Connection...")
    try:
        client = get_service()
        if not GOOGLE_SHEET_URL:
            logger.error("GOOGLE_SHEET_URL is missing.")
            return False
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        logger.info(f"Successfully connected to Google Sheet: {sheet.title}")
        return True
    except Exception as e:
        logger.error(f"Google Sheets Connection Failed: {e}")
        return False

def test_finmind():
    logger.info("Testing FinMind Connection...")
    try:
        dl = DataLoader()
        if FINMIND_API_TOKEN:
            dl.login_by_token(api_token=FINMIND_API_TOKEN)
        
        # Test fetching info for TSMC (2330)
        df = dl.taiwan_stock_info()
        row = df[df['stock_id'] == '2330']
        if not row.empty:
            logger.info(f"Successfully fetched FinMind data for 2330: {row.iloc[0]['stock_name']}")
            return True
        else:
            logger.warning("FinMind connected but returned no data for 2330.")
            return False
            
    except Exception as e:
        logger.error(f"FinMind Connection Failed: {e}")
        return False

def test_gemini():
    logger.info("Testing Gemini API Connection...")
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is missing.")
        return False
        
    try:
        # Use new generic Client
        client = genai.Client(api_key=GEMINI_API_KEY)
        # Use the stable model found in investigation
        model_name = "gemini-2.5-flash-lite" 
        
        response = client.models.generate_content(
            model=model_name,
            contents="Hello, this is a connection test."
        )
        # Inspect response structure (it returns an object with .text in the new SDK)
        logger.info(f"Gemini Response: {response.text.strip()[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Gemini Connection Failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Connection Tests...")
    
    sheets_ok = test_google_sheets()
    finmind_ok = test_finmind()
    gemini_ok = test_gemini()
    
    logger.info("--------------------------------------------------")
    logger.info(f"Google Sheets: {'PASS' if sheets_ok else 'FAIL'}")
    logger.info(f"FinMind:       {'PASS' if finmind_ok else 'FAIL'}")
    logger.info(f"Gemini:        {'PASS' if gemini_ok else 'FAIL'}")
    logger.info("--------------------------------------------------")
    
    if sheets_ok and finmind_ok and gemini_ok:
        sys.exit(0)
    else:
        sys.exit(1)
