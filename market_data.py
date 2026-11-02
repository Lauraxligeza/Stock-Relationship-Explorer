import yfinance as yf
import pandas as pd

def parse_tickers(tickers_input: str) -> list:
    if not tickers_input or not tickers_input.strip():
        raise ValueError("Please enter at least one stock ticker.")
        
    tickers = [t.strip().upper() for t in tickers_input.replace(",", " ").split() if t.strip()]
    unique_tickers = list(dict.fromkeys(tickers))
    
    if len(unique_tickers) < 2:
        raise ValueError("Please enter at least two different stock tickers.")
        
    return unique_tickers

def fetch_stock_data(tickers: list, period: str = "1y") -> pd.DataFrame:
    if not tickers:
        raise ValueError("No tickers provided.")
        
    data = yf.download(tickers, period=period, progress=False)
    
    if data.empty:
        raise ValueError("No data found for the specified tickers.")
        
    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.levels[0]:
            prices = data["Close"]
        else:
            prices = data.iloc[:, 0:len(tickers)]
    else:
        if "Close" in data.columns:
            prices = data[["Close"]]
            prices.columns = tickers
        else:
            prices = data
            
    prices = prices.dropna(how="all")
    if prices.empty:
        raise ValueError("No valid price data returned for the selected tickers.")
        
    # Ensure all requested tickers are present in prices columns
    missing_tickers = [t for t in tickers if t not in prices.columns]
    if missing_tickers:
        raise ValueError(f"No data found for ticker(s): {', '.join(missing_tickers)}")
        
    return prices

def fetch_company_names(tickers: list) -> dict:
    names = {}
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            name = info.get("longName") or info.get("shortName") or ticker
            names[ticker] = name
        except Exception:
            names[ticker] = ticker
    return names