from linebot import LineBotApi
from linebot.models import TextSendMessage
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
