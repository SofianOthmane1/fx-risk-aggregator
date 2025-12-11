"""
Unit tests for the Black-Scholes Math Engine.
Verifies pricing logic, Greeks, and Currency Normalization.
"""
import pytest
from pydantic import ValidationError
from src.models import FXOptionTrade
from src.pricing import BlackScholesFX

# Reuse the standard data structure
EURUSD_DATA = {
    "TradeID": "TEST_EUR",
    "Underlying": "EUR/USD",
    "Spot": 1.10,
    "Strike": 1.10,
    "Notional": 1_000_000,
    "NotionalCurrency": "USD",
    "Vol": 0.20,
    "RateDomestic": 0.05,
    "RateForeign": 0.02,
    "Expiry": 1.0,
    "OptionType": "Call"
}

# JPY Data for currency tests
JPY_DATA = {
    "TradeID": "TEST_JPY",
    "Underlying": "USD/JPY",
    "Spot": 100.0,
    "Strike": 100.0,
    "Notional": 100_000_000,
    "NotionalCurrency": "JPY",
    "Vol": 0.10,
    "RateDomestic": 0.01,
    "RateForeign": 0.05,
    "Expiry": 0.5,
    "OptionType": "Call"
}

def test_standard_eurusd_pricing():
    """Test standard Garman-Kohlhagen pricing and consistency."""
    trade = FXOptionTrade(**EURUSD_DATA)
    metrics = BlackScholesFX.calculate_metrics(trade, reporting_currency="USD")
    
    # Logic Checks
    assert metrics["PV_Native"] > 0
    # Delta check (approx 0.5 for ATM Call)
    assert 0.4 < metrics["Delta_Native"] / trade.notional < 0.7
    
    # Currency Logic Check
    assert metrics["PV_USD"] == pytest.approx(metrics["PV_Native"])
    assert metrics["Currency"] == "USD"

def test_jpy_currency_conversion():
    """Test USD/JPY conversion logic (Native JPY -> USD Report)."""
    trade = FXOptionTrade(**JPY_DATA)
    metrics = BlackScholesFX.calculate_metrics(trade, reporting_currency="USD")
    
    pv_native = metrics["PV_Native"]
    pv_usd = metrics["PV_USD"]
    spot = trade.spot_price
    
    # Logic: 100 JPY (Native) / 100 (Spot) = 1 USD
    expected_usd = pv_native / spot
    assert pv_usd == pytest.approx(expected_usd, rel=1e-5)
    assert metrics["Currency"] == "JPY"

def test_validation_blocks_bad_math_inputs():
    """
    Verify that invalid inputs (Vol=0, Expiry=0) are blocked by the 
    Schema (Pydantic) BEFORE reaching the pricing engine.
    """
    # Case 1: Zero Volatility
    bad_vol_data = EURUSD_DATA.copy()
    bad_vol_data["Vol"] = 0.0
    
    with pytest.raises(ValidationError):
        FXOptionTrade(**bad_vol_data)

    # Case 2: Expired Trade (T=0)
    bad_expiry_data = EURUSD_DATA.copy()
    bad_expiry_data["Expiry"] = 0.0
    
    with pytest.raises(ValidationError):
        FXOptionTrade(**bad_expiry_data)