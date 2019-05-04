
import datetime as dt
import pandas as pd
import util as ut
from indicators import *

from BagLearner import BagLearner

from RTLearner import RTLearner


class StrategyLearner(object):

    # constructor 			  		 			     			  	   		   	  			  	
    def __init__(self, verbose=False, impact=0.0):
        self.verbose = verbose
        self.impact = impact
        self.N = 10
        self.learner = BagLearner(learner=RTLearner, kwargs={"leaf_size": 5}, bags=20, boost=False, verbose=False)

    def create_x_data(self, prices):
        window = 10
        simple_moving_average = simple_moving_average_over_window(prices, window)
        simple_moving_std = simple_moving_std_over_window(prices, window)

        upper_bb, lower_bb = calculate_bollinger_bands(simple_moving_average, simple_moving_std)
        momentum = calculate_momentum_over_window(prices, window)
        upper_diff_price = upper_bb - prices
        lower_diff_price = lower_bb - prices

        # pd.concat
        x_data = prices.join(simple_moving_average, lsuffix='_Normalized Price', rsuffix='_SMA') \
            .join(upper_diff_price, lsuffix='_', rsuffix='_upperband_diff') \
            .join(lower_diff_price, lsuffix='_', rsuffix='_lowerband_diff') \
            .join(momentum, lsuffix='_', rsuffix="_momentum")

        x_data.columns = ['norm_price', "sma", "upper_band_diff", "lower_band_diff", "momentum"]
        # x_data = x_data.fillna(0)
        x_data = x_data.fillna(method='ffill')
        x_data = x_data.fillna(method='bfill')
        return x_data

    def addEvidence(self, symbol="JPM", \
                    sd=dt.datetime(2008, 1, 1), \
                    ed=dt.datetime(2008, 8, 1), \
                    sv=10000):

        syms = [symbol]
        dates = pd.date_range(sd, ed)
        prices_all = ut.get_data(syms, dates)  # automatically adds SPY
        prices_all = prices_all.fillna(method='ffill')
        prices_all = prices_all.fillna(method='bfill')
        prices_all.sort_index(axis=0)

        prices = prices_all[syms]  # only portfolio symbols
        prices_SPY = prices_all['SPY']  # only SPY, for comparison later 			  		 			     			  	   		   	  			  	
        if self.verbose: print prices

        # example use with new colname 			  		 			     			  	   		   	  			  	
        volume_all = ut.get_data(syms, dates,
                                 colname="Volume")  # automatically adds SPY
        volume = volume_all[syms]  # only portfolio symbols 			  		 			     			  	   		   	  			  	
        x_train = self.create_x_data(prices)

        # Create y labled data
        y_values = []
        for i in range(prices.shape[0] - 5):
            price_change = (prices.ix[i + 5, symbol] - prices.ix[i, symbol]) / prices.ix[i, symbol]
            if price_change > (0.02 + self.impact):
                y_values.append(1)
            elif price_change < (-0.02 - self.impact):
                y_values.append(-1)
            else:
                y_values.append(0)
        y_values.extend([0, 0, 0, 0, 0])
        y_train = pd.DataFrame(data=y_values, index=prices.index, columns=['y_values'])

        self.learner.addEvidence(x_train.values, y_train.values)
        pass

    def testPolicy(self, symbol="JPM", \
                   sd=dt.datetime(2009, 1, 1), \
                   ed=dt.datetime(2010, 1, 1), \
                   sv=10000):

        # here we build a fake set of trades 			  		 			     			  	   		   	  			  	
        # your code should return the same sort of data 			  		 			     			  	   		   	  			  	
        syms = [symbol]
        dates = pd.date_range(sd, ed)
        prices_all = ut.get_data(syms, dates)  # automatically adds SPY
        prices_all = prices_all.fillna(method='ffill')
        prices_all = prices_all.fillna(method='bfill')
        # prices_all = prices_all / prices_all.ix[0,]
        prices_all.sort_index(axis=0)
        prices = prices_all[syms]  # only portfolio symbols
        x_test = self.create_x_data(prices)
        # Steps

        # Create x data with indicators

        # query learner
        y_test = self.learner.query(x_test.values)

        # create trades pd using signal and portfolio_position
        trade_shares = []
        portfolio_position = 0

        for i in range(0, len(prices) - 5):
            hint = y_test[i]
            if y_test[i] == -1:
                # do sell
                trade_shares.append(self.do_sell_trade(portfolio_position))
            elif y_test[i] == 1:
                # do buy
                trade_shares.append(self.do_buy_trade(portfolio_position))
            else:
                trade_shares.append(0)
            portfolio_position = portfolio_position + trade_shares[-1]
        trade_shares.extend([0, 0, 0, 0, 0])
        df_trades = pd.DataFrame(data=trade_shares, index=prices.index, columns=['orders'])
        # print(df_trades.values.tolist())
        return df_trades

    def do_buy_trade(self, portfolio_position):
        # buy
        if portfolio_position == 0:
            return 1000
        elif portfolio_position == -1000:
            return 2000
        elif portfolio_position == 1000:
            return 0

    def do_sell_trade(self, portfolio_position):
        if portfolio_position == 0:
            return -1000
        elif portfolio_position == -1000:
            return 0
        elif portfolio_position == 1000:
            return -2000

