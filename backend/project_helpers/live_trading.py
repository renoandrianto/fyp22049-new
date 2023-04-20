from __future__ import annotations

import datetime
import pytz
import threading
# from finrl.meta.data_processors.processor_alpaca import AlpacaProcessor
import alpaca_trade_api as tradeapi
import time
import pandas as pd
import numpy as np
import torch
import gym
import threading
# from finrl.meta.data_processors.processor_alpaca import AlpacaProcessor
import alpaca_trade_api as tradeapi
import time
import pandas as pd
import numpy as np
import torch
import gym
from datetime import timedelta


import alpaca_trade_api as tradeapi
import exchange_calendars as tc
import numpy as np
import pandas as pd
import pytz
from stockstats import StockDataFrame as Sdf
from finrl.meta.preprocessor.preprocessors import FeatureEngineer, data_split
from FinRL.finrl.agents.stablebaselines3.models import DRLAgent
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

from FinRL.finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv


class AlpacaProcessor:
    def __init__(self, API_KEY=None, API_SECRET=None, API_BASE_URL=None, api=None):
        if api is None:
            try:
                self.api = tradeapi.REST(API_KEY, API_SECRET, API_BASE_URL, "v2")
            except BaseException:
                raise ValueError("Wrong Account Info!")
        else:
            self.api = api

    def download_data(
        self, ticker_list, start_date, end_date, time_interval
    ) -> pd.DataFrame:
        """
        ticker_list : list string of ticket
        time_interval: time interval
        start_date : start date of America/New_York time
        end_date : end date of America/New_York time
        The function tries to retrieve the data, between the start date and the end date, from the Alpaca server.
        if time_interval < 1D: period of data retrieved is the opening time of the New York Stock Exchange (NYSE) (from 9:30 am to 4:00 pm), in UTC offset zone.
        if time_interval >= 1D: each bar is the midnight of the day in America/New_York time, in UTC offset zone.
        """
        self.start = start_date
        self.end = end_date
        self.time_interval = time_interval

        # download
        NY = "America/New_York"
        start_date = pd.Timestamp(start_date + " 09:30:00", tz=NY)
        end_date = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
        # end_date = pd.Timestamp(end_date + " 15:59:00", tz=NY)
        barset = self.api.get_bars(
            ticker_list,
            time_interval,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        ).df

        # from trepan.api import debug;debug()
        # filter opening time of the New York Stock Exchange (NYSE) (from 9:30 am to 4:00 pm) if time_interval < 1D
        day_delta = 86400000000000  # pd.Timedelta('1D').delta == 86400000000000
        if pd.Timedelta(time_interval).delta < day_delta:
            NYSE_open_hour = "14:30"  # in UTC
            NYSE_close_hour = "20:59"  # in UTC
            data_df = barset.between_time(NYSE_open_hour, NYSE_close_hour)
        else:
            data_df = barset

        # reformat to finrl expected schema
        data_df = data_df.reset_index().rename(columns={"symbol": "tic"})
        data_df["timestamp"] = data_df["timestamp"].apply(lambda x: x.tz_convert(NY))

        return data_df

    def clean_data(self, df):
        tic_list = np.unique(df.tic.values)
        n_tickers = len(tic_list)

        # align start and end dates
        unique_times = df["timestamp"].unique()
        for time in unique_times:
            if len(df[df.timestamp == time].index) < n_tickers:
                df = df[df.timestamp != time]

        trading_days = self.get_trading_days(start=self.start, end=self.end)
        # produce full timestamp index
        times = []
        for day in trading_days:
            NY = "America/New_York"
            current_time = pd.Timestamp(day + " 09:30:00").tz_localize(NY)
            for i in range(390):
                times.append(current_time)
                current_time += pd.Timedelta(minutes=1)

        # create a new dataframe with full timestamp series
        new_df = pd.DataFrame()
        for tic in tic_list:
            tmp_df = pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"], index=times
            )
            tic_df = df[df.tic == tic]
            for i in range(tic_df.shape[0]):
                tmp_df.loc[tic_df.iloc[i]["timestamp"]] = tic_df.iloc[i][
                    ["open", "high", "low", "close", "volume"]
                ]

            # if the close price of the first row is NaN
            if str(tmp_df.iloc[0]["close"]) == "nan":
                print(
                    "The price of the first row for ticker ",
                    tic,
                    " is NaN. ",
                    "It will filled with the first valid price.",
                )
                for i in range(tmp_df.shape[0]):
                    if str(tmp_df.iloc[i]["close"]) != "nan":
                        first_valid_price = tmp_df.iloc[i]["close"]
                        tmp_df.iloc[0] = [
                            first_valid_price,
                            first_valid_price,
                            first_valid_price,
                            first_valid_price,
                            0.0,
                        ]
                        break

            # if the close price of the first row is still NaN (All the prices are NaN in this case)
            if str(tmp_df.iloc[0]["close"]) == "nan":
                print(
                    "Missing data for ticker: ",
                    tic,
                    " . The prices are all NaN. Fill with 0.",
                )
                tmp_df.iloc[0] = [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ]

            # forward filling row by row
            for i in range(tmp_df.shape[0]):
                if str(tmp_df.iloc[i]["close"]) == "nan":
                    previous_close = tmp_df.iloc[i - 1]["close"]
                    if str(previous_close) == "nan":
                        raise ValueError
                    tmp_df.iloc[i] = [
                        previous_close,
                        previous_close,
                        previous_close,
                        previous_close,
                        0.0,
                    ]

            tmp_df = tmp_df.astype(float)
            tmp_df["tic"] = tic
            new_df = pd.concat([new_df, tmp_df])

        new_df = new_df.reset_index()
        new_df = new_df.rename(columns={"index": "timestamp"})

        # print("Data clean finished!")

        return new_df

    def add_technical_indicator(
        self,
        df,
        tech_indicator_list=[
            "macd",
            "boll_ub",
            "boll_lb",
            "rsi_30",
            "dx_30",
            "close_30_sma",
            "close_60_sma",
        ],
    ):
        df = df.rename(columns={"timestamp": "date"})
        df = df.copy()
        df = df.sort_values(by=["tic", "date"])
        stock = Sdf.retype(df.copy())
        unique_ticker = stock.tic.unique()
        tech_indicator_list = tech_indicator_list

        for indicator in tech_indicator_list:
            indicator_df = pd.DataFrame()
            for i in range(len(unique_ticker)):
                # print(unique_ticker[i], i)
                temp_indicator = stock[stock.tic == unique_ticker[i]][indicator]
                temp_indicator = pd.DataFrame(temp_indicator)
                temp_indicator["tic"] = unique_ticker[i]
                # print(len(df[df.tic == unique_ticker[i]]['date'].to_list()))
                temp_indicator["date"] = df[df.tic == unique_ticker[i]][
                    "date"
                ].to_list()
                indicator_df = pd.concat(
                    [indicator_df, temp_indicator], ignore_index=True
                )
            df = df.merge(
                indicator_df[["tic", "date", indicator]], on=["tic", "date"], how="left"
            )
        df = df.sort_values(by=["date", "tic"])
        df = df.rename(columns={"date": "timestamp"})
        #        print("Succesfully add technical indicators")
        return df

    def add_vix(self, data):
        vix_df = self.download_data(["VIXY"], self.start, self.end, self.time_interval)
        cleaned_vix = self.clean_data(vix_df)
        vix = cleaned_vix[["timestamp", "close"]]
        vix = vix.rename(columns={"close": "VIXY"})

        df = data.copy()
        df = df.merge(vix, on="timestamp")
        df = df.sort_values(["timestamp", "tic"]).reset_index(drop=True)
        return df

    def calculate_turbulence(self, data, time_period=252):
        # can add other market assets
        df = data.copy()
        df_price_pivot = df.pivot(index="timestamp", columns="tic", values="close")
        # use returns to calculate turbulence
        df_price_pivot = df_price_pivot.pct_change()

        unique_date = df.timestamp.unique()
        # start after a fixed timestamp period
        start = time_period
        turbulence_index = [0] * start
        # turbulence_index = [0]
        # print(start)
        # print(len(unique_date))
        count = 0
        for i in range(start, len(unique_date)):
            current_price = df_price_pivot[df_price_pivot.index == unique_date[i]]
            # use one year rolling window to calcualte covariance
            hist_price = df_price_pivot[
                (df_price_pivot.index < unique_date[i])
                & (df_price_pivot.index >= unique_date[i - time_period])
            ]
            # Drop tickers which has number missing values more than the "oldest" ticker
            filtered_hist_price = hist_price.iloc[
                hist_price.isna().sum().min() :
            ].dropna(axis=1)

            cov_temp = filtered_hist_price.cov()
            current_temp = current_price[[x for x in filtered_hist_price]] - np.mean(
                filtered_hist_price, axis=0
            )
            temp = current_temp.values.dot(np.linalg.pinv(cov_temp)).dot(
                current_temp.values.T
            )
            if temp > 0:
                count += 1
                if count > 2:
                    turbulence_temp = temp[0][0]
                else:
                    # avoid large outlier because of the calculation just begins
                    turbulence_temp = 0
            else:
                turbulence_temp = 0
            turbulence_index.append(turbulence_temp)

        turbulence_index = pd.DataFrame(
            {"timestamp": df_price_pivot.index, "turbulence": turbulence_index}
        )

        # print("turbulence_index\n", turbulence_index)

        return turbulence_index

    def add_turbulence(self, data, time_period=252):
        """
        add turbulence index from a precalcualted dataframe
        :param data: (df) pandas dataframe
        :return: (df) pandas dataframe
        """
        df = data.copy()
        turbulence_index = self.calculate_turbulence(df, time_period=time_period)
        df = df.merge(turbulence_index, on="timestamp")
        df = df.sort_values(["timestamp", "tic"]).reset_index(drop=True)
        return df

    def df_to_array(self, df, tech_indicator_list, if_vix):
        df = df.copy()
        unique_ticker = df.tic.unique()
        if_first_time = True
        for tic in unique_ticker:
            if if_first_time:
                price_array = df[df.tic == tic][["close"]].values
                tech_array = df[df.tic == tic][tech_indicator_list].values
                if if_vix:
                    turbulence_array = df[df.tic == tic]["VIXY"].values
                else:
                    turbulence_array = df[df.tic == tic]["turbulence"].values
                if_first_time = False
            else:
                price_array = np.hstack(
                    [price_array, df[df.tic == tic][["close"]].values]
                )
                tech_array = np.hstack(
                    [tech_array, df[df.tic == tic][tech_indicator_list].values]
                )
        #        print("Successfully transformed into array")
        return price_array, tech_array, turbulence_array

    def get_trading_days(self, start, end):
        nyse = tc.get_calendar("NYSE")
        df = nyse.sessions_in_range(
            pd.Timestamp(start, tz=pytz.UTC), pd.Timestamp(end, tz=pytz.UTC)
        )
        trading_days = []
        for day in df:
            trading_days.append(str(day)[:10])

        return trading_days

    def fetch_latest_data(
        self, ticker_list, time_interval, tech_indicator_list, limit=1000
    ) -> pd.DataFrame:
        data_df = pd.DataFrame()
        ticker_list = ticker_list+["VIXY"]
        for tic in ticker_list:
            barset = self.api.get_bars([tic], time_interval, end=datetime.datetime.now(datetime.timezone.utc).isoformat(), limit=limit).df  # [tic]
            barset["tic"] = tic
            barset = barset.reset_index()
            data_df = pd.concat([data_df, barset])
        print(data_df)
        data_df = data_df.reset_index(drop=True)
        start_time = data_df.timestamp.min()
        end_time = data_df.timestamp.max()
        # self.start = start_time.strftime("%Y-%m-%d")
        # self.end = end_time.strftime("%Y-%m-%d")
        # self.time_interval = time_interval
        times = []
        current_time = start_time
        end = end_time + pd.Timedelta(minutes=1)
        while current_time != end:
            times.append(current_time)
            current_time += pd.Timedelta(minutes=1)

        df = data_df.copy()
        new_df = pd.DataFrame()
        for tic in ticker_list:
            tmp_df = pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"], index=times
            )
            tic_df = df[df.tic == tic]
            for i in range(tic_df.shape[0]):
                tmp_df.loc[tic_df.iloc[i]["timestamp"]] = tic_df.iloc[i][
                    ["open", "high", "low", "close", "volume"]
                ]

                if str(tmp_df.iloc[0]["close"]) == "nan":
                    for i in range(tmp_df.shape[0]):
                        if str(tmp_df.iloc[i]["close"]) != "nan":
                            first_valid_close = tmp_df.iloc[i]["close"]
                            tmp_df.iloc[0] = [
                                first_valid_close,
                                first_valid_close,
                                first_valid_close,
                                first_valid_close,
                                0.0,
                            ]
                            break
                if str(tmp_df.iloc[0]["close"]) == "nan":
                    print(
                        "Missing data for ticker: ",
                        tic,
                        " . The prices are all NaN. Fill with 0.",
                    )
                    tmp_df.iloc[0] = [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    ]

            for i in range(tmp_df.shape[0]):
                if str(tmp_df.iloc[i]["close"]) == "nan":
                    previous_close = tmp_df.iloc[i - 1]["close"]
                    if str(previous_close) == "nan":
                        previous_close = 0.0
                    tmp_df.iloc[i] = [
                        previous_close,
                        previous_close,
                        previous_close,
                        previous_close,
                        0.0,
                    ]
            tmp_df = tmp_df.astype(float)
            tmp_df["tic"] = tic
            new_df = pd.concat([new_df, tmp_df])

        new_df = new_df.reset_index()
        new_df = new_df.rename(columns={"index": "timestamp"})

        df = self.add_technical_indicator(new_df, tech_indicator_list)
        df = self.add_turbulence(df)
        # df = self.add_vix(df)
        # df["VIXY"] = 0
        # price_array, tech_array, turbulence_array = self.df_to_array(
        #     df, tech_indicator_list, if_vix=True
        # )
        # latest_price = price_array[-1]
        # latest_tech = tech_array[-1]
        vix_df = df[df['tic']=='VIXY'][["timestamp", "close"]].rename(columns={"close":"VIXY"})
        df = df[~(df['tic']=='VIXY')]
        df = df.merge(vix_df, on="timestamp").rename(columns={"timestamp":"date"})
        df = data_split(df, start_time, end_time+timedelta(1))
        turb_df = self.api.get_bars(["VIXY"], time_interval, end=datetime.datetime.now(datetime.timezone.utc).isoformat(), limit=1).df
        latest_turb = turb_df["close"].values
        return df, latest_turb
        # return latest_price, latest_tech, latest_turb


