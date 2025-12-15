"""
src/pricing.py
---------------------
The math core of the application.

This implements the Garman-Kohlhagen model, which is just the standard 
Black-Scholes adjusted for Foreign Exchange. The main difference is that 
instead of a dividend yield (like in stocks), we have a foreign interest rate.

Key Assumptions I make here:
1. No transaction costs (frictionless).
2. No arbitrage (free money) exists.
3. Rates and Volatility don't change over the life of the option.
"""

import numpy as np
from scipy.stats import norm
from src.models import FXOptionTrade, OptionType

class BlackScholesFX:
    """
    Stateless pricing engine.
    It doesn't store anything, so it's safe to run in parallel.
    """
    
    @staticmethod
    def _calculate_d1_d2(S, K, T, rd, rf, sigma):
        """
        Standard Black-Scholes procedure.
        We need d1 and d2 to figure out the probabilities of the option 
        finishing in-the-money.
        """
        sqrt_T = np.sqrt(T)
        
        # Plug in d1 and d2 formulas
        d1 = (np.log(S / K) + (rd - rf + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        return d1, d2

    @staticmethod
    def calculate_metrics(trade: FXOptionTrade, reporting_currency: str = "USD") -> dict:
        """
        This is the main workhorse function.
        
        It calculates the Present Value (PV) and the Greeks (Delta, Vega).
        
        Note to self: I have normalised everything to USD for reporting purposes.
        """
        
        # 1. Unpack inputs
        # We don't need to check for T > 0 here because the Pydantic model 
        # rejected any invalid data before reaching this point.
        S = trade.spot_price
        K = trade.strike_price
        T = trade.time_to_maturity
        sigma = trade.volatility
        rd = trade.domestic_rate
        rf = trade.foreign_rate
        notional = trade.notional
        
        # 2. Run the Garman-Kohlhagen Calculations
        d1, d2 = BlackScholesFX._calculate_d1_d2(S, K, T, rd, rf, sigma)
        
        # Pre-calculate discount factors (time value of money)
        disc_d = np.exp(-rd * T) # Domestic discount factor
        disc_f = np.exp(-rf * T) # Foreign discount factor

        # 3. Calculate Unit Metrics (Per 1 Unit of Base Currency)
        
        if trade.option_type == OptionType.CALL:
            # This is the standard Call Formula
            price_unit = (S * disc_f * norm.cdf(d1)) - (K * disc_d * norm.cdf(d2))
            
            # Delta: Sensitivity to Spot Price.
            delta_unit = disc_f * norm.cdf(d1)
        else: # PUT
            # Standard Put Formula
            price_unit = (K * disc_d * norm.cdf(-d2)) - (S * disc_f * norm.cdf(-d1))
            
            # Put Delta = e^(-rf*T) * (N(d1) - 1)
            delta_unit = disc_f * (norm.cdf(d1) - 1)

        # Vega (Same for Call and Put)
        # This is essentially the sensitivity to Volatility.
        vega_unit = S * disc_f * norm.pdf(d1) * np.sqrt(T)

        # 4. Scale by Notional
        # The math gave us the price for 1 unit. Now we have to multiply by the actual trade size.
        # Note to self: These results are in the "Quote Currency" (e.g., JPY for USD/JPY).
        pv_native = price_unit * notional
        delta_native = delta_unit * notional
        vega_native = vega_unit * notional

        # 5. Currency Normalisation
        try:
            base_ccy, quote_ccy = trade.pair.split('/')
        except ValueError:
            # Should never happen due to regex, but safety first.
            quote_ccy = "Unknown"

        # Default conversion: Assume 1:1 (e.g., if the quote is already USD)
        fx_rate_to_usd = 1.0
        
        if quote_ccy == reporting_currency:
            fx_rate_to_usd = 1.0
        elif base_ccy == reporting_currency and quote_ccy != reporting_currency:
            # This is the special Case: USD/JPY
            # The value is in JPY, but we want USD. 
            # Since Spot is JPY per USD, we divide by Spot to flip it back.USD
            fx_rate_to_usd = 1.0 / S 
        else:
            # Fallback for Cross-Rates (e.g., EUR/GBP). 
            # In a real system, here the system would I deally look up the GBPUSD rate here. 
            # For now, leaving as 1.0 to keep it simple.
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