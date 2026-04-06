from __future__ import annotations
import logging
import os
import tempfile
from typing import Optional

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from core.sheets import (
    get_watchlist_details, 
    update_last_revenue_month, 
    update_last_financial_quarter, 
    update_stock_name_cell,
    replace_watchlist
)
from core.data import get_stock_name, get_latest_revenue_month, get_latest_financial_quarter
from core.ai import extract_stocks_from_image
from core.analysis import analyze_stock_for_flex, analyze_index_for_flex
from core.notifier import send_flex_carousel, reply_flex_carousel
from core.flex_message import (
    build_stock_bubble, 
    build_index_bubble, 
    build_carousel, 
    split_bubbles_to_carousels
)
# from core.test_logic import run_batch_test 

app = Flask(__name__)

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LINE Bot Setup
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


def process_analysis(reply_token: Optional[str] = None) -> tuple[str, int]:
    """
    執行完整的股票分析流程
    
    Args:
        reply_token: 若有提供，則使用 reply_message (免費); 若無，則使用 push_message (付費)
        
    Returns:
        (message, status_code)
    """
    logger.info("開始執行完整分析任務...")
    
    try:
        # 1. 讀取 Google Sheet 觀察清單
        stock_list = get_watchlist_details()
        if not stock_list:
            msg = "觀察清單為空或讀取失敗，任務結束。"
            logger.warning(msg)
            return msg, 200
            
        logger.info(f"觀察清單: {[s['id'] for s in stock_list]}")
        
        # 準備 Flex Message Bubbles
        bubbles = []
        updates_rev = []
        updates_fin = []
        updates_name = []
        
        # 2. 分析大盤指數 (放在 Carousel 最前面)
        market_indices = [('TAIEX', '加權指數'), ('TPEx', '櫃買指數')]
        
        for idx_id, idx_name in market_indices:
            try:
                logger.info(f"正在分析指數 {idx_name} ({idx_id})...")
                idx_data = analyze_index_for_flex(idx_id, idx_name)
                
                if idx_data:
                    bubble = build_index_bubble(
                        index_id=idx_data['index_id'],
                        index_name=idx_data['index_name'],
                        date_str=idx_data['date_str'],
                        close_price=idx_data['close_price'],
                        price_change=idx_data['price_change'],
                        ma20=idx_data['ma20'],
                        inertia_str=idx_data.get('inertia_str'),
                        three_day_str=idx_data.get('three_day_str'),
                        three_day_zone=idx_data.get('three_day_zone'),
                        ma_cross_str=idx_data.get('ma_cross_str'),
                    )
                    bubbles.append(bubble)
            except Exception as e:
                logger.error(f"分析指數 {idx_id} 失敗: {e}")

        # 3. 分析個股
        for stock_info in stock_list:
            stock_id = stock_info['id']
            last_rev_month = stock_info.get('last_revenue_month')
            last_fin_quarter = stock_info.get('last_financial_quarter')
            stock_name = stock_info.get('name')
            row_idx = stock_info.get('row_idx')
            
            # Check/Update Name if missing
            if not stock_name:
                fetched_name = get_stock_name(stock_id)
                if fetched_name:
                    stock_name = fetched_name
                    updates_name.append({
                        'row_idx': row_idx,
                        'name': stock_name
                    })
                    logger.info(f"已補全 {stock_id} 名稱: {stock_name}")
            
            logger.info(f"正在分析 {stock_id} {stock_name}...")
            
            try:
                # 使用新的 Flex 分析函式
                stock_data = analyze_stock_for_flex(
                    stock_id, 
                    stock_name,
                    last_revenue_month=last_rev_month,
                    last_financial_quarter=last_fin_quarter
                )
                
                if stock_data:
                    bubble = build_stock_bubble(
                        stock_id=stock_data['stock_id'],
                        stock_name=stock_data['stock_name'],
                        date_str=stock_data['date_str'],
                        close_price=stock_data['close_price'],
                        price_change=stock_data['price_change'],
                        ma20=stock_data['ma20'],
                        inertia_str=stock_data.get('inertia_str'),
                        three_day_str=stock_data.get('three_day_str'),
                        three_day_zone=stock_data.get('three_day_zone'),
                        ma_cross_str=stock_data.get('ma_cross_str'),
                        ma_cross_key_price=stock_data.get('ma_cross_key_price'),
                        chips_data=stock_data.get('chips_data'),
                        fundamental_str=stock_data.get('fundamental_str'),
                    )
                    bubbles.append(bubble)
                    
                    # 收集更新資料
                    rev_update = stock_data.get('revenue_update')
                    fin_update = stock_data.get('financial_update')
                    
                    if rev_update:
                        updates_rev.append({
                            'row_idx': row_idx,
                            'date_str': rev_update['date_str']
                        })
                    
                    if fin_update:
                        updates_fin.append({
                            'row_idx': row_idx,
                            'quarter_str': fin_update['quarter_str']
                        })
                    
            except Exception as e:
                logger.error(f"分析 {stock_id} 時發生錯誤: {e}")
        
        # 4. 發送 Flex Message Carousel
        if not bubbles:
            return "No analysis results generated.", 200
        
        carousels = split_bubbles_to_carousels(bubbles)
        
        if reply_token:
            # 使用 Reply Token 回覆 (僅能回覆一次，如果有多個 Carousel 怎麼辦？)
            # LINE Reply Token 只能用一次。多個 Carousel 必須用一次 reply_message 傳送 (max 5 output messages)
            # send_flex_carousel logic for push uses loop push.
            # reply_flex_carousel logic uses reply_message.
            
            # 目前 reply_flex_carousel 只支援傳入單一 carousel。
            # 如果 bubbles > 12，會有 split carousels。
            
            # 策略：
            # 如果只有 1 個 carousel -> Use Reply
            # 如果有多個 -> Use Reply for 1st, Push for others (Mixing is tricky if token invalidates?)
            # 其實可以一次 reply_message 帶最多 5 個 Flex Message。
            # 但我們的 carousels 是一個 list of dict (Flex Container).
            # 我們需要修改 reply_flex_carousel 支援多個 carousels?
            
            # 簡單做法：只 Reply 第一個。剩下的用 Push?
            # 或者修改 reply_flex_carousel 讓它支援 list[carousel]。
            
             # 如果只有一個 Carousel
            if len(carousels) == 1:
                reply_flex_carousel(reply_token, carousels[0], alt_text="每日台股分析報告")
            else:
                # 多個 Carousel
                # Reply 第一個
                reply_flex_carousel(reply_token, carousels[0], alt_text=f"每日台股分析報告 (1/{len(carousels)})")
                # Push 剩下的
                if len(carousels) > 1:
                    send_flex_carousel(carousels[1:], alt_text="每日台股分析報告 (續)")
        else:
            # Push (排程觸發)
            send_flex_carousel(carousels, alt_text="每日台股分析報告")
        
        # 5. 更新 Google Sheets
        for up in updates_name:
            try:
                update_stock_name_cell(up['row_idx'], up['name'])
            except Exception as e:
                logger.error(f"Failed to update name for row {up['row_idx']}: {e}")
        
        for up in updates_rev:
            try:
                update_last_revenue_month(up['row_idx'], up['date_str'])
            except Exception as e:
                logger.error(f"Failed to update revenue for row {up['row_idx']}: {e}")
                
        for up in updates_fin:
            try:
                update_last_financial_quarter(up['row_idx'], up['quarter_str'])
            except Exception as e:
                logger.error(f"Failed to update financial for row {up['row_idx']}: {e}")
        
        logger.info(f"分析任務完成，已發送 {len(carousels)} 個 Carousel ({len(bubbles)} 張卡片)。")
        return f"Analysis completed: {len(bubbles)} cards in {len(carousels)} carousel(s)", 200

    except Exception as e:
        logger.error(f"執行分析任務時發生未預期錯誤: {e}")
        return f"Error: {e}", 500


