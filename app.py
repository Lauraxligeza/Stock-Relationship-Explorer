import itertools
import logging
import streamlit as st
import plotly.express as px
from market_data import parse_tickers, fetch_stock_data, fetch_company_names
from stock_statistics import (
    calculate_returns,
    calculate_correlations,
    calculate_rolling_correlation,
    normalize_prices,
    calculate_pair_observations,
    calculate_relationship_stability
)
from relationships import rank_stock_pairs, create_network_edges
from network_graph import build_stock_network, create_network_figure
from opportunity_radar import detect_correlation_changes

st.title("Stock Relationship Explorer")

@st.cache_data(ttl=3600)
def load_market_data(tickers_tuple, period):
    return fetch_stock_data(list(tickers_tuple), period=period)

@st.cache_data(ttl=86400)
def load_company_names(tickers_tuple):
    return fetch_company_names(list(tickers_tuple))

tickers_input = st.text_input("Enter stock tickers:")
period = st.selectbox("Select period", ["1y", "2y", "5y"])
analyze_button = st.button("Analyze")

if analyze_button:
    st.session_state["analyzed"] = False
    st.session_state.pop("correlation_matrix", None)
    st.session_state.pop("returns", None)
    st.session_state.pop("obs_matrix", None)
    st.session_state.pop("tickers", None)
    st.session_state.pop("normalized_prices", None)
    st.session_state.pop("prices", None)
    st.session_state.pop("period", None)
    st.session_state.pop("company_names", None)
    st.session_state.pop("selected_pair", None)
    st.session_state.pop("pending_investigation", None)
    st.session_state.pop("comp_stock_a", None)
    st.session_state.pop("comp_stock_b", None)
    
    try:
        tickers = parse_tickers(tickers_input)
        prices = load_market_data(tuple(tickers), period=period)
        returns = calculate_returns(prices)
        correlation_matrix = calculate_correlations(returns)
        obs_matrix = calculate_pair_observations(returns)
        normalized = normalize_prices(prices)
        company_names = load_company_names(tuple(tickers))
        
        st.session_state["prices"] = prices
        st.session_state["returns"] = returns
        st.session_state["correlation_matrix"] = correlation_matrix
        st.session_state["obs_matrix"] = obs_matrix
        st.session_state["tickers"] = tickers
        st.session_state["normalized_prices"] = normalized
        st.session_state["period"] = period
        st.session_state["company_names"] = company_names
        st.session_state["analyzed"] = True
    except ValueError as e:
        st.error(f"Input/Data Error: {str(e)}")
    except Exception as e:
        logging.exception("Unexpected error during analysis:")
        st.error("An unexpected error occurred while processing the analysis. Please check your inputs.")

if st.session_state.get("analyzed", False):
    tickers = st.session_state["tickers"]
    period_used = st.session_state["period"]
    prices = st.session_state["prices"]
    company_names = st.session_state.get("company_names", {})
    
    if st.session_state.get("pending_investigation", False):
        pair = st.session_state.get("selected_pair")
        if pair and len(pair) == 2:
            stock_a, stock_b = pair
            if stock_a in tickers and stock_b in tickers and stock_a != stock_b:
                st.session_state["comp_stock_a"] = stock_a
                st.session_state["comp_stock_b"] = stock_b
        st.session_state["pending_investigation"] = False

    n_stocks = len(tickers)
    n_pairs = n_stocks * (n_stocks - 1) // 2
    n_observations = len(prices)
    
    start_date = prices.index.min().strftime("%B %d, %Y")
    end_date = prices.index.max().strftime("%B %d, %Y")
    
    st.markdown("### Analysis Overview")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Stocks", n_stocks)
    with col_m2:
        st.metric("Pairs", n_pairs)
    with col_m3:
        st.metric("Observations", n_observations)
        
    st.caption(f"Coverage: {start_date} – {end_date} · Requested period: {period_used}")
    
    with st.expander("View Analyzed Stocks"):
        for ticker in tickers:
            name = company_names.get(ticker, ticker)
            if name != ticker:
                st.write(f"- **{name}** ({ticker})")
            else:
                st.write(f"- **{ticker}**")
            
    st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["Discover", "Compare", "Opportunity Radar", "About"])

