import random
import logging
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sheets import get_watchlist
from core.data import fetch_stock_data, get_stock_name
from core.notifier import send_line_notification

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting LINE Notification Test...")
    
    # 1. Get Watchlist
    stock_ids = get_watchlist()
    if not stock_ids:
        logger.error("Watchlist is empty!")
        return

    # 2. Pick Random Stock
    target_id = random.choice(stock_ids)
    logger.info(f"Selected Stock ID: {target_id}")

    # 3. Get Stock Name
    name = get_stock_name(target_id)
    if not name:
        name = "Unknown"
    logger.info(f"Stock Name: {name}")

    # 4. Fetch Data (Fetch enough days to ensure we get recent data)
    df = fetch_stock_data(target_id, days=10)
    if df.empty:
        logger.error(f"No data found for {target_id}")
        return

    # 5. Get Last Row (Latest Close)
    last_row = df.iloc[-1]
    last_date = last_row['date'].strftime('%Y-%m-%d')
    close_price = last_row['close']
    
    logger.info(f"Latest Data Date: {last_date}")
    logger.info(f"Close Price: {close_price}")

    # 6. Construct Message
    message = (
        f"【LINE 通知測試】\n"
        f"股票代號: {target_id}\n"
        f"股票名稱: {name}\n"
        f"日期: {last_date}\n"
        f"收盤價: {close_price}"
    )

    # 7. Send Notification
    logger.info("Sending LINE message...")
    send_line_notification(message)
    logger.info("Message sent (check your device).")

if __name__ == "__main__":
    main()
