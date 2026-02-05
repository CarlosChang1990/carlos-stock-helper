"""
Core Analysis Module
Handles technical analysis, chips analysis, and fundamental analysis integration.
"""
from __future__ import annotations
import logging
from typing import Optional

from ta.momentum import StochasticOscillator
from ta.trend import SMAIndicator

from core.data import fetch_stock_data, fetch_monthly_revenue, fetch_financial_statements
from core.strategy import (
    analyze_all_inertia, 
    analyze_3day_high_low, 
    analyze_ma_cross, 
    analyze_revenue, 
    analyze_financials
)
from core.chips import fetch_chips_data, analyze_chips_consecutive

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


def _format_state_with_dates(res: Optional[dict]) -> Optional[str]:
    """
    Format state with dates:
    State (連N) [First ~ Last]
    or
    State [First] (if only 1)
    """
    if not res:
        return None
    
    state = res.get('state', '')
    # Filter out neutral states
    if '盤整' in state or '無訊號' in state:
        return None
        
    count = res.get('count', 0)
    trigger_dates = res.get('trigger_dates', [])
    
    date_str = ""
    if trigger_dates:
        first = trigger_dates[0]
        # If count > 1, show range if different
        if count > 1:
            last = trigger_dates[-1]
            if first != last:
                date_str = f"[{first}~{last}]"
            else:
                date_str = f"[{first}]"
        else:
            date_str = f"[{first}]"
            
    if count > 1:
        return f"{state} (連{count}) {date_str}"
    else:
        return f"{state} {date_str}"


def _build_chips_data(stock_id: str) -> Optional[list[dict]]:
    """Build chips analysis data for Flex Message"""
    chips_data = None
    try:
        df_chips = fetch_chips_data(stock_id)
        chips_results = analyze_chips_consecutive(df_chips)
        
        if chips_results:
            chips_data = []
            for key, data in chips_results.items():
                count = data.get('count', 0)
                state = data.get('state', '')  # 增加 or 減少 or 無變化
                label = data.get('label', key)
                current_value = data.get('current_value', 0)
                
                # Shorten label for display
                short_label = label
                if '400張大戶持股比' in label:
                    short_label = '400張大戶'
                elif '1000張大戶持股比' in label:
                    short_label = '千張大戶'
                
                # Format based on type
                if 'Pct' in key:
                    value_str = f"{current_value:.1f}%"
                else:
                    value_str = f"{int(current_value):,}"
                
                # Format state description
                if count > 0:
                    state_desc = f"({state} 連{count}週)"
                else:
                    state_desc = "(持平)"
                
                chips_data.append({
                    'name': short_label,
                    'desc': f"{value_str} {state_desc}"
                })
    except Exception as e:
        logger.error(f"籌碼分析失敗 (Flex): {e}")
        
    return chips_data


def _build_fundamental_data(
    stock_id: str, 
    last_revenue_month: Optional[str], 
    last_financial_quarter: Optional[str]
) -> tuple[Optional[str], Optional[dict], Optional[dict]]:
    """
    Build fundamental analysis string and updates
    
    Returns:
        (fundamental_str, revenue_update, financial_update)
    """
    fundamental_parts = []
    revenue_update = None
    financial_update = None
    
    # 1. Revenue
    try:
        df_rev = fetch_monthly_revenue(stock_id)
        revenue_result = analyze_revenue(df_rev, last_revenue_month)
        
        if revenue_result:
            rev_val = revenue_result['revenue'] / 100000000  # 轉成億
            fundamental_parts.append(
                f"📊 營收 {revenue_result['year']}-{revenue_result['month']}: {rev_val:.2f}億\n"
                f"MoM: {revenue_result['mom_pct']:+.1f}% | YoY: {revenue_result['yoy_pct']:+.1f}%"
            )
            if revenue_result.get('high_status'):
                fundamental_parts[-1] += f"\n{revenue_result['high_status']}"
            
            revenue_update = {
                'id': stock_id,
                'date_str': revenue_result['date_str']
            }
    except Exception as e:
        logger.error(f"營收分析失敗 (Flex): {e}")
    
    # 2. Financial Statements
    try:
        df_fin = fetch_financial_statements(stock_id)
        fin_result = analyze_financials(df_fin, last_financial_quarter)
        
        if fin_result:
            fundamental_parts.append(
                f"📈 季報 {fin_result['quarter_str']}\n"
                f"毛利率: {fin_result['gm']:.1f}% | 營益率: {fin_result['om']:.1f}%\n"
                f"EPS: {fin_result['eps']:.2f}元 (YoY {fin_result['eps_yoy']:+.1f}%)"
            )
            financial_update = {
                'id': stock_id,
                'quarter_str': fin_result['quarter_str']
            }
    except Exception as e:
        logger.error(f"財報分析失敗 (Flex): {e}")
    
    fundamental_str = "\n".join(fundamental_parts) if fundamental_parts else None
    return fundamental_str, revenue_update, financial_update


