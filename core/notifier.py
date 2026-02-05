from __future__ import annotations
from linebot import LineBotApi
from linebot.models import TextSendMessage, FlexSendMessage
from linebot.exceptions import LineBotApiError
from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID
import logging

# 設定日誌
logger = logging.getLogger(__name__)

def send_line_notification(message):
    """
    發送 LINE 訊息
    
    Args:
        message (str): 要發送的訊息內容
    """
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        logger.warning("未設定 LINE Token 或 User ID，略過發送通送。")
        logger.info(f"模擬發送內容:\n{message}")
        return

    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        
        # LINE 文字訊息上限為 5000 字，如果超過需要分段
        # 這裡做簡單的處理，如果真的很長，LINE API 會報錯
        # 簡單切分邏輯 (保守一點切 4000)
        chunk_size = 4000
        
        for i in range(0, len(message), chunk_size):
            chunk = message[i:i + chunk_size]
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=chunk)
            )
            logger.info(f"已發送 LINE 訊息片段 {i//chunk_size + 1}")
            
    except LineBotApiError as e:
        logger.error(f"LINE API 錯誤: {e}")
    except Exception as e:
        logger.error(f"發送 LINE 訊息失敗: {e}")


def send_flex_carousel(carousels: list[dict], alt_text: str = "股票分析報告"):
    """
    發送 Flex Message Carousel
    
    Args:
        carousels (list[dict]): Carousel JSON 列表 (每個最多 12 張卡片)
        alt_text (str): 替代文字 (在通知預覽顯示)
    """
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        logger.warning("未設定 LINE Token 或 User ID，略過發送通送。")
        logger.info(f"模擬發送 Flex Message: {len(carousels)} 個 Carousel")
        return

    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        
        for i, carousel in enumerate(carousels):
            flex_message = FlexSendMessage(
                alt_text=alt_text,
                contents=carousel
            )
            
            line_bot_api.push_message(
                LINE_USER_ID,
                flex_message
            )
            logger.info(f"已發送 Flex Carousel {i + 1}/{len(carousels)}")
            
    except LineBotApiError as e:
        logger.error(f"LINE API 錯誤 (Flex): {e}")
    except Exception as e:
        logger.error(f"發送 Flex Message 失敗: {e}")


def reply_flex_carousel(reply_token: str, carousel: dict, alt_text: str = "股票分析報告"):
    """
    回覆 Flex Message Carousel (用於 webhook 回應)
    
    Args:
        reply_token (str): LINE reply token
        carousel (dict): 單個 Carousel JSON
        alt_text (str): 替代文字
    """
    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        
        flex_message = FlexSendMessage(
            alt_text=alt_text,
            contents=carousel
        )
        
        line_bot_api.reply_message(reply_token, flex_message)
        logger.info("已回覆 Flex Carousel")
        
    except LineBotApiError as e:
        logger.error(f"LINE API 回覆錯誤 (Flex): {e}")
    except Exception as e:
        logger.error(f"回覆 Flex Message 失敗: {e}")

