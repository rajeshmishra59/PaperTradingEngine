# File: portfolio_manager.py (Final Version with Partial Exits)
import json, os, logging
from datetime import datetime
from charge_calculator import calculate_charges

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, db_manager, strategy_capital: dict):
        self.db = db_manager
        self.strategy_capital_config = strategy_capital
        self.cash, self.banked_profit, self.total_charges, self.initial_capital, self.positions = {}, {}, {}, {}, {}
        self._initialize_state()
        logger.info("✅ Portfolio Manager (Partial Exits) initialized.")
        self.log_portfolio_summary()

    def _initialize_state(self):
        state_from_db = self.db.load_full_portfolio_state()
        for strat_name, initial_cap in self.strategy_capital_config.items():
            if strat_name in state_from_db:
                self.initial_capital[strat_name], self.cash[strat_name], self.banked_profit[strat_name], self.total_charges[strat_name] = state_from_db[strat_name]['initial_capital'], state_from_db[strat_name]['trading_capital'], state_from_db[strat_name]['banked_profit'], state_from_db[strat_name]['total_charges']
            else:
                logger.warning(f"No state for '{strat_name}' in DB. Creating fresh record.")
                self.initial_capital[strat_name], self.cash[strat_name], self.banked_profit[strat_name], self.total_charges[strat_name] = initial_cap, initial_cap, 0.0, 0.0
                self.db.save_portfolio_state(strat_name, initial_cap, initial_cap, 0.0, 0.0)

    def _update_db_state(self, strategy_name):
        self.db.save_portfolio_state(strategy_name=strategy_name, initial_capital=self.initial_capital[strategy_name], trading_capital=self.cash[strategy_name], banked_profit=self.banked_profit[strategy_name], total_charges=self.total_charges[strategy_name])

    def record_trade(self, strategy_name: str, symbol: str, action: str, price: float, quantity: int, timestamp: datetime, 
                     stop_loss: float, targets: dict):
        entry_charges = calculate_charges(quantity, price)['total']
        total_cost = (price * quantity) + entry_charges
        if self.cash.get(strategy_name, 0) < total_cost: return False

        self.cash[strategy_name] -= total_cost
        self.total_charges[strategy_name] += entry_charges
        
        position_details = {
            'action': action.upper(), 'entry_price': price, 'original_quantity': quantity,
            'current_quantity': quantity, 'entry_time': timestamp.isoformat(), 
            'stop_loss': stop_loss, 'targets': targets, 'exited_targets': []
        }
        self.positions.setdefault(strategy_name, {})[symbol] = position_details
        self._update_db_state(strategy_name)
        logger.info(f"EXECUTED: {strategy_name} {action.upper()} {quantity} of {symbol} @ {price:.2f}")
        return True

    def _calculate_pnl(self, position, closing_price, quantity):
        entry_price = position['entry_price']
        charges = calculate_charges(quantity, entry_price)['total'] + calculate_charges(quantity, closing_price)['total']
        gross_pnl = (closing_price - entry_price) * quantity if position['action'] == 'LONG' else (entry_price - closing_price) * quantity
        net_pnl = gross_pnl - charges
        self.total_charges[position['strategy']] += charges
        return net_pnl

    def close_partial_position(self, strategy_name: str, symbol: str, closing_price: float, quantity_to_close: int, target_level: str, timestamp: datetime):
        open_position = self.get_open_position(strategy_name, symbol)
        if not open_position or quantity_to_close == 0: return None
        open_position['current_quantity'] -= quantity_to_close
        net_pnl = self._calculate_pnl(open_position, closing_price, quantity_to_close)
        self.cash[strategy_name] += closing_price * quantity_to_close + net_pnl
        open_position['exited_targets'].append(target_level)
        self._update_db_state(strategy_name)
        logger.info(f"PARTIAL EXIT ({target_level}): Closed {quantity_to_close} of {symbol}. P&L: ₹{net_pnl:,.2f}")
        self.log_portfolio_summary()
        return net_pnl

    def close_full_position(self, strategy_name: str, symbol: str, closing_price: float, timestamp: datetime):
        open_position = self.get_open_position(strategy_name, symbol)
        if not open_position: return None
        remaining_quantity = open_position['current_quantity']
        net_pnl = self._calculate_pnl(open_position, closing_price, remaining_quantity)
        self.cash[strategy_name] += closing_price * remaining_quantity
        if net_pnl > 0:
            self.banked_profit[strategy_name] += net_pnl * 0.5
            self.cash[strategy_name] = self.initial_capital[strategy_name] + (net_pnl * 0.5)
        else:
            self.banked_profit[strategy_name] += net_pnl
            self.cash[strategy_name] = self.initial_capital[strategy_name]
        del self.positions[strategy_name][symbol]
        self._update_db_state(strategy_name)
        logger.info(f"FULL EXIT: Closed remaining {remaining_quantity} of {symbol}. P&L: ₹{net_pnl:,.2f}")
        self.log_portfolio_summary()
        return net_pnl

    def get_open_position(self, strategy_name: str, symbol: str):
        return self.positions.get(strategy_name, {}).get(symbol)
        
    def log_portfolio_summary(self):
        logger.info("--- Portfolio Summary ---")
        for s_name in self.strategy_capital_config:
            logger.info(f"  > {s_name} | Trading Capital: ₹{self.cash.get(s_name, 0):,.2f} | Banked Profit: ₹{self.banked_profit.get(s_name, 0):,.2f}")