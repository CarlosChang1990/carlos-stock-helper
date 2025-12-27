import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEET_URL
import logging

# 設定日誌
logger = logging.getLogger(__name__)

def get_service():
    """
    取得 gspread 服務實例
    使用設定檔中的憑證路徑
    """
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_SHEETS_CREDENTIALS_FILE, scope
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"無法取得 Google Sheets 服務: {e}")
        raise

def get_watchlist():
    """
    從 Google Sheets 讀取股票觀察清單
    假設第一欄為股票代碼 (Stock ID)
    
    Returns:
        list: 股票代碼列表 (例如 ['2330', '2317'])
    """
    try:
        client = get_service()
        if not GOOGLE_SHEET_URL:
            raise ValueError("未設定 GOOGLE_SHEET_URL")
            
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        
        # 讀取第一欄的所有值
        # 假設第一行是標題，從第二行開始讀取
        # 如果整欄都沒有標題，可以調整 slice
        col_values = sheet.col_values(1)
        
        # 過濾掉標題（如果有的話，這裡簡單判斷如果是 purely numeric 或是長度符合才算）
        # 這裡假設使用者會自己維護，或者我們過濾掉非數字的行
        # 簡單起見，我們回傳所有非空值，使用時再做清理
        stock_ids = [str(x).strip() for x in col_values if str(x).strip().isdigit()]
        
        # 去重
        stock_ids = list(set(stock_ids))
        
        logger.info(f"從 Google Sheets 讀取到 {len(stock_ids)} 檔股票")
        return stock_ids

    except Exception as e:
        logger.error(f"讀取觀察清單失敗: {e}")
        return []

def update_stock_names(stock_map):
    """
    更新 Google Sheets 中的股票名稱
    
    Args:
        stock_map (dict): key=stock_id, value=stock_name
    """
    try:
        client = get_service()
        if not GOOGLE_SHEET_URL:
            raise ValueError("未設定 GOOGLE_SHEET_URL")
            
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        
        # 讀取第一欄 (Stock ID)
        col_values = sheet.col_values(1)
        
        # 準備要更新的 cells
        # 假設第二欄是股票名稱
        cells_to_update = []
        
        for i, val in enumerate(col_values):
            # 跳過非數字的 ID (如果是標題)
            sid = str(val).strip()
            if not sid.isdigit():
                continue
                
            if sid in stock_map:
                name = stock_map[sid]
                # row 是 i + 1, col 是 2 (名稱欄)
                # Cell(row, col, value)
                cells_to_update.append(gspread.Cell(i + 1, 2, name))
        
        if cells_to_update:
            sheet.update_cells(cells_to_update)
            logger.info(f"成功更新 {len(cells_to_update)} 筆股票名稱")
        else:
            logger.info("沒有需要更新的股票名稱")
            
    except Exception as e:
        logger.error(f"更新股票名稱失敗: {e}")

def get_watchlist_details():
    """
    讀取觀察清單的詳細資訊 (ID, Name, Last Revenue Month)
    
    Returns:
        list: List of dicts, e.g., [{'id': '2330', 'name': '台積電', 'last_revenue_month': '2025-11', 'row_idx': 2}, ...]
    """
    try:
        client = get_service()
        if not GOOGLE_SHEET_URL:
            raise ValueError("未設定 GOOGLE_SHEET_URL")
            
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        
        # 讀取前4欄: ID, Name, Last Revenue Month, Last Financial Quarter
        # get_all_values 回傳二維陣列
        all_values = sheet.get_all_values()
        
        results = []
        for i, row in enumerate(all_values):
            # i is 0-indexed, so row_idx in sheet is i+1
            if not row:
                continue
                
            sid = str(row[0]).strip()
            
            # Skip non-digit IDs (header)
            if not sid.isdigit():
                continue
            
            # Handle missing columns safely
            name = row[1] if len(row) > 1 else ""
            last_rev = row[2] if len(row) > 2 else ""
            last_fin = row[3] if len(row) > 3 else ""
            
            results.append({
                'id': sid,
                'name': name,
                'last_revenue_month': last_rev,
                'last_financial_quarter': last_fin,
                'row_idx': i + 1
            })
            
        logger.info(f"讀取詳細觀察清單: {len(results)} 筆")
        return results
        
    except Exception as e:
        logger.error(f"讀取詳細觀察清單失敗: {e}")
        return []

def update_last_revenue_month(row_idx, revenue_month_str):
    """
    更新最後營收月份 (Column C)
    
    Args:
        row_idx (int): Sheet row index (1-based)
        revenue_month_str (str): e.g. "2025-11"
    """
    try:
        client = get_service()
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        
        # Column C is 3
        sheet.update_cell(row_idx, 3, revenue_month_str)
        logger.info(f"Row {row_idx} 更新營收月份為 {revenue_month_str}")
        
    except Exception as e:
        logger.error(f"更新營收月份失敗: {e}")

def update_last_financial_quarter(row_idx, quarter_str):
    """
    更新最後財報季度 (Column D)
    
    Args:
        row_idx (int): Sheet row index (1-based)
        quarter_str (str): e.g. "2024-Q3"
    """
    try:
        client = get_service()
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        
        # Column D is 4
        sheet.update_cell(row_idx, 4, quarter_str)
        logger.info(f"Row {row_idx} 更新財報季度為 {quarter_str}")
        
    except Exception as e:
        logger.error(f"更新財報季度失敗: {e}")

def update_stock_name_cell(row_idx, name):
    """
    更新股票名稱 (Column B)
    
    Args:
        row_idx (int): Sheet row index (1-based)
        name (str): Stock Name
    """
    try:
        client = get_service()
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        
        # Column B is 2
        sheet.update_cell(row_idx, 2, name)
        logger.info(f"Row {row_idx} 更新股票名稱為 {name}")
        
    except Exception as e:
        logger.error(f"更新股票名稱失敗: {e}")
