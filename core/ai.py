from __future__ import annotations
import os
import logging
import time
from dotenv import load_dotenv

# New SDK
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Model fallback list - verified to support Google Search tool
# Paid tier: 使用 gemini-2.5-pro 做財務分析，品質最佳
SEARCH_CAPABLE_MODELS = [
    "gemini-3.5-flash",     # 主要：最強推理能力，適合財務分析
    "gemini-2.5-pro",   # 備援：速度與品質平衡
]

# Vision capable models for image recognition
# 圖片辨識用便宜的 model 就足夠
VISION_CAPABLE_MODELS = [
    "gemini-3.1-flash-lite",   # 主要：便宜且足夠辨識股票名稱
    "gemini-3.5-flash",   # 備援
]


def extract_stocks_from_image(image_path: str) -> list[dict]:
    """
    使用 Gemini Vision 辨識證券 app 截圖中的股票名稱，
    並轉換成股票代碼列表
    
    Args:
        image_path (str): 圖片檔案路徑
        
    Returns:
        list[dict]: [{'id': '2330', 'name': '台積電'}, ...]
                    如果辨識失敗，回傳空列表
    """
    import json
    from pathlib import Path
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY missing.")
        return []
    
    # Read and encode image
    try:
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"Image file not found: {image_path}")
            return []
            
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Determine mime type
        suffix = image_path.suffix.lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(suffix, "image/png")
        
    except Exception as e:
        logger.error(f"Failed to read image: {e}")
        return []
    
    try:
        # Initialize Client
        client = genai.Client(api_key=api_key)
        
        prompt = """
你是一名台灣股票專家。請仔細辨識這張證券 app 截圖中的「個股名稱」。

**辨識規則:**
1. 只辨識「個股」，忽略大盤指數（如加權指數、櫃買指）
2. 只輸出 JSON 格式，不要任何其他文字
3. 如果無法辨識任何股票，回傳空陣列 []

**輸出格式 (嚴格遵守 JSON):**
["股票名稱1", "股票名稱2", "股票名稱3"]

**範例輸出:**
["台積電", "聯發科", "鴻海"]
"""
        
        # Model fallback mechanism
        for model_name in VISION_CAPABLE_MODELS:
            logger.info(f"Extracting stocks from image (Model: {model_name})...")
            
            try:
                # Create image part using inline_data
                image_part = types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type
                )
                
                # API Call with image
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, image_part],
                )
                
                # Add delay to avoid rate limiting
                time.sleep(2)
                
                if response and response.text:
                    logger.info(f"Image recognition succeeded with model: {model_name}")
                    raw_text = response.text.strip()
                    
                    # Parse JSON from response
                    # Handle potential markdown code blocks
                    if "```json" in raw_text:
                        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_text:
                        raw_text = raw_text.split("```")[1].split("```")[0].strip()
                    
                    stock_names = json.loads(raw_text)
                    
                    if not isinstance(stock_names, list):
                        logger.warning(f"Unexpected response format: {raw_text}")
                        continue
                    
                    logger.info(f"Identified stock names: {stock_names}")
                    
                    # Convert names to stock IDs
                    result = _convert_names_to_stock_ids(stock_names)
                    return result
                    
                else:
                    logger.warning(f"Empty response from {model_name}, trying next model...")
                    continue
                    
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}, response: {raw_text}")
                continue
            except Exception as e:
                error_msg = str(e)
                
                # Check if quota/rate limit error - try next model
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg or "UNAVAILABLE" in error_msg:
                    logger.warning(f"Model {model_name} 額度已滿或不可用，切換到下一個 model...")
                    continue
                else:
                    # Non-retriable error
                    logger.error(f"Gemini Vision Error ({model_name}): {e}")
                    return []
        
        # All models exhausted
        logger.error("所有備援 model 都無法使用")
        return []
            
    except Exception as e:
        logger.error(f"Gemini Vision Init Error: {e}")
        return []


def _convert_names_to_stock_ids(stock_names: list[str]) -> list[dict]:
    """
    將股票名稱轉換成股票代碼
    使用 FinMind 的 taiwan_stock_info 查詢
    
    Args:
        stock_names (list[str]): 股票名稱列表
        
    Returns:
        list[dict]: [{'id': '2330', 'name': '台積電'}, ...]
    """
    from FinMind.data import DataLoader
    from config import FINMIND_API_TOKEN
    
    try:
        dl = DataLoader()
        if FINMIND_API_TOKEN:
            dl.login_by_token(api_token=FINMIND_API_TOKEN)
            
        # Get all stock info
        df_info = dl.taiwan_stock_info()
        
        if df_info.empty:
            logger.error("Failed to fetch taiwan_stock_info")
            return []
        
        results = []
        
        for name in stock_names:
            name = name.strip()
            if not name:
                continue
                
            # Try exact match first
            match = df_info[df_info['stock_name'] == name]
            
            if match.empty:
                # Try partial match (stock name contains input)
                match = df_info[df_info['stock_name'].str.contains(name, na=False)]
            
            if not match.empty:
                # Take first match
                stock_id = match.iloc[0]['stock_id']
                stock_name = match.iloc[0]['stock_name']
                results.append({'id': stock_id, 'name': stock_name})
                logger.info(f"Matched: {name} -> {stock_id} ({stock_name})")
            else:
                logger.warning(f"No match found for stock name: {name}")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to convert stock names to IDs: {e}")
        return []


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
