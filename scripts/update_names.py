import logging
import time
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sheets import get_watchlist, update_stock_names
from core.data import get_stock_name

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Stock Name Update Process...")
    
    # 1. 讀取觀察清單
    stock_ids = get_watchlist()
    if not stock_ids:
        logger.warning("No stock IDs found in Google Sheets.")
        return

    logger.info(f"Found {len(stock_ids)} stock IDs: {stock_ids}")

    # 2. 查詢每個 ID 的名稱
    stock_map = {}
    for sid in stock_ids:
        logger.info(f"Fetching name for {sid}...")
        name = get_stock_name(sid)
        if name:
            stock_map[sid] = name
            logger.info(f"  -> {name}")
        else:
            logger.warning(f"  -> Name not found for {sid}")
        # 避免請求過快 (雖然 FinMind 限制寬鬆，但好習慣)
        time.sleep(0.5)
    
    if not stock_map:
        logger.warning("No stock names fetched successfully.")
        return

    # 3. 更新回 Google Sheets
    logger.info("Updating Google Sheets...")
    update_stock_names(stock_map)
    logger.info("Update Complete.")

if __name__ == "__main__":
    main()
