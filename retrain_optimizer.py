# retrain_optimizer.py
# FINAL PROFESSIONAL VERSION: Dono projects ko jodta hai aur sabhi strategies ko optimize karta hai.

import pandas as pd
import os
import sys
import json
import multiprocessing
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import itertools
import numpy as np

# --- YAHAN BADLAV KIYA GAYA HAI: Dono Projects Ko Jodne Ke Liye Antim Pul ---
# Yeh code sunishchit karega ki Python hamesha 'quantbacktest' folder ko dhoondh paaye.
# Is script ki current directory lein (e.g., .../PaperTradingV1.3)
current_dir = os.path.dirname(os.path.abspath(__file__))
try:
    # Isse ek level upar jaayein (e.g., .../AI Generated App)
    parent_dir = os.path.dirname(current_dir)
    
    # Ab 'quantbacktest' folder ka poora path banayein
    quantbacktest_path = os.path.join(parent_dir, 'quantbacktest')

    # Check karein ki kya 'quantbacktest' folder sach mein maujood hai
    if not os.path.isdir(quantbacktest_path):
        raise FileNotFoundError

    # Parent directory ko Python ke search path mein sabse aage jodein
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Ensure quantbacktest directory itself is also in the path
    if quantbacktest_path not in sys.path:
        sys.path.insert(0, quantbacktest_path)
        
    # Print debug information about the paths
    print(f"Python paths: {sys.path}")
    print(f"Looking for quantbacktest in: {quantbacktest_path}")
    print(f"Files in quantbacktest directory: {os.listdir(quantbacktest_path) if os.path.exists(quantbacktest_path) else 'Directory not found'}")

except FileNotFoundError:
    print("FATAL ERROR: 'quantbacktest' directory nahi mili.")
    print(f"Kripya sunishchit karein ki 'quantbacktest' aur '{os.path.basename(current_dir)}' dono ek hi folder ke andar hain.")
    sys.exit(1)
# --- END OF BADLAV ---


# Ab yeh imports bina kisi error ke kaam karenge
from quantbacktest.data.data_loader import DataLoader
from quantbacktest.utils.strategy_loader import load_strategy
from quantbacktest.utils.metrics import calculate_performance_metrics
from quantbacktest.engine.upgraded_portfolio import UpgradedPortfolio
import quantbacktest.config as q_config

from config_loader import CONFIG as p_config # Paper trading config ko import karein

def generate_param_combinations(strategy_name):
    """Quant config se parameter combinations banata hai."""
    param_config = q_config.STRATEGY_OPTIMIZATION_CONFIG.get(strategy_name, {}) # 'strategy_name.lower()' ko 'strategy_name' se badle
    if not param_config: return [{}]
    keys, values = zip(*param_config.items())
    return [dict(zip(keys, v)) for v in itertools.product(*values)]

def run_single_backtest(task_info):
    """Ek single backtest chalata hai."""
    try:
        symbol, timeframe, strategy_name, strategy_params, data_df = task_info
        
        if data_df.empty: return None

        strategy_obj = load_strategy(strategy_name.lower()) # 'strategy_name.lower()' ko 'strategy_name' se badle
        if not strategy_obj: return None

        tf_value = int(''.join(filter(str.isdigit, timeframe)) or 1)
        if 'H' in timeframe.upper(): tf_value *= 60
        
        strategy_instance = strategy_obj(df=data_df.copy(), symbol=symbol, primary_timeframe=tf_value, **strategy_params)
        signals_df = strategy_instance.run()
        if signals_df.empty: return None

        # Yahan prices_1min_df ka istemal
        prices_1min_df = data_df.join(signals_df[['entries', 'exits', 'stop_loss', 'target']])
        prices_1min_df['entries'] = prices_1min_df['entries'].astype('boolean').fillna(False)
        prices_1min_df['exits'] = prices_1min_df['exits'].astype('boolean').fillna(False)

        portfolio = UpgradedPortfolio(q_config.INITIAL_CASH, q_config.RISK_PER_TRADE_PCT, q_config.MAX_DAILY_LOSS_PCT, q_config.BROKERAGE_PCT, q_config.SLIPPAGE_PCT)

        for candle in prices_1min_df.itertuples():
            timestamp = candle.Index
            portfolio.on_new_day(timestamp)
            if portfolio.is_trading_halted_today: continue
            if symbol in portfolio.positions:
                portfolio.update_open_positions(timestamp, candle.low, candle.high)
            if candle.entries:
                portfolio.request_trade(timestamp, symbol, 'buy', candle.open, candle.stop_loss, candle.target)
            elif candle.exits and symbol in portfolio.positions:
                portfolio.request_trade(timestamp, symbol, 'sell', candle.open)
        
        if symbol in portfolio.positions:
            last_price = prices_1min_df.iloc[-1]['close']
            portfolio.request_trade(prices_1min_df.index[-1], symbol, 'sell', last_price)
        
        return calculate_performance_metrics(pd.DataFrame(portfolio.trade_log), portfolio.equity_df, q_config.INITIAL_CASH)

    except Exception:
        return None

