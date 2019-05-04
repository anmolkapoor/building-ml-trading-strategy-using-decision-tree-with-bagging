# Indicator - Simple moving average
def simple_moving_average_over_window(values, window):
    return values.rolling(window).mean()


def simple_moving_std_over_window(values, window):
    return values.rolling(window).std()


def calculate_bb_value(values, window):
    # Return Bollinger Value
    BB = (values - simple_moving_average_over_window(values, window)) / (
            2 * simple_moving_std_over_window(values, window))
    return BB


# Indicator - Bollinger bands
def calculate_bollinger_bands(rm, rstd):
    upper_band = rm + rstd * 2
    lower_band = rm - rstd * 2
    return upper_band, lower_band


def calculate_momentum_over_window(values, window):
    # Return Momentum Value
    return (values / values.shift(window)) - 1


