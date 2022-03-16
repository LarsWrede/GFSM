import pandas as pd
from datetime import timedelta
from datetime import datetime
from lib import dir_utils
import scipy.stats

git_uri = dir_utils.get_local_git_uri()
delim = dir_utils.get_directory_delimiter()


def prep_dfs():
    """
    loads, prepares and returns the important dataframes for this script
    :return: stockdata volume, stockdata close, info
    """
    stocks = pd.read_csv(git_uri + delim + '01_Data_and_Preprocessing' + delim + 'stockdata_df.csv',
                         parse_dates=['Date'], index_col='Date')
    info = pd.read_csv(git_uri + delim + '01_Data_and_Preprocessing' + delim + 'info_df.csv',
                       parse_dates=['Date', 'Announcement'])
    del info['Unnamed: 0']

    vol = pd.DataFrame(data={col.split(" ")[0]: stocks[col] for col in stocks.columns if 'Volume' in col})
    vol.insert(0, 'Date_Increment_ID', range(0, len(vol)))
    close = pd.DataFrame(data={col.split(" ")[0]: stocks[col] for col in stocks.columns if 'Close' in col})

    returns = pd.DataFrame(data={col: close[col].pct_change() for col in close.columns})

    close.insert(0, 'Date_Increment_ID', range(0, len(vol)))
    returns.insert(0, 'Date_Increment_ID', range(0, len(vol)))

    return vol, returns, close, info


def calc_mvr_multiple_days(year_start, year_end, inclusions, day_range, stocks, market_symbol,
                           event_type='Announcement'):
    """
    Calculates MVR measures and takes the average over multiple days.

    :param year_start:
        year in which to start checking for inclusions to the index
    :param year_end:
        year in which to end checking for inclusions to the index
    :param inclusions:
        dataframe showing inclusions to an index
        Needed columns:
            Aufgenommen - Date included to the index
            Symbol - stock's symbol
    :param day_range:
        range of days for "event period" i
    :param stocks:
        stock data of all stocks for the entire time horizon
    :param market_symbol:
        stock symbol for the market for the entire time horizon
    :param event_type:
        The event date to use.
        'Announcement' for announcement date of the inclusion
        'Date' for inclusion date

    :return:
        mean, stddev, N of all Volume Ratios of included stocks in the selected time period
    """
    s = pd.Series([], dtype='float64')
    for i in day_range:
        s_, _, _, n = calc_mvr(year_start, year_end, inclusions, i, stocks, market_symbol, event_type)
        s = s.append(s_)
    return s, s.mean(), s.std(), n


def calc_mvr(year_start, year_end, inclusions, day, stocks, market_symbol, event_type='Announcement'):
    """
    MVR of stock i is the mean VR (Volume Ratio) for event period t
    VR of stock i is the ratio of Volume of stock i traded in period t to volume traded in the market times volume traded
        in the market over the past 8 weeks over volume of stock i in the past 8 weeks

    :param year_start:
        year in which to start checking for inclusions to the index
    :param year_end:
        year in which to end checking for inclusions to the index
    :param inclusions:
        dataframe showing inclusions to an index
        Needed columns:
            Aufgenommen - Date included to the index
            Symbol - stock's symbol
    :param day:
        how many days after the announcement date is the "event period" i?
    :param stocks:
        stock data of all stocks for the entire time horizon
    :param market_symbol:
        stock symbol for the market
    :param event_type:
        The event date to use.
        'Announcement' for announcement date of the inclusion
        'Date' for inclusion date

    :return:
        series (the series of VRs), mean, stddev, N of all Volume Ratios of included stocks in the selected time period
    """

    year_start = datetime.strptime('01.01.' + str(year_start), '%d.%m.%Y')
    year_end = datetime.strptime('31.12.' + str(year_end), '%d.%m.%Y')

    inclusions_in_time_period = inclusions[
        (inclusions[event_type] >= year_start) & (inclusions[event_type] <= year_end)]

    apply_calc_vr = lambda row: calc_vr(row[event_type], day, stocks, row['Ticker'], market_symbol)
    vr_series = inclusions_in_time_period.apply(apply_calc_vr, axis=1)
    return vr_series, vr_series.mean(), vr_series.std(), vr_series.size


