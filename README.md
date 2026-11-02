# Stock Relationship Explorer

A Python application for comparing stocks and exploring how their correlations change over time.

I wanted to see which stocks tend to move together, which move in opposite directions, and whether those relationships stay consistent over different periods.

## Features

- **Correlation Heatmap:** View correlations between selected stocks.
- **Network Graph:** Visualize connections between stocks based on correlation strength.
- **Stock Comparison:** Compare the historical performance of two stocks.
- **Rolling Correlation:** See how correlations change across 30, 60, or 90 trading sessions.
- **Relationship Stability:** Calculate the average and standard deviation of rolling correlations.
- **Opportunity Radar:** Compare correlations between two historical periods and highlight changes.
- **Filtering:** Adjust correlation thresholds, select relationship types, and filter by volatility.
- **CSV Export:** Download correlation rankings and Radar results.

## Opportunity Radar

The Radar compares correlations from two nonoverlapping historical periods.

Based on predefined thresholds, it labels relationships as:

- Correlation Reversal
- Correlation Breakdown
- Emerging Relationship
- No Significant Pattern

It also calculates the standard deviation of rolling correlations to give an indication of how much a relationship has varied historically.

These are simple statistical classifications, not predictions.

## Technologies

- **Python** for the application logic
- **Pandas and NumPy** for data analysis
- **yfinance** for historical stock prices
- **Streamlit** for the interface
- **Plotly and NetworkX** for visualizations

## Running the application

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Start the application:

```bash
python3 -m streamlit run app.py
```

Enter at least two stock tickers, select a historical period, and click **Analyze**.

For example:

`AAPL, MSFT, NVDA, AMD`

## Testing

The project includes automated tests using pytest.

```bash
python3 -m pytest -v
```

## Limitations

The analysis uses historical prices and Pearson correlation. Correlations can change, and the results do not establish causation or predict future stock performance.

This project is intended for exploring historical market data, not generating trading signals or investment recommendations.