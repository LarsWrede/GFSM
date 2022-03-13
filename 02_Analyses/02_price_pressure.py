import sys

import pandas as pd
import numpy as np
from datetime import timedelta
from datetime import datetime
from lib import dir_utils

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
                       parse_dates=['Announcement'])
    del info['Unnamed: 0']

    vol = pd.DataFrame(data={col.split(" ")[0]: stocks[col] for col in stocks.columns if 'Volume' in col})
    vol.insert(0, 'Date_Increment_ID', range(0, len(vol)))
    close = pd.DataFrame(data={col.split(" ")[0]: stocks[col] for col in stocks.columns if 'Close' in col})

    return vol, close, info

def calc_mvr_multiple_days(year_start, year_end, inclusions, day_range, stocks, market_symbol):
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

    :return:
        mean, stddev, N of all Volume Ratios of included stocks in the selected time period
    """
    s = pd.Series([], dtype='float64')
    for i in day_range:
        s_, _, _, n = calc_mvr(year_start, year_end, inclusions, i, stocks, market_symbol)
        s = s.append(s_)
    return s, s.mean(), s.std(), n


def calc_mvr(year_start, year_end, inclusions, day, stocks, market_symbol):
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
        stock symbol for the market for the entire time horizon

    :return:
        series (the series of VRs), mean, stddev, N of all Volume Ratios of included stocks in the selected time period
    """

    year_start = datetime.strptime('01.01.' + str(year_start), '%d.%m.%Y')
    year_end = datetime.strptime('31.12.' + str(year_end), '%d.%m.%Y')

    inclusions_in_time_period = inclusions[
        (inclusions['Announcement'] >= year_start) & (inclusions['Announcement'] <= year_end)]

    apply_calc_vr = lambda row: calc_vr(row['Announcement'], day, stocks, row['Ticker'], market_symbol)
    vr_series = inclusions_in_time_period.apply(apply_calc_vr, axis=1)
    return vr_series, vr_series.mean(), vr_series.std(), vr_series.size


def calc_vr(announcement_date, day, stocks, stock_symbol, market_symbol):
    """
    VR of stock i is the ratio of Volume of stock i traded in period t to volume traded in the market times volume traded
        in the market over the past 8 weeks over volume of stock i in the past 8 weeks
    $ VR_{it} = \frac{V_{it}}{V_{mt}} * \frac{V_m}{V_i} $

    :param announcement_date:
        the announcement date
    :param day:
        how many days after the announcement date is the "event period" i?
    :param stock:
        stock data of single stock for the entire time horizon
    :param market:
        stock data for the market for the entire time horizon
    """

    start_date = announcement_date - timedelta(weeks=8)
    i = stocks[stocks.index == announcement_date]['Date_Increment_ID'].iloc[0] + day
    i = stocks[stocks['Date_Increment_ID'] == i].index[0]

    stock = stocks[stock_symbol]
    market = stocks[market_symbol]

    i_slice = stock[(stock.index >= start_date) & (stock.index <= announcement_date)]
    m_slice = market[(market.index >= start_date) & (market.index <= announcement_date)]

    v_it = stock[stock.index == i].values[0]
    v_mt = market[market.index == i].values[0]

    v_i = i_slice.mean()
    v_m = m_slice.mean()

    return (v_it / v_mt) * (v_m / v_i)


volumes, prices, info = prep_dfs()
inclusions = info[info['Type'] == 'Included']

#print(calc_vr(inclusions['Announcement'].iloc[0], 1, volumes, 'HEIG.DE', '.GDAXI'))
#print(inclusions['Announcement'].iloc[0])

print(calc_mvr(2010, 2012, inclusions, 1, volumes, '.GDAXI'))
print(calc_mvr(2010, 2012, inclusions, 2, volumes, '.GDAXI'))
print(calc_mvr(2010, 2012, inclusions, 3, volumes, '.GDAXI'))
print(calc_mvr(2010, 2012, inclusions, 4, volumes, '.GDAXI'))
print(calc_mvr(2010, 2012, inclusions, 5, volumes, '.GDAXI'))

print(calc_mvr_multiple_days(2010, 2022, inclusions, range(1, 5), volumes, '.GDAXI'))

