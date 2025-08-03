# File: trade_logger.py
# Upgraded to log trades directly to the SQLite database.

from datetime import datetime
from database_manager import DatabaseManager # Import our new DatabaseManager

class TradeLogger:
    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the TradeLogger. It now requires a DatabaseManager instance.
        
        Args:
            db_manager (DatabaseManager): An active instance of the DatabaseManager.
        """
        self.db = db_manager

    def log_trade(self, date: datetime, strategy: str, symbol: str, action: str, price: float, qty: int, details: str):
        """
        Logs a single trade event by calling the database manager's log_trade method.
        """
        # The database manager handles all the logic for saving the trade.
        # This function just passes the data along.
        self.db.log_trade(
            timestamp=date,
            strategy_name=strategy,
            symbol=symbol,
            action=action.upper(),
            price=price,
            quantity=qty,
            details=details
        )