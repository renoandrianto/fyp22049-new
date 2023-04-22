from datetime import datetime
from datetime import timedelta
from FinRL.finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
from FinRL.finrl.meta.preprocessor.yahoodownloader import YahooDownloader
from FinRL.finrl.meta.preprocessor.preprocessors import FeatureEngineer, data_split
from FinRL.finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
from FinRL.finrl.meta.env_stock_trading.env_stocktrading_np import StockTradingEnv as StockTradingEnvNP
from FinRL.finrl.agents.stablebaselines3.models import DRLAgent
from stable_baselines3.common.logger import configure
from FinRL.finrl.meta.data_processor import DataProcessor
import pandas as pd
import numpy as np
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


START_DATE = datetime.now() - timedelta(days=31)
END_DATE = datetime.now() - timedelta(days=1)
CURRENT_PATH = sys.path[0]
print("cur path", CURRENT_PATH)


def download_and_clean(DP):
    data = DP.download_data(start_date = START_DATE.strftime('%Y-%m-%d'),
                        end_date = END_DATE.strftime('%Y-%m-%d'),
                        ticker_list = config_tickers.DOW_30_TICKER,
                        time_interval= '1min')
    data = DP.clean_data(data)
    data = DP.add_technical_indicator(data, INDICATORS)
    data = DP.add_vix(data)
    data = DP.add_turbulence(data)
    data = data.fillna(method="ffill").fillna(method="bfill").replace([np.inf, -np.inf], 0).rename(columns={"VIXY":"vix"})
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    data.to_pickle("./datasets/alpaca_1m(30days).pkl")

def train_a2c(env_train):
    agent = DRLAgent(env = env_train)
    model_a2c = agent.get_model("a2c")
    # set up logger
    tmp_path = RESULTS_DIR + '/a2c'
    new_logger_a2c = configure(tmp_path, ["stdout", "csv", "tensorboard"])
    # Set new logger
    model_a2c.set_logger(new_logger_a2c)
    trained_a2c = agent.train_model(model=model_a2c, 
                             tb_log_name='a2c',
                             total_timesteps=50000)
    trained_a2c.save("./trained_models/a2cmodel-alpaca1mindata")

def train_ppo(env_train):
    PPO_PARAMS = {
        "n_steps": 2048,
        "ent_coef": 0.01,
        "learning_rate": 0.00025,
        "batch_size": 128,
    }
    agent = DRLAgent(env = env_train)
    model_ppo = agent.get_model("ppo",model_kwargs = PPO_PARAMS)
    # set up logger
    tmp_path = RESULTS_DIR + '/ppo'
    new_logger_ppo = configure(tmp_path, ["stdout", "csv", "tensorboard"])
    # Set new logger
    model_ppo.set_logger(new_logger_ppo)
    trained_ppo = agent.train_model(model=model_ppo, 
                             tb_log_name='ppo',
                             total_timesteps=50000)
    trained_ppo.save("./trained_models/ppomodel-alpaca1mindata")

def train_ddpg(env_train):
    agent = DRLAgent(env = env_train)
    model_ddpg = agent.get_model("ddpg")
    # set up logger
    tmp_path = RESULTS_DIR + '/ddpg'
    new_logger_ddpg = configure(tmp_path, ["stdout", "csv", "tensorboard"])
    # Set new logger
    model_ddpg.set_logger(new_logger_ddpg)
    trained_ddpg = agent.train_model(model=model_ddpg, 
                             tb_log_name='ddpg',
                             total_timesteps=50000)
    trained_ddpg.save("./trained_models/ddpgmodel-alpaca1mindata")

def train_td3(env_train):
    agent = DRLAgent(env = env_train)
    TD3_PARAMS = {"batch_size": 100, 
                "buffer_size": 1000000, 
                "learning_rate": 0.001}

    model_td3 = agent.get_model("td3",model_kwargs = TD3_PARAMS)
    # set up logger
    tmp_path = RESULTS_DIR + '/td3'
    new_logger_td3 = configure(tmp_path, ["stdout", "csv", "tensorboard"])
    # Set new logger
    model_td3.set_logger(new_logger_td3)
    trained_td3 = agent.train_model(model=model_td3, 
                             tb_log_name='td3',
                             total_timesteps=30000)
    trained_td3.save("./trained_models/td3model-alpaca1mindata")

