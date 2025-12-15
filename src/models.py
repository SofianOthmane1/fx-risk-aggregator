"""
src/models.py
-------------
Defines a strict and realistic data contract for the FX Option trades.

In this script I validate everything (regex, bounds, logic) at the entry gate so the 
pricing engine doesn't crash later on incorrect/irregular data.
"""

from pydantic import BaseModel, Field, PositiveFloat, ConfigDict, model_validator
from enum import Enum
import re

class OptionType(str, Enum):
    CALL = "Call"
    PUT = "Put"

class FXOptionTrade(BaseModel):
    """
    Represents a single FX Option trade.
    """
    
    # --- Identity & Structure ---
    trade_id: str = Field(..., alias="TradeID", description="Unique identifier")
    
    # Here, I enforce the standard "EUR/USD" format with regex.
    # If we don't force the slash and 3-char codes here, parsing it later becomes more complex.
    pair: str = Field(..., alias="Underlying", pattern=r"^[A-Z]{3}/[A-Z]{3}$")
    
    # --- Financials ---
    spot_price: PositiveFloat = Field(..., alias="Spot")
    strike_price: PositiveFloat = Field(..., alias="Strike")
    notional: PositiveFloat = Field(..., alias="Notional")
    
    # Standard 3-letter code for the currency (e.g., "USD").
    notional_currency: str = Field(..., alias="NotionalCurrency", pattern=r"^[A-Z]{3}$")
    
    # --- Market Data ---
    # This is a sanity check on Volatility. 
    # We cap it at 500% (5.0) to catch fat-finger errors.
    volatility: float = Field(..., alias="Vol", gt=0, le=5.0)
    
    domestic_rate: float = Field(..., alias="RateDomestic")
    foreign_rate: float = Field(..., alias="RateForeign")
    
    # Cap maturity at 100 years. It's an arbitrary safety net, but 
    # if I get an option expiring in 2200, it's probably a data error.
    time_to_maturity: float = Field(..., alias="Expiry", gt=0, le=100.0)
    
    option_type: OptionType = Field(..., alias="OptionType")

    # --- Pydantic Config ---
    # This allows us to use the field names (snake_case) or the aliases (PascalCase) when loading data.
    model_config = ConfigDict(populate_by_name=True)

    # --- Domain Logic Validators ---

    @model_validator(mode='after')
    def check_currency_consistency(self) -> 'FXOptionTrade':
        """
        Cross-Field Logic
        """
        # 1. Quick format check. If the regex failed above, Pydantic stops us before here, 
        # but it doesn't hurt to be thorough.
        if '/' not in self.pair:
            return self

        base, quote = self.pair.split('/')

        # 2. The Logic Check:
        # Here I am making sure the payout currency actually exists in the pair.
        if self.notional_currency not in (base, quote):
            raise ValueError(
                f"Notional Currency '{self.notional_currency}' is invalid for Pair '{self.pair}'. "
                f"Must be either '{base}' or '{quote}'."
            )
            
        return self