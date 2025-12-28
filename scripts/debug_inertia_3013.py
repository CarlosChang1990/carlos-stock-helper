import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from core.data import fetch_stock_data
from core.strategy import analyze_inertia_with_state

def debug_3013():
    print("Fetching 3013 data...")
    # Fetch default data
    df = fetch_stock_data("3013")
    
    if df.empty:
        print("No data found.")
        return

    # Filter around 12/22
    target_start = "2025-12-15"
    target_end = "2025-12-28"
    
    mask = (df['date'] >= target_start) & (df['date'] <= target_end)
    subset = df[mask].copy()
    
    print(f"\nData from {target_start} to {target_end}:")
    print(subset[['date', 'open', 'max', 'min', 'close']].to_string())
    
    print("\nRunning Inertia Analysis...")
    res = analyze_inertia_with_state(df, "日線")
    print(f"\nResult: {res}")
    
    # Manual Check for 12/22 (or nearby trading day)
    # 12/22/2025 is a Monday.
    
    print("\n--- Step-by-Step Logic Check ---")
    # Iterate through subset to find the specific day match
    # Re-implement loop logic to show 'why' it failed/passed
    
    subset = df.tail(20).reset_index(drop=True)
    for i in range(1, len(subset)):
        t1 = subset.loc[i]   # Today
        t2 = subset.loc[i-1] # Yesterday
        date_str = pd.to_datetime(t1['date']).strftime('%Y/%m/%d')
        
        if "12/22" in date_str or "12/23" in date_str or "12/19" in date_str: # Check nearby
            print(f"\nDate: {date_str}")
            print(f"  T-1 (Prev): High={t2['max']}, Low={t2['min']}, Close={t2['close']}")
            print(f"  T   (Curr): Open={t1['open']}, High={t1['max']}, Low={t1['min']}, Close={t1['close']}")
            
            c1 = t1['max'] > t2['max']
            c2 = t1['min'] > t2['min']
            c3 = t1['close'] > t2['close']
            
            print(f"  Cond 1 (High > PrevHigh): {c1}")
            print(f"  Cond 2 (Low > PrevLow)  : {c2}")
            print(f"  Cond 3 (Close > PrevClose): {c3}")
            
            if c1 and c2 and c3:
                print("  => SIGNAL: 慣性向上")
            else:
                print("  => NO SIGNAL")

if __name__ == "__main__":
    debug_3013()
