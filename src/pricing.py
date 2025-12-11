"""
Implements the Garman-Kohlhagen model (Black-Scholes for FX).

Model Assumptions:
1. Asset prices follow a Geometric Brownian Motion (Lognormal dynamics).
2. Interest rates (rd, rf) and Volatility (sigma) are constant.
3. Markets are frictionless (no transaction costs) and continuous.
4. No arbitrage opportunities exist.
5. European exercise style (no early exercise).
6. Inputs are pre-validated: The engine assumes T > 0 and sigma > 0.
"""

import numpy as np
from scipy.stats import norm
from src.models import FXOptionTrade, OptionType

class BlackScholesFX:
    """
    Stateless pricing engine for FX Options.
    """
    
    @staticmethod
    def _calculate_d1_d2(S, K, T, rd, rf, sigma):
        """
        Internal helper for d1/d2 probability factors.
        """
        sqrt_T = np.sqrt(T)
        d1 = (np.log(S / K) + (rd - rf + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        return d1, d2

    @staticmethod
    def calculate_metrics(trade: FXOptionTrade, reporting_currency: str = "USD") -> dict:
        """
        Calculates PV and Greeks, scaling by Notional and normalizing to USD.
        
        Assumptions:
            - Inputs (T, Vol, etc.) are already validated by the FXOptionTrade schema.
            - Time to Maturity (T) is strictly positive.
            - Volatility (sigma) is strictly positive.
        
        Args:
            trade (FXOptionTrade): The validated trade object.
            reporting_currency (str): The currency to normalize results into (default "USD").
            
        Returns:
            dict: Contains both Native and Normalized (USD) metrics.
        """
        # 1. Extract inputs
        S = trade.spot_price
        K = trade.strike_price
        T = trade.time_to_maturity
        sigma = trade.volatility
        rd = trade.domestic_rate
        rf = trade.foreign_rate
        notional = trade.notional
        
        # 2. Garman-Kohlhagen Calculations
        d1, d2 = BlackScholesFX._calculate_d1_d2(S, K, T, rd, rf, sigma)
        
        # Discount factors
        disc_d = np.exp(-rd * T) # Domestic discount factor
        disc_f = np.exp(-rf * T) # Foreign discount factor

        # 3. Calculate Unit Metrics (Per 1 Unit of Base Currency)
        
        if trade.option_type == OptionType.CALL:
            # Call Value = S * e^(-rf*T) * N(d1) - K * e^(-rd*T) * N(d2)
            price_unit = (S * disc_f * norm.cdf(d1)) - (K * disc_d * norm.cdf(d2))
            
            # Delta = e^(-rf*T) * N(d1)
            delta_unit = disc_f * norm.cdf(d1)
        else: # PUT
            # Put Value = K * e^(-rd*T) * N(-d2) - S * e^(-rf*T) * N(-d1)
            price_unit = (K * disc_d * norm.cdf(-d2)) - (S * disc_f * norm.cdf(-d1))
            
            # Put Delta = e^(-rf*T) * (N(d1) - 1)
            delta_unit = disc_f * (norm.cdf(d1) - 1)

        # Vega (Same for Call and Put)
        # Vega = S * e^(-rf*T) * N'(d1) * sqrt(T)
        vega_unit = S * disc_f * norm.pdf(d1) * np.sqrt(T)

        # 4. Scale by Notional (Native Units)
        # The result is now in the Quote Currency (e.g., JPY for USD/JPY)
        pv_native = price_unit * notional
        delta_native = delta_unit * notional
        vega_native = vega_unit * notional

        # 5. Currency Normalization
        try:
            base_ccy, quote_ccy = trade.pair.split('/')
        except ValueError:
            quote_ccy = "Unknown"

        # Calculate conversion rate to USD
        fx_rate_to_usd = 1.0
        
        if quote_ccy == reporting_currency:
            fx_rate_to_usd = 1.0
        elif base_ccy == reporting_currency and quote_ccy != reporting_currency:
            # Special Case: USD/JPY -> Divide by Spot to get USD
            fx_rate_to_usd = 1.0 / S 
        else:
            # Fallback (e.g. EUR/GBP)
            fx_rate_to_usd = 1.0

        return {
            "PV_Native": pv_native,
            "Delta_Native": delta_native,
            "Vega_Native": vega_native,
            "Currency": quote_ccy,
            "PV_USD": pv_native * fx_rate_to_usd,
            "Delta_USD": delta_native * fx_rate_to_usd,
            "Vega_USD": vega_native * fx_rate_to_usd
        }