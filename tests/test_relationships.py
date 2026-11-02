import pandas as pd
import pytest
from relationships import rank_stock_pairs, create_network_edges

def test_create_network_edges():
    corr_matrix = pd.DataFrame(
        [
            [1.0, 0.8, -0.6, 0.2],
            [0.8, 1.0, -0.1, 0.4],
            [-0.6, -0.1, 1.0, -0.7],
            [0.2, 0.4, -0.7, 1.0]
        ],
        index=["A", "B", "C", "D"],
        columns=["A", "B", "C", "D"]
    )
    
    edges = create_network_edges(corr_matrix, threshold=0.5)
    
    assert len(edges) == 3
    corrs = set(edges["Correlation"].values)
    assert 0.8 in corrs
    assert -0.6 in corrs
    assert -0.7 in corrs
    assert 0.2 not in corrs
    assert 0.4 not in corrs
    assert -0.1 not in corrs