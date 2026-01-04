import pandas as pd
import logging
from ta.momentum import StochasticOscillator
from ta.trend import SMAIndicator

# 設定日誌
logger = logging.getLogger(__name__)

def calculate_technical_indicators(df):
    """
    計算技術指標：MA (5, 20, 60) 與 KD (9, 3)
    
    Args:
        df (pd.DataFrame): 原始股價資料
        
    Returns:
        pd.DataFrame: 新增指標後的 DataFrame
    """
    if df.empty or len(df) < 60:
        logger.warning("資料不足，無法計算長天期指標")
        return df

    # 1. 計算移動平均線 (MA)
    # 使用 ta 套件或 pandas rolling
    
    # MA5 (週線)
    ma5_indicator = SMAIndicator(close=df['close'], n=5)
    df['MA5'] = ma5_indicator.sma_indicator()
    
    # MA20 (月線)
    ma20_indicator = SMAIndicator(close=df['close'], n=20)
    df['MA20'] = ma20_indicator.sma_indicator()
    
    # MA60 (季線)
    ma60_indicator = SMAIndicator(close=df['close'], n=60)
    df['MA60'] = ma60_indicator.sma_indicator()

    # 2. 計算 KD 指标 (Stochastic Oscillator)
    # 參數：n=9 (9天), d_n=3 (D值平滑)
    kd_indicator = StochasticOscillator(
        high=df['max'], 
        low=df['min'], 
        close=df['close'], 
        n=9, 
        d_n=3
    )
    
    df['K'] = kd_indicator.stoch()  # 注意：ta 套件的 stoch() 通常指 %K
    df['D'] = kd_indicator.stoch_signal() # %D
    
    # 填補 NaN (前端幾天無法計算)
    df = df.fillna(0)
    
    return df