def calc_vr(event_date, day, stocks, stock_symbol, market_symbol):
    """
    VR of stock i is the ratio of Volume of stock i traded in period t to volume traded in the market times volume traded
        in the market over the past 8 weeks over volume of stock i in the past 8 weeks
    $ VR_{it} = \frac{V_{it}}{V_{mt}} * \frac{V_m}{V_i} $

    :param event_date:
        the date for which to calculate the VR
    :param day:
        how many days after the announcement date is the "event period" i?
    :param stock_symbol:
        stock symbol of the stock
    :param market_symbol:
        stock symbol for the market
    """

    start_date = event_date - timedelta(weeks=8)
    i = stocks[stocks.index == event_date]['Date_Increment_ID'].iloc[0] + day
    i = stocks[stocks['Date_Increment_ID'] == i].index[0]

    stock = stocks[stock_symbol]
    market = stocks[market_symbol]

    i_slice = stock[(stock.index >= start_date) & (stock.index <= event_date)]
    m_slice = market[(market.index >= start_date) & (market.index <= event_date)]

    v_it = stock[stock.index == i].values[0]
    v_mt = market[market.index == i].values[0]

    v_i = i_slice.mean()
    v_m = m_slice.mean()

    return (v_it / v_mt) * (v_m / v_i)


def calc_mean_return_multiple_days(year_start, year_end, inclusions, day_range, returns, event_type='Announcement'):
    s = pd.Series([], dtype='float64')
    for i in day_range:
        s_, _, _, n = calc_mean_return(year_start, year_end, inclusions, i, returns, event_type)
        s = s.append(s_)
    return s, s.mean(), s.std(), n


def calc_mean_return(year_start, year_end, inclusions, day, returns, event_type='Announcement'):
    year_start = datetime.strptime('01.01.' + str(year_start), '%d.%m.%Y')
    year_end = datetime.strptime('31.12.' + str(year_end), '%d.%m.%Y')

    inclusions_in_time_period = inclusions[
        (inclusions[event_type] >= year_start) & (inclusions[event_type] <= year_end)]

    returns_list = inclusions_in_time_period.apply(lambda row:
                                                   get_return_x_days_after_event(row[event_type],
                                                                                 day,
                                                                                 returns,
                                                                                 row['Ticker']), axis=1)
    return returns_list, returns_list.mean(), returns_list.std(), returns_list.size


def get_return_x_days_after_event(event_date, day, returns, stock_symbol):
    i = returns[returns.index == event_date]['Date_Increment_ID'].iloc[0] + day
    i = returns[returns['Date_Increment_ID'] == i].index[0]

    stock = returns[stock_symbol]

    return stock[stock.index == i].values[0]


