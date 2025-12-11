"""
main.py

Features:
- CLI Arguments: Use --input and --output to specify file directories.
- Reporting: Exports Valid Trades, Risk Summaries (USD), and Rejected Trades.
"""

import argparse
import logging
import pandas as pd
import sys
from pathlib import Path
from pydantic import ValidationError

# Import the modular components
from src.models import FXOptionTrade
from src.pricing import BlackScholesFX
from src.aggregator import PortfolioAggregator

# --- CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("FXRiskEngine")

def parse_arguments():
    """
    Defines command-line arguments.
    """
    parser = argparse.ArgumentParser(description="FX Options Risk Aggregator")
    
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/fx_trades__1_.xlsx",
        help="Path to the input Excel file"
    )
    
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed_risk_report.xlsx", 
        help="Path to save the output report"
    )
    
    return parser.parse_args()

def run_risk_engine():
    # 1. Setup Environment
    args = parse_arguments()
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    logger.info("Starting Risk Engine...")
    logger.info(f"Input File:  {input_path}")
    logger.info(f"Output File: {output_path}")

    # 2. Smart Data Loading (Excel -> Fallback to CSV)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        # Attempt 1: Try reading as a standard Excel file
        df_raw = pd.read_excel(input_path, engine='openpyxl')
        logger.info(f"Successfully loaded {len(df_raw)} rows from Excel binary.")
        
    except Exception:
        logger.warning("File is not a binary Excel file. Attempting fallback to Text/TSV parser...")
        
        try:
            # Attempt 2: Read as a Tab-Separated text file (handling '1,000' format)
            df_raw = pd.read_csv(input_path, sep='\t', thousands=',')
            logger.info(f"Successfully loaded {len(df_raw)} rows from Text/TSV.")
            
        except Exception as e_csv:
            logger.critical(f"CRITICAL: Failed to load file. It is neither valid Excel nor valid CSV: {e_csv}")
            sys.exit(1)

    # Containers for results
    valid_results = []
    rejected_trades = []

    # 3. Process Loop
    logger.info("Processing trades...")
    
    for index, row in df_raw.iterrows():
        # Convert row to dictionary for easier handling
        row_dict = row.to_dict()
        
        # Fallback ID for logging if TradeID is missing
        trade_id = row_dict.get("TradeID", f"Row_{index}") 

        try:
            # A. VALIDATION 
            # This raises ValidationError if data is invalid (e.g. Vol=0, Mismatch Currency)
            trade_obj = FXOptionTrade(**row_dict)

            # B. PRICING (The Engine)
            # Calculates metrics AND converts them to USD
            metrics = BlackScholesFX.calculate_metrics(trade_obj, reporting_currency="USD")

            # C. SUCCESS RECORD
            valid_results.append({
                "TradeID": trade_obj.trade_id,
                "Pair": trade_obj.pair,
                "Type": trade_obj.option_type.value,
                "Notional": trade_obj.notional,
                "Currency": metrics["Currency"],
                
                # Native Metrics 
                "PV_Native": metrics["PV_Native"],
                "Delta_Native": metrics["Delta_Native"],
                "Vega_Native": metrics["Vega_Native"],
                
                # Normalized Metrics (For Aggregation)
                "PV_USD": metrics["PV_USD"],
                "Delta_USD": metrics["Delta_USD"],
                "Vega_USD": metrics["Vega_USD"],
                
                "Status": "Success"
            })

        except ValidationError as e:
            # Data Validation Failure (Schema issues)
            error_msg = str(e).replace('\n', '; ')
            logger.warning(f"Trade {trade_id} REJECTED (Validation): {error_msg}")
            
            row_dict["Error"] = f"Validation: {error_msg}"
            rejected_trades.append(row_dict)

        except ValueError as e:
            # Math/Domain Failure (e.g. T=0 if not caught by validator)
            logger.warning(f"Trade {trade_id} REJECTED (Pricing): {e}")
            
            row_dict["Error"] = f"Pricing: {e}"
            rejected_trades.append(row_dict)

        except Exception as e:
            # Catch-all for unexpected system bugs
            logger.error(f"Trade {trade_id} CRASHED: {e}")
            
            row_dict["Error"] = f"System Error: {e}"
            rejected_trades.append(row_dict)

    # 4. Aggregation
    logger.info(f"Aggregation: {len(valid_results)} Valid, {len(rejected_trades)} Rejected.")
    
    # Generate DataFrames using our Aggregator Class
    df_trades = PortfolioAggregator.prepare_trade_report(valid_results)
    
    # These methods now strictly look for '_USD' columns
    df_summary = PortfolioAggregator.calculate_portfolio_totals(df_trades)
    df_by_pair = PortfolioAggregator.group_risk_by_pair(df_trades)
    df_by_ccy = PortfolioAggregator.group_risk_by_currency(df_trades)
    
    df_rejected = pd.DataFrame(rejected_trades)

    # 5. Export
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            if not df_trades.empty:
                df_trades.to_excel(writer, sheet_name="Trade Level", index=False)
                df_summary.to_excel(writer, sheet_name="Portfolio Summary", index=False)
                df_by_pair.to_excel(writer, sheet_name="Risk by Pair", index=False)
                df_by_ccy.to_excel(writer, sheet_name="Risk by Currency", index=False)
            else:
                logger.warning("No valid trades to report.")

            if not df_rejected.empty:
                df_rejected.to_excel(writer, sheet_name="Rejected Trades", index=False)

        logger.info(f"Report saved successfully to: {output_path}")

    except Exception as e:
        logger.critical(f"Failed to save output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_risk_engine()