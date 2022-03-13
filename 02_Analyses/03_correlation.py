import pandas as pd
import numpy as np

info_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/info_df.csv')
stockdata_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/stockdata_df.csv')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'])
stockdata_df.set_index('Date', inplace=True)
unique_stocks = list(dict.fromkeys(list(info_df.loc[~info_df['Type'].isnull()]['Ticker'])))

corr_df_list = []
for s in unique_stocks:
    for t in info_df.loc[~info_df['Type'].isnull()].loc[info_df['Ticker'] == s]['Type']:
        temp_date = pd.to_datetime(info_df.loc[info_df['Ticker'] == s].loc[info_df['Type'] == t]['Date'].values[0])
        temp_data_before = stockdata_df[s + ' Return'].loc[temp_date - np.timedelta64(365, 'D'):temp_date]
        temp_data_after = stockdata_df[s + ' Return'].loc[temp_date:temp_date + np.timedelta64(365, 'D')]
        temp_dax_before = stockdata_df['.GDAXI Return'].loc[temp_date - np.timedelta64(365, 'D'):temp_date]
        temp_dax_after = stockdata_df['.GDAXI Return'].loc[temp_date:temp_date + np.timedelta64(365, 'D')]
        corr_before = temp_data_before.corr(temp_dax_before)
        corr_after = temp_data_after.corr(temp_dax_after)
        if temp_date == np.datetime64('2021-09-20'):
            big_inc = True
        else:
            big_inc = False
        corr_df_list.append({'Ticker': s, 'Type': t, '30 -> 40': big_inc, 'Corr_before': corr_before, 'Corr_after': corr_after, 'Delta': corr_after - corr_before})

corr_df = pd.DataFrame(corr_df_list)
corr_df.sort_values(by=['Delta'], inplace=True)

print()
