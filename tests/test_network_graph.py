import pandas as pd
import pytest
from network_graph import build_stock_network

def test_node_creation():
    tickers = ["NVDA", "AMD", "ASML", "AAPL"]
    edges = pd.DataFrame([
        {"Stock A": "NVDA", "Stock B": "AMD", "Correlation": 0.80},
        {"Stock A": "AMD", "Stock B": "ASML", "Correlation": -0.65}
    ])
    G = build_stock_network(edges, tickers)
    assert set(G.nodes) == set(tickers)
    assert G.number_of_nodes() == 4

def test_edge_creation():
    tickers = ["NVDA", "AMD", "ASML", "AAPL"]
    edges = pd.DataFrame([
        {"Stock A": "NVDA", "Stock B": "AMD", "Correlation": 0.80},
        {"Stock A": "AMD", "Stock B": "ASML", "Correlation": -0.65}
    ])
    G = build_stock_network(edges, tickers)
    assert G.number_of_edges() == 2
    assert G.has_edge("NVDA", "AMD")
    assert G.has_edge("AMD", "ASML")
    assert not G.has_edge("NVDA", "AAPL")
    assert not G.has_edge("AAPL", "ASML")

def test_correlation_attributes():
    tickers = ["NVDA", "AMD", "ASML", "AAPL"]
    edges = pd.DataFrame([
        {"Stock A": "NVDA", "Stock B": "AMD", "Correlation": 0.80},
        {"Stock A": "AMD", "Stock B": "ASML", "Correlation": -0.65}
    ])
    G = build_stock_network(edges, tickers)
    assert pytest.approx(G["NVDA"]["AMD"]["correlation"]) == 0.80
    assert pytest.approx(G["AMD"]["ASML"]["correlation"]) == -0.65