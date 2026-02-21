import json
from core.analysis import analyze_stock_for_flex
from core.flex_message import build_stock_bubble

def main():
    stock_id = '2330'
    stock_name = '台積電'

    print(f"Analyze stock: {stock_id} {stock_name}")
    try:
        data = analyze_stock_for_flex(stock_id, stock_name)
        if data:
            print("--- Analysis Output ---")
            print(f"Fundamental string:")
            print(data.get('fundamental_str'))
            print("-----------------------")
            
            # test bubble building to ensure no format errors
            bubble = build_stock_bubble(
                stock_id=data['stock_id'],
                stock_name=data['stock_name'],
                date_str=data['date_str'],
                close_price=data['close_price'],
                price_change=data['price_change'],
                ma20=data['ma20'],
                inertia_str=data.get('inertia_str'),
                three_day_str=data.get('three_day_str'),
                three_day_zone=data.get('three_day_zone'),
                ma_cross_str=data.get('ma_cross_str'),
                ma_cross_key_price=data.get('ma_cross_key_price'),
                chips_data=data.get('chips_data'),
                fundamental_str=data.get('fundamental_str'),
            )
            print("Flex Bubble Built successfully!")
        else:
            print("No data returned")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