with tab1:
    if st.session_state.get("analyzed", False):
        correlation_matrix = st.session_state["correlation_matrix"]
        obs_matrix = st.session_state["obs_matrix"]
        tickers = st.session_state["tickers"]
        company_names = st.session_state.get("company_names", {})
        
        st.subheader("Data Quality & Coverage")
        min_obs = st.slider("Minimum observations", 20, 200, 60, 5, key="disc_min_obs")
        
        low_obs_pairs = []
        for stock_a, stock_b in itertools.combinations(tickers, 2):
            count = obs_matrix.loc[stock_a, stock_b]
            if count < min_obs:
                low_obs_pairs.append((stock_a, stock_b, count))
                
        if low_obs_pairs:
            st.warning(f"{len(low_obs_pairs)} pair(s) below threshold")
            with st.expander("View pairs with insufficient observations"):
                for stock_a, stock_b, count in low_obs_pairs:
                    name_a = company_names.get(stock_a, stock_a)
                    name_b = company_names.get(stock_b, stock_b)
                    st.write(f"- {name_a} ({stock_a}) / {name_b} ({stock_b}): {count} observations")
        else:
            st.success("All stock pairs meet the minimum observation threshold.")
            
        st.subheader("Stock Relationship Network")
        threshold = st.slider("Correlation Threshold", 0.0, 1.0, 0.5, 0.05, key="disc_threshold")
        edges = create_network_edges(correlation_matrix, threshold=threshold)
        G = build_stock_network(edges, tickers)
        fig_network = create_network_figure(G)
        st.plotly_chart(fig_network)
        
        st.subheader("Stock Correlation Heatmap")
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            zmin=-1,
            zmax=1,
            color_continuous_scale="RdBu_r",
            aspect="auto"
        )
        st.plotly_chart(fig)
        
        ranked_pairs = rank_stock_pairs(correlation_matrix)
        if ranked_pairs.empty or "Stock A" not in ranked_pairs.columns or "Stock B" not in ranked_pairs.columns:
            st.info("Not enough valid stock pairs available for correlation rankings.")
        else:
            display_ranked_pairs = ranked_pairs.copy()
            display_ranked_pairs["Stock A"] = display_ranked_pairs["Stock A"].map(lambda t: f"{company_names.get(t, t)} ({t})")
            display_ranked_pairs["Stock B"] = display_ranked_pairs["Stock B"].map(lambda t: f"{company_names.get(t, t)} ({t})")
            
            st.subheader("Top 5 Strongest Positive Correlations")
            positive_pairs = display_ranked_pairs[display_ranked_pairs["Correlation"] > 0]
            if not positive_pairs.empty:
                st.dataframe(positive_pairs.head(5))
            else:
                st.write("No positive correlations found.")
                
            st.subheader("Top 5 Strongest Negative Correlations")
            negative_pairs = display_ranked_pairs[display_ranked_pairs["Correlation"] < 0]
            if not negative_pairs.empty:
                strongest_negative = negative_pairs.sort_values(by="Correlation", ascending=True)
                st.dataframe(strongest_negative.head(5))
            else:
                st.write("No negative correlations found.")
                
            pairs = list(zip(ranked_pairs["Stock A"], ranked_pairs["Stock B"]))
            selected_disc_pair = st.selectbox(
                "Select a relationship to investigate",
                pairs,
                format_func=lambda pair: (
                    f"{company_names.get(pair[0], pair[0])} ({pair[0]}) / "
                    f"{company_names.get(pair[1], pair[1])} ({pair[1]})"
                ),
                key="disc_selected_pair"
            )
            if st.button("Investigate Relationship", key="disc_investigate_btn"):
                st.session_state["selected_pair"] = selected_disc_pair
                st.session_state["pending_investigation"] = True
                st.success(f"Selected pair {selected_disc_pair[0]} / {selected_disc_pair[1]} for investigation.")
                
            csv_ranked = ranked_pairs.to_csv(index=False)
            st.download_button(
                label="Download Correlation Rankings",
                data=csv_ranked,
                file_name="correlation_rankings.csv",
                mime="text/csv",
                key="download_rankings"
            )
    else:
        st.info("Please enter stock tickers and click Analyze above to view the Discover section.")

