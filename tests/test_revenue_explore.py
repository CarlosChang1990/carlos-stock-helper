import logging
import sys
import os
import pandas as pd
from FinMind.data import DataLoader

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import FINMIND_API_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_revenue_data(stock_id='2330'):
    dl = DataLoader()
    if FINMIND_API_TOKEN:
        dl.login_by_token(api_token=FINMIND_API_TOKEN)
        
    logger.info(f"Fetching monthly revenue for {stock_id}...")
    
    # Fetch data for the last 2 years to calculate YoY and Highs
    df = dl.taiwan_stock_month_revenue(
        stock_id=stock_id,
        start_date='2020-01-01'
    )
    
    if df.empty:
        logger.warning("No data found.")
        return
        
    logger.info(f"Columns: {df.columns.tolist()}")
    logger.info("Last 5 rows:")
    print(df.tail(5))
    
    # Check latest row
    last_row = df.iloc[-1]
    logger.info(f"Latest Data: Year {last_row.get('revenue_year')}, Month {last_row.get('revenue_month')}")
    logger.info(f"Revenue: {last_row.get('revenue')}")

if __name__ == "__main__":
    test_revenue_data()
