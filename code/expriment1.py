
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt

from util import get_data
from StrategyLearner import StrategyLearner
from ManualStrategy import ManualStrategy


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


def run():
    start_date = dt.datetime(2008, 01, 01)
    end_date = dt.datetime(2009, 12, 31)

    symbol = 'JPM'
    # Commission: $9.95, Impact: 0.005.
    stlearner = StrategyLearner()

    stlearner.addEvidence(symbol, start_date, end_date,100000)
    stlearner_trades = stlearner.testPolicy(symbol,start_date,end_date,100000)
    stlearner_port_values = compute_portvals(orders_df=stlearner_trades, start_val=100000,
                                           commission=0, impact=0)

    manual_strategy = ManualStrategy()
    manual_strategy_trades = manual_strategy.testPolicy(symbol, start_date, end_date, 100000)
    optimized_port_vals = compute_portvals(orders_df=manual_strategy_trades, start_val=100000,
                                           commission=0, impact=0)

    benchmark_trades = manual_strategy.benchmark(symbol, start_date, end_date, 100000)
    benchmark_port_vals = compute_portvals(orders_df=benchmark_trades, start_val=100000,
                                           commission=0.00, impact=0.00)

    print "Printing stats : ", start_date, " ", end_date

    st_cummulative_returns, st_average_daily_return, st_std_daily_return = compute_portfolio_stats(
        stlearner_port_values)

    opt_cummulative_returns, opt_average_daily_return, opt_std_daily_return = compute_portfolio_stats(
        optimized_port_vals)
    bnch_cummulative_returns, bnch_average_daily_return, bnch_std_daily_return = compute_portfolio_stats(
        benchmark_port_vals)

    print "Date Range: {} to {}".format(start_date, end_date)

    print
    print "Cumulative Return of Strategy learner: {}".format(st_cummulative_returns)
    print "Standard Deviation of Strategy learner: {}".format(st_std_daily_return)
    print "Average Daily Return of Strategy learner: {}".format(st_average_daily_return)
    print "Final Portfolio Value of Strategy learner: {}".format(stlearner_port_values[-1])

    print
    print "Cumulative Return of Manual Strategy: {}".format(opt_cummulative_returns)
    print "Standard Deviation of Manual Strategy: {}".format(opt_std_daily_return)
    print "Average Daily Return of Manual Strategy: {}".format(opt_average_daily_return)
    print "Final Portfolio Value of Manual Strategy: {}".format(optimized_port_vals[-1])
    print
    print "Cumulative Return of Benchmark: {}".format(bnch_cummulative_returns)
    print "Standard Deviation of Benchmark: {}".format(bnch_std_daily_return)
    print "Average Daily Return of Benchmark: {}".format(bnch_average_daily_return)
    print "Final Benchmark Value of Benchmark: {}".format(benchmark_port_vals[-1])

    stlearner_port_values_normalized = (stlearner_port_values/stlearner_port_values.ix[0,]).to_frame()
    optimized_port_vals_normalized = (optimized_port_vals / optimized_port_vals.ix[0,]).to_frame()
    benchmark_port_vals_normalized = (benchmark_port_vals / benchmark_port_vals.ix[0,]).to_frame()

    chart_1 = benchmark_port_vals_normalized.join(optimized_port_vals_normalized, lsuffix='_benchmark',
                                                  rsuffix='_strategy').join(stlearner_port_values_normalized,lsuffix='_',rsuffix='_stlearner')

    chart_1.columns = ['Benchmark', 'ManualStrategy','StrategyLearner']
    ax1 = chart_1.plot(title="Benchmark, ManualStrategy and StrategyLearner portfolio (Normalized)", fontsize=12,
                       color=["green", "red","blue"], lw=.7)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Portfolio")

    plt.savefig("experiment_1_graph")
    pass


if __name__ == '__main__':
    run()
