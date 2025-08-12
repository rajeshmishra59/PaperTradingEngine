# File: strategies/base_strategy.py (Final Production Version)

import pandas as pd
import logging
from typing import Optional

class BaseStrategy:
    """
    The fundamental structure for all strategies. It ensures that every 
    strategy has a consistent interface for initialization, logging, and 
    signal generation.
    """
    def __init__(self, df: pd.DataFrame, symbol: Optional[str] = None, logger=None, 
                 primary_timeframe: Optional[int] = None, **kwargs):
        """
        Initializes the base strategy.

        Args:
            df (pd.DataFrame): The primary DataFrame, which must be the raw 1-minute data.
            symbol (Optional[str], optional): The trading symbol. Defaults to None.
            logger (logging.Logger, optional): The logger instance. Defaults to None.
            primary_timeframe (Optional[int], optional): The main timeframe for the strategy (e.g., 5 for 5-min).
        """
        self.name = self.__class__.__name__
        self.symbol = symbol
        self.primary_timeframe = primary_timeframe
        
        # This will always hold the raw 1-min data passed during initialization
        self.df_1min_raw = df 
        
        # This will hold the resampled, strategy-specific timeframe data (e.g., 5-min)
        # It's initialized as empty and populated by calculate_indicators()
        self.df = pd.DataFrame() 
        
        self.logger = logger or logging.getLogger(__name__)

    def log(self, message: str, level: str = 'info'):
        """Helper method for structured logging."""
        if self.logger:
            # Safely get the logging function (e.g., logger.info, logger.warning)
            log_func = getattr(self.logger, level, self.logger.info)
            log_func(f"[{self.name}][{self.symbol}] {message}")

    def calculate_indicators(self):
        """
        Resamples data and calculates technical indicators.
        Must be implemented by child strategies.
        This method is responsible for populating `self.df`.
        """
        raise NotImplementedError(f"'calculate_indicators' must be implemented in {self.name}")

    def generate_signals(self):
        """
        Generates trading signals based on calculated indicators.
        Must be implemented by child strategies.
        """
        raise NotImplementedError(f"'generate_signals' must be implemented in {self.name}")

    def run(self) -> pd.DataFrame:
        """
        Executes the full strategy logic: calculates indicators and generates signals.
        Returns the DataFrame with signals.
        """
        self.calculate_indicators()
        # Only generate signals if the indicators were calculated successfully
        if not self.df.empty:
            self.generate_signals()
        return self.df