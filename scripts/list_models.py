import google.generativeai as genai
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import GEMINI_API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not GEMINI_API_KEY:
    logger.error("No API Key")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        logger.info("Listing models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                logger.info(f"Model: {m.name}")
    except Exception as e:
        logger.error(f"Error listing models: {e}")
