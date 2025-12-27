import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
FINMIND_API_TOKEN = os.getenv("FINMIND_API_TOKEN")

def inspect_chips():
    stock_id = "2330" # TSMC
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockHoldingSharesPer",
        "data_id": stock_id,
        "start_date": start_date,
        "token": FINMIND_API_TOKEN
    }
    
    print(f"Requesting {url} with params (token hidden)...")
    try:
        resp = requests.get(url, params=params)
        print(f"Status Code: {resp.status_code}")
        
        data = resp.json()
        if "data" in data:
            df = pd.DataFrame(data["data"])
            if not df.empty:
                print("Columns:", df.columns)
                print("\nSample Data (First 5 rows):")
                print(df.head())
                
                if 'HoldingRange' in df.columns:
                    print("Unique Ranges:", df['HoldingRange'].unique())
            else:
                print("Response 'data' is empty list.")
        else:
            print("Response JSON keys:", data.keys())
            if "msg" in data:
                print("Message:", data["msg"])
            print("Full Response:", data)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    inspect_chips()
