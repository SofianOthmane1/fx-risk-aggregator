# FX Options Risk Aggregator

## 1. Overview

This project implements the case study **FX Options Risk Aggregator** application, designed to price, validate, and aggregate risk for a portfolio of **Foreign Exchange (FX) options**.

The system uses the **Garman–Kohlhagen model** (the FX extension of Black–Scholes) to compute:

- **Present Value (PV)**
- **Delta**
- **Vega**

The overview and focus of my implementation is:
- strict input validation using Pydantic,
- clean separation of modules,
- transparent currency normalization,
- strong risk engine,
- and auditable output reporting.

The result is a small risk engine that resembles how FX options risk could be handled in a real trading or risk environment.

---

## 2. Key Features

- **Smart Data Loading**  
  Automatically attempts to load input as a binary Excel file (`.xlsx`).  
  If that fails, it will fall back to CSV/TSV parsing to handle real-world data inconsistencies.

- **Strict Data Validation**  
  Uses **Pydantic** with:
  - Regex validation (e.g. FX pair format),
  - Range checks (e.g. volatility, maturity),
  - Cross-field logic (e.g. notional currency must match the FX pair).  
  Invalid trades are rejected *before* reaching the pricing engine.

- **Garman–Kohlhagen Pricing**  
  Correctly accounts for distinct:
  - Domestic risk-free rate $r_d$,
  - Foreign risk-free rate $r_f$.

- **Currency Normalization**  
  All risk metrics are normalized into a **USD reporting currency**, ensuring portfolio aggregation is consistent.

- **Detailed Excel Reporting**  
  Produces a multi-tab Excel report including:
  - Trade-level results,
  - Portfolio-level summary,
  - Risk grouped by FX pair,
  - Risk grouped by currency,
  - A **Rejected Trades** audit log.

---

## 3. Project Architecture

```
fx_risk_aggregator/
├── data/                   # Input files and generated output reports
├── src/
│   ├── __init__.py
│   ├── models.py           # Data schemas & validation logic
│   ├── pricing.py          # Garman–Kohlhagen pricing & normalisation
│   └── aggregator.py       # Portfolio aggregation and grouping logic
├── tests/
│   ├── __init__.py
│   ├── test_models.py      # Validation and schema tests
│   ├── test_pricing.py     # Pricing and FX-normalization tests
│   └── test_aggregator.py  # Portfolio aggregation tests
├── main.py                 # CLI entry point & orchestration
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 4. Setup and Installation

### Prerequisites

- **Python 3.8+**
- A terminal environment (macOS, Linux, or Windows PowerShell)

### Installation Steps

```bash
# If you want to create and activate virtual environment like I did:
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt
```

### Core Dependencies

- pandas
- numpy
- scipy
- pydantic
- openpyxl
- pytest

---

## 5. Running the Application

### Default Execution

```bash
python main.py
```

By default, the program:
- Reads from `data/fx_trades__1_.xlsx`
- Writes to `data/processed_risk_report.xlsx`

### Custom Input / Output Paths

```bash
python main.py --input data/my_trades.xlsx --output reports/risk_report.xlsx
```

---

## 6. Pricing Model: Garman–Kohlhagen

The Garman–Kohlhagen model extends Black–Scholes to FX by incorporating both domestic and foreign interest rates.

### Model Inputs

- $S$ — Spot FX rate
- $K$ — Strike
- $T$ — Time to maturity (years)
- $\sigma$ — Volatility
- $r_d$ — Domestic risk-free rate
- $r_f$ — Foreign risk-free rate

### Core Quantities

$$d_1 = \frac{\ln(S/K) + (r_d - r_f + \frac{1}{2}\sigma^2)T}{\sigma\sqrt{T}}$$

$$d_2 = d_1 - \sigma\sqrt{T}$$

### Option Values

**Call Option:**

$$PV = Se^{-r_f T}N(d_1) - Ke^{-r_d T}N(d_2)$$

**Put Option:**

$$PV = Ke^{-r_d T}N(-d_2) - Se^{-r_f T}N(-d_1)$$

### Greeks

**Delta (Call):**

$$\Delta = e^{-r_f T}N(d_1)$$

**Delta (Put):**

$$\Delta = e^{-r_f T}(N(d_1) - 1)$$

**Vega:**

$$\text{Vega} = Se^{-r_f T}\phi(d_1)\sqrt{T}$$

All values are scaled by the trade notional.

---

## 7. Validation Rules & Assumptions

### Validation Rules

Trades are rejected if:

- FX pair does not match `XXX/YYY` format,
- Volatility $\leq 0$ or unreasonably large,
- Time to maturity $\leq 0$,
- Spot, strike, or notional are non-positive,
- Notional currency does not match either base or quote currency.

Rejected trades are logged explicitly in the output report.

### Modelling Assumptions

- Flat volatility per trade (no smile or surface),
- Continuous compounding of interest rates,
- No transaction costs,
- USD is the reporting currency,
- Pricing engine receives only validated inputs.

---

## 8. Output Report Structure

The generated Excel file contains the following sheets:

- **Trade Level:** Detailed per-trade PV and Greeks (native and USD).
- **Portfolio Summary:** Total PV, Delta, and Vega (USD).
- **Risk by Pair:** Aggregated risk grouped by FX pair.
- **Risk by Currency:** Aggregated risk grouped by quote currency.

---

## 9. Testing

The project includes a full pytest test suite.

### Run All Tests

```bash
pytest
```

### Test Coverage

- **test_models.py:** Validates regex rules, ranges, and cross-field consistency.
- **test_pricing.py:** Verifies pricing behavior, Greeks, and FX normalization.
- **test_aggregator.py:** Ensures aggregation uses USD metrics and ignores invalid trades.