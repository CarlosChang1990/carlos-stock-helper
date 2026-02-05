from core.analysis import _format_state_with_dates

def test_cases():
    cases = [
        # Case 1: Single trigger
        (
            {"state": "站上三日高點", "count": 1, "trigger_dates": ["2026/02/05"]},
            "站上三日高點 [2026/02/05]"
        ),
        # Case 2: Multiple triggers
        (
            {"state": "跌破三日低點", "count": 3, "trigger_dates": ["2026/02/03", "2026/02/04", "2026/02/05"]},
            "跌破三日低點 (連3) [2026/02/03~2026/02/05]"
        ),
        # Case 3: Weekly Inertia
        (
            {"state": "慣性向上", "count": 2, "trigger_dates": ["2026/01/20", "2026/02/03"]},
            "慣性向上 (連2) [2026/01/20~2026/02/03]"
        ),
        # Case 4: No change
        (
            {"state": "盤整", "count": 0, "trigger_dates": []},
            None
        ),
        # Case 5: Single date multiple counts (if triggers missed recording but count inc? unlikely but test robust)
        (
             {"state": "Test", "count": 2, "trigger_dates": ["2026/02/05"]},
             "Test (連2) [2026/02/05]"
        )
    ]
    
    print("Testing Date Formatting...")
    for inp, expected in cases:
        res = _format_state_with_dates(inp)
        if res == expected:
            print(f"✅ PASS: {inp['state']} -> {res}")
        else:
            print(f"❌ FAIL: {inp['state']} -> Got '{res}', Expected '{expected}'")

if __name__ == "__main__":
    test_cases()
