# File: database_manager.py
# Swing Trading Upgrade: open_positions table ko manage karne ke liye naye functions.

import sqlite3
import logging
import pandas as pd
import json # JSON ka istemal position details ko save karne ke liye

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_name="trading_data.db"):
        """
        Database Manager ko initialize karta hai aur sabhi zaroori tables banata hai.
        """
        self.db_name = db_name
        
        try:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            logger.info(f"✅ Successfully connected to database '{self.db_name}'.")
            self._create_tables()
        except sqlite3.Error as e:
            logger.error(f"❌ Database connection error: {e}")
            raise

    def _create_tables(self):
        """
        Zaroori tables (portfolio_state, trades, open_positions) banata hai.
        """
        cursor = self.conn.cursor()
        try:
            # Table 1: Har strategy ka financial state store karne ke liye
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_state (
                    strategy_name TEXT PRIMARY KEY,
                    initial_capital REAL NOT NULL,
                    trading_capital REAL NOT NULL,
                    banked_profit REAL NOT NULL,
                    total_charges REAL NOT NULL
                )
            """)
            
            # Table 2: Har trade ko log karne ke liye
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

            # --- NAYI TABLE: Open positions ko save karne ke liye ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS open_positions (
                    id TEXT PRIMARY KEY, -- "strategy_name:symbol" format
                    strategy_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    position_details TEXT NOT NULL -- Position dictionary ko JSON string ke roop mein save karein
                )
            """)

            self.conn.commit()
            logger.info("✅ Database tables verified/created successfully.")
        except sqlite3.Error as e:
            logger.error(f"❌ Error creating tables: {e}")
            self.conn.rollback()

    # --- NAYE FUNCTIONS ---

    def save_open_position(self, strategy_name, symbol, position_details):
        """Ek open position ko database mein save ya update karta hai."""
        position_id = f"{strategy_name}:{symbol}"
        details_json = json.dumps(position_details) # Dictionary ko JSON string mein convert karein
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO open_positions (id, strategy_name, symbol, position_details)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                    position_details=excluded.position_details
                """, (position_id, strategy_name, symbol, details_json))
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to save open position for {symbol}: {e}")

    def delete_open_position(self, strategy_name, symbol):
        """Ek open position ko database se delete karta hai jab woh close ho jaati hai."""
        position_id = f"{strategy_name}:{symbol}"
        try:
            with self.conn:
                self.conn.execute("DELETE FROM open_positions WHERE id = ?", (position_id,))
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to delete open position for {symbol}: {e}")

    def load_all_open_positions(self):
        """Engine start hone par sabhi open positions ko database se load karta hai."""
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT strategy_name, symbol, position_details FROM open_positions")
                rows = cursor.fetchall()
                positions = {}
                for row in rows:
                    strategy_name, symbol, details_json = row
                    if strategy_name not in positions:
                        positions[strategy_name] = {}
                    positions[strategy_name][symbol] = json.loads(details_json) # JSON string ko dictionary mein convert karein
                logger.info(f"Loaded {len(rows)} open position(s) from database.")
                return positions
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to load open positions: {e}")
            return {}

    # --- Purane functions waise hi rahenge ---
    def save_portfolio_state(self, strategy_name, initial_capital, trading_capital, banked_profit, total_charges):
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
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM portfolio_state")
                rows = cursor.fetchall()
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
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO trades (timestamp, strategy_name, symbol, action, price, quantity, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (timestamp.isoformat(), strategy_name, symbol, action, price, quantity, details))
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to log trade for {strategy_name}: {e}")
            
    def load_all_trades(self):
        try:
            df = pd.read_sql_query("SELECT * FROM trades", self.conn)
            return df
        except Exception as e:
            logger.error(f"❌ Failed to load trades from database: {e}")
            return pd.DataFrame()

    def close_connection(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
