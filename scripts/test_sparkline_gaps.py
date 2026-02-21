from core.data import fetch_monthly_revenue
from core.strategy import generate_sparkline
import pandas as pd

for stock_id in ['6770', '3152']:
    print(f"\n--- Stock {stock_id} ---")
    df = fetch_monthly_revenue(stock_id)
    print("Las 15 rows of raw data:")
    print(df.tail(15)[['date', 'revenue_year', 'revenue_month', 'revenue']])
    
    # Simulate sparkline generation logic from strategy.py
    last_row = df.iloc[-1]
    
    end_period = pd.Period(year=last_row['revenue_year'], month=last_row['revenue_month'], freq='M')
    start_period = end_period - 11
    
    df_rev_copy = df.copy()
    df_rev_copy['period'] = df_rev_copy.apply(lambda r: pd.Period(year=int(r['revenue_year']), month=int(r['revenue_month']), freq='M'), axis=1)
    
    # Check for duplicates before setting index! This might be the issue!
    duplicates = df_rev_copy[df_rev_copy.duplicated(subset=['period'], keep=False)]
    if not duplicates.empty:
        print("FOUND DUPLICATES IN PERIODS!")
        print(duplicates[['date', 'revenue_year', 'revenue_month', 'revenue']])

    # Try setting index (will fail if duplicates exist)
    try:
        df_rev_copy = df_rev_copy.drop_duplicates(subset=['period'], keep='last')
        df_rev_copy = df_rev_copy.set_index('period')
        
        all_periods = pd.period_range(start=start_period, end=end_period, freq='M')
        df_12m = df_rev_copy.reindex(all_periods)
        revenue_values = df_12m['revenue'].tolist()
        
        print("\nReindexed values (last 12):")
        for p, v in zip(all_periods, revenue_values):
            print(f"{p}: {v}")
            
        sparkline = generate_sparkline(revenue_values)
        print(f"Generated Sparkline: '{sparkline}'")
    except Exception as e:
        print(f"Error during reindex: {e}")
