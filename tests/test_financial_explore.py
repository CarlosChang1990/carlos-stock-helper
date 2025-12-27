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

def test_financial_data(stock_id='2330'):
    dl = DataLoader()
    if FINMIND_API_TOKEN:
        dl.login_by_token(api_token=FINMIND_API_TOKEN)
        
    logger.info(f"Fetching financial statements for {stock_id}...")
    
    # Fetch data for the last 2 years 
    # Check what columns are returned.
    df = dl.taiwan_stock_financial_statement(
        stock_id=stock_id,
        start_date='2020-01-01'
    )
    
    if df.empty:
        logger.warning("No data found.")
        return
        
    logger.info(f"Columns: {df.columns.tolist()}")
    
    # Check unique types of data (Balance Sheet, Income Statement, etc. might be mixed or specific types)
    # FinMind usually returns 'type' column (e.g. 'EPS', 'GrossProfit', etc.) or we need to pivot
    if 'type' in df.columns:
        logger.info(f"Unique types: {df['type'].unique()}")
        
    # Print sample of latest quarter
    logger.info("Last 10 rows:")
    print(df.tail(10))
    
    # Need to check how to assemble EPS, Gross Margin, etc.

if __name__ == "__main__":
    test_financial_data()
