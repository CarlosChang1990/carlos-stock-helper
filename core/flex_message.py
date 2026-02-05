"""
Flex Message 建構模組
用於產生 LINE Flex Message Carousel 格式的股票報告
"""
from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def build_stock_bubble(
    stock_id: str,
    stock_name: str,
    date_str: str,
    close_price: float,
    ma20: float,
    inertia_str: Optional[str] = None,
    three_day_str: Optional[str] = None,
    three_day_zone: Optional[str] = None,
    ma_cross_str: Optional[str] = None,
    ma_cross_key_price: Optional[str] = None,
    chips_data: Optional[list] = None,
    fundamental_str: Optional[str] = None,
) -> dict:
    """
    建立股票卡片 Bubble
    
    Args:
        stock_id: 股票代碼
        stock_name: 股票名稱
        date_str: 日期
        close_price: 收盤價
        ma20: 20日均線
        inertia_str: 週線慣性描述
        three_day_str: 日線狀態描述
        three_day_zone: 壓力/支撐區間
        ma_cross_str: MA交叉描述
        ma_cross_key_price: MA關鍵價位
        chips_data: 籌碼資料 [{'name': '外資', 'desc': '連3賣 -1,234張'}, ...]
        fundamental_str: 基本面摘要 (選填)
        
    Returns:
        dict: Flex Bubble JSON
    """
    
    # Header
    header = {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": f"📊 {stock_name}",
                "weight": "bold",
                "size": "lg",
                "color": "#FFFFFF"
            },
            {
                "type": "text",
                "text": f"{stock_id} | {date_str}",
                "size": "xs",
                "color": "#AAAAAA"
            }
        ],
        "backgroundColor": "#1a1a2e",
        "paddingAll": "15px"
    }
    
    # Body sections
    body_contents = []
    
    # 基本訊息區
    price_color = "#00C853" if close_price >= ma20 else "#FF5252"
    body_contents.append({
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {"type": "text", "text": "收盤", "size": "sm", "color": "#888888", "flex": 2},
            {"type": "text", "text": f"{close_price:.2f}", "size": "sm", "color": price_color, "flex": 3, "align": "end"},
            {"type": "text", "text": "月線", "size": "sm", "color": "#888888", "flex": 2},
            {"type": "text", "text": f"{ma20:.2f}", "size": "sm", "color": "#FFFFFF", "flex": 3, "align": "end"},
        ],
        "margin": "md"
    })
    
    # 分隔線
    body_contents.append({"type": "separator", "margin": "lg"})
    
    # 技術面區
    body_contents.append({
        "type": "text",
        "text": "[技術面]",
        "size": "sm",
        "color": "#4FC3F7",
        "weight": "bold",
        "margin": "lg"
    })
    
    # 週線慣性
    if inertia_str:
        body_contents.append({
            "type": "text",
            "text": inertia_str,
            "size": "xs",
            "color": "#FFFFFF",
            "wrap": True,
            "margin": "sm"
        })
    
    # 日線狀態
    if three_day_str:
        body_contents.append({
            "type": "text",
            "text": f"日線: {three_day_str}",
            "size": "xs",
            "color": "#FFFFFF",
            "wrap": True,
            "margin": "sm"
        })
        if three_day_zone:
            body_contents.append({
                "type": "text",
                "text": f"  ↳ {three_day_zone}",
                "size": "xs",
                "color": "#888888",
                "wrap": True
            })
    
    # MA交叉
    if ma_cross_str:
        body_contents.append({
            "type": "text",
            "text": f"MA: {ma_cross_str}",
            "size": "xs",
            "color": "#FFFFFF",
            "wrap": True,
            "margin": "sm"
        })
        if ma_cross_key_price:
            body_contents.append({
                "type": "text",
                "text": f"  ↳ {ma_cross_key_price}",
                "size": "xs",
                "color": "#888888",
                "wrap": True
            })
    
    # 籌碼面區
    if chips_data:
        body_contents.append({"type": "separator", "margin": "lg"})
        body_contents.append({
            "type": "text",
            "text": "[籌碼面]",
            "size": "sm",
            "color": "#FFB74D",
            "weight": "bold",
            "margin": "lg"
        })
        
        for chip in chips_data:
            chip_color = "#00C853" if "買" in chip.get('desc', '') else "#FF5252" if "賣" in chip.get('desc', '') else "#FFFFFF"
            body_contents.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": chip.get('name', ''), "size": "xs", "color": "#888888", "flex": 2},
                    {"type": "text", "text": chip.get('desc', ''), "size": "xs", "color": chip_color, "flex": 5, "align": "end"},
                ],
                "margin": "sm"
            })
    
    # 基本面區 (如果有)
    if fundamental_str:
        body_contents.append({"type": "separator", "margin": "lg"})
        body_contents.append({
            "type": "text",
            "text": "[基本面]",
            "size": "sm",
            "color": "#81C784",
            "weight": "bold",
            "margin": "lg"
        })
        body_contents.append({
            "type": "text",
            "text": fundamental_str,
            "size": "xs",
            "color": "#FFFFFF",
            "wrap": True,
            "margin": "sm"
        })
    
    # Body
    body = {
        "type": "box",
        "layout": "vertical",
        "contents": body_contents,
        "backgroundColor": "#16213e",
        "paddingAll": "15px"
    }
    
    # Bubble
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "header": header,
        "body": body
    }
    
    return bubble


