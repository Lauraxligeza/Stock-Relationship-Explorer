import pandas as pd

def rank_stock_pairs(correlation_matrix):
    pairs = []
    columns = correlation_matrix.columns
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            stock_a = columns[i]
            stock_b = columns[j]
            corr = correlation_matrix.loc[stock_a, stock_b]
            pairs.append({"Stock A": stock_a, "Stock B": stock_b, "Correlation": corr})
    
    df = pd.DataFrame(pairs)
    if not df.empty:
        df["Abs_Correlation"] = df["Correlation"].abs()
        df = df.sort_values(by="Abs_Correlation", ascending=False).drop(columns=["Abs_Correlation"])
        df = df.reset_index(drop=True)
    return df

def create_network_edges(correlation_matrix, threshold=0.5):
    ranked_pairs = rank_stock_pairs(correlation_matrix)
    if ranked_pairs.empty:
        return ranked_pairs
    filtered = ranked_pairs[ranked_pairs["Correlation"].abs() >= threshold].copy()
    return filtered.reset_index(drop=True)