class AlpacaPaperTrading():

    def __init__(self,ticker_list, time_interval, drl_lib, agent, cwd, net_dim, 
                 state_dim, action_dim, API_KEY, API_SECRET, 
                 API_BASE_URL, tech_indicator_list, turbulence_thresh=30, 
                 max_stock=1e2, latency = None):
        #load agent
        self.drl_lib = drl_lib
        #connect to Alpaca trading API
        try:
            self.alpaca = tradeapi.REST(API_KEY,API_SECRET,API_BASE_URL, 'v2')
        except:
            raise ValueError('Fail to connect Alpaca. Please check account info and internet connection.')
        
        #read trading time interval
        if time_interval == '1s':
            self.time_interval = 1
        elif time_interval == '5s':
            self.time_interval = 5
        elif time_interval == '1Min':
            self.time_interval = 60
        elif time_interval == '5Min':
            self.time_interval = 60 * 5
        elif time_interval == '15Min':
            self.time_interval = 60 * 15
        elif time_interval == '1day':
            self.time_interval = 3600*24
        else:
            raise ValueError('Time interval input is NOT supported yet.')
        
        #read trading settings
        self.tech_indicator_list = tech_indicator_list
        self.turbulence_thresh = turbulence_thresh
        self.max_stock = max_stock 
        
        #initialize account
        self.stocks = np.asarray([0] * len(ticker_list)) #stocks holding
        self.stocks_cd = np.zeros_like(self.stocks) 
        self.cash = None #cash record 
        self.stocks_df = pd.DataFrame(self.stocks, columns=['stocks'], index = ticker_list)
        self.asset_list = []
        self.price = np.asarray([0] * len(ticker_list))
        self.stockUniverse = ticker_list
        self.turbulence_bool = 0
        self.equities = []
        self.action_dim = action_dim
        self.state_dim = state_dim

        state = self.get_state()
        print(state)
        print(ticker_list, len(ticker_list))
        buy_cost_list = [0] * len(ticker_list)
        sell_cost_list = [0] * len(ticker_list)
        print(state_dim)
        print(len(INDICATORS))
        env_kwargs = {
            "hmax": 100,
            "initial_amount": 0,
            "num_stock_shares": [0]*len(ticker_list),
            "buy_cost_pct": buy_cost_list,
            "sell_cost_pct": sell_cost_list,
            "state_space": state_dim,
            "stock_dim": len(ticker_list),
            "tech_indicator_list": INDICATORS,
            "action_space": len(ticker_list),
            "reward_scaling": 1e-4
        }
        e_trade_gym = StockTradingEnv(df = state, turbulence_threshold = 30, **env_kwargs)
        env_trade, obs_trade = e_trade_gym.get_sb_env()
        if agent=="a2c":
            if drl_lib == 'stable_baselines3':
                try:
                    #load agent
                    cwd = cwd + 'a2cmodel-alpaca1mindata.zip'
                    env_trade, _ = e_trade_gym.get_sb_env()
                    self.model = DRLAgent(env = env_trade).get_model("a2c").load(cwd)
                    print("Successfully load model", cwd)
                except:
                    raise ValueError('Fail to load agent!')
                    
            else:
                raise ValueError('The DRL library input is NOT supported yet. Please check your input.')
        elif agent=="ppo":
            if drl_lib == 'stable_baselines3':
                try:
                    #load agent
                    cwd = cwd + 'ppomodel-alpaca1mindata.zip'
                    env_trade, _ = e_trade_gym.get_sb_env()
                    self.model = DRLAgent(env = env_trade).get_model("ppo").load(cwd)
                    print("Successfully load model", cwd)
                except:
                    raise ValueError('Fail to load agent!')
                    
            else:
                raise ValueError('The DRL library input is NOT supported yet. Please check your input.')
        elif agent=="ddpg":
            if drl_lib == 'stable_baselines3':
                try:
                    #load agent
                    cwd = cwd + 'ddpgmodel-alpaca1mindata.zip'
                    env_trade, _ = e_trade_gym.get_sb_env()
                    self.model = DRLAgent(env = env_trade).get_model("ddpg").load(cwd)
                    print("Successfully load model", cwd)
                except:
                    raise ValueError('Fail to load agent!')
                    
            else:
                raise ValueError('The DRL library input is NOT supported yet. Please check your input.')
        elif agent=="td3":
            if drl_lib == 'stable_baselines3':
                try:
                    #load agent
                    cwd = cwd + 'td3model-alpaca1mindata.zip'
                    env_trade, _ = e_trade_gym.get_sb_env()
                    self.model = DRLAgent(env = env_trade).get_model("td3").load(cwd)
                    print("Successfully load model", cwd)
                except:
                    raise ValueError('Fail to load agent!')
                    
            else:
                raise ValueError('The DRL library input is NOT supported yet. Please check your input.')
        else:
            raise ValueError('Agent input is NOT supported yet.')

        
    def test_latency(self, test_times = 10): 
        total_time = 0
        for i in range(0, test_times):
            time0 = time.time()
            self.get_state()
            time1 = time.time()
            temp_time = time1 - time0
            total_time += temp_time
        latency = total_time/test_times
        print('latency for data processing: ', latency)
        return latency
        
    def run(self):
        orders = self.alpaca.list_orders(status="open")
        for order in orders:
          self.alpaca.cancel_order(order.id)
    
        # Wait for market to open.
        print("Waiting for market to open...")
        self.awaitMarketOpen()
        print("Market opened.")

        while True:

          # Figure out when the market will close so we can prepare to sell beforehand.
          clock = self.alpaca.get_clock()
          closingTime = clock.next_close.replace(tzinfo=datetime.timezone.utc).timestamp()
          currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
          self.timeToClose = closingTime - currTime
    
          if(self.timeToClose < (60)):
            # Close all positions when 1 minutes til market close.
            print("Market closing soon. Stop trading.")
            break
            
            '''# Close all positions when 1 minutes til market close.
            print("Market closing soon.  Closing positions.")

            threads = []
            positions = self.alpaca.list_positions()
            for position in positions:
              if(position.side == 'long'):
                orderSide = 'sell'
              else:
                orderSide = 'buy'
              qty = abs(int(float(position.qty)))
              respSO = []
              tSubmitOrder = threading.Thread(target=self.submitOrder(qty, position.symbol, orderSide, respSO))
              tSubmitOrder.start()
              threads.append(tSubmitOrder)    # record thread for joining later

            for x in threads:   #  wait for all threads to complete
                x.join()     
            # Run script again after market close for next trading day.
            print("Sleeping until market close (15 minutes).")
            time.sleep(60 * 15)'''
            
          else:
            self.trade()
            last_equity = float(self.alpaca.get_account().last_equity)
            cur_time = time.time()
            self.equities.append([cur_time,last_equity])
            time.sleep(self.time_interval)
            
    def awaitMarketOpen(self):
        isOpen = self.alpaca.get_clock().is_open
        while(not isOpen):
          clock = self.alpaca.get_clock()
          openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
          currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
          timeToOpen = int((openingTime - currTime) / 60)
          print(str(timeToOpen) + " minutes til market open.")
          time.sleep(60)
          isOpen = self.alpaca.get_clock().is_open
    
    def trade(self):
        state = self.get_state()
        
        if self.drl_lib == 'elegantrl':
            with torch.no_grad():
                s_tensor = torch.as_tensor((state,), device=self.device)
                a_tensor = self.act(s_tensor)  
                action = a_tensor.detach().cpu().numpy()[0]  
            action = (action * self.max_stock).astype(int)
            
        elif self.drl_lib == 'rllib':
            action = self.agent.compute_single_action(state)
        
        elif self.drl_lib == 'stable_baselines3':
                env_kwargs = {
                    "hmax": 100,
                    "initial_amount": self.cash,
                    "num_stock_shares": list(self.stocks) if len(self.stocks)==self.action_dim else [0]*self.action_dim,
                    "buy_cost_pct": [0]*self.action_dim,
                    "sell_cost_pct": [0]*self.action_dim,
                    "state_space": self.state_dim,
                    "stock_dim": self.action_dim,
                    "tech_indicator_list": INDICATORS,
                    "action_space": self.action_dim,
                    "reward_scaling": 1e-4
                }
                e_trade_gym = StockTradingEnv(df = state, turbulence_threshold = 30, **env_kwargs)
                env_trade, obs_trade = e_trade_gym.get_sb_env()
                env_trade.reset()
                action, _states = self.model.predict(obs_trade, deterministic=True)
                obs_trade, rewards, dones, info = env_trade.step(action)
                action = env_trade.env_method(method_name="save_action_memory")
                action = np.array(action)[0]
        else:
            raise ValueError('The DRL library input is NOT supported yet. Please check your input.')
        
        self.stocks_cd += 1
        if self.turbulence_bool == 0:
            min_action = 0  # stock_cd
            threads = []
            for index in np.where(action[0] < -min_action)[0]:  # sell_index:
                print(f"stocks[{index}] = {self.stocks[index]}")
                print(f"action[{index}] = {-action[0][index]}")
                sell_num_shares = min(self.stocks[index], -action[0][index])
                qty =  abs(int(sell_num_shares))
                respSO = []
                tSubmitOrder = threading.Thread(target=self.submitOrder(qty, self.stockUniverse[index], 'sell', respSO))
                tSubmitOrder.start()
                threads.append(tSubmitOrder)    # record thread for joining later
                self.cash = float(self.alpaca.get_account().cash)
                self.stocks_cd[index] = 0
            
            for x in threads:   #  wait for all threads to complete
                x.join()     

            threads = []
            for index in np.where(action[0] > min_action)[0]:  # buy_index:
                if self.cash < 0:
                    tmp_cash = 0
                else:
                    tmp_cash = self.cash
                buy_num_shares = min(tmp_cash // self.price[index], abs(int(action[0][index])))
                if (buy_num_shares != buy_num_shares): # if buy_num_change = nan
                    qty = 0 # set to 0 quantity
                else:
                    qty = abs(int(buy_num_shares))
                qty = abs(int(buy_num_shares))
                respSO = []
                tSubmitOrder = threading.Thread(target=self.submitOrder(qty, self.stockUniverse[index], 'buy', respSO))
                tSubmitOrder.start()
                threads.append(tSubmitOrder)    # record thread for joining later
                self.cash = float(self.alpaca.get_account().cash)
                self.stocks_cd[index] = 0

            for x in threads:   #  wait for all threads to complete
                x.join()     
                
        else:  # sell all when turbulence
            threads = []
            positions = self.alpaca.list_positions()
            for position in positions:
                if(position.side == 'long'):
                    orderSide = 'sell'
                else:
                    orderSide = 'buy'
                qty = abs(int(float(position.qty)))
                respSO = []
                tSubmitOrder = threading.Thread(target=self.submitOrder(qty, position.symbol, orderSide, respSO))
                tSubmitOrder.start()
                threads.append(tSubmitOrder)    # record thread for joining later

            for x in threads:   #  wait for all threads to complete
                x.join()     
            
            self.stocks_cd[:] = 0
            
    
    def get_state(self):
        alpaca = AlpacaProcessor(api=self.alpaca)
        stocks_df, turbulence = alpaca.fetch_latest_data(ticker_list = self.stockUniverse, time_interval='1Min',
                                                     tech_indicator_list=self.tech_indicator_list)
        turbulence_bool = 1 if turbulence >= self.turbulence_thresh else 0
        self.turbulence_bool = turbulence_bool
        stocks_df = stocks_df.fillna(method="ffill").fillna(method="bfill").replace([np.inf, -np.inf], 0).rename(columns={"VIXY":"vix"})
        # stocks_df['date'] = stocks_df['date'].dt.tz_localize(None)
        # turbulence = (self.sigmoid_sign(turbulence, self.turbulence_thresh) * 2 ** -5).astype(np.float32)
        
        # tech = tech * 2 ** -7
        positions = self.alpaca.list_positions()
        # # print(positions)
        stocks = [0] * len(self.stockUniverse)
        for position in positions:
            ind = self.stockUniverse.index(position.symbol)
            stocks[ind] = ( abs(int(float(position.qty))))
        
        stocks = np.asarray(stocks, dtype = float)
        cash = float(self.alpaca.get_account().cash)
        self.cash = cash
        self.stocks = stocks
        return stocks_df
        
    def submitOrder(self, qty, stock, side, resp):
        if(qty > 0):
          try:
            self.alpaca.submit_order(stock, qty, side, "market", "day")
            print("Market order of | " + str(qty) + " " + stock + " " + side + " | completed.")
            resp.append(True)
          except:
            print("Order of | " + str(qty) + " " + stock + " " + side + " | did not go through.")
            resp.append(False)
        else:
          print("Quantity is 0, order of | " + str(qty) + " " + stock + " " + side + " | not completed.")
          resp.append(True)

    @staticmethod
    def sigmoid_sign(ary, thresh):
        def sigmoid(x):
            return 1 / (1 + np.exp(-x * np.e)) - 0.5

        return sigmoid(ary / thresh) * thresh
    
class StockEnvEmpty(gym.Env):
    #Empty Env used for loading rllib agent
    def __init__(self,config):
      state_dim = config['state_dim']
      action_dim = config['action_dim']
      self.env_num = 1
      self.max_step = 10000
      self.env_name = 'StockEnvEmpty'
      self.state_dim = state_dim  
      self.action_dim = action_dim
      self.if_discrete = False  
      self.target_return = 9999
      self.observation_space = gym.spaces.Box(low=-3000, high=3000, shape=(state_dim,), dtype=np.float32)
      self.action_space = gym.spaces.Box(low=-1, high=1, shape=(action_dim,), dtype=np.float32)
        
    def reset(self):
        return 

    def step(self, actions):
        return