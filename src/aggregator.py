"""

Responsibility:
1. Summarize risk metrics at the Portfolio level.
2. Group risk by specific dimensions (Pair, Currency).
3. Ensure all aggregation is performed on NORMALIZED (USD) metrics.

"""
import pandas as pd

class PortfolioAggregator:
    """
    Stateless aggregator for FX risk metrics. 
    All summing operations assume inputs are standardized to the USD.
    """

    @staticmethod
    def prepare_trade_report(results: list) -> pd.DataFrame:
        """
        Converts list of dict results into a DataFrame.
        """
        return pd.DataFrame(results) if results else pd.DataFrame()

    @staticmethod
    def calculate_portfolio_totals(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates global portfolio totals.
       
        """
        if df.empty or "Status" not in df.columns:
            return pd.DataFrame()

        # Filter for successful trades only
        valid_df = df[df["Status"] == "Success"]
        
        if valid_df.empty:
            return pd.DataFrame({"Metric": ["Status"], "Value": ["No Valid Trades"]})

        # Summing ONLY the Normalized USD columns
        total_pv = valid_df["PV_USD"].sum()
        total_delta = valid_df["Delta_USD"].sum()
        total_vega = valid_df["Vega_USD"].sum()

        return pd.DataFrame({
            "Metric": ["Total PV (USD)", "Total Delta (USD)", "Total Vega (USD)", "Valid Trades"],
            "Value": [total_pv, total_delta, total_vega, len(valid_df)]
        })

    @staticmethod
    def group_risk_by_pair(df: pd.DataFrame) -> pd.DataFrame:
        """
        Groups risk metrics by Currency Pair (e.g., EUR/USD).
        """
        if df.empty or "Pair" not in df.columns: 
            return pd.DataFrame()
        
        valid_df = df[df["Status"] == "Success"]
        
        return valid_df.groupby("Pair")[["PV_USD", "Delta_USD", "Vega_USD"]].sum().reset_index()

    @staticmethod
    def group_risk_by_currency(df: pd.DataFrame) -> pd.DataFrame:
        """
        Groups risk metrics by the Quote Currency.
        
        Example:
        - A USD/JPY trade (Quote=JPY) contributes to the JPY row.
        - The values shown are the USD-equivalent risk arising from that currency exposure.
        """
        if df.empty or "Currency" not in df.columns: 
            return pd.DataFrame()
        
        valid_df = df[df["Status"] == "Success"]
        
        return valid_df.groupby("Currency")[["PV_USD", "Delta_USD", "Vega_USD"]].sum().reset_index()