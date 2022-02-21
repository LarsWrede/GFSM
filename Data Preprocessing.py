import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import yfinance as yf
import performanceanalytics.table.table as pat

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
    stock_dict[s] = yf.download(s, start='2021-1-1', end='2021-12-31', progress=False)
# Concatenate all data
stocks_as_df = pd.concat(stock_dict, axis = 0)

''' Transform daily price data to daily returns
Parameters
----------
:stock_weekly:  dictionary
    Contains the stock symbols as key and the weekly returns as values.
-------
'''
returns_daily = {}
for s in stock_data['Symbol']:
    returns_daily[s] = stock_dict['ADS.DE']['Adj Close'].pct_change()

''' Transform daily price data to weekly returns
Parameters
----------
:stock_weekly:  dictionary
    Contains the stock symbols as key and the weekly returns as values.
-------
'''
returns_weekly = {}
for s in stock_data['Symbol']:
    returns_weekly[s] = stock_dict[s]['Adj Close'].resample('W').ffill().pct_change()

''' Calculating measures of location, statistical dispersion and shape
Parameters
----------
:des_stat:  dataframe
    Contains the descriptive statistics.
-------
'''

des_stat = pd.DataFrame(columns=stock_data['Symbol'], 
                        index=['Observations', 'NAs', 'Minimum', 'Quartile 1', 'Median', 
                               'Artithmetic Mean', 'Geometric Mean', 'Quartile 3', 'Maximum', 'SE Mean',
                               'LCL Mean (.95)', 'UCL Mean (.95)', 'Variance', 'Stdev', 'Skewness','Kurtosis'])

for s in stock_data['Symbol']:
    df = pd.DataFrame(returns_daily[s])
    des_stat[s] = pat.stats_table(df, manager_col=0)

''' Calculating the downside statistics
Parameters
----------
:down_stat:  dataframe
    Contains the downside statistics.
-------
'''
down_stat = pd.DataFrame(columns=stock_data['Symbol'], 
                        index=['Semi Deviation', 'Gain Deviation', 'Loss Deviation', 'Downside Deviation (MAR=2.0%)',
                               'Downside Deviation (rf=0.5%)', 'Downside Deviation (0%)', 'Maximum Drawdown', 
                               'Historical VaR (95%)', 'Historical ES (95%)', 'Modified VaR (95%)', 'Modified ES (95%)'])

for s in stock_data['Symbol']:
    df = pd.DataFrame(returns_daily[s])
    down_stat[s] = pat.create_downside_table(df,0)‚