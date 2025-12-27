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
    logger.info("Starting Financial Logic Verification...")
    
    # Pick a stock (e.g. 2330)
    stock_id = '2330' 
    
    # Test Case: First Run (New Financials)
    # last_financial_quarter = None
    logger.info("--- Test Case 1: First Run (New Financials) ---")
    
    # We pass '2099-12' as revenue month to suppress revenue output (focus on financials)
    # Or just ignore revenue part.
    result1 = analyze_stock(stock_id, last_revenue_month="2099-12", last_financial_quarter=None)
    
    report1 = result1.get('report', '')
    update1 = result1.get('financial_update')
    
    logger.info(f"Report Output:\n{report1}")
    
    if update1:
        logger.info(f"Financial Update Triggered: {update1}")
        last_processed_fin = update1['quarter_str']
    else:
        logger.warning("No financial update triggered?")
        last_processed_fin = "2025-Q3" # Fallback

    # Test Case: Second Run (Old Financials)
    logger.info(f"--- Test Case 2: Second Run (Last processed = {last_processed_fin}) ---")
    result2 = analyze_stock(stock_id, last_revenue_month="2099-12", last_financial_quarter=last_processed_fin)
    
    report2 = result2.get('report', '')
    update2 = result2.get('financial_update')
    
    if "最新季報公布" in report2:
        logger.error("Error: Financial section reported again!")
    else:
        logger.info("Pass: Financial section correctly omitted.")
        
    if update2:
        logger.error("Error: Financial Update triggered again!")
    else:
        logger.info("Pass: No financial update triggered.")

if __name__ == "__main__":
    main()