with tab2:
    if st.session_state.get("analyzed", False):
        tickers = st.session_state["tickers"]
        prices = st.session_state["prices"]
        company_names = st.session_state.get("company_names", {})
        
        st.subheader("Stock Selection for Comparison & Rolling Analysis")
        stock_a = st.selectbox(
            "Select Stock A",
            tickers,
            format_func=lambda ticker: f"{company_names.get(ticker, ticker)} ({ticker})",
            key="comp_stock_a"
        )
        available_stock_b = [t for t in tickers if t != stock_a]
        if not available_stock_b:
            st.warning("Please select a valid Stock A with at least one other stock available.")
            stock_b = None
        else:
            stock_b = st.selectbox(
                "Select Stock B",
                available_stock_b,
                format_func=lambda ticker: f"{company_names.get(ticker, ticker)} ({ticker})",
                key="comp_stock_b"
            )
        
        min_date = prices.index.min().date()
        max_date = prices.index.max().date()
        date_range = st.date_input(
            "Select historical date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="comp_date_range"
        )
        
        filtered_prices = None
        if len(date_range) != 2:
            st.info("Please select both a start and end date.")
        else:
            start_d, end_d = date_range
            if start_d >= end_d:
                st.warning("The start date must be earlier than the end date.")
            else:
                filtered_prices = prices.loc[str(start_d):str(end_d)]
            
        st.subheader("Stock Performance Comparison")
        filtered_returns = None
        if filtered_prices is not None and not filtered_prices.empty and stock_a and stock_b and stock_a in filtered_prices.columns and stock_b in filtered_prices.columns:
            filtered_returns = calculate_returns(filtered_prices)
            subset = filtered_prices[[stock_a, stock_b]].dropna()
            if len(subset) < 2:
                st.warning("Not enough shared price observations for this pair in the selected date range to calculate normalized performance.")
            else:
                filtered_normalized = normalize_prices(subset)
                comparison_data = filtered_normalized
                name_a = company_names.get(stock_a, stock_a)
                name_b = company_names.get(stock_b, stock_b)
                fig_perf = px.line(
                    comparison_data,
                    title=f"Normalized Price Performance: {name_a} ({stock_a}) vs {name_b} ({stock_b}) (Starts at 100)",
                    labels={"value": "Normalized Price", "index": "Date", "variable": "Stock"}
                )
                st.plotly_chart(fig_perf)
        elif filtered_prices is not None:
            st.warning("Please select valid stocks for comparison or ensure price data is available.")
        
        st.subheader("Rolling Correlation Explorer")
        window = st.selectbox("Select Rolling Window", [30, 60, 90], key="comp_window")
        
        if filtered_returns is not None and not filtered_returns.empty and stock_a and stock_b and stock_a in filtered_returns.columns and stock_b in filtered_returns.columns:
            rolling_series = calculate_rolling_correlation(filtered_returns, stock_a, stock_b, window=window)
            if rolling_series.dropna().empty:
                st.warning(f"Not enough historical observations to calculate a {window}-session rolling correlation for this pair within the selected date range.")
            else:
                name_a = company_names.get(stock_a, stock_a)
                name_b = company_names.get(stock_b, stock_b)
                fig_rolling = px.line(
                    x=rolling_series.index,
                    y=rolling_series.values,
                    labels={"x": "Date", "y": "Rolling Correlation"},
                    title=f"{window}-Session Rolling Correlation: {name_a} ({stock_a}) vs {name_b} ({stock_b})"
                )
                fig_rolling.update_layout(yaxis=dict(range=[-1, 1]))
                st.plotly_chart(fig_rolling)
        else:
            st.info("Please select a valid date range and stocks above to view rolling correlations.")

        st.subheader("Relationship Stability Analysis")
        if filtered_returns is not None and not filtered_returns.empty and stock_a and stock_b and stock_a in filtered_returns.columns and stock_b in filtered_returns.columns:
            stability = calculate_relationship_stability(filtered_returns, stock_a, stock_b, window=window)
            if stability is not None:
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("Mean correlation", f"{stability['mean_correlation']:+.2f}")
                with col_s2:
                    st.metric("Correlation std. dev.", f"{stability['std_correlation']:.2f}")
                with col_s3:
                    st.metric("Rolling observations", stability['observations'])
            else:
                st.warning("Not enough observations to calculate relationship stability metrics for the selected window and date range.")
        else:
            st.info("Please select a valid date range and stocks above to view relationship stability metrics.")
    else:
        st.info("Please enter stock tickers and click Analyze above to view the Compare section.")

