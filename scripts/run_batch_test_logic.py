import random
import logging
from datetime import datetime
from core.sheets import get_watchlist
from core.data import fetch_stock_data, get_stock_name

# 配置日誌
logger = logging.getLogger(__name__)

def run_batch_test(num_stocks=2, target_date_str="2025-12-01"):
    """
    執行批次測試：隨機挑選股票並查詢特定日期的收盤價
    
    Args:
        num_stocks (int): 挑選幾檔股票
        target_date_str (str): 目標日期 (YYYY-MM-DD)
        
    Returns:
        str: 彙整好的訊息內容
    """
    logger.info("Running Batch Test Logic...")
    
    # 1. Get Watchlist
    stock_ids = get_watchlist()
    if not stock_ids:
        return "錯誤：觀察清單為空或讀取失敗。"
        
    if len(stock_ids) < num_stocks:
        logger.warning(f"Watchlist has fewer than {num_stocks} stocks, using all.")
        target_ids = stock_ids
    else:
        target_ids = random.sample(stock_ids, num_stocks)
        
    logger.info(f"Selected Stock IDs: {target_ids}")

    messages = []
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")

    for stock_id in target_ids:
        # Get Name
        name = get_stock_name(stock_id) or "Unknown"
        
        # Fetch Data
        # Fetch 60 days of data to look for the closest date
        df = fetch_stock_data(stock_id, days=60)
        
        close_price = "N/A"
        date_display = "N/A"
        
        if not df.empty:
            # Filter for date <= target_date
            mask = df['date'] <= target_date
            filtered_df = df[mask]
             
            if not filtered_df.empty:
                row = filtered_df.iloc[-1]
                close_price = row['close']
                date_display = row['date'].strftime('%Y-%m-%d')
            else:
                 logger.warning(f"No data found for {stock_id} on or before {target_date_str}")
        
        messages.append(
            f"{stock_id} {name}\n"
            f"日期: {date_display}\n"
            f"收盤: {close_price}"
        )

    # 3. Construct Consolidated Message
    full_message = f"【LINE 批次通知測試】\n(目標日期: {target_date_str})\n\n" + "\n\n".join(messages)
    
    return full_message
