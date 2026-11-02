import pandas as pd
import numpy as np
import pytest
from opportunity_radar import classify_relationship_change, detect_correlation_changes

@pytest.mark.parametrize(
    "baseline, recent, expected",
    [
        (0.80, -0.50, "Correlation Reversal"),
        (0.85, 0.20, "Correlation Breakdown"),
        (0.10, 0.80, "Emerging Relationship"),
        (0.60, 0.55, "No Significant Pattern"),
        (-0.80, -0.10, "Correlation Breakdown"),
        (0.30, -0.30, "Correlation Reversal"),
        (0.70, 0.39, "Correlation Breakdown"),
        (0.29, 0.70, "Emerging Relationship"),
    ],
)
def test_classify_relationship_change(baseline, recent, expected):
    assert classify_relationship_change(baseline, recent) == expected

def test_detect_correlation_changes_insufficient_data():
    dates = pd.date_range("2026-01-01", periods=50)
    returns = pd.DataFrame({
        "A": [0.01] * 50,
        "B": [0.02] * 50
    }, index=dates)
    
    df = detect_correlation_changes(returns, baseline_window=120, recent_window=30)
    assert df.empty
    assert "Classification" in df.columns
    assert "Rolling Correlation Volatility" in df.columns

def test_detect_correlation_changes_reversal():
    dates = pd.date_range("2026-01-01", periods=150)
    np.random.seed(42)
    base_a = np.random.normal(0, 0.01, 120)
    base_b = base_a + np.random.normal(0, 0.001, 120)
    
    rec_a = np.random.normal(0, 0.01, 30)
    rec_b = -rec_a + np.random.normal(0, 0.001, 30)
    
    series_a = np.concatenate([base_a, rec_a])
    series_b = np.concatenate([base_b, rec_b])
    
    returns = pd.DataFrame({
        "A": series_a,
        "B": series_b
    }, index=dates)
    
    df = detect_correlation_changes(returns, baseline_window=120, recent_window=30)
    assert not df.empty
    assert df.loc[0, "Classification"] == "Correlation Reversal"
    assert "Rolling Correlation Volatility" in df.columns

def test_detect_correlation_changes_volatility():
    dates = pd.date_range("2026-01-01", periods=200)
    np.random.seed(42)
    
    a = np.random.normal(0, 0.01, 200)
    b = a + np.random.normal(0, 0.0001, 200)
    
    c = np.random.normal(0, 0.01, 200)
    d = np.concatenate([c[:100], -c[100:]]) + np.random.normal(0, 0.0001, 200)
    
    returns = pd.DataFrame({
        "Stable1": a,
        "Stable2": b,
        "Unstable1": c,
        "Unstable2": d
    }, index=dates)
    
    df = detect_correlation_changes(returns, baseline_window=100, recent_window=30)
    assert not df.empty
    
    stable_row = df[((df["Stock A"] == "Stable1") & (df["Stock B"] == "Stable2")) | 
                    ((df["Stock A"] == "Stable2") & (df["Stock B"] == "Stable1"))]
    unstable_row = df[((df["Stock A"] == "Unstable1") & (df["Stock B"] == "Unstable2")) | 
                    ((df["Stock A"] == "Unstable2") & (df["Stock B"] == "Unstable1"))]
    
    if not stable_row.empty and not unstable_row.empty:
        stable_vol = stable_row.iloc[0]["Rolling Correlation Volatility"]
        unstable_vol = unstable_row.iloc[0]["Rolling Correlation Volatility"]
        assert unstable_vol > stable_vol