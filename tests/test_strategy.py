import pytest
from core.strategy import generate_sparkline

def test_generate_sparkline_normal():
    values = [10, 20, 30, 40, 50, 60, 70, 80]
    result = generate_sparkline(values)
    # Length should match input
    assert len(result) == 8
    # Min value should be mapped to the lowest block '▂', max to '█'
    assert result[0] == '▂'
    assert result[-1] == '█'

def test_generate_sparkline_with_none():
    values = [10, None, 30, 40]
    result = generate_sparkline(values)
    assert len(result) == 4
    # The None value should be a space ' '
    assert result[1] == ' '
    assert result[0] == '▂'
    assert result[-1] == '█'

def test_generate_sparkline_all_same():
    values = [50, 50, 50]
    result = generate_sparkline(values)
    # Should fallback to the lowest block 
    assert result == '▂▂▂'

def test_generate_sparkline_empty():
    assert generate_sparkline([]) == ""
    assert generate_sparkline(None) == ""

def test_generate_sparkline_all_none():
    values = [None, None, None]
    result = generate_sparkline(values)
    assert result == "   "
