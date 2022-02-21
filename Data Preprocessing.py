import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt

import yfinance as yf
from yahoofinancials import YahooFinancials

''' Import stock symbols as well as company name '''
stock_data = pd.read_csv('Companies_Ticker.csv', sep = ';')

''' Pulls time series data for stocks on a daily basis from 2021-1-1 until 2021-12-31.
Parameters
----------
:stock_dict:  dictionary
    Contains the stock symbols as key and the time series as values.
:stocks_as_df:  dataframe
    Contains the time series data as one df.
-------
'''

stock_dict = {}
for s in stock_data['Symbol']: # iterate for every stock indices
    # Retrieve data from Yahoo Finance
    tickerData = yf.Ticker(s)
    # Save historical data 
    stock_dict[s] = tickerData.history(period='1d', start='2021-1-1', end='2021-12-31')
# Concatenate all data
stocks_as_df = pd.concat(stock_list, axis = 0)

''' Pulls time series data for stocks on a daily basis from 2021-1-1 until 2021-12-31.
Parameters
----------
:stock_dict:  dictionary
    Contains the stock symbols as key and the time series as values.
:stocks_as_df:  dataframe
    Contains the time series data as one df.
-------
'''

stock_dict = {}
for s in stock_data['Symbol']: # iterate for every stock indices
    # Retrieve data from Yahoo Finance
    tickerData = yf.Ticker(s)
    # Save historical data 
    stock_dict[s] = yf.download(s, start='2021-1-1', end='2021-12-31', progress=False)
# Concatenate all data
stocks_as_df = pd.concat(stock_list, axis = 0)

''' Transform daily data to weekly 
Parameters
----------
:stock_weekly:  dictionary
    Contains the stock symbols as key and the weekly adj. closing prices as values.
-------
'''
stock_weekly = {}
for s in stock_data['Symbol']:
    stock_weekly[s] = stock_dict[s['Adj Close'].resample("W").mean()