@app.route("/", methods=["GET"])
def health_check():
    return "Stock Bot is running", 200

@app.route("/callback", methods=['POST'])
def callback():
    """
    LINE Webhook Callback
    """
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    Handle incoming text messages
    """
    text = event.message.text.strip()
    
    if text == "測試":
        # 觸發測試邏輯
        logger.info("收到 '測試' 指令，開始執行批次測試...")
        
        # 注意: run_batch_test 是舊邏輯，可能需要更新或直接呼叫 process_analysis
        # 為了保持功能簡單，這裡改為呼叫完整分析但只針對前 2 檔？
        # 或者直接執行完整流程
        process_analysis(event.reply_token)
    else:
        pass


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """
    Handle incoming image messages - extract stocks -> update watchlist -> full analysis
    """
    logger.info("收到圖片訊息，開始處理...")
    
    try:
        # 1. Download image from LINE
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            for chunk in message_content.iter_content():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        logger.info(f"圖片已下載至暫存: {tmp_path}")
        
        # 2. Extract stocks from image using Gemini Vision
        stocks = extract_stocks_from_image(tmp_path)
        
        # Clean up temp file
        try:
            os.remove(tmp_path)
        except OSError as e:
            logger.warning(f"Error removing temp file: {e}")
        
        if not stocks:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="無法從截圖中辨識出任何股票，請確認截圖內容是否清晰。")
            )
            return
        
        logger.info(f"辨識到 {len(stocks)} 檔股票: {[s['name'] for s in stocks]}")
        
        # 3. Update Watchlist (Preparation for Analysis)
        # We need to construct the list for replace_watchlist
        # process_analysis reads from sheet, so we must write to sheet first.
        
        stock_list_with_data = []
        for stock in stocks:
            stock_id = stock['id']
            stock_name = stock['name']
            
            # Try to get latest data periods to prepopulate?
            # Or just leave empty and let process_analysis fill them later (via separate fetch)?
            # process_analysis reads 'last_revenue_month' from sheet.
            # If we overwrite with empty string, process_analysis will see empty and re-analyze. -> Correct.
            
            # Optimization: Pre-fetch? No, process_analysis does it cleanly.
            # Just create basic entry.
            
            latest_rev = get_latest_revenue_month(stock_id)
            latest_fin = get_latest_financial_quarter(stock_id)
            
            stock_data_for_sheets = {
                'id': stock_id,
                'name': stock_name,
                'last_revenue_month': latest_rev or '',
                'last_financial_quarter': latest_fin or ''
            }
            stock_list_with_data.append(stock_data_for_sheets)
        
        success = replace_watchlist(stock_list_with_data)
        
        if not success:
            logger.error("更新 Google Sheets 失敗")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="更新觀察清單失敗，請稍後再試。")
            )
            return
            
        # 4. Trigger Full Analysis
        # Pass reply_token so it replies to this image message
        process_analysis(event.reply_token)
        
        logger.info("圖片處理流程完成")
        
    except Exception as e:
        logger.error(f"處理圖片訊息時發生錯誤: {e}")
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"處理截圖時發生錯誤: {e}")
            )
        except Exception:
            pass

@app.route("/run_analysis", methods=["POST", "GET"])
def run_analysis():
    # Cron Job entry point
    return process_analysis(reply_token=None)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