def find_best_parameters_for_live():
    """Live trading ke liye sabhi active strategies ke best parameters dhoondhta hai."""
    
    strategies_to_run = p_config['strategy_config']
    
    print(f"--- Starting Retraining for {len(strategies_to_run)} active strategies ---")
    
    all_best_params = {}
    loader = DataLoader()

    for strategy_class_name, details in strategies_to_run.items():
        strategy_name_lower = strategy_class_name.lower().replace('strategy', '')
        symbols = details['symbols']
        timeframe = details['timeframe']
        
        for symbol in symbols:
            print(f"\n--- Optimizing {strategy_class_name} for {symbol} on {timeframe} TF ---")
            
            train_months = q_config.WALK_FORWARD_CONFIG['training_period_months']
            end_date = datetime.now()
            start_date = end_date - relativedelta(months=train_months)
            
            train_data = loader.fetch_data_for_symbol(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            if train_data.empty:
                print(f"Could not load training data for {symbol}. Skipping.")
                continue

            if isinstance(train_data.index, pd.DatetimeIndex) and train_data.index.tz is not None:
                train_data.index = train_data.index.tz_localize(None)

            param_combos = generate_param_combinations(strategy_name_lower)
            if len(param_combos) <= 1:
                print(f"No optimization parameters found for {strategy_class_name}. Using defaults.")
                all_best_params[strategy_class_name] = { "best_params": {} }
                continue

            optimization_tasks = [(symbol, timeframe, strategy_name_lower, params, train_data) for params in param_combos]
            
            best_params = {}
            best_performance_metric = -np.inf
            
            with multiprocessing.Pool(os.cpu_count()) as pool:
                results = list(tqdm(pool.imap_unordered(run_single_backtest, optimization_tasks), total=len(optimization_tasks), desc=f"Optimizing {symbol}"))
            
            for i, performance in enumerate(results):
                if performance:
                    metric_value = performance.get(q_config.WALK_FORWARD_CONFIG['optimization_metric'], -np.inf)
                    # Ensure metric_value is numeric before comparison
                    try:
                        metric_value = float(metric_value)
                        if metric_value > best_performance_metric:
                            best_performance_metric = metric_value
                            best_params = param_combos[i]
                    except (ValueError, TypeError):
                        # Skip this result if metric_value cannot be converted to float
                        continue

            if best_params:
                print(f"Found best parameters for {symbol}: {best_params} (Metric: {best_performance_metric:.2f})")
                if strategy_class_name not in all_best_params:
                    all_best_params[strategy_class_name] = {}
                all_best_params[strategy_class_name][symbol] = best_params
            else:
                print(f"Could not find optimal parameters for {symbol}.")

    if not all_best_params:
        print("Could not find optimal parameters for any strategy. No update will be made.")
        return
        
    output_data = {
        "params_by_strategy": all_best_params,
        "last_updated": datetime.now().isoformat()
    }
    
    with open("live_params.json", "w") as f:
        def convert(o):
            if isinstance(o, np.integer): return int(o)  
            if isinstance(o, np.floating): return float(o)
            raise TypeError
        json.dump(output_data, f, indent=4, default=convert)
        
    print("\nSuccessfully saved best parameters for all strategies to live_params.json")


if __name__ == '__main__':
    multiprocessing.freeze_support()
    find_best_parameters_for_live()
