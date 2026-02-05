import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analysis import analyze_stock_for_flex

# Setup Logging to see errors if any
logging.basicConfig(level=logging.INFO)

def simulate(stock_id):
    print(f"\n{'='*30}")
    print(f"Simulating Analysis for {stock_id}...")
    print(f"{'='*30}")
    
    try:
        result = analyze_stock_for_flex(stock_id)
        
        if not result:
            print("No result returned.")
            return

        print(f"Stock: {result['stock_name']} ({result['stock_id']})")
        print(f"Date: {result['date_str']}")
        print(f"Close: {result['close_price']}")
        
        print("\n--- Technical Analysis Output ---")
        
        # Check Inertia
        inertia = result.get('inertia_str')
        print(f"Inertia String:\n{inertia}")
        
        # Check 3-Day
        three_day = result.get('three_day_str')
        print(f"3-Day String:\n{three_day}")
        
        if result.get('three_day_zone'):
             print(f"3-Day Zone:\n{result['three_day_zone']}")
             
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simulate('2330') # TSMC
    simulate('2317') # Foxconn
