import requests
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_chips_data(stock_id):
    """
    從神秘金字塔抓取股權分散表
    URL: https://norway.twsthr.info/StockHolders.aspx?stock={stock_id}
    
    Returns:
        pd.DataFrame: Columns [Date, TotalShareholders, BigHand400_Pct, BigHand1000_Pct]
    """
    url = f"https://norway.twsthr.info/StockHolders.aspx?stock={stock_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        logging.info(f"Fetching chips data from {url}...")
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Chips fetch failed: {resp.status_code}")
            return pd.DataFrame()

        # Parse Tables
        tables = pd.read_html(resp.text)
        
        target_df = None
        
        for df in tables:
            # Robust check: Flatten matches
            # Check headers + first 3 rows
            
            check_str = ""
            # Add columns
            check_str += " ".join([str(c) for c in df.columns])
            
            # Add first 3 rows data
            for r in range(min(3, len(df))):
                check_str += " " + " ".join(df.iloc[r].astype(str).tolist())
            
            # Check keywords
            has_date = "資料日期" in check_str
            has_total = "總股東" in check_str and "人數" in check_str
            has_400 = "400" in check_str and "百分比" in check_str
            has_1000 = "1000" in check_str and "百分比" in check_str
            
            # Must have at least a few rows of data (Header + Data)
            # Table 8 (Header only) has 1 row. Table 9 has 300+.
            has_rows = len(df) > 5
            
            if has_date and has_total and has_400 and has_1000 and has_rows:
                target_df = df
                # Clean headers
                # Find row with "資料日期"
                for r in range(min(3, len(df))):
                    row_vals = df.iloc[r].astype(str).tolist()
                    if any("資料日期" in s for s in row_vals):
                        target_df.columns = row_vals
                        target_df = target_df.drop(range(r+1)).reset_index(drop=True)
                        break
                break
        
        if target_df is None:
            logger.warning(f"Chips: Main table not found for {stock_id} (Checked {len(tables)} tables)")
            return pd.DataFrame()

        # Extract Columns
        def find_col(df, keywords):
            for col in df.columns:
                c_str = str(col).replace(" ", "").replace("\n", "")
                if all(k in c_str for k in keywords):
                    return col
            return None

        col_date = find_col(target_df, ["資料日期"])
        col_total = find_col(target_df, ["總股東", "人數"])
        
        # Search specifically for percentages
        cols = target_df.columns.tolist()
        
        col_400_pct = None
        col_1000_pct = None
        
        for c in cols:
            c_str = str(c).replace(" ", "").replace("\n", "")
            if "持有百分比" in c_str:
                if "400" in c_str:
                    col_400_pct = c
                elif "1000" in c_str:
                    col_1000_pct = c
        
        if not col_date or not col_total:
             logger.warning("Chips: Critical columns missing")
             return pd.DataFrame()
             
        final_df = pd.DataFrame()
        final_df['Date'] = target_df[col_date]
        final_df['TotalShareholders'] = target_df[col_total]
        final_df['BigHand400_Pct'] = target_df[col_400_pct] if col_400_pct else 0
        final_df['BigHand1000_Pct'] = target_df[col_1000_pct] if col_1000_pct else 0

        # Clean Date
        # Handle float conversion (e.g. 20251219.0)
        final_df['Date'] = final_df['Date'].astype(str).str.replace(r'\.0$', '', regex=True)
        final_df['Date'] = final_df['Date'].str.replace(r'\D', '', regex=True)
        final_df = final_df[final_df['Date'].str.len() == 8]
        final_df = final_df.sort_values('Date')
        
        # Numeric
        for c in ['TotalShareholders', 'BigHand400_Pct', 'BigHand1000_Pct']:
             final_df[c] = pd.to_numeric(final_df[c], errors='coerce').fillna(0)
             
        return final_df

    except Exception as e:
        logger.error(f"Error fetching chips data: {e}")
        return pd.DataFrame()

def analyze_chips_consecutive(df):
    """
    分析籌碼連續變化 (總股東, 400張, 1000張)
    Result format similar to inertia/3-day
    """
    if df.empty or len(df) < 2:
        return {}
        
    # Analyze last available week vs previous
    # The dataframe is sorted by Date ascending.
    # Last row = Latest
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    date_str = current['Date'] # YYYYMMDD
    
    # metrics to check
    metrics = {
        'TotalShareholders': '總股東人數',
        'BigHand400_Pct': '400張大戶持股比',
        'BigHand1000_Pct': '1000張大戶持股比'
    }
    
    results = {}
    
    for col, label in metrics.items():
        val_curr = current.get(col, 0)
        val_prev = prev.get(col, 0)
        
        diff = val_curr - val_prev
        
        state = "無變化"
        if diff > 0:
            state = "增加"
        elif diff < 0:
            state = "減少"
            
        # Count consecutive
        count = 0
        dates = []
        
        if state != "無變化":
            count = 1
            dates = [current['Date']]
            
            # Start loop from len-3 (prev_prev) compare to len-2 (prev)
            # We want to check if prev vs prev_prev matches the state
            
            # Index logic:
            # We compare pair (i+1, i) where `i+1` is the later date.
            # Initial pair was (len-1, len-2) which established 'state'.
            # Next pair should be (len-2, len-3).
            # So `i+1` should be `len-2`. `i` should be `len-3`.
            
            start_idx = len(df) - 3
            
            for i in range(start_idx, -1, -1):
                row_later = df.iloc[i+1] # e.g. len-2 (prev)
                row_earlier = df.iloc[i] # e.g. len-3 (prev_prev)
                
                d = row_later.get(col, 0) - row_earlier.get(col, 0)
                
                hist_state = "無變化"
                if d > 0: hist_state = "增加"
                elif d < 0: hist_state = "減少"
                
                if hist_state == state:
                    count += 1
                    dates.insert(0, row_later['Date'])
                else:
                    break
        
        results[col] = {
            'label': label,
            'current_value': val_curr,
            'diff': diff,
            'state': state,
            'count': count,
            'dates': dates,
            'date_str': date_str
        }
        
    return results

def format_chips_report(results):
    """
    Format the analysis into string
    """
    if not results:
        return ""
        
    lines = []
    # Get Date from one of the metrics
    latest_date = list(results.values())[0]['date_str']
    formatted_date = f"{latest_date[:4]}/{latest_date[4:6]}/{latest_date[6:]}" # YYYY/MM/DD
    
    # lines.append(f"【籌碼面分析】({formatted_date})") # Removed header to let analysis.py handle it

    
    for key in ['TotalShareholders', 'BigHand400_Pct', 'BigHand1000_Pct']:
        if key not in results: continue
        
        res = results[key]
        val_fmt = f"{int(res['current_value']):,}" if key == 'TotalShareholders' else f"{res['current_value']:.2f}%"
        
        # State String
        state_str = "持平"
        if res['state'] == "增加":
            state_str = "增加"
        elif res['state'] == "減少":
            state_str = "減少"
            
        # Consective String
        cons_str = ""
        if res['count'] > 1:
            cons_str = f" (連續 {res['count']} 週)"
        
        lines.append(f"{res['label']}: {val_fmt} ({state_str}{cons_str})")
        
    return "\n".join(lines) + "\n"
