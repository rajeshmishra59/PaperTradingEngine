# File: trade_logger.py

import csv
from datetime import datetime
import os # Ensure os is imported

class TradeLogger:
    def __init__(self, filename="trade_log.csv"):
        """
        Initializes the TradeLogger.
        
        Args:
            filename (str): The name of the CSV file to log trades to.
        """
        self.filename = filename
        self._init_log()

    def _init_log(self):
        """
        Initializes the log file with headers if it doesn't exist.
        """
        # Create the directory if it doesn't exist
        log_dir = os.path.dirname(self.filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Check if file exists to avoid overwriting headers
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                # File exists, do nothing
                pass
        except FileNotFoundError:
            # File doesn't exist, create it and write headers
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Strategy", "Symbol", "Action", 
                    "Price", "Quantity", "Details"
                ])

    def log_trade(self, date: datetime, strategy: str, symbol: str, action: str, price: float, qty: int, details: str):
        """
        Logs a single trade event to the CSV file.
        """
        if not isinstance(date, datetime):
            date = datetime.now()
            
        row = [
            date.strftime("%Y-%m-%d %H:%M:%S"), 
            strategy, 
            symbol, 
            action.upper(), 
            f"{price:.2f}", 
            qty, 
            details
        ]
        
        try:
            with open(self.filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            # In a real system, you'd want a more robust logger here
            print(f"CRITICAL: Could not write to trade log! Error: {e}")