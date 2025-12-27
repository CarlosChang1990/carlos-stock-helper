import sys
import os
import pandas as pd
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.strategy import analyze_3day_high_low

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_3day_rule():
    # Scenario: 
    # Days 0-2: Range 90-110
    # Day 3: Breakout Up > 110 (State -> Bull)
    # Day 4: Drop but inside range (State -> Bull)
    # Day 5: Breakdown < 90 (State -> Bear)
    
    data = [
        # 0,1,2: Setup
        {'date': '2025-01-01', 'max': 100, 'min': 90, 'close': 95},
        {'date': '2025-01-02', 'max': 105, 'min': 95, 'close': 100},
        {'date': '2025-01-03', 'max': 110, 'min': 100, 'close': 105},
        
        # 3: Breakout! (Prev3 Max=110)
        {'date': '2025-01-04', 'max': 115, 'min': 105, 'close': 112}, # 112 > 110 -> Bull
        
        # 4: Pullback (Prev3 Max=115, Min=100) -> Range 100-115
        {'date': '2025-01-05', 'max': 110, 'min': 108, 'close': 109}, # 100 < 109 < 115 -> Keep Bull
        
        # 5: Breakdown (Prev3 Max=115, Min=100)
        # Prev3 (2,3,4): Min(95?? No day 2.. wait)
        # Day 5 looks at 2,3,4.
        # Day 2 Min: 100
        # Day 3 Min: 105
        # Day 4 Min: 108
        # Barrier Low = 100.
        {'date': '2025-01-06', 'max': 98, 'min': 80, 'close': 85}, # 85 < 100 -> Bear
    ]
    df = pd.DataFrame(data)
    
    # Test incremental to verify state history works? 
    # analyze_3day_high_low iterates internally.
    
    # 1. Run on first 4 days (Index 0-3) -> Expect Bull
    res_bull = analyze_3day_high_low(df.iloc[:4])
    logger.info(f"Day 3 Result (Exp: 站上): {res_bull['state']}")
    logger.info(f"Description: {res_bull['description']}")
    assert res_bull['state'] == "站上三日高點"
    assert res_bull['zone_type'] == "support"
    assert res_bull['zone_range'][1] == 110 
    assert "2025/01/03" in res_bull['description'] # Expect YYYY/MM/DD
    
    # 2. Run on first 5 days (Index 0-4) -> Expect Bull (Hold)
    res_hold = analyze_3day_high_low(df.iloc[:5])
    logger.info(f"Day 4 Result (Exp: 站上-Hold): {res_hold['state']}")
    assert res_hold['state'] == "站上三日高點"
    
    # 3. Run on all 6 days (Index 0-5) -> Expect Bear
    # Breakdown at Day 5 (< Min 100).
    # Prev 3 days (Indices 2,3,4):
    # Day 2: Range 100-110, Min 100
    res_bear = analyze_3day_high_low(df)
    logger.info(f"Day 5 Result (Exp: 跌破): {res_bear['state']}")
    assert res_bear['state'] == "跌破三日低點"
    assert res_bear['zone_type'] == "resistance"
    assert res_bear['zone_range'][0] == 100
    assert "2025/01/03" in res_bear['description'] # Expect YYYY/MM/DD
    
    # 4. Strict Inequality Check (Equal Case)
    # Day 6: Close = 100 (Day 2 Min). Barrier Low is 100.
    # Close(100) < Barrier(100) is False. Should NOT trigger Bear.
    # Should maintain previous state (Bear from Day 5)?? 
    # Wait, Day 5 state was Bear. If Day 6 is equal, it holds Bear.
    # Let's test a breakout equal case from neutral or bull.
    
    data_eq = [
        {'date': '2025-01-01', 'max': 100, 'min': 90, 'close': 95},
        {'date': '2025-01-02', 'max': 100, 'min': 90, 'close': 95},
        {'date': '2025-01-03', 'max': 100, 'min': 90, 'close': 95},
        # Barrier High = 100.
        # Day 3 Close = 100. (Equal) -> Should NOT stay "站上", should be "盤整" (Initial)
        {'date': '2025-01-04', 'max': 100, 'min': 90, 'close': 100} 
    ]
    df_eq = pd.DataFrame(data_eq)
    res_eq = analyze_3day_high_low(df_eq)
    logger.info(f"Equal High Result (Exp: 盤整/無訊號): {res_eq['state']}")
    assert res_eq['state'] == "盤整/無訊號"
    
    # 5. Consecutive Count Test
    # Day 0,1,2: Setup
    # Day 3: Breakout Use (Count 1)
    # Day 4: Hold (Count 1)
    # Day 5: Breakout Again (Count 2)
    
    data_count = [
        {'date': '2025-01-01', 'max': 100, 'min': 90, 'close': 95},
        {'date': '2025-01-02', 'max': 100, 'min': 90, 'close': 95},
        {'date': '2025-01-03', 'max': 100, 'min': 90, 'close': 95},
        
        # D3: Breakout > 100
        {'date': '2025-01-04', 'max': 105, 'min': 95, 'close': 101}, # State: Bull, Count: 1
        
        # D4: Pullback 100-105 range (Prev 3: D1(100), D2(100), D3(105). Max=105)
        # Close 102 (Between 90 and 105). HOLD state.
        {'date': '2025-01-05', 'max': 105, 'min': 102, 'close': 102}, # Hold (State=Bull, Count=1)
        
        # D5: Breakout again! > Max(Prev 3: D2(100), D3(105), D4(105). Max=105)
        {'date': '2025-01-06', 'max': 110, 'min': 106, 'close': 106}, # 106 > 105 -> Trigger Bull again. Count=2
    ]
    df_count = pd.DataFrame(data_count)
    
    # Check D3
    res_d3 = analyze_3day_high_low(df_count.iloc[:4]) # D0..D3
    logger.info(f"D3 Result: {res_d3['state']} Count: {res_d3['count']} Dates: {res_d3['trigger_dates']}")
    assert res_d3['state'] == "站上三日高點"
    assert res_d3['count'] == 1
    assert "2025/01/04" in res_d3['trigger_dates']
    
    # Check D4 (Hold)
    res_d4 = analyze_3day_high_low(df_count.iloc[:5]) # D0..D4
    logger.info(f"D4 Result: {res_d4['state']} Count: {res_d4['count']} Dates: {res_d4['trigger_dates']}")
    assert res_d4['state'] == "站上三日高點"
    assert res_d4['count'] == 1
    # Dates should still contain only D3 date
    assert len(res_d4['trigger_dates']) == 1
    assert "2025/01/04" in res_d4['trigger_dates']
    
    # Check D5 (Consecutive)
    res_d5 = analyze_3day_high_low(df_count)
    logger.info(f"D5 Result: {res_d5['state']} Count: {res_d5['count']} Dates: {res_d5['trigger_dates']}")
    assert res_d5['state'] == "站上三日高點"
    assert res_d5['count'] == 2
    # Dates should contain D3 and D5
    assert "2025/01/04" in res_d5['trigger_dates']
    assert "2025/01/06" in res_d5['trigger_dates']

    print("All 3-day rule tests passed!")

if __name__ == "__main__":
    test_3day_rule()
