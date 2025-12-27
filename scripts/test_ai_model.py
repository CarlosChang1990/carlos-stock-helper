import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ai import search_eps_forecast
from core.sheets import get_watchlist_details

# Logging Config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai():
    # Pick a stock to test, e.g., 3037 欣興
    stock_id = "3037"
    stock_name = "欣興"
    
    logger.info(f"Testing AI Model with {stock_id} {stock_name}...")
    result = search_eps_forecast(stock_id, stock_name)
    print("\n=== AI Result ===")
    print(result)
    print("=================")

if __name__ == "__main__":
    test_ai()
