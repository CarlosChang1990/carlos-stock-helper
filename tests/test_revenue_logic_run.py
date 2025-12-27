import logging
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.analysis import analyze_stock

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Revenue Logic Verification...")
    
    # Pick a stock that likely has revenue data (e.g. 2330)
    stock_id = '2330' 
    
    # Simulate first run (last_revenue_month = None) - Should detect new revenue
    logger.info("--- Test Case 1: First Run (New Revenue) ---")
    result1 = analyze_stock(stock_id, last_revenue_month=None)
    
    report1 = result1.get('report', '')
    update1 = result1.get('revenue_update')
    
    logger.info(f"Report Output:\n{report1}")
    if update1:
        logger.info(f"Update Triggered: {update1}")
        last_processed = update1['date_str']
    else:
        logger.warning("No update triggered? (Maybe no data available)")
        last_processed = "2025-12" # Fallback for next test

    # Simulate second run (last_revenue_month = last_processed) - Should NOT detect new revenue
    logger.info(f"--- Test Case 2: Second Run (Last processed = {last_processed}) ---")
    result2 = analyze_stock(stock_id, last_revenue_month=last_processed)
    
    report2 = result2.get('report', '')
    update2 = result2.get('revenue_update')
    
    if "最新月營收公布" in report2:
        logger.error("Error: Revenue reported again despite being up to date!")
    else:
        logger.info("Pass: Revenue section correctly omitted.")
        
    if update2:
        logger.error("Error: Update triggered again!")
    else:
        logger.info("Pass: No update triggered.")

if __name__ == "__main__":
    main()
