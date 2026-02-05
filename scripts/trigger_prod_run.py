import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_analysis

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("🚀 Triggering Full Analysis (Production Run)...")
    print("This will:")
    print("1. Read watchlist from Google Sheets")
    print("2. Analyze stocks")
    print("3. SEND LINE MESSAGE to you")
    print("4. Update Google Sheets")
    print("-" * 30)
    
    try:
        # run_analysis returns (response_string, status_code)
        response, status = run_analysis()
        print(f"\n✅ Result: {response}")
        print(f"Status: {status}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
