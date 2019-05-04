import pandas as pd
import datetime as dt
from util import get_data
import indicators


def compute_portfolio_stats(port_val):
    daily_ret = (port_val / port_val.shift(1)) - 1
    cummulative_returns = (port_val[-1] / port_val[0]) - 1
    average_daily_return = daily_ret.mean()
    std_daily_return = daily_ret.std()
    return cummulative_returns, average_daily_return, std_daily_return


def compute_portvals(orders_df, start_val=1000000, commission=9.95, impact=0.005):
    # orders_df = orders_df.sort_index()
    st_v = min(orders_df.index)
    ed_v = max(orders_df.index)
    dr = pd.date_range(st_v, ed_v)
    traded_symbols = ["JPM"]
    traded_symbol_data = get_data(symbols=traded_symbols, dates=dr)
    traded_symbol_data = traded_symbol_data.fillna(method="ffill")
    traded_symbol_data = traded_symbol_data.fillna(method="bfill")

    traded_symbol_data["traded_today"] = pd.Series(0.0, index=traded_symbol_data.index)
    traded_symbol_data["p_value"] = pd.Series(0.0, index=traded_symbol_data.index)
    # traded_symbol_data["t_value"] = pd.Series(0, index=traded_symbol_data.index)
    for symbol_key in traded_symbols:
        traded_symbol_data[symbol_key + "_shares"] = pd.Series(0.0, index=traded_symbol_data.index)

    for trade_date, row in orders_df.iterrows():
        symbol = "JPM"
        shares = row['orders']
        order = "BUY"
        if shares > 0:
            order = "BUY"
        # elif shares < 0:
        #     order = "SELL"
        # elif shares == 0:
        #     continue
        else:
            order = "SELL"
            shares = -1 * shares

        if trade_date not in traded_symbol_data.index:
            continue
        traded_value_on_day = traded_symbol_data.ix[trade_date, "traded_today"]
        symbol_rate_on_day = traded_symbol_data.ix[trade_date, symbol]

        if order == "BUY":
            multiplier = -1
        else:
            multiplier = 1

        trade = multiplier * symbol_rate_on_day * shares
        extras = symbol_rate_on_day * shares * impact + commission
        traded_value_on_day = traded_value_on_day + trade - extras
        traded_symbol_data.ix[trade_date, "traded_today"] = traded_value_on_day
        already_shares = traded_symbol_data.ix[trade_date, symbol + "_shares"]
        traded_symbol_data.ix[trade_date, symbol + "_shares"] = already_shares + (multiplier * (-1) * shares)

    for i in range(1, traded_symbol_data.shape[0]):
        for symbol_key in traded_symbols:
            traded_symbol_data.ix[i, symbol_key + "_shares"] = traded_symbol_data.ix[i, symbol_key + "_shares"] + \
                                                               traded_symbol_data.ix[i - 1, symbol_key + "_shares"]
    current_start_val = start_val
    for date_v, row in traded_symbol_data.iterrows():
        total_share_value = 0
        current_start_val = current_start_val + row["traded_today"]
        for symbol_key in traded_symbols:
            total_share_value = total_share_value + row[symbol_key + "_shares"] * traded_symbol_data.ix[
                date_v, symbol_key]

        traded_symbol_data.ix[date_v, "p_value"] = current_start_val + total_share_value
    return traded_symbol_data['p_value']


class ManualStrategy:
    def author(self):
        return 'akapoor64'

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

    def testPolicy(self, symbol="JPM", sd=dt.datetime(2010, 1, 1), ed=dt.datetime(2011, 12, 31), sv=100000):

        dates = pd.date_range(sd, ed)

        df = get_data([symbol], dates)
        df = df.fillna(method='ffill')
        df = df.fillna(method='bfill')
        df = df / df.ix[0,]
        df.sort_index(axis=0)
        portfolio_position = 0
        trade_shares = []

        stock_data = df[symbol]
        window = 30
        simple_moving_average = indicators.simple_moving_average_over_window(df[symbol], window)
        simple_moving_std = indicators.simple_moving_std_over_window(df[symbol], window)

        upper_bb, lower_bb = indicators.calculate_bollinger_bands(simple_moving_average, simple_moving_std)
        bb_value = indicators.calculate_bb_value(df[symbol], window)
        momentum = indicators.calculate_momentum_over_window(df[symbol], window)
        sma_threshold_sell = 0.25
        sma_threshold_buy = 0.25
        momentum_threshold_sell = 0.30
        momentum_threshold_buy = 0.30


        date_before = None
        is_first = True
        for date_current, row in df.iterrows():
            if is_first:
                is_first = False
                date_before = date_current
                trade_shares.append(0)
                continue

            # Using indicators
            current_price = stock_data[date_current]
            previous_price = stock_data[date_before]
            current_upper_value = upper_bb[date_current]
            previous_upper_value = upper_bb[date_before]
            current_lower_value = lower_bb[date_current]
            previous_lower_value = lower_bb[date_before]
            current_momentum = momentum[date_current]

            # previous_sma = stock_data[date_before]
            current_sma = simple_moving_average[date_current]
            #BB value : price crossing back the upper band
            if previous_price > previous_upper_value and current_price < current_upper_value:
                #do sell
                trade_shares.append(self.do_sell_trade(portfolio_position))
            elif previous_price < previous_lower_value and current_price > current_lower_value:
                #do buy
                trade_shares.append(self.do_buy_trade(portfolio_position))
            #SMA - Volitality
            elif current_price > current_sma and current_price-current_sma>sma_threshold_sell:
                #do sell
                trade_shares.append(self.do_sell_trade(portfolio_position))
            elif current_price < current_sma and current_sma - current_price > sma_threshold_buy:
                #do buy
                trade_shares.append(self.do_buy_trade(portfolio_position))
            #Momentum
            elif current_momentum > momentum_threshold_buy:
                # do buy
                trade_shares.append(self.do_buy_trade(portfolio_position))
            elif current_momentum < (momentum_threshold_sell * -1):
                # do sell
                trade_shares.append(self.do_sell_trade(portfolio_position))


            else:
                trade_shares.append(0)
            date_before = date_current
            portfolio_position = portfolio_position + trade_shares[-1]

        df_trades = pd.DataFrame(data=trade_shares, index=df.index, columns=['orders'])
        return df_trades

    def benchmark(self, symbol="JPM", sd=dt.datetime(2010, 1, 1), ed=dt.datetime(2011, 12, 31), sv=100000):
        dates = pd.date_range(sd, ed)
        df = get_data([symbol], dates)
        trade_shares = [1000, 0]
        trade_date = [df.index[0], df.index[len(df.index) - 1]]
        df_trades = pd.DataFrame(data=trade_shares, index=trade_date, columns=['orders'])
        return df_trades
