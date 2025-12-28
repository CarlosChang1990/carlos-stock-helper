import os
import logging
import time
from dotenv import load_dotenv

# New SDK
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

def search_eps_forecast(stock_id, stock_name):
    """
    使用 Gemini (v1 SDK) 聯網搜尋法人對該公司的最新 EPS 預估
    
    Args:
        stock_id (str): 股票代號
        stock_name (str): 股票名稱
        
    Returns:
        str: 整理後的預估報告文字
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY missing.")
        return "無法執行 EPS 搜尋 (Missing API Key)"
        
    try:
        # Initialize Client
        client = genai.Client(api_key=api_key)
        
        # Define Tool (Google Search)
        # In New SDK, simple string or typed config works
        # types.Tool(google_search=types.GoogleSearch())
        
        tools = [types.Tool(google_search=types.GoogleSearch())]
        
        # Model Name
        model_name = "gemini-flash-latest" # Stable, efficient, supports search
        
        prompt = f"""
你是一名極簡風格的財務助手。請針對台灣股市代號 {stock_id} ({stock_name}) 進行「法人EPS預估」的聯網搜尋。
範圍限定：**最近一個月內**。

目標：找出「本年度」與「下年度」(若有) 的 EPS 預估值 (單位：新台幣 TWD)。

請嚴格遵守以下「極簡輸出規則」：
1. **只輸出數字與趨勢**：不要任何摘要、不要引言、不要廢話。
2. **格式限定**：
   年份 EPS: 數字 (趨勢)
   Source: [來源名稱](URL)
3. **趨勢標記**：若報告有提到「調升」、「調降」、「持平」，請括號標註。若無，則不標註。
4. **無數據時**：若搜尋不到明確數字，請回傳 "Unknown"。

輸出範例：
2024 EPS: 5.5元 (調升)
2025 EPS: 6.2~6.5元
Source: [工商時報](https://...)
"""
        
        # Retry logic for Quota (429) errors
        logger.info(f"Generating EPS forecast search for {stock_id} {stock_name} (Model: {model_name})...")
        
        delay = 60
        retries = 3
        
        for attempt in range(retries):
            try:
                # API Call
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=tools
                    )
                )
                
                time.sleep(delay)
                if response and response.text:
                    return response.text.strip()
                else:
                    return "無搜尋結果或生成失敗。"
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Quota" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    # Wait time increases: 60s, 120s, 180s...
                    wait_time = 60 * (attempt + 1)
                    logger.warning(f"Gemini EPS Search 觸發限額 (429)，等待 {wait_time} 秒後重試 ({attempt + 1}/{retries})...")
                    time.sleep(wait_time)
                else:
                    # Non-retriable error
                    logger.error(f"Gemini Search Error (Attempt {attempt+1}): {e}")
                    return f"EPS 搜尋發生錯誤: {e}"
                    
        return "EPS 搜尋失敗 (重試多次仍遇限額)"
            
    except Exception as e:
        logger.error(f"Gemini Search Init Error: {e}")
        return f"EPS 搜尋初始化錯誤: {e}"