def calc_volume_table(inclusions, stocks, market_symbol, year_ranges, event_type='Announcement'):
    df = pd.DataFrame(
        columns=['N', 'MVR Day 1', 'STD Day 1', 't Day 1', 'p Day 1', '% > 1 Day 1', 'MVR Day 1-5', 'STD Day 1-5',
                 't Day 1-5', 'p Day 1-5', '% > 1 Day 1-5'])

    calc_p = lambda s: s.gt(1).sum() / s.size * 100
    t_test = lambda s: scipy.stats.ttest_1samp(s, 1)

    def calc_and_append_with_index(df, y1, y2, inclusions, stocks, market_symbol, event_type, index):
        s, m, stdev, n = calc_mvr(y1, y2, inclusions, 1, stocks, market_symbol, event_type)
        if n <= 1:
            return df
        t = t_test(s)
        p = calc_p(s)
        d = {'N': n, 'MVR Day 1': m, 'STD Day 1': stdev, 't Day 1': t.statistic, 'p Day 1': t.pvalue, '% > 1 Day 1': p}
        s, m, stdev, _ = calc_mvr_multiple_days(y1, y2, inclusions, range(1, 6), stocks, market_symbol, event_type)
        d['MVR Day 1-5'] = m
        d['STD Day 1-5'] = stdev
        t = t_test(s)
        d['t Day 1-5'] = t.statistic
        d['p Day 1-5'] = t.pvalue
        d['% > 1 Day 1-5'] = calc_p(s)

        return df.append(pd.DataFrame(data=d, index=[index]))

    for (y1, y2) in year_ranges:
        df = calc_and_append_with_index(df, y1, y2, inclusions, stocks, market_symbol, event_type,
                                        str(y1) if y1 == y2 else str(y1) + '-' + str(y2))

    df = calc_and_append_with_index(df, 2021, 2021, inclusions[inclusions['Announcement'] == '2021-09-03'], stocks,
                                    market_symbol, event_type, 'DAX 30 -> 40')

    df = calc_and_append_with_index(df, 2021, 2021, inclusions[inclusions['Announcement'] != '2021-09-03'], stocks,
                                    market_symbol, event_type, '2021 Without 30 -> 40')

    df = calc_and_append_with_index(df, 2010, 2021, inclusions[inclusions['Announcement'] != '2021-09-03'], stocks,
                                    market_symbol, event_type, 'All Without 30 -> 40')

    return df


def calc_return_table(inclusions, returns, year_ranges, event_type='Announcement'):
    df = pd.DataFrame(
        columns=['N', 'Mean Day 1', 'STD Day 1', 't Day 1', 'p Day 1', '% > 0 Day 1', 'Mean Day 1-5', 'STD Day 1-5',
                 't Day 1-5', 'p Day 1-5', '% > 0 Day 1-5'])

    calc_p = lambda s: s.gt(0).sum() / s.size * 100
    t_test = lambda s: scipy.stats.ttest_1samp(s, 0)

    def calc_and_append_with_index(df, y1, y2, inclusions, returns, event_type, index):
        s, m, stdev, n = calc_mean_return(y1, y2, inclusions, 1, returns, event_type)
        if n <= 1:
            return df
        t = t_test(s)
        p = calc_p(s)
        d = {'N': n, 'Mean Day 1': m, 'STD Day 1': stdev, 't Day 1': t.statistic, 'p Day 1': t.pvalue, '% > 0 Day 1': p}
        s, m, stdev, _ = calc_mean_return_multiple_days(y1, y2, inclusions, range(1, 6), returns, event_type)
        d['Mean Day 1-5'] = m
        d['STD Day 1-5'] = stdev
        t = t_test(s)
        d['t Day 1-5'] = t.statistic
        d['p Day 1-5'] = t.pvalue
        d['% > 0 Day 1-5'] = calc_p(s)

        return df.append(pd.DataFrame(data=d, index=[index]))

    for (y1, y2) in year_ranges:
        df = calc_and_append_with_index(df, y1, y2, inclusions, returns, event_type,
                                        str(y1) if y1 == y2 else str(y1) + '-' + str(y2))

    df = calc_and_append_with_index(df, 2021, 2021, inclusions[inclusions['Announcement'] == '2021-09-03'], returns,
                                    event_type, 'DAX 30 -> 40')

    df = calc_and_append_with_index(df, 2021, 2021, inclusions[inclusions['Announcement'] != '2021-09-03'], returns,
                                    event_type, '2021 Without 30 -> 40')

    df = calc_and_append_with_index(df, 2010, 2021, inclusions[inclusions['Announcement'] != '2021-09-03'], returns,
                                    event_type, 'Without 30 -> 40')
    return df


