# File: strategies/base_strategy.py

import pandas as pd
import logging

class BaseStrategy:
    """
    The fundamental structure for all strategies. It ensures that every 
    strategy has a consistent interface for initialization, logging, and 
    signal generation.
    """
    def __init__(self, df: pd.DataFrame, df_15min: pd.DataFrame = None, symbol: str = None, logger=None, **kwargs):
        """
        Initializes the base strategy.

        Args:
            df (pd.DataFrame): The primary DataFrame, which will be the raw 1-minute data.
            df_15min (pd.DataFrame, optional): Secondary timeframe data. Defaults to None.
            symbol (str, optional): The trading symbol. Defaults to None.
            logger (logging.Logger, optional): The logger instance. Defaults to None.
        """
        self.name = self.__class__.__name__
        self.symbol = symbol
        self.df = df # This will hold the aggregated dataframe
        self.df_1min_raw = df # This will always be the raw 1-min data
        self.logger = logger or logging.getLogger(__name__)

    def log(self, message, level='info'):
        """Helper method for logging."""
        if self.logger:
            if level == 'info':
                self.logger.info(f"[{self.name}][{self.symbol}] {message}")
            elif level == 'debug':
                self.logger.debug(f"[{self.name}][{self.symbol}] {message}")
            elif level == 'warning':
                self.logger.warning(f"[{self.name}][{self.symbol}] {message}")
            elif level == 'error':
                self.logger.error(f"[{self.name}][{self.symbol}] {message}")

    def calculate_indicators(self):
        """
        Placeholder for calculating technical indicators.
        Must be implemented by child strategies.
        """
        raise NotImplementedError("Each strategy must implement 'calculate_indicators'")

    def generate_signals(self):
        """
        Placeholder for generating trading signals.
        Must be implemented by child strategies.
        """
        raise NotImplementedError("Each strategy must implement 'generate_signals'")

    def run(self):
        """
        Executes the strategy's logic: calculates indicators and generates signals.
        Returns the DataFrame with signals.
        """
        self.calculate_indicators()
        self.generate_signals()
        return self.df