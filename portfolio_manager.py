# File: portfolio_manager.py (Version 1.8 - Final)

import json
import os
import logging
from datetime import datetime
from charge_calculator import calculate_charges

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, strategy_capital: dict, state_file='portfolio_state.json'):
        self.strategy_capital_config = strategy_capital
        self.state_file = state_file
        self.cash, self.positions, self.banked_profit, self.total_charges, self.initial_capital = {}, {}, {}, {}, {}
        self._load_state()
        logger.info("✅ Portfolio Manager (v1.8) initialized.")
        self.log_portfolio_summary()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.cash = state.get('cash', self.strategy_capital_config.copy())
                self.positions = state.get('positions', {})
                self.banked_profit = state.get('banked_profit', {s: 0 for s in self.strategy_capital_config})
                self.total_charges = state.get('total_charges', {s: 0 for s in self.strategy_capital_config})
                self.initial_capital = state.get('initial_capital', self.strategy_capital_config.copy())
            except Exception: self._start_fresh()
        else: self._start_fresh()
    
    def _start_fresh(self):
        logger.warning("Starting with a fresh portfolio state.")
        self.cash = self.strategy_capital_config.copy()
        self.initial_capital = self.strategy_capital_config.copy()
        self.positions = {s: {} for s in self.strategy_capital_config}
        self.banked_profit = {s: 0 for s in self.strategy_capital_config}
        self.total_charges = {s: 0 for s in self.strategy_capital_config}
        self._save_state()

    def _save_state(self):
        try:
            state = {'cash': self.cash, 'positions': self.positions, 'banked_profit': self.banked_profit, 'total_charges': self.total_charges, 'initial_capital': self.initial_capital}
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"❌ Could not save portfolio state! Error: {e}")
            
    def record_trade(self, strategy_name: str, symbol: str, action: str, price: float, quantity: int, timestamp: datetime):
        entry_charges = calculate_charges(quantity, price)['total']
        total_cost = (price * quantity) + entry_charges
        if self.cash.get(strategy_name, 0) < total_cost: return False
        self.cash[strategy_name] -= total_cost
        self.total_charges.setdefault(strategy_name, 0)
        self.total_charges[strategy_name] += entry_charges
        position_details = {'action': action.upper(), 'entry_price': price, 'quantity': quantity, 'entry_time': timestamp.isoformat()}
        self.positions.setdefault(strategy_name, {})[symbol] = position_details
        self._save_state()
        logger.info(f"EXECUTED: {strategy_name} {action.upper()} {quantity} of {symbol} @ {price:.2f}")
        return True

    def close_position(self, strategy_name: str, symbol: str, closing_price: float, timestamp: datetime):
        open_position = self.get_open_position(strategy_name, symbol)
        if not open_position: return None
        entry_price, quantity = open_position['entry_price'], open_position['quantity']
        entry_value, closing_value = entry_price * quantity, closing_price * quantity
        entry_charges = calculate_charges(quantity, entry_price)['total']
        exit_charges = calculate_charges(quantity, closing_price)['total']
        total_trade_charges = entry_charges + exit_charges
        gross_pnl = (closing_value - entry_value) if open_position['action'] == 'LONG' else (entry_value - closing_value)
        net_pnl = gross_pnl - total_trade_charges
        self.total_charges[strategy_name] += exit_charges
        initial_cap = self.initial_capital.get(strategy_name, 0)
        self.cash[strategy_name] += closing_value
        if net_pnl > 0:
            profit_to_reinvest, profit_to_bank = net_pnl * 0.50, net_pnl * 0.50
            self.banked_profit.setdefault(strategy_name, 0)
            self.banked_profit[strategy_name] += profit_to_bank
            self.cash[strategy_name] = initial_cap + profit_to_reinvest
        else:
            self.banked_profit.setdefault(strategy_name, 0)
            self.banked_profit[strategy_name] += net_pnl
            self.cash[strategy_name] = initial_cap
        del self.positions[strategy_name][symbol]
        self._save_state()
        logger.info(f"CLOSED: {strategy_name} for {symbol}. Net P&L: ₹{net_pnl:,.2f}")
        self.log_portfolio_summary()
        return net_pnl

    def get_open_position(self, strategy_name: str, symbol: str):
        return self.positions.get(strategy_name, {}).get(symbol)
        
    def log_portfolio_summary(self):
        logger.info("--- Portfolio Summary ---")
        for s_name in self.strategy_capital_config:
            logger.info(f"  > {s_name} | Trading Capital: ₹{self.cash.get(s_name, 0):,.2f} | Banked Profit: ₹{self.banked_profit.get(s_name, 0):,.2f}")