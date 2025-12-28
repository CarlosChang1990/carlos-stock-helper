import pandas as pd
import logging

logger = logging.getLogger(__name__)

def analyze_revenue(df_revenue, last_processed_str=None):
    """
    分析月營收資料
    
    Args:
        df_revenue (pd.DataFrame): 包含月營收的 DataFrame
        last_processed_str (str): 上次處理的月份，格式 "YYYY-MM" (e.g., "2025-10")
        
    Returns:
        dict: 營收分析結果 (如果沒有新資料則回傳 None)
    """
    if df_revenue.empty:
        return None
        
    # 確保資料依照日期排序
    df_revenue = df_revenue.sort_values('date')
    last_row = df_revenue.iloc[-1]
    
    current_ym = f"{last_row['revenue_year']}-{str(last_row['revenue_month']).zfill(2)}"
    
    # Check if data is new
    if last_processed_str and current_ym <= last_processed_str:
        return None
        
    # Process new revenue data
    current_revenue = last_row['revenue']
    
    # 1. MoM (Month-on-Month)
    mom_pct = 0.0
    if len(df_revenue) >= 2:
        prev_month_rev = df_revenue.iloc[-2]['revenue']
        if prev_month_rev > 0:
            mom_pct = ((current_revenue - prev_month_rev) / prev_month_rev) * 100

    # 2. YoY (Year-on-Year)
    yoy_pct = 0.0
    # Find record from 12 months ago
    # Using shift logic assuming data is continuous monthly
    # Better to filter by year-1, same month
    target_year = last_row['revenue_year'] - 1
    target_month = last_row['revenue_month']
    
    prev_year_row = df_revenue[
        (df_revenue['revenue_year'] == target_year) & 
        (df_revenue['revenue_month'] == target_month)
    ]
    
    if not prev_year_row.empty:
        prev_year_rev = prev_year_row.iloc[0]['revenue']
        if prev_year_rev > 0:
            yoy_pct = ((current_revenue - prev_year_rev) / prev_year_rev) * 100
            
    # 3. All-time High
    all_max_revenue = df_revenue['revenue'].max()
    is_all_time_high = (current_revenue >= all_max_revenue)
    
    # 4. N-Month High (e.g., 6 months, 12 months)
    # Exclude current month for calculation? Or include? "New high in N months" usually means highest in last N including current.
    # Let's verify highest in last N rows
    months_high_desc = ""
    if is_all_time_high:
        months_high_desc = "歷史新高"
    else:
        # Check against recent window (excluding current itself for comparison context, or simple max check)
        # Simply: Current is max of last N?
        windows = [12, 6, 3]
        for w in windows:
            if len(df_revenue) >= w:
                recent_max = df_revenue.tail(w)['revenue'].max()
                if current_revenue >= recent_max:
                    months_high_desc = f"近 {w} 個月新高"
                    break
    
    return {
        "year": last_row['revenue_year'],
        "month": last_row['revenue_month'],
        "revenue": current_revenue,
        "mom_pct": mom_pct,
        "yoy_pct": yoy_pct,
        "high_status": months_high_desc,
        "is_new": True,
        "date_str": current_ym
    }

