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

def verify_cumulative_revenue(stock_id='2330', year=2024, quarter_month=9):
    """
    Compare SUM(Monthly Revenue) vs Financial Statement Revenue to check if it's Cumulative.
    Q3 (Sep) Cumulative = Jan-Sep. Single = Jul-Sep.
    """
    dl = DataLoader()
    if FINMIND_API_TOKEN:
        dl.login_by_token(api_token=FINMIND_API_TOKEN)
        
    # 1. Fetch Monthly Revenue
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    logger.info("Fetching Monthly Revenue...")
    df_month = dl.taiwan_stock_month_revenue(
        stock_id=stock_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Q3 Months: 7, 8, 9
    # Cumulative: 1..9
    
    q3_single_sum = df_month[df_month['revenue_month'].isin([7, 8, 9])]['revenue'].sum()
    q3_cum_sum = df_month[df_month['revenue_month'].isin(range(1, 10))]['revenue'].sum()
    
    logger.info(f"Month Revenue Sum (Q3 Single): {q3_single_sum / 1e9:.2f} B")
    logger.info(f"Month Revenue Sum (Q3 Cum):    {q3_cum_sum / 1e9:.2f} B")
    
    # 2. Fetch Financial Statement
    logger.info("Fetching Financial Statement...")
    df_fin = dl.taiwan_stock_financial_statement(
        stock_id=stock_id,
        start_date=f"{year}-09-01", # Close scan
        end_date=f"{year}-10-01"
    )
    
    # Look for 2024-09-30
    target_date = f"{year}-09-30"
    df_fin = df_fin[df_fin['date'] == target_date]
    df_rev = df_fin[df_fin['type'] == 'Revenue']
    
    if not df_rev.empty:
        fin_rev = df_rev.iloc[0]['value']
        logger.info(f"Financial Stmt Revenue ({target_date}): {fin_rev / 1e9:.2f} B")
        
        if abs(fin_rev - q3_cum_sum) < abs(fin_rev - q3_single_sum):
            logger.info("CONCLUSION: Financial Statement is CUMULATIVE (YTD).")
        else:
            logger.info("CONCLUSION: Financial Statement is SINGLE QUARTER.")
    else:
        logger.warning("Financial Statement Revenue not found.")

if __name__ == "__main__":
    verify_cumulative_revenue()
