# File: database_manager.py
# Manages all interactions with the SQLite database.

import sqlite3
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_name="trading_data.db"):
        """
        Initializes the Database Manager and ensures all necessary tables exist.
        """
        self.db_name = db_name
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            logger.info(f"✅ Successfully connected to database '{self.db_name}'.")
            self._create_tables()
        except sqlite3.Error as e:
            logger.error(f"❌ Database connection error: {e}")
            raise

    def _create_tables(self):
        """
        Creates the 'portfolio_state' and 'trades' tables if they don't already exist.
        """
        cursor = self.conn.cursor()
        try:
            # Table to store portfolio state for each strategy
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_state (
                    strategy_name TEXT PRIMARY KEY,
                    initial_capital REAL NOT NULL,
                    trading_capital REAL NOT NULL,
                    banked_profit REAL NOT NULL,
                    total_charges REAL NOT NULL
                )
            """)
            
            # Table to log every single trade
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    details TEXT
                )
            """)
            self.conn.commit()
            logger.info("✅ Database tables verified/created successfully.")
        except sqlite3.Error as e:
            logger.error(f"❌ Error creating tables: {e}")
            self.conn.rollback()

    def save_portfolio_state(self, strategy_name, initial_capital, trading_capital, banked_profit, total_charges):
        """
        Saves or updates the financial state for a single strategy.
        """
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO portfolio_state (strategy_name, initial_capital, trading_capital, banked_profit, total_charges)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(strategy_name) DO UPDATE SET
                    trading_capital=excluded.trading_capital,
                    banked_profit=excluded.banked_profit,
                    total_charges=excluded.total_charges
                """, (strategy_name, initial_capital, trading_capital, banked_profit, total_charges))
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to save portfolio state for {strategy_name}: {e}")

    def load_full_portfolio_state(self):
        """
        Loads the complete financial state for all strategies from the database.
        Returns a dictionary.
        """
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM portfolio_state")
                rows = cursor.fetchall()
                # Convert list of tuples to a nested dictionary for easy access
                state = {
                    row[0]: {
                        'initial_capital': row[1],
                        'trading_capital': row[2],
                        'banked_profit': row[3],
                        'total_charges': row[4]
                    } for row in rows
                }
                return state
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to load portfolio state: {e}")
            return {}

    def log_trade(self, timestamp, strategy_name, symbol, action, price, quantity, details):
        """
        Inserts a new trade record into the 'trades' table.
        """
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO trades (timestamp, strategy_name, symbol, action, price, quantity, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (timestamp.isoformat(), strategy_name, symbol, action, price, quantity, details))
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to log trade for {strategy_name}: {e}")
            
    def load_all_trades(self):
        """
        Loads all trades from the 'trades' table into a pandas DataFrame.
        """
        try:
            df = pd.read_sql_query("SELECT * FROM trades", self.conn)
            return df
        except Exception as e:
            logger.error(f"❌ Failed to load trades from database: {e}")
            return pd.DataFrame()

    def close_connection(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")