def analyze_financials(df_fin, last_processed_str=None):
    """
    分析季財報資料
    
    Args:
        df_fin (pd.DataFrame): 包含財報的 DataFrame (date, type, value, origin_name)
        last_processed_str (str): 上次處理的季度，格式 "YYYY-QQ" (e.g., "2024-Q3")
        
    Returns:
        dict: 財報分析結果
    """
    if df_fin.empty:
        return None
        
    # Pivot Data: index=date, columns=type, values=value
    # FinMind data might have duplicates for same date/type? (Usually no for same report)
    df_pivot = df_fin.pivot_table(index='date', columns='type', values='value', aggfunc='first')
    df_pivot = df_pivot.sort_index()
    
    if df_pivot.empty:
        return None
        
    last_date = df_pivot.index[-1]
    last_dt = pd.to_datetime(last_date)
    year = last_dt.year
    quarter = (last_dt.month - 1) // 3 + 1
    current_q_str = f"{year}-Q{quarter}"
    
    # Check if new
    if last_processed_str and current_q_str <= last_processed_str:
        return None
        
    latest_data = df_pivot.loc[last_date]
    
    # 1. Margins Only if Revenue > 0
    revenue = latest_data.get('Revenue', 0)
    gross_profit = latest_data.get('GrossProfit', 0)
    op_income = latest_data.get('OperatingIncome', 0)
    net_income = latest_data.get('IncomeAfterTaxes', 0) # Or 'TotalConsolidatedProfitForThePeriod' depending on preference
    
    gm = (gross_profit / revenue * 100) if revenue > 0 else 0
    om = (op_income / revenue * 100) if revenue > 0 else 0
    nm = (net_income / revenue * 100) if revenue > 0 else 0
    
    # 2. Comparison (QoQ, YoY) for Margins
    # Prev Quarter
    prev_q_date_idx = -2 if len(df_pivot) >= 2 else None
    
    # Prev Year Quarter (approx 4 quarters ago)
    # Better to find by date match, but index search is easier for now if data continuous
    prev_y_date_idx = -5 if len(df_pivot) >= 5 else None # Current is -1, 4 ago is -5
    
    def get_margin(row):
        r = row.get('Revenue', 0)
        return (row.get('GrossProfit', 0)/r*100, row.get('OperatingIncome', 0)/r*100, row.get('IncomeAfterTaxes', 0)/r*100) if r > 0 else (0,0,0)

    gm_qoq_diff = 0
    om_qoq_diff = 0
    nm_qoq_diff = 0
    
    if prev_q_date_idx is not None:
        prev_q_row = df_pivot.iloc[prev_q_date_idx]
        p_gm, p_om, p_nm = get_margin(prev_q_row)
        gm_qoq_diff = gm - p_gm
        om_qoq_diff = om - p_om
        nm_qoq_diff = nm - p_nm
        
    gm_yoy_diff = 0
    om_yoy_diff = 0
    nm_yoy_diff = 0
    
    if prev_y_date_idx is not None:
        prev_y_row = df_pivot.iloc[prev_y_date_idx]
        p_gm_y, p_om_y, p_nm_y = get_margin(prev_y_row)
        gm_yoy_diff = gm - p_gm_y
        om_yoy_diff = om - p_om_y
        nm_yoy_diff = nm - p_nm_y

    # 3. EPS
    eps = latest_data.get('EPS', 0)
    
    # Cumulative EPS (YTD)
    # Sum EPS for current year up to this quarter
    # Filter original df_fin for 'EPS' type and year == year
    # But df_fin dates are strings? pd.to_datetime needed
    df_fin['date_dt'] = pd.to_datetime(df_fin['date'])
    eps_ytd = df_fin[
        (df_fin['type'] == 'EPS') & 
        (df_fin['date_dt'].dt.year == year) &
        (df_fin['date_dt'] <= last_dt)
    ]['value'].sum()
    
    # Last Year Cumulative EPS (Same period)
    eps_ytd_last_year = df_fin[
        (df_fin['type'] == 'EPS') & 
        (df_fin['date_dt'].dt.year == year - 1) &
        (df_fin['date_dt'].dt.month <= last_dt.month)
    ]['value'].sum()
    
    eps_ytd_growth = 0
    if eps_ytd_last_year > 0:
        eps_ytd_growth = ((eps_ytd - eps_ytd_last_year) / eps_ytd_last_year) * 100
    
    # Single EPS Growth
    eps_qoq = 0
    if prev_q_date_idx is not None:
        p_eps = df_pivot.iloc[prev_q_date_idx].get('EPS', 0)
        if p_eps > 0:
            eps_qoq = ((eps - p_eps) / p_eps) * 100
            
    eps_yoy = 0
    if prev_y_date_idx is not None:
        p_eps_y = df_pivot.iloc[prev_y_date_idx].get('EPS', 0)
        if p_eps_y > 0:
            eps_yoy = ((eps - p_eps_y) / p_eps_y) * 100

    return {
        "quarter_str": current_q_str,
        "gm": gm, "om": om, "nm": nm,
        "gm_qoq": gm_qoq_diff, "om_qoq": om_qoq_diff, "nm_qoq": nm_qoq_diff,
        "gm_yoy": gm_yoy_diff, "om_yoy": om_yoy_diff, "nm_yoy": nm_yoy_diff,
        "eps": eps,
        "eps_qoq": eps_qoq, "eps_yoy": eps_yoy,
        "eps_ytd": eps_ytd, "eps_ytd_last_year": eps_ytd_last_year,
        "eps_ytd_growth": eps_ytd_growth,
        "is_new": True
    }



