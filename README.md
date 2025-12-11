# FX Options Risk Aggregator

## Overview
A production-grade CLI tool designed to price, validate, and aggregate risk for a portfolio of **Foreign Exchange (FX) Options**.

It implements the **Garman-Kohlhagen model** (Black-Scholes for FX) to calculate **Present Value (PV)**, **Delta**, and **Vega**. The engine features "Smart Loading" to handle real-world data inconsistencies and strictly separates data validation from pricing logic.

## Key Features
- **Smart Data Loading:** Automatically detects input format. It attempts to read as binary Excel (`.xlsx`), and gracefully falls back to TSV/CSV text parsing if the file structure is incorrect.
- **Robust Validation:** Uses **Pydantic** with Regex patterns and cross-field logic (e.g., ensuring Notional Currency matches the Pair) to reject invalid trades before they reach the pricing engine.
- **Currency Normalization:** Automatically converts non-USD risks (e.g., JPY-denominated PV) into a standardized **USD Reporting Currency** for accurate portfolio aggregation.
- **Garman-Kohlhagen Pricing:** Correctly accounts for distinct domestic ($r_d$) and foreign ($r_f$) risk-free rates.
- **Detailed Reporting:** Generates a multi-tab Excel report including a dedicated "Rejected Trades" log for audit trails.

---

## Project Architecture

```text
fx_risk_aggregator/
├── data/                   # Input files and Output reports
├── src/
│   ├── __init__.py
│   ├── models.py           # Data Schemas & Validation Logic (The "Gatekeeper")
│   ├── pricing.py          # Math Engine (Garman-Kohlhagen & Normalization)
│   └── aggregator.py       # Portfolio summarization and grouping logic
├── tests/
│   ├── __init__.py
│   ├── test_models.py      # Tests for validation rules
│   ├── test_pricing.py     # Tests for math and currency conversion
│   └── test_aggregator.py  # Tests for summation logic
├── main.py                 # CLI Entry Point & Orchestrator
├── requirements.txt        # Project dependencies
└── README.md               # Documentation

---

## Setup and Installation

1. Prerequisites

Python 3.8+

2. Installation 

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt