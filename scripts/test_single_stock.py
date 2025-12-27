import sys
import os
import logging
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sheets import get_watchlist_details
from core.analysis import analyze_stock

# Logging Config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_stock():
    load_dotenv()
    
    # LINE Setup
    line_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_user_id = os.getenv("LINE_USER_ID")
    
    if not line_access_token or not line_user_id:
        logger.error("LINE configs missing.")
        return

    line_bot_api = LineBotApi(line_access_token)

    # 1. Get Watchlist
    logger.info("Fetching watchlist...")
    stocks = get_watchlist_details()
    if not stocks:
        logger.error("No stocks found in watchlist.")
        return
        
    # 2. Pick Random Stock
    import random
    target = random.choice(stocks)
    # target = next((s for s in stocks if s['id'] == '3416'), stocks[0])
    
    stock_id = target['id']
    stock_name = target.get('name', '')
    logger.info(f"Selected Stock: {stock_id} {stock_name}")
    
    # 3. Analyze
    logger.info(f"Analyzing {stock_id}...")
    # analyze_stock returns: {'report': str, 'revenue_update': ..., 'financial_update': ...}
    result = analyze_stock(
        stock_id, 
        last_revenue_month=target.get('last_revenue_month'),
        last_financial_quarter=target.get('last_financial_quarter'),
        stock_name=stock_name
    )
    
    report_text = result.get('report')
    if not report_text:
        logger.error("Analysis failed (no report).")
        return
        
    logger.info("Analysis Complete. Report content:")
    print(report_text)
    
    # 4. Send to LINE
    logger.info("Sending to LINE...")
    try:
        line_bot_api.push_message(line_user_id, TextSendMessage(text=report_text))
        logger.info("Message sent successfully!")
    except Exception as e:
        logger.error(f"Failed to send LINE message: {e}")

if __name__ == "__main__":
    test_single_stock()
