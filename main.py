from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from core.sheets import (
    get_watchlist_details, 
    update_last_revenue_month, 
    update_last_financial_quarter, 
    update_stock_name_cell
)
from core.data import get_stock_name
from core.analysis import analyze_stock
from core.notifier import send_line_notification
from core.test_logic import run_batch_test 
import logging

app = Flask(__name__)

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LINE Bot Setup
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
        
        reply_text = run_batch_test()
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    else:
        pass

@app.route("/run_analysis", methods=["POST", "GET"])
def run_analysis():
    logger.info("收到執行分析請求...")
    
    try:
        # 1. 讀取 Google Sheet 觀察清單
        stock_list = get_watchlist_details()
        if not stock_list:
            msg = "觀察清單為空或讀取失敗，任務結束。"
            logger.warning(msg)
            return msg, 200
            
        logger.info(f"觀察清單: {[s['id'] for s in stock_list]}")
        
        # 2. 逐一分析
        results = []
        updates_rev = []
        updates_fin = []
        updates_name = []
        
        # 1.5. Analyze Market Indices (TAIEX, TPEx)
        from core.analysis import analyze_index
        market_indices = [('TAIEX', '加權指數'), ('TPEx', '櫃買指數')]
        
        for idx_id, idx_name in market_indices:
            try:
                logger.info(f"正在分析指數 {idx_name} ({idx_id})...")
                idx_report = analyze_index(idx_id, idx_name)
                results.append(idx_report)
            except Exception as e:
                logger.error(f"分析指數 {idx_id} 失敗: {e}")

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
            
            logger.info(f"正在分析 {stock_id} {stock_name} (Last Rev: {last_rev_month}, Last Fin: {last_fin_quarter})...")
            try:
                # analyze_stock return dict
                analysis_result = analyze_stock(stock_id, last_rev_month, last_fin_quarter, stock_name=stock_name)
                
                if isinstance(analysis_result, dict):
                    report = analysis_result.get('report', '')
                    rev_update = analysis_result.get('revenue_update')
                    fin_update = analysis_result.get('financial_update')
                    
                    results.append(report)
                    
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
                else:
                    results.append(str(analysis_result))
                    
            except Exception as e:
                logger.error(f"分析 {stock_id} 時發生錯誤: {e}")
                results.append(f"【{stock_id}】分析失敗: {e}\n")
        
        # 3. 彙整報告
        if not results:
             return "No analysis results generated.", 200
             
        final_report = "【每日台股分析機器人】\n" + "\n".join(results)
        
        # 4. 發送通知
        send_line_notification(final_report)
        
        # 5. 更新 Google Sheets
        # 5.1 Update Names first
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
        
        logger.info("分析任務完成並已發送通知。")
        return "Analysis completed successfully", 200

    except Exception as e:
        logger.error(f"執行分析任務時發生未預期錯誤: {e}")
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
