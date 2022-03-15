import pandas as pd
import numpy as np
from scipy.stats import ttest_ind

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
        _, p_y_d = ttest_ind(cb_y_d, ca_y_d, equal_var=False)
        cb_q_d, ca_q_d = stock_corr(s, t, 'Date', 'quarter')
        _, p_q_d = ttest_ind(cb_q_d, ca_q_d, equal_var=False)
        cb_m_d, ca_m_d = stock_corr(s, t, 'Date', 'month')
        _, p_m_d = ttest_ind(cb_m_d, ca_m_d, equal_var=False)
        cb_y_a, ca_y_a = stock_corr(s, t, 'Announcement', 'year')
        _, p_y_a = ttest_ind(cb_y_a, ca_y_a, equal_var=False)
        cb_q_a, ca_q_a = stock_corr(s, t, 'Announcement', 'quarter')
        _, p_q_a = ttest_ind(cb_q_a, ca_q_a, equal_var=False)
        cb_m_a, ca_m_a = stock_corr(s, t, 'Announcement', 'month')
        _, p_m_a = ttest_ind(cb_m_a, ca_m_a, equal_var=False)
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
        _, big_inc_p = ttest_ind(corr_df.loc[corr_df['30 -> 40']]['cb_' + timeframe + '_' + type], corr_df.loc[corr_df['30 -> 40']]['ca_' + timeframe + '_' + type], equal_var=False)
        rest_inc_corr = corr_df.loc[corr_df['Type'] == 'Included'].loc[corr_df['30 -> 40'] == False]['Delta_' + timeframe + '_' + type].mean()
        _, rest_inc_p = ttest_ind(corr_df.loc[corr_df['Type'] == 'Included'].loc[corr_df['30 -> 40'] == False]['cb_' + timeframe + '_' + type], corr_df.loc[corr_df['Type'] == 'Included'].loc[corr_df['30 -> 40'] == False]['ca_' + timeframe + '_' + type], equal_var=False)
        total_inc_corr = corr_df.loc[corr_df['Type'] == 'Included']['Delta_' + timeframe + '_' + type].mean()
        _, total_inc_p = ttest_ind(corr_df.loc[corr_df['Type'] == 'Included']['cb_' + timeframe + '_' + type], corr_df.loc[corr_df['Type'] == 'Included']['ca_' + timeframe + '_' + type], equal_var=False)
        ex_corr = corr_df.loc[corr_df['Type'] == 'Excluded']['Delta_' + timeframe + '_' + type].mean()
        _, ex_p = ttest_ind(corr_df.loc[corr_df['Type'] == 'Excluded']['cb_' + timeframe + '_' + type], corr_df.loc[corr_df['Type'] == 'Excluded']['ca_' + timeframe + '_' + type], equal_var=False)
        result_df_list.append({'Included': total_inc_corr, 'Included_40': big_inc_corr, 'Included_rest': rest_inc_corr, 'Excluded': ex_corr})
        result_df_list.append({'Included': total_inc_p, 'Included_40': big_inc_p, 'Included_rest': rest_inc_p, 'Excluded': ex_p})

result_df = pd.DataFrame(result_df_list)
result_df = result_df.T
result_df.columns = ['Avg. Delta year (Date)', 'p_value', 'Avg. Delta quarter (Date)', 'p_value', 'Avg. Delta month (Date)', 'p_value', 'Avg. Delta year (Announcement)', 'p_value', 'Avg. Delta quarter (Announcement)', 'p_value', 'Avg. Delta month (Announcement)', 'p_value']

result_df.to_excel('corr_results.xlsx')
# print(result_df)
