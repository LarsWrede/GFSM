import pandas as pd
from lib import dir_utils

"""Creating Info DataFrame
* Joining all Stocks that where at some point in time after 2010 in the DAX.
* Stocks that were in the Dax the whole time have will have all movement related columns set to N/A.
* Both dates are formatted in pandas datetime format.
* Symbol stands for the Yahoo Finance Ticker while Ticker is the Reuters one. This is due to the fact, that we first worked with yf but then switched to Reuters.
"""

exclusions = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/DAX_excluded_2010-2021.csv', sep=';').rename(columns={'Ausgeschieden': 'Date'})
exclusions['Type'] = 'Excluded'
exclusions['Date'] = pd.to_datetime(exclusions['Date'])

inclusions = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/DAX_included_2010-2021.csv', sep=';').rename(columns={'Aufgenommen': 'Date'})
inclusions['Type'] = 'Included'
inclusions['Date'] = pd.to_datetime(inclusions['Date'])

temp_rest = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/Companies_Ticker.csv', sep=';')
rest = temp_rest[temp_rest['Symbol'].isin(inclusions['Symbol']) == False]

info_df = pd.concat([exclusions, inclusions, rest])
info_df.reset_index(drop=True, inplace=True)

announcements = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/Historical_Index_Compositions.csv', sep=';')
announcements.rename(columns={'Date of change': 'Date', 'Date of announcement': 'Announcement'}, inplace=True)
announcements['Date'] = pd.to_datetime(announcements['Date'])

info_df = info_df.join(announcements.set_index('Date')['Announcement'], on='Date')
info_df['Announcement'] = pd.to_datetime(info_df['Announcement'])

stockdata_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/stocks-historical-data.csv', sep=';')[1:]
temp_list = list(stockdata_df.columns)
temp_list.remove('Unnamed: 0')
for header in temp_list:
    if '1' in header:
        temp_list.remove(header)

info_df['Ticker'] = info_df['Symbol'].str[:3]

for t in info_df['Ticker']:
    if t == 'POA':
        info_df['Ticker'].loc[info_df['Ticker'] == t] = 'PSHG_p.DE'
    elif t == 'SRT':
        info_df['Ticker'].loc[info_df['Ticker'] == t] = 'SATG.DE'
    elif t == '^GD':
        info_df['Ticker'].loc[info_df['Ticker'] == t] = 'XXX'
    elif t == 'HEN':
        info_df['Ticker'].loc[info_df['Ticker'] == t] = 'HNKG.DE'
    elif t == 'MRK':
        info_df['Ticker'].loc[info_df['Ticker'] == t] = 'MRCG.DE'
    else:
        for header in temp_list:
            if t in header:
                info_df['Ticker'].loc[info_df['Ticker'] == t] = header

info_df.to_csv(dir_utils.get_local_git_uri() + '/01_Data_and_Preprocessing/info_df.csv')

"""Creating StockData DataFrame
* All data is retrieved via Reuters.
* Close allways referrs to adjusted close.
* Dates are formatted in pandas datetime format and used as index.
"""

new_header = ['Date']
temp_list = list(stockdata_df.columns)
temp_list.remove('Unnamed: 0')

for header in temp_list:
    if '1' in header:
        new_header.append(header[:-2] + ' Volume')
    else:
        new_header.append(str(header) + ' Close')

stockdata_df.columns = new_header
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'], dayfirst=True)
stockdata_df.set_index('Date', inplace=True)

stockdata_df.to_csv(dir_utils.get_local_git_uri() + '/01_Data_and_Preprocessing/stockdata_df.csv')

print('checkpoint')
