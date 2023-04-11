
# Import flask and datetime module for showing date and time
from flask import Flask
from flask import Response
import datetime
  
x = datetime.datetime.now()
API_KEY = "PKOD4HWMOBLR8OVXTV9E"
API_SECRET = "qZ0YU9viniZnfWTtPXfsbwXIEokb2wHw2gdSWpcq"
APCA_API_BASE_URL = 'https://paper-api.alpaca.markets'
data_url = 'wss://data.alpaca.markets'

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
# matplotlib.use('Agg')
import datetime

from FinRL.finrl.meta.preprocessor.yahoodownloader import YahooDownloader
from FinRL.finrl.meta.preprocessor.preprocessors import FeatureEngineer, data_split
from FinRL.finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
from FinRL.finrl.meta.env_stock_trading.env_stocktrading_np import StockTradingEnv as StockTradingEnvNP
from FinRL.finrl.agents.stablebaselines3.models import DRLAgent
from stable_baselines3.common.logger import configure
from FinRL.finrl.meta.data_processor import DataProcessor

from FinRL.finrl.plot import backtest_stats, backtest_plot, get_daily_return, get_baseline
from pprint import pprint

import sys
import os

os.environ['KMP_DUPLICATE_LIB_OK']='True'
# sys.path.append("../FinRL.finrl")

import itertools

from FinRL.finrl import config
from FinRL.finrl import config_tickers
import os
from FinRL.finrl.main import check_and_make_directories
from FinRL.finrl.config import (
    DATA_SAVE_DIR,
    TRAINED_MODEL_DIR,
    TENSORBOARD_LOG_DIR,
    RESULTS_DIR,
    INDICATORS,
    TRAIN_START_DATE,
    TRAIN_END_DATE,
    TEST_START_DATE,
    TEST_END_DATE,
    TRADE_START_DATE,
    TRADE_END_DATE,
)
check_and_make_directories([DATA_SAVE_DIR, TRAINED_MODEL_DIR, TENSORBOARD_LOG_DIR, RESULTS_DIR])

DP = DataProcessor(data_source = 'alpaca',
                   API_KEY = API_KEY,
                   API_SECRET = API_SECRET,
                   APCA_API_BASE_URL = APCA_API_BASE_URL)

from datetime import datetime
from datetime import timedelta
START_DATE = datetime.now() - timedelta(days=30)
END_DATE = datetime.now() - timedelta(days=1)
  
# Initializing flask app
app = Flask(__name__)
  
  
# Route for seeing a data
@app.route('/data')
def get_time():
  
    # Returning an api for showing in  reactjs
    return {
        'Name':"geek", 
        "Age":"22",
        "Date":x, 
        "programming":"python"
        }

@app.route('/minutely_dji_data')
def get_minutely_dji_data():
    data = DP.download_data(start_date = START_DATE.strftime('%Y-%m-%d'),
                        end_date = END_DATE.strftime('%Y-%m-%d'),
                        ticker_list = config_tickers.DOW_30_TICKER,
                        time_interval= '1min')
    return Response(data.to_json(orient="records"), mimetype='application/json')
# Route for seeing a data
# @app.route('/data')
# def get_time():
  
#     # Returning an api for showing in  reactjs
#     return {
#         'Name':"geek", 
#         "Age":"22",
#         "Date":x, 
#         "programming":"python"
#         }

# # Route for seeing a data
# @app.route('/data')
# def get_time():
  
#     # Returning an api for showing in  reactjs
#     return {
#         'Name':"geek", 
#         "Age":"22",
#         "Date":x, 
#         "programming":"python"
#         }
      
# Running app
if __name__ == '__main__':
    app.run(debug=True)