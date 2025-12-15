"""
src/aggregator.py
-----------------
This script handles the aggregation of risk metrics across the portfolio.

The main focus here is ensuring their is consistency in the aggregation logic, and I have also added a few reporting measures for insight into the risk at higher levels.
"""
import pandas as pd

class PortfolioAggregator:
    
    @staticmethod
    def prepare_trade_report(results: list) -> pd.DataFrame:
        """
        This is a quick helper to dump the raw list of dictionaries into a DataFrame
        so we can actually do some math on it.
        """
        return pd.DataFrame(results) if results else pd.DataFrame()

    @staticmethod
    def calculate_portfolio_totals(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the grand totals for the dashboard.
        
        Note to self: This only sums the '_USD' columns. We cannot sum raw 'PV' 
        because adding 100 EUR to 1000 JPY is meaningless.
        """
        if df.empty or "Status" not in df.columns:
            return pd.DataFrame()

        # We only want to aggregate trades that actually priced successfully.
        valid_df = df[df["Status"] == "Success"]
        
        # If we have trades but none of them were successful, let the user know explicitly.
        if valid_df.empty:
            return pd.DataFrame({"Metric": ["Status"], "Value": ["No Valid Trades"]})

        # Calculate totals using the normalised USD values
        total_pv = valid_df["PV_USD"].sum()
        total_delta = valid_df["Delta_USD"].sum()
        total_vega = valid_df["Vega_USD"].sum()

        # Return a clean summary table for the frontend/report
        return pd.DataFrame({
            "Metric": ["Total PV (USD)", "Total Delta (USD)", "Total Vega (USD)", "Valid Trades"],
            "Value": [total_pv, total_delta, total_vega, len(valid_df)]
        })

    @staticmethod
    def group_risk_by_pair(df: pd.DataFrame) -> pd.DataFrame:
        """
        Breaks down the risk by Currency Pair.
        This can be useful for seeing exposure per instrument.
        """
        if df.empty or "Pair" not in df.columns: 
            return pd.DataFrame()
        
        # Filter out failed trades first like I did before
        valid_df = df[df["Status"] == "Success"]
        
        # Group by the pair name and sum the USD-normalized risk metrics.
        # I use reset_index() so 'Pair' comes back as a normal column.
        return valid_df.groupby("Pair")[["PV_USD", "Delta_USD", "Vega_USD"]].sum().reset_index()

    @staticmethod
    def group_risk_by_currency(df: pd.DataFrame) -> pd.DataFrame:
        """
        This function aggregates risk by the Quote Currency.
        
        This answers the question that we might encounter in industry: "If the JPY moves bearish/bullish, how much does it hurt us globally?"
        (regardless of whether it was a USD/JPY or EUR/JPY trade).
        """
        if df.empty or "Currency" not in df.columns: 
            return pd.DataFrame()
        
        valid_df = df[df["Status"] == "Success"]
        
        # Group by the currency code (e.g., 'JPY', 'EUR') and sum the USD risk.
        return valid_df.groupby("Currency")[["PV_USD", "Delta_USD", "Vega_USD"]].sum().reset_index()