def analyze_inertia_with_state(df, time_type="日線"):
    """
    慣性改變判斷 + 狀態鎖定 + 連續次數統計 + 觸發日期追蹤
    
    Args:
        df (pd.DataFrame): price data
        time_type (str): "日線", "週線", "月線" for labeling
    
    Returns:
        dict: {
            "state": str, ("慣性向上", "慣性向下", "盤整/無訊號")
            "count": int, 
            "trigger_dates": list,
            "description": str (Formatted string for report)
        }
    """
    default_res = {
        "state": "盤整/無訊號",
        "count": 0,
        "trigger_dates": [],
        "description": f"{time_type}慣性沒改變"
    }
    
    if df.empty or len(df) < 2:
        return default_res
        
    # Take last 60 periods to build state history
    subset = df.tail(60).copy().reset_index(drop=True)
    
    current_state = "盤整/無訊號"
    current_count = 0
    current_trigger_dates = []
    
    # Start form index 1 (compare i vs i-1)
    for i in range(1, len(subset)):
        t1 = subset.loc[i]   # Today
        t2 = subset.loc[i-1] # Yesterday
        
        # Get date string
        current_date_str = ""
        if 'date' in t1:
             current_date_str = pd.to_datetime(t1['date']).strftime('%Y/%m/%d')
        else:
             current_date_str = pd.to_datetime(subset.index[i]).strftime('%Y/%m/%d')
        
        # 1. Up Change
        # High > Prev High AND Low > Prev Low AND Close > Prev Close (Price Up)
        if (t1['max'] > t2['max']) and (t1['min'] > t2['min']) and (t1['close'] > t2['close']):
            if current_state == "慣性向上":
                current_count += 1
                current_trigger_dates.append(current_date_str)
            else:
                current_state = "慣性向上"
                current_count = 1
                current_trigger_dates = [current_date_str]
                
        # 2. Down Change
        # High < Prev High AND Low < Prev Low AND Close < Prev Close (Price Down)
        elif (t1['max'] < t2['max']) and (t1['min'] < t2['min']) and (t1['close'] < t2['close']):
            if current_state == "慣性向下":
                current_count += 1
                current_trigger_dates.append(current_date_str)
            else:
                current_state = "慣性向下"
                current_count = 1
                current_trigger_dates = [current_date_str]
        
        # 3. No Change -> Hold State
        # Do nothing, count stays same, list stays same
    
    # Format Result
    res = default_res.copy()
    if current_state != "盤整/無訊號":
        res['state'] = current_state
        res['count'] = current_count
        res['trigger_dates'] = current_trigger_dates
        
        dates_str = f" [{', '.join(res['trigger_dates'])}]" if res['trigger_dates'] else ""
        res['description'] = f"{time_type}{current_state} (連續 {current_count} 次){dates_str}"
    else:
        # Check if we have a state but just no new trigger today? 
        # Actually logic above maintains state even if no new trigger today.
        # If state is still default, it means NO trigger in the window.
        res['description'] = f"{time_type}慣性沒改變"
        
    return res

def resample_to_period(df, period):
    """
    將日線資料重取樣為週線或月線
    
    Args:
        df: daily dataframe (must have datetime index or 'date')
        period: 'W' (Weekly), 'M' (Month End)
    """
    df_res = df.copy()
    if 'date' in df_res.columns:
        df_res['date'] = pd.to_datetime(df_res['date'])
        df_res = df_res.set_index('date')
        
    logic = {
        'open': 'first',
        'max': 'max',
        'min': 'min',
        'close': 'last'
    }
    
    # Pandas 2.0+ uses 'ME' for Month End, older uses 'M'
    # Use 'M' for broader compatibility or check version if needed. 'M' is deprecated in future pandas.
    # Try-except block or just use 'M' and ignore warning for now.
    try:
        resampled = df_res.resample(period).agg(logic)
    except Exception:
         # Fallback if 'M'/'ME' issues
        resampled = df_res.resample(period).agg(logic)
        
    return resampled.dropna().reset_index()


