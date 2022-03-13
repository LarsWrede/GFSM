import pandas as pd
import numpy as np
import performanceanalytics.table.table as pat

info_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/info_df.csv')
stockdata_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/stockdata_df.csv')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'])
stockdata_df.set_index('Date', inplace=True)
unique_stocks = list(dict.fromkeys(list(info_df.loc[~info_df['Type'].isnull()]['Ticker'])))

l = info_df.iloc[:,6]
l = [s + ' Return' for s in l]

''' Calculating measures of location, statistical dispersion and shape
Parameters
----------
:des_stat:  dataframe
    Contains the descriptive statistics.
-------
'''

des_stat = pd.DataFrame(columns=l, 
                        index=['Observations', 'NAs', 'Minimum', 'Quartile 1', 'Median', 
                               'Artithmetic Mean', 'Geometric Mean', 'Quartile 3', 'Maximum', 'SE Mean',
                               'LCL Mean (.95)', 'UCL Mean (.95)', 'Variance', 'Stdev', 'Skewness','Kurtosis'])

for s in l:
    df = pd.DataFrame(stockdata_df[s])
    des_stat[s] = pat.stats_table(df, manager_col=0).iloc[:,0]
des_stat
