import os
import logging
import time
from dotenv import load_dotenv

# New SDK
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Model fallback list - verified to support Google Search tool
# gemini-2.5-flash-lite 不支援 Search，已移除
SEARCH_CAPABLE_MODELS = [
    "gemini-2.5-flash",   # 主要：支援 Search
    "gemini-2.0-flash",   # 備援：支援 Search
]

def search_eps_forecast(stock_id, stock_name):
    """
    使用 Gemini 聯網搜尋法人對該公司的最新 EPS 預估
    具備 Model 備援機制：當一個 model 額度用完時，自動切換到下一個
    
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
        tools = [types.Tool(google_search=types.GoogleSearch())]
        
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
4. **無數據時**：若搜尋不到明確數字，請回傳 \"暫無 EPS 預估資料\"。

輸出範例：
2024 EPS: 5.5元 (調升)
2025 EPS: 6.2~6.5元
Source: [工商時報](https://...)
"""
        
        # Model fallback mechanism
        for model_name in SEARCH_CAPABLE_MODELS:
            logger.info(f"Generating EPS forecast search for {stock_id} {stock_name} (Model: {model_name})...")
            
            try:
                # API Call
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=tools
                    )
                )
                
                # Add delay to avoid rate limiting
                time.sleep(5)
                
                if response and response.text:
                    logger.info(f"EPS search succeeded with model: {model_name}")
                    return response.text.strip()
                else:
                    logger.warning(f"Empty response from {model_name}, trying next model...")
                    continue
                    
            except Exception as e:
                error_msg = str(e)
                
                # Check if quota/rate limit error - try next model
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg or "UNAVAILABLE" in error_msg:
                    logger.warning(f"Model {model_name} 額度已滿或不可用，切換到下一個 model...")
                    continue
                else:
                    # Non-retriable error
                    logger.error(f"Gemini Search Error ({model_name}): {e}")
                    return f"EPS 搜尋發生錯誤: {e}"
        
        # All models exhausted
        logger.error("所有備援 model 都無法使用")
        return "EPS 搜尋失敗 (所有 model 額度已滿)"
            
    except Exception as e:
        logger.error(f"Gemini Search Init Error: {e}")
        return f"EPS 搜尋初始化錯誤: {e}"
