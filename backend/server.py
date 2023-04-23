from __future__ import annotations
# Import flask and datetime module for showing date and time
from flask import Flask
from flask_cors import CORS
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
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

curr_path = os.path.abspath(os.path.dirname(__file__))
  
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

# This code chunk is borrowed from finrl preprocessor for YahooDownloader
"""Contains methods and classes to collect data from
Yahoo Finance API
"""

# import pandas as pd
import yfinance as yf


class YahooDownloader:
    """Provides methods for retrieving daily stock data from
    Yahoo Finance API
    Attributes
    ----------
        start_date : str
            start date of the data (modified from neofinrl_config.py)
        end_date : str
            end date of the data (modified from neofinrl_config.py)
        ticker_list : list
            a list of stock tickers (modified from neofinrl_config.py)
    Methods
    -------
    fetch_data()
        Fetches data from yahoo API
    """

    def __init__(self, start_date: str, end_date: str, ticker_list: list):
        self.start_date = start_date
        self.end_date = end_date
        self.ticker_list = ticker_list

    def fetch_data(self, proxy=None, interval='1m') -> pd.DataFrame:
        """Fetches data from Yahoo API
        Parameters
        ----------
        Returns
        -------
        `pd.DataFrame`
            7 columns: A date, open, high, low, close, volume and tick symbol
            for the specified stock ticker
        """
        # Download and save the data in a pandas DataFrame:
        data_df = pd.DataFrame()
        num_failures = 0
        for tic in self.ticker_list:
            temp_df = yf.download(
                tic, start=self.start_date, end=self.end_date, interval=interval, proxy=proxy
            )
            temp_df["tic"] = tic
            if len(temp_df) > 0:
                data_df = data_df.append(temp_df)
            else:
                num_failures += 1
        if num_failures == len(self.ticker_list):
            raise ValueError("no data is fetched.")
        # reset the index, we want to use numbers as index instead of dates
        data_df = data_df.reset_index()
        try:
            # convert the column names to standardized names
            data_df.columns = [
                "date",
                "open",
                "high",
                "low",
                "close",
                "adjcp",
                "volume",
                "tic",
            ]
            # use adjusted close price instead of close price
            data_df["close"] = data_df["adjcp"]
            # drop the adjusted close price column
            data_df = data_df.drop(labels="adjcp", axis=1)
        except NotImplementedError:
            print("the features are not supported currently")
        # create day of the week column (monday = 0)
        data_df["day"] = data_df["date"].dt.dayofweek
        # convert date to standard string format, easy to filter
        data_df["date"] = data_df.date.apply(lambda x: x.strftime("%Y-%m-%d"))
        # drop missing data
        data_df = data_df.dropna()
        data_df = data_df.reset_index(drop=True)
        print("Shape of DataFrame: ", data_df.shape)
        # print("Display DataFrame: ", data_df.head())

        data_df = data_df.sort_values(by=["date", "tic"]).reset_index(drop=True)

        return data_df

    def select_equal_rows_stock(self, df):
        df_check = df.tic.value_counts()
        df_check = pd.DataFrame(df_check).reset_index()
        df_check.columns = ["tic", "counts"]
        mean_df = df_check.counts.mean()
        equal_list = list(df.tic.value_counts() >= mean_df)
        names = df.tic.value_counts().index
        select_stocks_list = list(names[equal_list])
        df = df[df.tic.isin(select_stocks_list)]
        return df


@app.route('/backtesting_data')
# @cross_origin
def get_backtesting_data():
    a2c_acc_value = pd.read_pickle(curr_path+'/results/a2c/a2c_test_account_value.pkl')
    ppo_acc_value = pd.read_pickle(curr_path+'/results/ppo/ppo_test_account_value.pkl')
    ddpg_acc_value = pd.read_pickle(curr_path+'/results/ddpg/ddpg_test_account_value.pkl')
    td3_acc_value = pd.read_pickle(curr_path+'/results/td3/td3_test_account_value.pkl')
    a2c_acc_value = a2c_acc_value.set_index(a2c_acc_value.columns[0])
    ppo_acc_value = ppo_acc_value.set_index(ppo_acc_value.columns[0])
    ddpg_acc_value = ddpg_acc_value.set_index(ddpg_acc_value.columns[0])
    td3_acc_value = td3_acc_value.set_index(td3_acc_value.columns[0])
    START_DATE_TEST = a2c_acc_value.index.min()
    END_DATE_TEST = a2c_acc_value.index.max()
    INITIAL_AMOUNT = a2c_acc_value.iloc[0]["account_value"]
    dji_df = YahooDownloader(start_date=START_DATE_TEST, end_date=END_DATE_TEST, ticker_list=["^DJI"]).fetch_data()
    dji_df = dji_df[['date', 'close']]
    if dji_df.shape[0]<len(a2c_acc_value.index):
        dji_df['date'] = a2c_acc_value.index[:dji_df.shape[0]]
    else:
        dji_df['date'] = a2c_acc_value.index
    dji_df['account_value'] = dji_df['close']/dji_df['close'][0]*INITIAL_AMOUNT
    dji_df = dji_df.set_index(dji_df.columns[0])
    dji_df = dji_df.drop(columns=['close'])
    result = pd.merge(a2c_acc_value, ppo_acc_value, left_index=True, right_index=True)
    result = pd.merge(result, ddpg_acc_value, left_index=True, right_index=True)
    result = pd.merge(result, td3_acc_value, left_index=True, right_index=True)
    print(result)
    print(dji_df)
    result = pd.merge(result, dji_df, left_index=True, right_index=True)
    
    result.columns = ['a2c','ppo','ddpg','td3','dji']
    result = result.reset_index()
    return Response(result.to_json(orient="records"), mimetype='application/json', headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST"})
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
    app.run(debug=True, host='192.168.50.99')
    # app.run(debug=True)