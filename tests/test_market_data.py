import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from market_data import parse_tickers, fetch_stock_data, fetch_company_names

def test_parse_tickers_normal():
    assert parse_tickers("NVDA, AMD, ASML") == ["NVDA", "AMD", "ASML"]

def test_parse_tickers_duplicates():
    assert parse_tickers("NVDA, AMD, NVDA") == ["NVDA", "AMD"]

def test_parse_tickers_empty_entries():
    assert parse_tickers("  NVDA ,, AMD  ") == ["NVDA", "AMD"]

def test_parse_tickers_invalid_raises_error():
    with pytest.raises(ValueError):
        parse_tickers("")

@patch("market_data.yf.download")
def test_fetch_stock_data(mock_download):
    dates = pd.date_range("2026-01-01", periods=3)
    mock_data = pd.DataFrame({
        ("Close", "NVDA"): [100.0, 105.0, 110.0],
        ("Close", "AMD"): [50.0, 52.0, 54.0]
    }, index=dates)
    mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
    mock_download.return_value = mock_data
    
    prices = fetch_stock_data(["NVDA", "AMD"], period="1y")
    assert list(prices.columns) == ["NVDA", "AMD"]
    assert len(prices) == 3

@patch("market_data.yf.download")
def test_fetch_stock_data_missing_ticker(mock_download):
    dates = pd.date_range("2026-01-01", periods=3)
    mock_data = pd.DataFrame({
        ("Close", "NVDA"): [100.0, 105.0, 110.0]
    }, index=dates)
    mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
    mock_download.return_value = mock_data
    
    with pytest.raises(ValueError):
        fetch_stock_data(["NVDA", "INVALID"], period="1y")

@patch("market_data.yf.download")
def test_fetch_stock_data_all_nans(mock_download):
    dates = pd.date_range("2026-01-01", periods=3)
    mock_data = pd.DataFrame({
        ("Close", "NVDA"): [None, None, None]
    }, index=dates)
    mock_data.columns = pd.MultiIndex.from_tuples(mock_data.columns)
    mock_download.return_value = mock_data
    
    with pytest.raises(ValueError):
        fetch_stock_data(["NVDA"], period="1y")

@patch("market_data.yf.Ticker")
def test_fetch_company_names_success(mock_ticker_class):
    mock_instance = MagicMock()
    mock_instance.info = {"longName": "NVIDIA Corporation"}
    mock_ticker_class.return_value = mock_instance
    
    result = fetch_company_names(["NVDA"])
    assert result == {"NVDA": "NVIDIA Corporation"}

@patch("market_data.yf.Ticker")
def test_fetch_company_names_missing(mock_ticker_class):
    mock_instance = MagicMock()
    mock_instance.info = {}
    mock_ticker_class.return_value = mock_instance
    
    result = fetch_company_names(["NVDA"])
    assert result == {"NVDA": "NVDA"}