def analyze_stock_for_flex(
    stock_id: str, 
    stock_name: Optional[str] = None, 
    last_revenue_month: Optional[str] = None, 
    last_financial_quarter: Optional[str] = None
) -> Optional[dict]:
    """
    分析股票並回傳結構化資料供 Flex Message 使用
    
    Args:
        stock_id: 股票代碼
        stock_name: 股票名稱
        last_revenue_month: 上次處理的營收月份
        last_financial_quarter: 上次處理的財報季度
    
    Returns:
        dict: Flex Message 所需的資料結構
    """
    # 1. Fetch Data
    df = fetch_stock_data(stock_id)
    if df.empty:
        return None
        
    # 2. Calc Tech
    df = calculate_technical_indicators(df)
    
    # 3. Strategy
    inertia_result = analyze_all_inertia(df)
    three_day_result = analyze_3day_high_low(df, "日線")
    ma_cross_result = analyze_ma_cross(df)
    
    # Format Inertia (Weekly + Daily)
    inertia_parts = []
    
    # Weekly
    weekly_str = _format_state_with_dates(inertia_result.get('weekly_res'))
    if weekly_str:
        inertia_parts.append(f"週線: {weekly_str}")
        
    # Daily
    daily_str = _format_state_with_dates(inertia_result.get('daily_res'))
    if daily_str:
        inertia_parts.append(f"日線慣性: {daily_str}")
        
    final_inertia_str = "\n".join(inertia_parts) if inertia_parts else None
    
    # 4. Last row data
    last_row = df.iloc[-1]
    last_date = last_row['date'].strftime('%Y-%m-%d')
    
    # 5. Chips analysis
    chips_data = _build_chips_data(stock_id)
    
    # 6. Fundamental analysis
    fundamental_str, revenue_update, financial_update = _build_fundamental_data(
        stock_id, last_revenue_month, last_financial_quarter
    )
    
    # 7. Build result
    result = {
        'stock_id': stock_id,
        'stock_name': stock_name or stock_id,
        'date_str': last_date,
        'close_price': float(last_row['close']),
        'ma20': float(last_row['MA20']),
        'inertia_str': final_inertia_str,
        'three_day_str': _format_state_with_dates(three_day_result) if three_day_result else None,
        'three_day_zone': three_day_result.get('description') if three_day_result and '最新' in three_day_result.get('description', '') else None,
        'ma_cross_str': ma_cross_result.get('state_desc') if ma_cross_result else None,
        'ma_cross_key_price': ma_cross_result.get('key_price_desc') if ma_cross_result else None,
        'chips_data': chips_data,
        'fundamental_str': fundamental_str,
        'revenue_update': revenue_update,
        'financial_update': financial_update,
    }
    
    return result


def analyze_index_for_flex(index_id: str, index_name: str) -> Optional[dict]:
    """
    分析指數並回傳結構化資料供 Flex Message 使用
    
    Returns:
        dict: Same structure as analyze_stock_for_flex but without chips_data
    """
    # 1. Fetch Data
    df = fetch_stock_data(index_id)
    if df.empty:
        return None
        
    # 2. Calc Tech
    df = calculate_technical_indicators(df)
    
    # 3. Strategy
    inertia_result = analyze_all_inertia(df)
    three_day_result = analyze_3day_high_low(df, "日線")
    ma_cross_result = analyze_ma_cross(df)
    
    # Format Inertia
    inertia_parts = []
    
    # Weekly
    weekly_str = _format_state_with_dates(inertia_result.get('weekly_res'))
    if weekly_str:
        inertia_parts.append(f"週線: {weekly_str}")
        
    # Daily
    daily_str = _format_state_with_dates(inertia_result.get('daily_res'))
    if daily_str:
        inertia_parts.append(f"日線慣性: {daily_str}")
        
    final_inertia_str = "\n".join(inertia_parts) if inertia_parts else None
    
    # 4. Last row data
    last_row = df.iloc[-1]
    last_date = last_row['date'].strftime('%Y-%m-%d')
    
    # 5. Build result
    result = {
        'index_id': index_id,
        'index_name': index_name,
        'date_str': last_date,
        'close_price': float(last_row['close']),
        'ma20': float(last_row['MA20']),
        'inertia_str': final_inertia_str,
        'three_day_str': _format_state_with_dates(three_day_result) if three_day_result else None,
        'three_day_zone': three_day_result.get('description') if three_day_result and '最新' in three_day_result.get('description', '') else None,
        'ma_cross_str': ma_cross_result.get('state_desc') if ma_cross_result else None,
    }
    
    return result
