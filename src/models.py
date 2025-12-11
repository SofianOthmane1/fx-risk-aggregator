"""
Defines strict data schemas for FX Option trades.
Includes domain-specific validation (regex, bounds) and cross-field logic.
"""

from pydantic import BaseModel, Field, PositiveFloat, ConfigDict, model_validator
from enum import Enum
import re

class OptionType(str, Enum):
    CALL = "Call"
    PUT = "Put"

class FXOptionTrade(BaseModel):
    """
    Represents a single FX Option trade with strict validation rules.
    """
    
    # --- Identity & Structure ---
    trade_id: str = Field(..., alias="TradeID", description="Unique identifier")
    
    # Regex enforces standard 3-letter ISO codes (e.g., "EUR/USD")
    pair: str = Field(..., alias="Underlying", pattern=r"^[A-Z]{3}/[A-Z]{3}$")
    
    # --- Financials ---
    spot_price: PositiveFloat = Field(..., alias="Spot")
    strike_price: PositiveFloat = Field(..., alias="Strike")
    notional: PositiveFloat = Field(..., alias="Notional")
    
    # Regex enforces 3-letter currency code (e.g. "USD")
    notional_currency: str = Field(..., alias="NotionalCurrency", pattern=r"^[A-Z]{3}$")
    
    # --- Market Data ---
    # Constraint: Volatility must be realistic (0% < vol <= 500%)
    volatility: float = Field(..., alias="Vol", gt=0, le=5.0)
    
    domestic_rate: float = Field(..., alias="RateDomestic")
    foreign_rate: float = Field(..., alias="RateForeign")
    
    # Constraint: Maturity must be realistic (0 < T <= 100 years)
    time_to_maturity: float = Field(..., alias="Expiry", gt=0, le=100.0)
    
    option_type: OptionType = Field(..., alias="OptionType")

    # --- Pydantic Config ---
    model_config = ConfigDict(populate_by_name=True)

    # --- Domain Logic Validators ---

    @model_validator(mode='after')
    def check_currency_consistency(self) -> 'FXOptionTrade':
        """
        Cross-Field Validation:
        Ensures the 'NotionalCurrency' matches either the Base or Quote currency of the Pair.
        """
        # 1. Check strict format first (should be covered by regex, but good to be safe)
        if '/' not in self.pair:
            return self

        base, quote = self.pair.split('/')

        # 2. Check Logic WITHOUT wrapping in a try-except block that swallows the error
        if self.notional_currency not in (base, quote):
            raise ValueError(
                f"Notional Currency '{self.notional_currency}' is invalid for Pair '{self.pair}'. "
                f"Must be either '{base}' or '{quote}'."
            )
            
        return self