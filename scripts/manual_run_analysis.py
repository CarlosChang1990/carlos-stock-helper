import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, run_analysis

if __name__ == "__main__":
    print("Starting Manual Analysis Run...")
    
    # Use app context to ensure Flask features work if needed (though run_analysis is mostly pure python logic)
    with app.app_context():
        # Call the function directly. It returns (response_string, status_code)
        result = run_analysis()
        
        print(f"Result: {result}")
