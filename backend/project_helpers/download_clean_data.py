from datetime import datetime
from datetime import timedelta
from FinRL.finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
import pandas as pd
START_DATE = datetime.now() - timedelta(days=30)
END_DATE = datetime.now() - timedelta(days=1)

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

def train_test_model():
    data = pd.read_pickle('./datasets/alpaca_1m(30days).pkl')
    processed = data.copy()
    processed['date'] = processed['date'].dt.tz_localize(None)
    START_DATE_TRAIN = START_DATE
    END_DATE_TRAIN = START_DATE+timedelta(23)
    START_DATE_TEST = START_DATE+timedelta(23)
    END_DATE_TEST = END_DATE
    train_df = data_split(processed, START_DATE_TRAIN, END_DATE_TRAIN)
    test_df = data_split(processed, START_DATE_TEST, END_DATE_TEST)
    stock_dimension = len(train_df.tic.unique())
    state_space = 1 + 2*stock_dimension + len(INDICATORS)*stock_dimension
    print(f"Stock Dimension: {stock_dimension}, State Space: {state_space}")