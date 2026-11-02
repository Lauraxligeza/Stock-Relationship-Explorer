import pandas as pd
from stock_statistics import calculate_relationship_stability

def classify_relationship_change(baseline_corr: float, recent_corr: float) -> str:
    if (baseline_corr * recent_corr < 0) and (abs(baseline_corr) >= 0.3) and (abs(recent_corr) >= 0.3):
        return "Correlation Reversal"
    elif abs(baseline_corr) >= 0.7 and abs(recent_corr) < 0.4:
        return "Correlation Breakdown"
    elif abs(baseline_corr) < 0.3 and abs(recent_corr) >= 0.7:
        return "Emerging Relationship"
    return "No Significant Pattern"

def detect_correlation_changes(returns: pd.DataFrame, baseline_window: int = 120, recent_window: int = 30) -> pd.DataFrame:
    tickers = returns.columns
    results = []
    required_obs = baseline_window + recent_window
    
    empty_columns = [
        "Stock A", "Stock B", "Baseline Correlation", "Recent Correlation", 
        "Change", "Classification", "Rolling Correlation Volatility"
    ]
    
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            stock_a = tickers[i]
            stock_b = tickers[j]
            
            pair_returns = returns[[stock_a, stock_b]].dropna()
            
            if len(pair_returns) < required_obs:
                continue
                
            recent_subset = pair_returns.iloc[-recent_window:]
            baseline_subset = pair_returns.iloc[-(baseline_window + recent_window):-recent_window]
            
            recent_corr = recent_subset.corr().iloc[0, 1]
            baseline_corr = baseline_subset.corr().iloc[0, 1]
            
            if pd.isna(recent_corr) or pd.isna(baseline_corr):
                continue
                
            change = recent_corr - baseline_corr
            classification = classify_relationship_change(baseline_corr, recent_corr)
            
            stability = calculate_relationship_stability(returns, stock_a, stock_b, window=30)
            volatility = round(stability["std_correlation"], 2) if stability is not None and not pd.isna(stability["std_correlation"]) else float("nan")
            
            results.append({
                "Stock A": stock_a,
                "Stock B": stock_b,
                "Baseline Correlation": round(baseline_corr, 2),
                "Recent Correlation": round(recent_corr, 2),
                "Change": round(change, 2),
                "Classification": classification,
                "Rolling Correlation Volatility": volatility,
                "_raw_change": change
            })
                    
    if not results:
        return pd.DataFrame(columns=empty_columns)
        
    df = pd.DataFrame(results)
    df["AbsChange"] = df["_raw_change"].abs()
    df = df.sort_values(by="AbsChange", ascending=False).drop(columns=["AbsChange", "_raw_change"]).reset_index(drop=True)
    return df