"""_summary_
"""

import pandas as pd
import datetime

exclusions = pd.read_csv('DAX_excluded_2010-2021.csv', sep = ';').rename(columns={'Ausgeschieden': 'Date'})
exclusions['Type'] = 'Excluded'
exclusions['Date'] = pd.to_datetime(exclusions['Date'])

inclusions = pd.read_csv('DAX_included_2010-2021.csv', sep = ';').rename(columns={'Aufgenommen': 'Date'})
inclusions['Type'] = 'Included'
inclusions['Date'] = pd.to_datetime(inclusions['Date'])

temp_rest = pd.read_csv('Companies_Ticker.csv', sep = ';')
rest = temp_rest[temp_rest['Symbol'].isin(inclusions['Symbol']) == False]

info_df = pd.concat([exclusions, inclusions, rest])
info_df.reset_index(drop=True, inplace=True)

announcements.rename(columns={'Date of change': 'Date', 'Date of announcement': 'Announcement'}, inplace=True)
announcements['Date'] = pd.to_datetime(announcements['Date'])

info_df = info_df.join(announcements.set_index('Date')['Announcement'], on='Date')
info_df['Announcement'] = pd.to_datetime(info_df['Announcement'])
info_df