def calc_vola_table(inclusions, returns, year_ranges, event_type='Announcement'):
    df = pd.DataFrame(
        columns=['N', 'Mean', 'STD', 't', 'p', '% > 0'])

    calc_p = lambda s: s.gt(0).sum() / s.size * 100
    t_test = lambda s: scipy.stats.ttest_1samp(s, 0)

    def calc_and_append_with_index(df, y1, y2, inclusions, returns, event_type, index):
        s, m, stdev, n = calc_mean_vola_change(inclusions, returns, y1, y2, event_type)
        if n <= 1:
            return df
        t = t_test(s)
        p = calc_p(s)
        d = {'N': n, 'Mean': m, 'STD': stdev, 't': t.statistic, 'p': t.pvalue, '% > 0': p}

        return df.append(pd.DataFrame(data=d, index=[index]))

    for (y1, y2) in year_ranges:
        df = calc_and_append_with_index(df, y1, y2, inclusions, returns, event_type,
                                        str(y1) if y1 == y2 else str(y1) + '-' + str(y2))

    df = calc_and_append_with_index(df, 2021, 2021, inclusions[inclusions['Announcement'] == '2021-09-03'], returns,
                                    event_type, 'DAX 30 -> 40')

    df = calc_and_append_with_index(df, 2021, 2021, inclusions[inclusions['Announcement'] != '2021-09-03'], returns,
                                    event_type, '2021 Without 30 -> 40')

    df = calc_and_append_with_index(df, 2010, 2021, inclusions[inclusions['Announcement'] != '2021-09-03'], returns,
                                    event_type, 'Without 30 -> 40')
    return df


def calc_mean_vola_change(inclusions, returns, year_start, year_end, event_type='Announcement'):
    year_start = datetime.strptime('01.01.' + str(year_start), '%d.%m.%Y')
    year_end = datetime.strptime('31.12.' + str(year_end), '%d.%m.%Y')

    inclusions_in_time_period = inclusions[
        (inclusions[event_type] >= year_start) & (inclusions[event_type] <= year_end)]

    vola_changes = inclusions_in_time_period.apply(lambda row: vola_change_before_to_after_event(returns,
                                                                                                 row['Ticker'],
                                                                                                 row[event_type]),
                                                   axis=1)

    return vola_changes, vola_changes.mean(), vola_changes.std(), vola_changes.size


def vola_change_before_to_after_event(returns, stock_symbol, event_date):
    """

    :param returns:
        Dataframe of all returns
    :param stock_symbol:
        Ticker of the stock in question
    :param event_date:
        date of the event
    :return:

    """
    vola_period = 80

    i = returns[returns.index == event_date]['Date_Increment_ID'].iloc[0] + vola_period
    end_date = returns[returns['Date_Increment_ID'] == i].index[0]
    i = returns[returns.index == event_date]['Date_Increment_ID'].iloc[0] + 1
    start_date = returns[returns['Date_Increment_ID'] == i].index[0]

    vola_after_event = calc_volatility(returns[stock_symbol], start_date, end_date)

    i = returns[returns.index == event_date]['Date_Increment_ID'].iloc[0] - 1
    end_date = returns[returns['Date_Increment_ID'] == i].index[0]
    i = returns[returns.index == event_date]['Date_Increment_ID'].iloc[0] - vola_period
    start_date = returns[returns['Date_Increment_ID'] == i].index[0]

    vola_before_event = calc_volatility(returns[stock_symbol], start_date, end_date)

    return vola_after_event - vola_before_event


def calc_volatility(returns, date_start, date_end):
    """
    Calculates the volatility of a stock in a specific time frame
    :param returns:
        Series of returns of a single stock
    :param date_start:
        first day of the time frame
    :param date_end:
        last day of the time frame
    """

    prices_in_time_frame = returns[(returns.index >= date_start) & (returns.index <= date_end)]
    return prices_in_time_frame.std()


