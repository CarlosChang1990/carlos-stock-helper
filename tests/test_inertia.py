import sys
import os
import pandas as pd
import logging
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.strategy import analyze_all_inertia, analyze_inertia_with_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_inertia_state():
    """Test state latching and counting for Inertia"""
    logger.info("Testing Inertia State Logic...")
    
    data = {
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
        'open': [100, 102, 105, 108, 110], 
        'max':  [105, 108, 112, 115, 120],
        'min':  [95,  98,  102, 105, 108],
        'close':[102, 105, 108, 112, 115] # Close > Open
    }
    df = pd.DataFrame(data)
    
    # Should maintain consecutive Up trend
    res = analyze_inertia_with_state(df, "日線")
    print(f"Inertia State Result: {res}")
    
    assert res['state'] == "慣性向上"
    assert res['count'] >= 4 # Matches consecutive days
    assert "2023/01/02" in res['trigger_dates']
    assert "日線慣性向上 (連續" in res['description']

def test_schedule_logic():
    """Test Weekly/Monthly scheduling logic in analyze_all_inertia"""
    logger.info("Testing Scheduling Logic...")
    
    # Mock Data: 
    # Data ends on Sunday Jan 31. Need enough history for >2 months.
    dates = pd.date_range(end='2025-01-31', periods=60, freq='D')
    data = [{'date': d, 'open': 100, 'max': 100, 'min': 100, 'close': 100} for d in dates]
    df = pd.DataFrame(data)
    
    # 1. Test Monday Trigger (2025-02-03 is Monday)
    target_monday = datetime(2025, 2, 3) 
    res_mon = analyze_all_inertia(df, current_date=target_monday)
    logger.info(f"Monday Run: Weekly should be present. Result: {res_mon['weekly']}")
    assert res_mon['weekly'] is not None
    
    # 2. Test Tuesday Trigger (Skip Weekly)
    target_tue = datetime(2025, 2, 4)
    res_tue = analyze_all_inertia(df, current_date=target_tue)
    logger.info(f"Tuesday Run: Weekly should be None. Result: {res_tue['weekly']}")
    assert res_tue['weekly'] is None

    # 3. Test Monthly Trigger
    # Data ends Jan 31. Current date Feb 3 (Month 2 != Month 1). Shoould Run.
    logger.info(f"Feb Run (Data Jan): Monthly should be present. Result: {res_mon['monthly']}")
    assert res_mon['monthly'] is not None
    
    # Mock Data ends Feb 1. Current Feb 3. (2 == 2). Should Skip.
    dates2 = pd.date_range(end='2025-02-01', periods=10, freq='D')
    df2 = pd.DataFrame([{'date': d, 'open': 100, 'max': 100, 'min': 100, 'close': 100} for d in dates2])
    res_skip_m = analyze_all_inertia(df2, current_date=target_monday)
    logger.info(f"Feb Run (Data Feb): Monthly should be None. Result: {res_skip_m['monthly']}")
    assert res_skip_m['monthly'] is None

if __name__ == "__main__":
    test_inertia_state()
    test_schedule_logic()
    print("All tests passed!")
