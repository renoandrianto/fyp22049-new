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

from project_helpers.download_data_train_models import download_and_clean, train_test_model
from project_helpers.live_trading import AlpacaPaperTrading

curr_path = os.path.abspath(os.path.dirname(__file__))
data = pd.read_pickle(os.path.join(curr_path, "./datasets/alpaca_1m_(30days).pkl"))
tickers = list(data["tic"].unique())
ERL_PARAMS = {"learning_rate": 3e-6,"batch_size": 2048,"gamma":  0.985,
        "seed":312,"net_dimension":[128,64], "target_step":5000, "eval_gap":30,
        "eval_times":1} 
action_dim = len(data["tic"].unique())
API_BASE_URL = 'https://paper-api.alpaca.markets'
state_space = 1 + 2 * action_dim + len(INDICATORS) * action_dim

paper_trading_erl = AlpacaPaperTrading(ticker_list = tickers, 
                                       time_interval = '1Min', 
                                       drl_lib = 'stable_baselines3', 
                                       agent = 'td3', 
                                       cwd = os.path.join(curr_path, "./trained_models/"), 
                                       net_dim = ERL_PARAMS['net_dimension'], 
                                       state_dim = state_space, 
                                       action_dim= action_dim, 
                                       API_KEY = API_KEY, 
                                       API_SECRET = API_SECRET, 
                                       API_BASE_URL = API_BASE_URL, 
                                       tech_indicator_list = INDICATORS, 
                                       turbulence_thresh=30, 
                                       max_stock=1e2)

paper_trading_erl.run()
# while True:
#     download_and_clean(DP)
# download_and_clean(DP)
# train_test_model()

# while True:
#     if datetime.now()==