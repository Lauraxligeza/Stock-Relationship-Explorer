import pandas as pd

def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change(fill_method=None).dropna(how="all")

def calculate_correlations(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.corr()

def calculate_rolling_correlation(returns: pd.DataFrame, stock_a: str, stock_b: str, window: int = 30) -> pd.Series:
    if stock_a not in returns.columns or stock_b not in returns.columns:
        return pd.Series(dtype=float)
    return returns[stock_a].rolling(window=window).corr(returns[stock_b])

def normalize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    return prices / prices.iloc[0] * 100

def calculate_pair_observations(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.notna().astype(int).T.dot(returns.notna().astype(int))

def calculate_relationship_stability(returns: pd.DataFrame, stock_a: str, stock_b: str, window: int = 30):
    rolling_series = calculate_rolling_correlation(returns, stock_a, stock_b, window=window).dropna()
    
    if len(rolling_series) < 2:
        return None
        
    mean_corr = float(rolling_series.mean())
    std_corr = float(rolling_series.std())
    observations = int(len(rolling_series))
    
    return {
        "mean_correlation": mean_corr,
        "std_correlation": std_corr,
        "observations": observations
    }