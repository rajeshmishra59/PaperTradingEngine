# File: portfolio_manager.py
# This class acts as the treasurer and risk manager for our trading system.

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, strategy_capital: dict, state_file='portfolio_state.json'):
        """
        Initializes the Portfolio Manager.

        Args:
            strategy_capital (dict): A dictionary mapping strategy names to their initial capital.
            state_file (str): The file to save and load the portfolio state.
        """
        self.strategy_capital_config = strategy_capital
        self.state_file = state_file
        self.cash = {}
        self.positions = {}  # Key: strategy_name, Value: {symbol: position_details}
        self._load_state()
        logger.info("✅ Portfolio Manager initialized.")
        self.log_portfolio_summary()

    def _load_state(self):
        """Loads the last saved state from the state file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.cash = state.get('cash', {})
                    self.positions = state.get('positions', {})
                # Ensure all configured strategies are in the cash dict
                for strategy_name in self.strategy_capital_config:
                    if strategy_name not in self.cash:
                        self.cash[strategy_name] = self.strategy_capital_config[strategy_name]
                logger.info(f"✅ Loaded portfolio state from '{self.state_file}'.")
            except Exception as e:
                logger.error(f"❌ Error loading state file, starting fresh. Error: {e}")
                self._start_fresh()
        else:
            logger.warning(f"No state file found. Starting with a fresh portfolio.")
            self._start_fresh()
    
    def _start_fresh(self):
        """Initializes a fresh portfolio based on config."""
        self.cash = self.strategy_capital_config.copy()
        self.positions = {strategy: {} for strategy in self.strategy_capital_config}
        self._save_state()

    def _save_state(self):
        """Saves the current state of cash and positions to the state file."""
        try:
            with open(self.state_file, 'w') as f:
                state = {'cash': self.cash, 'positions': self.positions}
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"❌ Could not save portfolio state! Error: {e}")

    def log_portfolio_summary(self):
        """Logs the current cash and open positions for each strategy."""
        logger.info("--- Portfolio Summary ---")
        for strategy_name in self.cash:
            cash_on_hand = self.cash.get(strategy_name, 0)
            open_positions = self.positions.get(strategy_name, {})
            logger.info(f"  > Strategy: {strategy_name} | Cash: ₹{cash_on_hand:,.2f} | Open Positions: {len(open_positions)}")
            for symbol, pos in open_positions.items():
                logger.info(f"    - {symbol}: {pos['action']} @ {pos['entry_price']} (Qty: {pos['quantity']})")
        logger.info("-------------------------")


    def get_open_position(self, strategy_name: str, symbol: str):
        """Returns the open position for a given strategy and symbol, or None."""
        return self.positions.get(strategy_name, {}).get(symbol)

    def record_trade(self, strategy_name: str, symbol: str, action: str, price: float, quantity: int, timestamp: datetime):
        """
        Records a new trade, updates cash, and adds the position.
        
        Returns:
            bool: True if the trade was recorded successfully, False otherwise.
        """
        trade_value = price * quantity
        
        # Risk Check: Does the strategy have enough cash?
        if self.cash.get(strategy_name, 0) < trade_value:
            logger.warning(f"REJECTED: Insufficient funds for {strategy_name} to {action} {symbol}. "
                           f"Required: {trade_value:.2f}, Available: {self.cash.get(strategy_name, 0):.2f}")
            return False

        # If already in a position, do not open another for the same strategy/symbol
        if self.get_open_position(strategy_name, symbol):
            logger.warning(f"REJECTED: {strategy_name} already has an open position for {symbol}.")
            return False

        self.cash[strategy_name] -= trade_value
        
        position_details = {
            'action': action.upper(),
            'entry_price': price,
            'quantity': quantity,
            'entry_time': timestamp.isoformat(),
            'symbol': symbol
        }
        
        if strategy_name not in self.positions:
            self.positions[strategy_name] = {}
        self.positions[strategy_name][symbol] = position_details
        
        self._save_state()
        logger.info(f"EXECUTED: {strategy_name} {action.upper()} {quantity} of {symbol} @ {price:.2f}")
        self.log_portfolio_summary()
        return True

    def close_position(self, strategy_name: str, symbol: str, closing_price: float, timestamp: datetime):
        """Closes an open position, updates cash, and calculates P&L."""
        open_position = self.get_open_position(strategy_name, symbol)
        
        if not open_position:
            logger.error(f"Error: Tried to close a position for {symbol} under {strategy_name}, but none exists.")
            return None

        # Add the value of the closing trade back to cash
        closing_value = closing_price * open_position['quantity']
        self.cash[strategy_name] += closing_value
        
        # Calculate P&L
        pnl = (closing_price - open_position['entry_price']) * open_position['quantity']
        if open_position['action'] == 'SHORT':
            pnl = -pnl # Reverse PnL for short trades
            
        # Remove the position from our records
        del self.positions[strategy_name][symbol]
        
        self._save_state()
        logger.info(f"CLOSED: {strategy_name} position for {symbol} at {closing_price:.2f}. P&L: ₹{pnl:,.2f}")
        self.log_portfolio_summary()
        return pnl