def analyze_stock(stock_id, last_revenue_month=None, last_financial_quarter=None, stock_name=None):
    """
    整合函式：抓資料 -> 算指標 -> 營收分析 -> 財報分析
    
    Args:
        stock_id (str): 股票代碼
        last_revenue_month (str): 上次處理的營收月份
        last_financial_quarter (str): 上次處理的財報季度 (e.g. "2024-Q3")
        stock_name (str): 股票名稱
        
    Returns:
        dict: {
            'report': str,
            'revenue_update': dict or None,
            'financial_update': dict or None
        }
    """
    from core.data import fetch_stock_data, fetch_monthly_revenue, fetch_financial_statements
    
    # 1. 抓資料 (日線)
    df = fetch_stock_data(stock_id)
    if df.empty:
        return {'report': f"股票 {stock_id} 抓取日線資料失敗。", 'revenue_update': None, 'financial_update': None}
        
    # 2. 算指標
    df = calculate_technical_indicators(df)
    
    # 3. 策略/邏輯運算 (技術面)
    from core.strategy import analyze_revenue, analyze_financials, analyze_all_inertia, analyze_3day_high_low, analyze_ma_cross
    strategy_result = {} # Empty dict for now, used for passing info to AI
    inertia_result = analyze_all_inertia(df)
    three_day_result = analyze_3day_high_low(df, "日線")
    ma_cross_result = analyze_ma_cross(df)
    
    # Add info for AI (Simple Version)
    strategy_result['inertia'] = inertia_result
    strategy_result['three_day'] = three_day_result['state']
    
    # 4. 營收分析
    from core.ai import search_eps_forecast
    
    revenue_info = None
    revenue_report_str = ""
    revenue_update = None
    
    try:
        df_rev = fetch_monthly_revenue(stock_id)
        revenue_result = analyze_revenue(df_rev, last_revenue_month)
        
        if revenue_result:
            # 偵測到新營收
            rev_val = revenue_result['revenue'] / 100000000 # 轉成億
            
            # Trigger EPS Search via Gemini
            eps_forecast_str = search_eps_forecast(stock_id, stock_name)
            
            revenue_report_str = f"""
【最新月營收公布】({revenue_result['year']}-{revenue_result['month']})
金額: {rev_val:.2f} 億
MoM: {revenue_result['mom_pct']:.2f}%
YoY: {revenue_result['yoy_pct']:.2f}%
{revenue_result['high_status'] if revenue_result['high_status'] else ''}

{eps_forecast_str}
"""
            revenue_update = {
                'id': stock_id,
                'date_str': revenue_result['date_str']
            }
            
            # 將營收資訊加入策略結果供 AI 參考
            strategy_result['revenue_note'] = f"公布最新月營收 {rev_val:.2f}億. 法人預估: {eps_forecast_str}"

    except Exception as e:
        # Import error fallback if core.ai fails or other issues
        logger.error(f"營收分析失敗: {e}")
        
    # 5. 財報分析
    fin_report_str = ""
    fin_update = None
    
    try:
        df_fin = fetch_financial_statements(stock_id)
        fin_result = analyze_financials(df_fin, last_financial_quarter)
        
        if fin_result:
             fin_report_str = f"""
【最新季報公布】({fin_result['quarter_str']})
毛利率: {fin_result['gm']:.2f}% (QoQ {fin_result['gm_qoq']:+.2f}%, YoY {fin_result['gm_yoy']:+.2f}%)
營益率: {fin_result['om']:.2f}% (QoQ {fin_result['om_qoq']:+.2f}%, YoY {fin_result['om_yoy']:+.2f}%)
淨利率: {fin_result['nm']:.2f}% (QoQ {fin_result['nm_qoq']:+.2f}%, YoY {fin_result['nm_yoy']:+.2f}%)

[EPS]
單季: {fin_result['eps']:.2f} 元 (QoQ {fin_result['eps_qoq']:+.2f}%, YoY {fin_result['eps_yoy']:+.2f}%)
累計: {fin_result['eps_ytd']:.2f} 元 (YoY {fin_result['eps_ytd_growth']:+.2f}%)
"""
             fin_update = {
                 'id': stock_id,
                 'quarter_str': fin_result['quarter_str']
             }
             
             strategy_result['financial_note'] = f"公布 {fin_result['quarter_str']} 財報: 單季EPS {fin_result['eps']:.2f}, 累計EPS {fin_result['eps_ytd']:.2f} (YoY {fin_result['eps_ytd_growth']:.2f}%)"
             
    except Exception as e:
        logger.error(f"財報分析失敗: {e}")

    # 6. 籌碼面分析 (週更)
    from core.chips import fetch_chips_data, analyze_chips_consecutive, format_chips_report
    chips_report_str = ""
    try:
        # Check if today is Monday (0) to reduce load? Or run always?
        # User requested "First trading day of week".
        # Let's run it always so the latest info is always visible, or restrict if performance issue.
        # Scraping is external, might be slow (2-3s).
        # Let's add a condition: Run if Monday OR if we haven't seen this week's data?
        # Simpler: Run always.
        df_chips = fetch_chips_data(stock_id)
        chips_results = analyze_chips_consecutive(df_chips)
        chips_report_str = format_chips_report(chips_results)
    except Exception as e:
        logger.error(f"籌碼分析失敗: {e}")
        chips_report_str = ""

    # 7. 格式化輸出
    last_row = df.iloc[-1]
    last_date = last_row['date'].strftime('%Y-%m-%d')
    
    title_name = f"{stock_id} {stock_name}" if stock_name else stock_id
    
    # --- 1. 基本訊息 ---
    basic_info_str = f"[基本訊息]\n收盤價: {last_row['close']}\n月線(20MA): {last_row['MA20']:.2f}"

    # --- 2. 技術面 ---
    # Helper to format 3-day line
    def fmt_3day(res, label):
        if not res: return None
        base = f"{label}狀態: {res['state']}"
        if res.get('count', 0) > 0:
             dates = res.get('trigger_dates', [])
             dates_str = f"[{', '.join(dates)}]" if dates else ""
             if res['count'] > 1:
                 base += f" (連{res['count']}) {dates_str}"
             else:
                 base += f" {dates_str}"
        
        # Start new line for Zone description if any
        if 'description' in res and "最新" in res['description']: # Check if zone description exists
             base += f"\n   ↳ {res['description']}"
        return base

    technical_lines = [
        # Inertia
        f"{inertia_result['weekly']}" if inertia_result.get('weekly') else None,
        "", # Empty line
        # 3-Day
        fmt_3day(three_day_result, "日線"),
        "", # Empty line
        # MA Cross
        f"MA交叉: {ma_cross_result['state_desc']}",
        f"   ↳ {ma_cross_result['key_price_desc']}" if ma_cross_result.get('key_price_desc') else None,
        f"   ↳ {ma_cross_result['trigger_desc']}" if ma_cross_result.get('trigger_desc') else None,
    ]

    technical_str = "\n".join([line for line in technical_lines if line])
    
    # --- 3. 籌碼面 ---
    chips_section_str = ""
    if chips_report_str and 'chips_results' in locals() and chips_results:
        # Get date from results
        latest_date = list(chips_results.values())[0]['date_str']
        fmt_date = f"{latest_date[:4]}/{latest_date[4:6]}/{latest_date[6:]}"
        chips_section_str = f"[籌碼面] ({fmt_date})\n{chips_report_str.strip()}"
    elif chips_report_str:
        chips_section_str = f"[籌碼面]\n{chips_report_str.strip()}"
    else:
        chips_section_str = f"[籌碼面]\n無籌碼資料"

    # --- 4. 基本面 ---
    # Combine Revenue and Financials
    fundamental_lines = []
    if revenue_report_str.strip():
        # Remove extra newlines for cleaner density
        fundamental_lines.append(revenue_report_str.strip())
    
    if fin_report_str.strip():
        fundamental_lines.append(fin_report_str.strip())
        
    fundamental_str = "\n\n".join(fundamental_lines) if fundamental_lines else "無近期基本面更新"
    
    output = f"""
【{title_name} 分析報告】({last_date})

{basic_info_str}

[技術面]
{technical_str}

{chips_section_str}

[基本面]
{fundamental_str}
----------------------
"""
    return {'report': output, 'revenue_update': revenue_update, 'financial_update': fin_update}

