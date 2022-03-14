import pandas as pd
import numpy as np

info_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/info_df.csv')
stockdata_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/stockdata_df.csv')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'])
stockdata_df.set_index('Date', inplace=True)
unique_stocks = list(dict.fromkeys(list(info_df.loc[~info_df['Type'].isnull()]['Ticker'])))


def stock_corr(stock, type, datetype, timeframe):
    if timeframe == 'year':
        timedelta = np.timedelta64(365, 'D')
    if timeframe == 'quarter':
        timedelta = np.timedelta64(91, 'D')
    if timeframe == 'month':
        timedelta = np.timedelta64(30, 'D')
    temp_date = pd.to_datetime(info_df.loc[info_df['Ticker'] == s].loc[info_df['Type'] == type][datetype].values[0])
    temp_data_before = stockdata_df[stock + ' Return'].loc[temp_date - timedelta:temp_date]
    temp_data_after = stockdata_df[stock + ' Return'].loc[temp_date:temp_date + timedelta]
    temp_dax_before = stockdata_df['.GDAXI Return'].loc[temp_date - timedelta:temp_date]
    temp_dax_after = stockdata_df['.GDAXI Return'].loc[temp_date:temp_date + timedelta]
    corr_before = temp_data_before.corr(temp_dax_before)
    corr_after = temp_data_after.corr(temp_dax_after)
    return corr_before, corr_after


corr_df_list = []
for s in unique_stocks:
    for t in info_df.loc[~info_df['Type'].isnull()].loc[info_df['Ticker'] == s]['Type']:
        cb_y_d, ca_y_d = stock_corr(s, t, 'Date', 'year')
        cb_q_d, ca_q_d = stock_corr(s, t, 'Date', 'quarter')
        cb_m_d, ca_m_d = stock_corr(s, t, 'Date', 'month')
        cb_y_a, ca_y_a = stock_corr(s, t, 'Announcement', 'year')
        cb_q_a, ca_q_a = stock_corr(s, t, 'Announcement', 'quarter')
        cb_m_a, ca_m_a = stock_corr(s, t, 'Announcement', 'month')
        if pd.to_datetime(info_df.loc[info_df['Ticker'] == s].loc[info_df['Type'] == t]['Date'].values[0]) == np.datetime64('2021-09-20'):
            big_inc = True
        else:
            big_inc = False
        corr_df_list.append({'Ticker': s, 'Type': t, '30 -> 40': big_inc
                             , 'cb_y_d': cb_y_d, 'ca_y_d': ca_y_d, 'Delta_y_d': ca_y_d - cb_y_d
                             , 'cb_q_d': cb_q_d, 'ca_q_d': ca_q_d, 'Delta_q_d': ca_q_d - cb_q_d
                             , 'cb_m_d': cb_m_d, 'ca_m_d': ca_m_d, 'Delta_m_d': ca_m_d - cb_m_d
                             , 'cb_y_a': cb_y_a, 'ca_y_a': ca_y_a, 'Delta_y_a': ca_y_a - cb_y_a
                             , 'cb_q_a': cb_q_a, 'ca_q_a': ca_q_a, 'Delta_q_a': ca_q_a - cb_q_a
                             , 'cb_m_a': cb_m_a, 'ca_m_a': ca_m_a, 'Delta_m_a': ca_m_a - cb_m_a
                             })

corr_df = pd.DataFrame(corr_df_list)
# corr_df.sort_values(by=['Ticker'], inplace=True)

result_df_list = []
timeframes = ['year', 'quarter', 'month']
types = ['date', 'announcement']
for t in timeframes:
    timeframe = t[:1]
    for ty in types:
        type = ty[:1]
        big_inc_corr = corr_df.loc[corr_df['30 -> 40']]['Delta_' + timeframe + '_' + type].mean()
        rest_inc_corr = corr_df.loc[corr_df['Type'] == 'Included'].loc[corr_df['30 -> 40'] == False]['Delta_' + timeframe + '_' + type].mean()
        total_inc_corr = corr_df.loc[corr_df['Type'] == 'Included']['Delta_' + timeframe + '_' + type].mean()
        ex_corr = corr_df.loc[corr_df['Type'] == 'Excluded']['Delta_' + timeframe + '_' + type].mean()
        result_df_list.append({'Included': total_inc_corr, 'Included 40 ': big_inc_corr, 'Included Rest ': rest_inc_corr, 'Excluded ': ex_corr})

result_df = pd.DataFrame(result_df_list)
result_df = result_df.T
result_df.columns = ['Avg. Delta year (Date)', 'Avg. Delta quarter (Date)', 'Avg. Delta month (Date)', 'Avg. Delta year (Announcement)', 'Avg. Delta quarter (Announcement)', 'Avg. Delta month (Announcement)']

result_df.to_excel('corr_results.xlsx')
# print(result_df)
