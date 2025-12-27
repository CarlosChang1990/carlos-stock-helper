import random
import logging
import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.test_logic import run_batch_test
from core.notifier import send_line_notification

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Batch LINE Notification Test (via core/test_logic)...")
    
    # 調用新的核心邏輯
    message = run_batch_test(num_stocks=2, target_date_str="2025-12-01")
    
    logger.info("Sending Consolidated LINE message...")
    logger.info(f"Content:\n{message}")
    
    # 測試發送
    send_line_notification(message)
    logger.info("Message sent.")

if __name__ == "__main__":
    main()
