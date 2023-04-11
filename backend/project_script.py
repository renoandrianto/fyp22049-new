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

from backend.project_helpers.download_clean_data import download_and_clean

while True:
    download_and_clean(DP)
    
# while True:
#     if datetime.now()==