volumes, returns, close, info = prep_dfs()
inclusions = info[info['Type'] == 'Included']
exclusions = info[info['Type'] == 'Excluded']
# print(inclusions)
"""
print(calc_vr(inclusions['Announcement'].iloc[0], 1, volumes, 'HEIG.DE', '.GDAXI'))
print(inclusions['Announcement'].iloc[0])

print(calc_mvr(2010, 2012, inclusions, 1, volumes, '.GDAXI'))
print(calc_mvr(2010, 2012, inclusions, 2, volumes, '.GDAXI'))
print(calc_mvr(2010, 2012, inclusions, 3, volumes, '.GDAXI'))
print(calc_mvr(2010, 2012, inclusions, 4, volumes, '.GDAXI'))
print(calc_mvr(2010, 2012, inclusions, 5, volumes, '.GDAXI'))

print(calc_mvr(2010, 2022, inclusions, 1, volumes, '.GDAXI'))
s, m, stdev, n = calc_mvr(2010, 2022, inclusions, 1, volumes, '.GDAXI')
t = scipy.stats.ttest_1samp(s, 1)
p = s.gt(1).sum() / s.size
print(t, p)

print(calc_mvr_multiple_days(2010, 2022, inclusions, range(1, 6), volumes, '.GDAXI'))
s, m, stdev, _ = calc_mvr_multiple_days(2010, 2022, inclusions, range(1, 6), volumes, '.GDAXI')
t = scipy.stats.ttest_1samp(s, 1).statistic
p = s.gt(1).sum() / s.size
print(t, p)

#print(inclusions['Date'])


#print(prices)
#print(get_return_x_days_after_event('2008-01-02', 1, prices, '.GDAXI'))

#print(calc_mean_return(2010, 2012, inclusions, 1, prices))
#print(calc_mean_return(2010, 2012, inclusions, 2, prices))
#print(calc_mean_return(2010, 2012, inclusions, 3, prices))
#print(calc_mean_return(2010, 2012, inclusions, 4, prices))
#print(calc_mean_return(2010, 2012, inclusions, 5, prices))

#print(calc_mean_return_multiple_days(2010, 2012, inclusions, range(1, 6), prices))
"""

year_ranges = [(2010, 2021), (2010, 2015), (2016, 2021)]
year_ranges += [(x, x) for x in range(2010, 2022)]
"""
with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    print('Inclusions\n--------------------------------------------')
    print('Announcement Day')
    print(calc_volume_table(inclusions, volumes, '.GDAXI', year_ranges, event_type='Announcement'))
    print(calc_return_table(inclusions, returns, year_ranges, event_type='Announcement'))

    print('Inclusion Day')
    print(calc_volume_table(inclusions, volumes, '.GDAXI', year_ranges, event_type='Date'))
    print(calc_return_table(inclusions, returns, year_ranges, event_type='Date'))

    print('Exclusions\n--------------------------------------------')
    print('Announcement Day')
    print(calc_volume_table(exclusions, volumes, '.GDAXI', year_ranges, event_type='Announcement'))
    print(calc_return_table(exclusions, returns, year_ranges, event_type='Announcement'))

    print('Exclusion Day')
    print(calc_volume_table(exclusions, volumes, '.GDAXI', year_ranges, event_type='Date'))
    print(calc_return_table(exclusions, returns, year_ranges, event_type='Date'))
"""

#print(calc_vola_table(inclusions, returns, year_ranges, 'Announcement'))
#print(calc_vola_table(inclusions, returns, year_ranges, 'Date'))
#
#print('Exclusions\n--------------------------------------------')
#print(calc_vola_table(exclusions, returns, year_ranges, 'Announcement'))
#print(calc_vola_table(exclusions, returns, year_ranges, 'Date'))


#print(returns[returns.index=='2021-09-20'])

print(calc_vr(exclusions[exclusions['Ticker'] == 'WDIG.H']['Date'].values[0], 1, volumes, 'WDIG.H', '.GDAXI'))