def analyze_all_inertia(df):
    """
    分析 日/週/月 慣性 (固定全部顯示)
    
    Args:
        df: daily dataframe
    """
    if 'date' in df.columns:
        last_date = pd.to_datetime(df.iloc[-1]['date'])
    else:
        last_date = pd.to_datetime(df.index[-1])
        
    # Daily: Always run
    d_res = analyze_inertia_with_state(df, "日線")
    d_inertia = d_res['description']
    
    w_inertia = None
    m_inertia = None
    
    # Weekly: Always run
    df_w = resample_to_period(df, 'W')
    if len(df_w) >= 2:
        w_res = analyze_inertia_with_state(df_w, "週線")
        w_inertia = w_res['description']
            
    # Monthly: Always run
    df_m = resample_to_period(df, 'M') # or 'ME'
    if len(df_m) >= 2:
        m_res = analyze_inertia_with_state(df_m, "月線")
        m_inertia = m_res['description']
    
    return {
        'daily': d_inertia,
        'weekly': w_inertia,
        'monthly': m_inertia,
    }

def analyze_3day_high_low(df, time_type="日線"):
    """
    三日高低點判斷 + 支撐/壓力區間 + 連續次數統計 + 觸發日期追蹤
    
    Args:
        df (pd.DataFrame): price data
        time_type (str): "日線", "週線", "月線"
        
    Returns:
        dict: {
            "state": str, 
            "count": int, 
            "trigger_dates": list, 
            "zone_type": str,
            "zone_range": [min, max],
            "zone_date": str,
            "description": str (Formatted string with time_type)
        }
    """
    default_res = {
        "state": "盤整",
        "count": 0,
        "trigger_dates": [],
        "zone_type": None,
        "zone_range": None,
        "zone_date": None,
        "description": f"{time_type}盤整"
    }
    
    if df.empty or len(df) < 4:
        return default_res
        
    # Take last 60 days
    subset = df.tail(60).copy().reset_index(drop=True)
    
    current_state = "盤整/無訊號"
    current_count = 0
    current_trigger_dates = []
    current_zone = None
    
    for i in range(3, len(subset)):
        today_row = subset.loc[i]
        today_close = today_row['close']
        # Try to get date string
        today_date_str = ""
        if 'date' in today_row:
             today_date_str = pd.to_datetime(today_row['date']).strftime('%Y/%m/%d')
        else:
             today_date_str = pd.to_datetime(subset.index[i]).strftime('%Y/%m/%d')
        
        # Previous 3 days indices
        indices_3 = [i-3, i-2, i-1]
        
        # Calculate Barrier
        prev_3_highs = subset.loc[indices_3, 'max'].max()
        prev_3_lows = subset.loc[indices_3, 'min'].min()
        
        if today_close > prev_3_highs:
            # Bullish Trigger
            if current_state == "站上三日高點":
                current_count += 1
                current_trigger_dates.append(today_date_str)
            else:
                current_state = "站上三日高點"
                current_count = 1
                current_trigger_dates = [today_date_str]
            
            # Update Zone (Always update on trigger)
            target_idx = subset.loc[indices_3, 'max'].idxmax()
            target_row = subset.loc[target_idx]
            current_zone = {
                "type": "support",
                "range": [target_row['min'], target_row['max']],
                "date": target_row['date'] if 'date' in target_row else subset.index[target_idx]
            }
            
        elif today_close < prev_3_lows:
            # Bearish Trigger
            if current_state == "跌破三日低點":
                current_count += 1
                current_trigger_dates.append(today_date_str)
            else:
                current_state = "跌破三日低點"
                current_count = 1
                current_trigger_dates = [today_date_str]
                
            # Update Zone
            target_idx = subset.loc[indices_3, 'min'].idxmin()
            target_row = subset.loc[target_idx]
            current_zone = {
                "type": "resistance",
                "range": [target_row['min'], target_row['max']],
                "date": target_row['date'] if 'date' in target_row else subset.index[target_idx]
            }
            
        # Else: Maintain State, Count, Dates, and Zone (Do nothing)
        # Count/Dates do not reset or increment on Hold
            
    # Format Result
    res = default_res.copy()
    res['state'] = current_state
    res['count'] = current_count
    res['trigger_dates'] = current_trigger_dates
    
    if current_state != "盤整" and current_zone:
        res['zone_type'] = current_zone['type']
        res['zone_range'] = current_zone['range']
        res['zone_date'] = current_zone['date']
        
        date_str = pd.to_datetime(res['zone_date']).strftime('%Y/%m/%d')
        min_v = float(res['zone_range'][0])
        max_v = float(res['zone_range'][1])
        
        label = "最新支撐" if res['zone_type'] == 'support' else "最新壓力"
        res['description'] = f"{label}: {date_str} ({min_v}~{max_v})"
        
    return res

