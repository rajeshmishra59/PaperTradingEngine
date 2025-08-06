# File: portfolio_manager.py
# Final Corrected Version with all fixes

import logging
from datetime import datetime
from typing import Optional
from database_manager import DatabaseManager
from charge_calculator import calculate_charges

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, db_manager: DatabaseManager, strategy_capital: dict):
        self.db = db_manager
        self.strategy_capital_config = strategy_capital
        
        self.cash = {}
        self.banked_profit = {}
        self.total_charges = {}
        self.initial_capital = {}
        self.positions = {}
        
        self._initialize_state()
        logger.info("✅ Portfolio Manager (DB version) initialized.")
        self.log_portfolio_summary()

    def _initialize_state(self):
        state_from_db = self.db.load_full_portfolio_state()
        
        for strat_name, initial_cap in self.strategy_capital_config.items():
            if strat_name in state_from_db:
                self.initial_capital[strat_name] = state_from_db[strat_name]['initial_capital']
                self.cash[strat_name] = state_from_db[strat_name]['trading_capital']
                self.banked_profit[strat_name] = state_from_db[strat_name]['banked_profit']
                self.total_charges[strat_name] = state_from_db[strat_name]['total_charges']
            else:
                logger.warning(f"No state found for '{strat_name}' in DB. Creating fresh record.")
                self.initial_capital[strat_name] = initial_cap
                self.cash[strat_name] = initial_cap
                self.banked_profit[strat_name] = 0.0
                self.total_charges[strat_name] = 0.0
                self.db.save_portfolio_state(strat_name, initial_cap, initial_cap, 0.0, 0.0)

    def _update_db_state(self, strategy_name):
        self.db.save_portfolio_state(
            strategy_name=strategy_name,
            initial_capital=self.initial_capital[strategy_name],
            trading_capital=self.cash[strategy_name],
            banked_profit=self.banked_profit[strategy_name],
            total_charges=self.total_charges[strategy_name]
        )

    # --- SAHI LOGIC WALA FUNCTION ---
    def record_trade(self, strategy_name: str, symbol: str, action: str, price: float, quantity: int, timestamp: datetime, 
                     stop_loss: float, target: float, trailing_sl_pct: float = 0.0):
        entry_charges = calculate_charges(quantity, price, is_intraday=True)['total']
        total_cost = (price * quantity) + entry_charges
        
        if self.cash.get(strategy_name, 0) < total_cost:
            logger.warning(f"REJECTED: Insufficient funds for {strategy_name}.")
            return False

        if self.get_open_position(strategy_name, symbol):
            logger.warning(f"REJECTED: {strategy_name} already has a position for {symbol}.")
            return False

        # Cash se poori laagat (cost) kam karein
        self.cash[strategy_name] -= total_cost
        
        # --- YAHAN PAR BUG FIX KIYA GAYA HAI ---
        # Entry charges ko total charges me record karein
        self.total_charges[strategy_name] += entry_charges
        # --- END OF FIX ---
        
        position_details = {
            'action': action.upper(), 'entry_price': price, 'quantity': quantity,
            'entry_time': timestamp.isoformat(), 'stop_loss': stop_loss, 'target': target,
            'trailing_sl_pct': trailing_sl_pct,
            'highest_price_since_entry': price if action.upper() == 'LONG' else 0,
            'lowest_price_since_entry': price if action.upper() == 'SHORT' else 999999,
        }
        self.positions.setdefault(strategy_name, {})[symbol] = position_details
        
        self._update_db_state(strategy_name)
        logger.info(f"EXECUTED: {strategy_name} {action.upper()} {quantity} of {symbol} @ {price:.2f}")
        return True

    def close_position(self, strategy_name: str, symbol: str, closing_price: float, timestamp: datetime):
        open_position = self.get_open_position(strategy_name, symbol)
        if not open_position: return None

        entry_price = open_position['entry_price']
        quantity = open_position['quantity']
        
        entry_value = entry_price * quantity
        closing_value = closing_price * quantity
        entry_charges = calculate_charges(quantity, entry_price, is_intraday=True)['total']
        exit_charges = calculate_charges(quantity, closing_price, is_intraday=True)['total']
        total_trade_charges = entry_charges + exit_charges
        gross_pnl = (closing_value - entry_value) if open_position['action'] == 'LONG' else (entry_value - closing_value)
        net_pnl = gross_pnl - total_trade_charges

        self.cash[strategy_name] += (closing_value - exit_charges)
        self.total_charges[strategy_name] += exit_charges

        initial_cap = self.initial_capital.get(strategy_name, 0)
        
        if net_pnl > 0:
            profit_to_bank = net_pnl * 0.50
            self.cash[strategy_name] -= profit_to_bank
            self.banked_profit[strategy_name] += net_pnl
            logger.info(f"PROFIT: Moved ₹{profit_to_bank:,.2f} to bank for {strategy_name}.")
        else:
            self.banked_profit[strategy_name] += net_pnl
            
            if self.cash[strategy_name] < initial_cap:
                shortfall = initial_cap - self.cash[strategy_name]
                available_bank_funds = max(0, self.banked_profit[strategy_name] - net_pnl)
                refill_amount = min(shortfall, available_bank_funds)
                
                if refill_amount > 0:
                    self.cash[strategy_name] += refill_amount
                    self.banked_profit[strategy_name] -= refill_amount
                    logger.info(f"REFILL: Moved ₹{refill_amount:,.2f} from bank to capital for {strategy_name}.")

        del self.positions[strategy_name][symbol]
        self._update_db_state(strategy_name)
        logger.info(f"CLOSED: {strategy_name} position for {symbol}. Net P&L: ₹{net_pnl:,.2f}")
        self.log_portfolio_summary()
        return net_pnl

    def update_position_price_and_sl(self, strategy_name: str, symbol: str, current_price: float):
        position = self.get_open_position(strategy_name, symbol)
        if not position or position.get('trailing_sl_pct', 0) == 0: return

        original_sl = position['stop_loss']
        new_sl = original_sl

        if position['action'] == 'LONG':
            position['highest_price_since_entry'] = max(position.get('highest_price_since_entry', 0), current_price)
            trailing_stop_price = position['highest_price_since_entry'] * (1 - position['trailing_sl_pct'] / 100)
            new_sl = max(original_sl, trailing_stop_price)
        elif position['action'] == 'SHORT':
            position['lowest_price_since_entry'] = min(position.get('lowest_price_since_entry', 999999), current_price)
            trailing_stop_price = position['lowest_price_since_entry'] * (1 + position['trailing_sl_pct'] / 100)
            new_sl = min(original_sl, trailing_stop_price)

        if new_sl != original_sl:
            position['stop_loss'] = new_sl
            logger.info(f"TSL UPDATE for {symbol}: Stop-loss trailed to ₹{new_sl:,.2f}")
            self._update_db_state(strategy_name)

    def get_open_position(self, strategy_name: str, symbol: str):
        return self.positions.get(strategy_name, {}).get(symbol)
        
    def log_portfolio_summary(self):
        logger.info("--- Portfolio Summary ---")
        for s_name in self.strategy_capital_config:
            logger.info(f"  > {s_name} | Trading Capital: ₹{self.cash.get(s_name, 0):,.2f} | Banked Profit: ₹{self.banked_profit.get(s_name, 0):,.2f}")