def analyze_index(index_id, index_name):
    """
    分析大盤/櫃買指數 (僅包含基本訊息與技術面)
    """
    from core.data import fetch_stock_data
    from core.strategy import analyze_all_inertia, analyze_3day_high_low, analyze_ma_cross
    
    # 1. Fetch Data
    df = fetch_stock_data(index_id)
    if df.empty:
        return f"【{index_name}】無法取得資料"
        
    # 2. Calc Tech
    df = calculate_technical_indicators(df)
    
    # 3. Strategy
    inertia_result = analyze_all_inertia(df)
    three_day_result = analyze_3day_high_low(df, "日線")
    ma_cross_result = analyze_ma_cross(df)
    
    # 4. Format Output
    last_row = df.iloc[-1]
    last_date = last_row['date'].strftime('%Y-%m-%d')
    
    # --- 1. Basic Info ---
    basic_info_str = f"[基本訊息]\n收盤價: {last_row['close']}\n月線(20MA): {last_row['MA20']:.2f}"
    
    # --- 2. Technical ---
    # Inertia
    tech_lines = [
        f"{inertia_result['weekly']}" if inertia_result.get('weekly') else None
    ]
    
    # 3-Day
    # 3-Day
    def fmt_3day_simple(res, label):
        if not res: return None
        base = f"{label}狀態: {res['state']}"
        if res.get('count', 0) > 0:
             # Index report usually simpler, maybe keep trigger dates?
             dates = res.get('trigger_dates', [])
             dates_str = f"[{dates[-1]}]" if dates else "" # Show last date only for simplicity? Or full. Let's keep full.
             if res['count'] > 1:
                 base += f" (連{res['count']})"
             # Index report: keep concise.
        if 'description' in res and "最新" in res['description']:
            base += f"\n   ↳ {res['description']}"
        return base

    tech_lines.append(fmt_3day_simple(three_day_result, "日線"))
    
    # MA Cross
    tech_lines.append(f"MA交叉: {ma_cross_result['state_desc']}")
    if ma_cross_result.get('key_price_desc'):
         tech_lines.append(f"   ↳ {ma_cross_result['key_price_desc']}")
    if ma_cross_result.get('trigger_desc'):
         tech_lines.append(f"   ↳ {ma_cross_result['trigger_desc']}")
    
    technical_str = "\n".join([line for line in tech_lines if line])
    
    output = f"""
【{index_name} ({index_id})】({last_date})

{basic_info_str}

[技術面]
{technical_str}
---------------------------
"""
    return output.strip()
