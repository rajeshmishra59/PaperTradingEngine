# File: config_loader.py
# Loads configuration from config.yml and provides it to the application.

import yaml
import os
from datetime import time
from dotenv import load_dotenv

# Load .env file to get API keys into environment variables
load_dotenv()

def load_config(config_path="config.yml"):
    """
    Loads the YAML configuration file and resolves environment variables.
    """
    with open(config_path, 'r') as f:
        config_str = f.read()

    # Simple environment variable substitution
    # This looks for ${VAR_NAME} and replaces it with the value of the environment variable VAR_NAME
    for key, value in os.environ.items():
        config_str = config_str.replace(f'${{{key}}}', value)

    config = yaml.safe_load(config_str)

    # --- Post-processing and object creation ---

    # Convert time strings to datetime.time objects
    start_str = config['trading_session']['start_time']
    end_str = config['trading_session']['end_time']
    config['trading_session']['start_time_obj'] = time.fromisoformat(start_str)
    config['trading_session']['end_time_obj'] = time.fromisoformat(end_str)

    eod_tsl_str = config['execution']['risk_management']['aggressive_tsl_start_time']
    final_exit_str = config['execution']['risk_management']['final_exit_time']
    config['execution']['risk_management']['aggressive_tsl_start_time_obj'] = time.fromisoformat(eod_tsl_str)
    config['execution']['risk_management']['final_exit_time_obj'] = time.fromisoformat(final_exit_str)


    # Replace symbol list names in strategies with the actual lists
    for strat_name, strat_conf in config['strategy_config'].items():
        symbol_list_name = strat_conf.get('symbols')
        if symbol_list_name and symbol_list_name in config['symbol_lists']:
            strat_conf['symbols'] = config['symbol_lists'][symbol_list_name]

    return config

# Load the configuration once when the module is imported
CONFIG = load_config()

if __name__ == '__main__':
    # For testing purposes, print the loaded config
    import json
    print(json.dumps(CONFIG, indent=2))
