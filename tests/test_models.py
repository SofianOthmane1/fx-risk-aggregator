"""
Unit tests for Data Validation in src/models.py.
Verifies Regex patterns, Range bounds, and Cross-Field logic.
"""
import pytest
from pydantic import ValidationError
from src.models import FXOptionTrade

# A baseline trade to start all tests with
VALID_DATA = {
    "TradeID": "T1",
    "Underlying": "EUR/USD",
    "Spot": 1.10,
    "Strike": 1.12,
    "Notional": 1000000,
    "NotionalCurrency": "USD",
    "Vol": 0.20,
    "RateDomestic": 0.02,
    "RateForeign": 0.01,
    "Expiry": 0.5,
    "OptionType": "Call"
}

def test_valid_trade_creation():
    """Test that a perfectly formatted row works."""
    trade = FXOptionTrade(**VALID_DATA)
    assert trade.trade_id == "T1"
    assert trade.pair == "EUR/USD"
    assert trade.volatility == 0.20

def test_invalid_pair_format():
    """Test Regex: Pair must be 'XXX/XXX'."""
    bad_data = VALID_DATA.copy()
    bad_data["Underlying"] = "EURUSD" # Missing slash
    
    with pytest.raises(ValidationError) as excinfo:
        FXOptionTrade(**bad_data)
    
    assert "pattern" in str(excinfo.value)

def test_invalid_volatility_range():
    """Test Range: Volatility must be > 0 and <= 5 (500%)."""
    # Case A: Zero Volatility (Should be blocked to protect math engine)
    bad_data_zero = VALID_DATA.copy()
    bad_data_zero["Vol"] = 0.0
    with pytest.raises(ValidationError):
        FXOptionTrade(**bad_data_zero)

    # Case B: Massive Volatility (e.g. 5.1 = 510%)
    bad_data_huge = VALID_DATA.copy()
    bad_data_huge["Vol"] = 5.1
    with pytest.raises(ValidationError):
        FXOptionTrade(**bad_data_huge)

def test_invalid_expiry_range():
    """Test Range: Expiry must be > 0."""
    bad_data = VALID_DATA.copy()
    bad_data["Expiry"] = 0.0 # Expired
    with pytest.raises(ValidationError):
        FXOptionTrade(**bad_data)

def test_cross_field_currency_mismatch():
    """
    Test Cross-Field Logic:
    If Pair is EUR/USD, Notional Currency CANNOT be GBP.
    """
    bad_data = VALID_DATA.copy()
    bad_data["Underlying"] = "EUR/USD"
    bad_data["NotionalCurrency"] = "GBP" # Mismatch!
    
    with pytest.raises(ValidationError) as excinfo:
        FXOptionTrade(**bad_data)
    
    # Assert the error message contains our custom logic
    assert "Notional Currency 'GBP' is invalid for Pair 'EUR/USD'" in str(excinfo.value)