with tab3:
    if st.session_state.get("analyzed", False):
        returns = st.session_state["returns"]
        company_names = st.session_state.get("company_names", {})
        
        st.subheader("Opportunity Radar")
        st.write("These findings are historical statistical observations, not trading recommendations.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            baseline_window = st.selectbox("Baseline Window", [60, 90, 120], index=2, key="radar_baseline")
        with col2:
            recent_window = st.selectbox("Recent Window", [20, 30, 60], index=1, key="radar_recent")
        with col3:
            min_change = st.slider("Min Absolute Change", 0.0, 2.0, 0.2, 0.05, key="radar_min_change")
            
        selected_patterns = st.multiselect(
            "Filter relationship patterns",
            ["Correlation Reversal", "Correlation Breakdown", "Emerging Relationship", "No Significant Pattern"],
            default=["Correlation Reversal", "Correlation Breakdown", "Emerging Relationship", "No Significant Pattern"],
            key="radar_patterns"
        )
        
        max_volatility = st.slider("Maximum Rolling Correlation Volatility", 0.0, 1.0, 0.5, 0.05, key="radar_max_volatility")
        st.caption("Relationships without sufficient volatility data are excluded.")
            
        radar_df = detect_correlation_changes(returns, baseline_window=baseline_window, recent_window=recent_window)
        
        if not radar_df.empty:
            filtered_radar = radar_df[
                (radar_df["Change"].abs() >= min_change) &
                (radar_df["Classification"].isin(selected_patterns)) &
                (radar_df["Rolling Correlation Volatility"] <= max_volatility)
            ]
            if not filtered_radar.empty:
                display_radar = filtered_radar.copy()
                display_radar["Stock A"] = display_radar["Stock A"].map(lambda t: f"{company_names.get(t, t)} ({t})")
                display_radar["Stock B"] = display_radar["Stock B"].map(lambda t: f"{company_names.get(t, t)} ({t})")
                
                st.dataframe(display_radar, use_container_width=True)
                
                pairs = list(zip(filtered_radar["Stock A"], filtered_radar["Stock B"]))
                selected_pair_option = st.selectbox(
                    "Select a pair to investigate",
                    pairs,
                    format_func=lambda pair: (
                        f"{company_names.get(pair[0], pair[0])} ({pair[0]}) / "
                        f"{company_names.get(pair[1], pair[1])} ({pair[1]})"
                    ),
                    key="radar_selected_pair"
                )
                if st.button("Investigate Pair", key="radar_investigate_btn"):
                    st.session_state["selected_pair"] = selected_pair_option
                    st.session_state["pending_investigation"] = True
                    st.success(f"Selected pair {selected_pair_option[0]} / {selected_pair_option[1]} for investigation.")
                
                csv_radar = filtered_radar.to_csv(index=False)
                st.download_button(
                    label="Download Opportunity Radar Results",
                    data=csv_radar,
                    file_name="opportunity_radar_results.csv",
                    mime="text/csv",
                    key="download_radar"
                )
            else:
                st.info("No relationships meet the selected thresholds and filters.")
        else:
            st.warning("Insufficient historical observations to run the Opportunity Radar for the selected windows.")
    else:
        st.info("Please enter stock tickers and click Analyze above to view the Opportunity Radar section.")

with tab4:
    st.subheader("About Stock Relationship Explorer")
    st.write(
        "The Stock Relationship Explorer is a modular financial analysis tool designed to help users "
        "understand co-movements, correlations, and structural relationships among a custom set of stock tickers."
    )
    st.markdown("### Methodology")
    st.markdown(
        "- **Data Retrieval & Returns:** Downloads historical price data and computes daily percentage returns.\n"
        "- **Correlation & Heatmaps:** Measures linear relationships across selected periods.\n"
        "- **Network Analysis:** Constructs an interactive graph where nodes represent stocks and weighted, colored edges represent correlation strength and direction.\n"
        "- **Normalized Performance:** Indexes stock prices starting at 100 to compare relative growth trajectories.\n"
        "- **Opportunity Radar:** Scans for structural shifts by comparing baseline historical correlations against recent windows."
    )
    st.markdown("### Limitations & Disclaimer")
    st.markdown(
        "**Important:** Historical correlations and statistical observations are descriptive metrics of past market behavior "
        "and **are not predictions or investment recommendations**. Past performance does not guarantee future results."
    )