def build_index_bubble(
    index_id: str,
    index_name: str,
    date_str: str,
    close_price: float,
    ma20: float,
    inertia_str: Optional[str] = None,
    three_day_str: Optional[str] = None,
    three_day_zone: Optional[str] = None,
    ma_cross_str: Optional[str] = None,
) -> dict:
    """
    建立指數卡片 Bubble (簡化版，無籌碼面和基本面)
    """
    
    # Header - 指數用不同顏色
    header = {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": f"📈 {index_name}",
                "weight": "bold",
                "size": "lg",
                "color": "#FFFFFF"
            },
            {
                "type": "text",
                "text": f"{index_id} | {date_str}",
                "size": "xs",
                "color": "#AAAAAA"
            }
        ],
        "backgroundColor": "#0d47a1",
        "paddingAll": "15px"
    }
    
    # Body
    body_contents = []
    
    # 基本訊息
    price_color = "#00C853" if close_price >= ma20 else "#FF5252"
    body_contents.append({
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {"type": "text", "text": "收盤", "size": "sm", "color": "#888888", "flex": 2},
            {"type": "text", "text": f"{close_price:.2f}", "size": "sm", "color": price_color, "flex": 3, "align": "end"},
            {"type": "text", "text": "月線", "size": "sm", "color": "#888888", "flex": 2},
            {"type": "text", "text": f"{ma20:.2f}", "size": "sm", "color": "#FFFFFF", "flex": 3, "align": "end"},
        ],
        "margin": "md"
    })
    
    body_contents.append({"type": "separator", "margin": "lg"})
    
    # 技術面
    body_contents.append({
        "type": "text",
        "text": "[技術面]",
        "size": "sm",
        "color": "#4FC3F7",
        "weight": "bold",
        "margin": "lg"
    })
    
    if inertia_str:
        body_contents.append({
            "type": "text",
            "text": inertia_str,
            "size": "xs",
            "color": "#FFFFFF",
            "wrap": True,
            "margin": "sm"
        })
    
    if three_day_str:
        body_contents.append({
            "type": "text",
            "text": f"日線: {three_day_str}",
            "size": "xs",
            "color": "#FFFFFF",
            "wrap": True,
            "margin": "sm"
        })
        if three_day_zone:
            body_contents.append({
                "type": "text",
                "text": f"  ↳ {three_day_zone}",
                "size": "xs",
                "color": "#888888",
                "wrap": True
            })
    
    if ma_cross_str:
        body_contents.append({
            "type": "text",
            "text": f"MA: {ma_cross_str}",
            "size": "xs",
            "color": "#FFFFFF",
            "wrap": True,
            "margin": "sm"
        })
    
    body = {
        "type": "box",
        "layout": "vertical",
        "contents": body_contents,
        "backgroundColor": "#1a237e",
        "paddingAll": "15px"
    }
    
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "header": header,
        "body": body
    }
    
    return bubble


def build_carousel(bubbles: list[dict]) -> dict:
    """
    建立 Carousel 容器
    
    Args:
        bubbles: Bubble 列表 (最多 12 個)
        
    Returns:
        dict: Flex Carousel JSON
    """
    if len(bubbles) > 12:
        logger.warning(f"Carousel 最多 12 個 Bubble，目前有 {len(bubbles)} 個，將截斷")
        bubbles = bubbles[:12]
    
    return {
        "type": "carousel",
        "contents": bubbles
    }


def split_bubbles_to_carousels(bubbles: list[dict], max_per_carousel: int = 12) -> list[dict]:
    """
    將 Bubbles 分割成多個 Carousel (每個最多 12 張)
    
    Args:
        bubbles: 所有 Bubble 列表
        max_per_carousel: 每個 Carousel 最大 Bubble 數
        
    Returns:
        list[dict]: Carousel 列表
    """
    carousels = []
    
    for i in range(0, len(bubbles), max_per_carousel):
        chunk = bubbles[i:i + max_per_carousel]
        carousels.append(build_carousel(chunk))
    
    return carousels
