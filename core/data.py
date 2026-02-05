import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
from typing import Optional
from config import FINMIND_API_TOKEN
import logging


# 設定日誌
logger = logging.getLogger(__name__)

def fetch_stock_data(stock_id, days=180):
    """
    從 FinMind 抓取個股的日線資料 (股價與成交量)
    
    Args:
        stock_id (str): 股票代碼，例如 '2330'
        days (int): 要抓取的天數，預設 180 天 (為了計算長天期 MA)
        
    Returns:
        pd.DataFrame: 包含 date, open, max, min, close, current_volume 等欄位
                      如果不成功或沒資料，回傳空的 DataFrame
    """
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        logger.info(f"開始抓取 {stock_id} 資料: {start_date} ~ {end_date}")
        
        dl = DataLoader()
        # 如有 Token 則設定
        if FINMIND_API_TOKEN:
            dl.login_by_token(api_token=FINMIND_API_TOKEN)
            
        df = dl.taiwan_stock_daily(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            logger.warning(f"股票 {stock_id} 查無資料")
            return pd.DataFrame()
            
        # 重新命名欄位以符合習慣 (FinMind 欄位: date, open, max, min, close, Trading_Volume, ...)
        # FinMind v1.5+ 回傳欄位通常是: date, stock_id, Trading_Volume, Trading_money, open, max, min, close, ...
        # 注意：成交量單位通常是 '股'，我們可能需要轉成 '張' (除以 1000) 方便閱讀，但在這裡先保持原樣或僅做標準化
        
        # 確保日期格式正確
        df['date'] = pd.to_datetime(df['date'])
        
        # 排序
        df = df.sort_values('date')
        
        # 轉換數值型態 (有時候 API 會回傳字串)
        cols_to_numeric = ['open', 'max', 'min', 'close', 'Trading_Volume']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        return df

    except Exception as e:
        logger.error(f"抓取 {stock_id} 資料時發生錯誤: {e}")
        return pd.DataFrame()

def get_stock_name(stock_id):
    """
    從 FinMind 取得股票名稱
    """
    try:
        dl = DataLoader()
        if FINMIND_API_TOKEN:
            dl.login_by_token(api_token=FINMIND_API_TOKEN)
            
        # 取得個股基本資料
        df = dl.taiwan_stock_info()
        
        if df.empty:
            return None
            
        # 篩選特定股票
        row = df[df['stock_id'] == stock_id]
        if not row.empty:
            return row.iloc[0]['stock_name']
            
        return None
    except Exception as e:
        logger.error(f"無法取得股票名稱 {stock_id}: {e}")
        return None

def fetch_monthly_revenue(stock_id, years=3):
    """
    抓取月營收資料
    """
    try:
        dl = DataLoader()
        if FINMIND_API_TOKEN:
            dl.login_by_token(api_token=FINMIND_API_TOKEN)
            
        start_date = (datetime.now() - timedelta(days=years*365)).strftime("%Y-%m-%d")
        
        df = dl.taiwan_stock_month_revenue(
            stock_id=stock_id,
            start_date=start_date
        )
        
        return df
    except Exception as e:
        logger.error(f"抓取營收失敗 {stock_id}: {e}")
        return pd.DataFrame()

def fetch_financial_statements(stock_id, years=3):
    """
    抓取季財報資料
    """
    try:
        dl = DataLoader()
        if FINMIND_API_TOKEN:
            dl.login_by_token(api_token=FINMIND_API_TOKEN)
            
        start_date = (datetime.now() - timedelta(days=years*365)).strftime("%Y-%m-%d")
        
        df = dl.taiwan_stock_financial_statement(
            stock_id=stock_id,
            start_date=start_date
        )
        
        return df
    except Exception as e:
        logger.error(f"抓取財報失敗 {stock_id}: {e}")
        return pd.DataFrame()


def get_latest_revenue_month(stock_id: str) -> Optional[str]:
    """
    查詢股票最新公布的營收月份
    
    Args:
        stock_id (str): 股票代碼
        
    Returns:
        Optional[str]: 最新營收月份，例如 '2024-12'，如果查無資料回傳 None
    """
    try:
        df_rev = fetch_monthly_revenue(stock_id, years=1)
        
        if df_rev.empty:
            logger.warning(f"查無 {stock_id} 營收資料")
            return None
        
        # Sort by date descending and get the latest
        df_rev = df_rev.sort_values('date', ascending=False)
        latest = df_rev.iloc[0]
        
        # Extract year and month from the 'date' column or 'revenue_year'/'revenue_month'
        if 'revenue_year' in df_rev.columns and 'revenue_month' in df_rev.columns:
            year = int(latest['revenue_year'])
            month = int(latest['revenue_month'])
        else:
            # Fallback: parse from date
            date_val = pd.to_datetime(latest['date'])
            year = date_val.year
            month = date_val.month
        
        revenue_month_str = f"{year}-{month:02d}"
        logger.info(f"{stock_id} 最新營收月份: {revenue_month_str}")
        return revenue_month_str
        
    except Exception as e:
        logger.error(f"查詢最新營收月份失敗 {stock_id}: {e}")
        return None


def get_latest_financial_quarter(stock_id: str) -> Optional[str]:
    """
    查詢股票最新公布的財報季度
    
    Args:
        stock_id (str): 股票代碼
        
    Returns:
        Optional[str]: 最新財報季度，例如 '2024-Q3'，如果查無資料回傳 None
    """
    try:
        df_fin = fetch_financial_statements(stock_id, years=2)
        
        if df_fin.empty:
            logger.warning(f"查無 {stock_id} 財報資料")
            return None
        
        # Financial statements usually have 'date' column in format like '2024-09-30'
        # Quarter is determined by the month: Q1=3, Q2=6, Q3=9, Q4=12
        df_fin['date'] = pd.to_datetime(df_fin['date'])
        df_fin = df_fin.sort_values('date', ascending=False)
        
        # Get unique dates (each quarter has multiple financial statement items)
        unique_dates = df_fin['date'].drop_duplicates().sort_values(ascending=False)
        
        if unique_dates.empty:
            return None
            
        latest_date = unique_dates.iloc[0]
        year = latest_date.year
        month = latest_date.month
        
        # Map month to quarter
        quarter_map = {3: 'Q1', 6: 'Q2', 9: 'Q3', 12: 'Q4'}
        quarter = quarter_map.get(month)
        
        if not quarter:
            # Fallback: approximate quarter
            if month <= 3:
                quarter = 'Q1'
            elif month <= 6:
                quarter = 'Q2'
            elif month <= 9:
                quarter = 'Q3'
            else:
                quarter = 'Q4'
        
        quarter_str = f"{year}-{quarter}"
        logger.info(f"{stock_id} 最新財報季度: {quarter_str}")
        return quarter_str
        
    except Exception as e:
        logger.error(f"查詢最新財報季度失敗 {stock_id}: {e}")
        return None
