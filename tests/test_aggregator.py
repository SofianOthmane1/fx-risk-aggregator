"""
This is the unit tests for the PortfolioAggregator.

By giving aggregation its own test suite, we make failures here obvious.
If someone upstream changes column names, or adds new metrics, or passes
non-USD values by mistake, these tests will break immediately — which is what
we want. It's a guardrail to ensure the reporting layer stays predictable.
"""
import pandas as pd
from src.aggregator import PortfolioAggregator

def test_calculate_portfolio_totals():
    """
    Test that totals are correctly summed from USD columns.
    """
    # Setup dummy data
    data = [
        {"Status": "Success", "PV_USD": 100.0, "Delta_USD": 50.0, "Vega_USD": 10.0},
        {"Status": "Success", "PV_USD": 200.0, "Delta_USD": 25.0, "Vega_USD": 20.0},
        {"Status": "Failed",  "PV_USD": 999.0, "Delta_USD": 0.0,  "Vega_USD": 0.0}, # Should be ignored
    ]
    df = pd.DataFrame(data)
    
    # Run Aggregation
    summary = PortfolioAggregator.calculate_portfolio_totals(df)
    
    # Verify PV Total (100 + 200 = 300)
    pv_row = summary[summary["Metric"] == "Total PV (USD)"]
    assert float(pv_row["Value"].iloc[0]) == 300.0
    
    # Verify Valid Trades Count (2)
    count_row = summary[summary["Metric"] == "Valid Trades"]
    assert int(count_row["Value"].iloc[0]) == 2

def test_group_risk_by_currency():
    """
    Test grouping logic by Currency.
    
    Desks might want to know not just "risk by pair" but "risk by funding currency".
    This function groups by the Currency column (quote currency) and sums only
    USD-normalised PV/Delta/Vega.
    """
    data = [
        {"Status": "Success", "Currency": "USD", "PV_USD": 100.0, "Delta_USD": 50.0, "Vega_USD": 0.0},
        {"Status": "Success", "Currency": "JPY", "PV_USD": 50.0,  "Delta_USD": 10.0, "Vega_USD": 0.0},
        {"Status": "Success", "Currency": "USD", "PV_USD": 100.0, "Delta_USD": 50.0, "Vega_USD": 0.0},
    ]
    df = pd.DataFrame(data)
    
    grouped = PortfolioAggregator.group_risk_by_currency(df)
    
    # Check USD group (100 + 100 = 200)
    usd_row = grouped[grouped["Currency"] == "USD"]
    assert float(usd_row["PV_USD"].iloc[0]) == 200.0
    
    # Check JPY group (50)
    jpy_row = grouped[grouped["Currency"] == "JPY"]
    assert float(jpy_row["PV_USD"].iloc[0]) == 50.0