def split_data_train_test():
    data = pd.read_pickle(CURRENT_PATH + "/datasets/alpaca_1m(30days).pkl")
    data = data.rename(columns={"timestamp":"date"})
    processed = data.copy()
    print(processed)
    processed['date'] = processed['date'].dt.tz_localize(None)
    START_DATE_TRAIN = START_DATE
    END_DATE_TRAIN = START_DATE+timedelta(24)
    START_DATE_TEST = START_DATE+timedelta(24)
    END_DATE_TEST = END_DATE
    train_df = data_split(processed, START_DATE_TRAIN, END_DATE_TRAIN)
    test_df = data_split(processed, START_DATE_TEST, END_DATE_TEST)
    # save both the train and test datasets
    train_df.to_pickle("./datasets/train_df.pkl")
    test_df.to_pickle("./datasets/test_df.pkl")

def train_test_model():
    train_df = pd.read_pickle(CURRENT_PATH+"/datasets/train_df.pkl")
    test_df = pd.read_pickle(CURRENT_PATH+"/datasets/test_df.pkl")
    stock_dimension = len(train_df.tic.unique())
    state_space = 1 + 2*stock_dimension + len(INDICATORS)*stock_dimension
    print(f"Stock Dimension: {stock_dimension}, State Space: {state_space}")
    buy_cost_list = sell_cost_list = [0.001] * stock_dimension
    num_stock_shares = [0] * stock_dimension

    env_kwargs = {
        "hmax": 100,
        "initial_amount": 1000000,
        "num_stock_shares": num_stock_shares,
        "buy_cost_pct": buy_cost_list,
        "sell_cost_pct": sell_cost_list,
        "state_space": state_space,
        "stock_dim": stock_dimension,
        "tech_indicator_list": INDICATORS,
        "action_space": stock_dimension,
        "turbulence_threshold": 99,
        "reward_scaling": 1e-4
    }

    e_train_gym = StockTradingEnv(df = train_df.fillna(method="ffill").fillna(method="bfill").replace([np.inf, -np.inf], 0).rename(columns={"VIXY":"vix"}), **env_kwargs)
    env_train, _ = e_train_gym.get_sb_env()

    train_a2c(env_train)
    train_ppo(env_train)
    train_ddpg(env_train)
    train_td3(env_train)

    # test a2c
    load_agent = DRLAgent(env = env_train)
    load_a2c = load_agent.get_model("a2c")
    load_a2c_trained = load_a2c.load(CURRENT_PATH+"/trained_models/a2cmodel-alpaca1mindata")
    trained_a2c = load_a2c_trained
    
    e_trade_gym = StockTradingEnv(df = test_df, risk_indicator_col='vix', **env_kwargs)

    df_account_value_a2c, df_actions_a2c = DRLAgent.DRL_prediction(
        model= trained_a2c, 
        environment = e_trade_gym)
    df_account_value_a2c.to_pickle(CURRENT_PATH+'/results/a2c/a2c_test_account_value.pkl')
    
    # test ppo
    load_agent = DRLAgent(env = env_train)
    load_ppo = load_agent.get_model("ppo")
    load_ppo_trained = load_ppo.load(CURRENT_PATH+"/trained_models/ppomodel-alpaca1mindata")
    trained_ppo = load_ppo_trained

    df_account_value_ppo, df_actions_ppo = DRLAgent.DRL_prediction(
        model= trained_ppo, 
        environment = e_trade_gym)
    df_account_value_ppo.to_pickle(CURRENT_PATH+'/results/ppo/ppo_test_account_value.pkl')
    
    # test ddpg
    load_agent = DRLAgent(env = env_train)
    load_ddpg = load_agent.get_model("ddpg")
    load_ddpg_trained = load_ddpg.load(CURRENT_PATH+"/trained_models/ddpgmodel-alpaca1mindata")
    trained_ddpg = load_ddpg_trained

    df_account_value_ddpg, df_actions_ddpg = DRLAgent.DRL_prediction(
        model= trained_ddpg, 
        environment = e_trade_gym)
    df_account_value_ddpg.to_pickle(CURRENT_PATH+'/results/ddpg/ddpg_test_account_value.pkl')
    
    # test td3
    load_agent = DRLAgent(env = env_train)
    load_td3 = load_agent.get_model("td3")
    load_td3_trained = load_td3.load(CURRENT_PATH+"/trained_models/td3model-alpaca1mindata")
    trained_td3 = load_td3_trained

    df_account_value_td3, df_actions_td3 = DRLAgent.DRL_prediction(
        model= trained_td3, 
        environment = e_trade_gym)
    df_account_value_td3.to_pickle(CURRENT_PATH+'/results/td3/td3_test_account_value.pkl')
