import pandas as pd
import numpy as np
import datetime
import statistics
import statsmodels.formula.api as smf

info_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/info_df.csv')
stockdata_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/stockdata_df.csv')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'])
stockdata_df.set_index('Date', inplace=True)
unique_stocks = list(dict.fromkeys(list(info_df.loc[~info_df['Type'].isnull()]['Ticker'])))
benchmark = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/Archive/DAX_Kurs.csv', sep = ';')

DAX_excluded = info_df[0:10].iloc[:,[1,2,3,5]]
DAX_excluded['Symbol'] = info_df[0:10].iloc[:,6].tolist()
DAX_excluded['Date'] = pd.to_datetime(DAX_excluded['Date'], format='%Y-%m-%d')
DAX_excluded['Announcement'] = pd.to_datetime(DAX_excluded['Announcement'], format='%Y-%m-%d')
DAX_included = info_df[10:32].iloc[:,[1,2,3,5]]
DAX_included['Symbol'] = info_df[10:32].iloc[:,6].tolist()
DAX_included['Date'] = pd.to_datetime(DAX_included['Date'], format='%Y-%m-%d')
DAX_included['Announcement'] = pd.to_datetime(DAX_included['Announcement'], format='%Y-%m-%d')

benchmark['Date'] = pd.to_datetime(benchmark['Umtauschdatum'], format='%d.%m.%y')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'], format='%Y-%m-%d')
stockdata_df = pd.merge(stockdata_df, benchmark, on ='Date')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'], format='%Y-%m-%d')
stockdata_df = stockdata_df.set_index('Date')

returns_daily_excluded = {new: stockdata_df[new + ' Return'] for new in DAX_excluded['Symbol'].tolist()}
returns_daily_included = {new: stockdata_df[new + ' Return'] for new in DAX_included['Symbol'].tolist()}
benchmark = pd.DataFrame(stockdata_df['Schlusskurs'].pct_change())

DAX_ticker_new = info_df[22:32].iloc[:,[1,2,3,5]]
DAX_ticker_new['Symbol'] = info_df[22:32].iloc[:,6].tolist()
DAX_ticker_new['Date'] = pd.to_datetime(DAX_ticker_new['Date'], format='%Y-%m-%d')
DAX_ticker_new['Announcement'] = pd.to_datetime(DAX_ticker_new['Announcement'], format='%Y-%m-%d')
dax_new = {new: stockdata_df[new + ' Return'] for new in info_df[22:32].iloc[:,6].tolist()}

''' Calculating the systmatic risk after the inclusion AND exclusion of the Stocks in the DAX.
To estimate the regression equations, OLS was used in conjunction with a correction procedure (Newey/West) 
for serially correlated error terms. 
This approach leads to test statistics that are robust against autocorrelated and 
heteroskedastic disturbance terms.

Time Horizon
----------
Start: 2009-06-21
End: 2022-03-01
----------

Parameters
----------
:sys_risk:  df
    Stock: Name of the specific stock.
    Rank: Sorted after index weight (ascending).
    Delta: Measures the change in the systematic risk of the share triggered by the inclusion.
    p-Value: The two-tailed p-values for the t-stats of the params.
    R^2: R-squared of the model.
-------
'''
def betas(ticker, returns, day: int):
    i = 0
    j = 1
    sys_risk = []
    while i in range(0,len(returns)):
        # Annoucement day
        d = []
        for date in benchmark.index:
            if str(date) < str(ticker.iloc[i][0]):
                d.append(0)
            else: d.append(1)
        benchmark['Dummy'] = d

        data = pd.DataFrame(returns[ticker.iloc[i][1]][(ticker.iloc[i][0] - datetime.timedelta(days=day)):(ticker.iloc[i][0] + datetime.timedelta(days=day))])
        data['Benchmark'] = benchmark['Schlusskurs'][(ticker.iloc[i][0] - datetime.timedelta(days=day)):(ticker.iloc[i][0] + datetime.timedelta(days=day))]
        data['Dummy'] = benchmark['Dummy'][(ticker.iloc[i][0] - datetime.timedelta(days=day)):(ticker.iloc[i][0] + datetime.timedelta(days=day))]
        data = data.rename(columns = {f"{ticker.iloc[i][1]} Return": 'y', 'Dummy': 'D', 'Benchmark': 'x'})
        reg = smf.ols('y ~ x + D*x', data).fit(cov_type='HAC',cov_kwds={'maxlags':1})
        
        # Inclusion day
        d = []
        for date in benchmark.index:
            if str(date) < str(ticker.iloc[i][3]):
                d.append(0)
            else: d.append(1)
        benchmark['Dummy'] = d

        data = pd.DataFrame(returns[ticker.iloc[i][1]][(ticker.iloc[i][3] - datetime.timedelta(days=day)):(ticker.iloc[i][3] + datetime.timedelta(days=day))])
        data['Benchmark'] = benchmark['Schlusskurs'][(ticker.iloc[i][3] - datetime.timedelta(days=day)):(ticker.iloc[i][3] + datetime.timedelta(days=day))]
        data['Dummy'] = benchmark['Dummy'][(ticker.iloc[i][3] - datetime.timedelta(days=day)):(ticker.iloc[i][3] + datetime.timedelta(days=day))]
        data = data.rename(columns = {f"{ticker.iloc[i][1]} Return": 'y', 'Dummy': 'D', 'Benchmark': 'x'})
        reg2 = smf.ols('y ~ x + D*x', data).fit(cov_type='HAC',cov_kwds={'maxlags':1})
        sys_risk.append(
            {
                'Stock': ticker.iloc[i][2],
                'Rank': j, 
                r"$\Delta$ Inclusion": reg.params[3], 
                'p_Value Inclusion': reg.pvalues[3], 
                r"$R^{2}$ Inclusion": reg.rsquared,
                r"$\Delta$ Exclusion": reg2.params[3], 
                'p_Value Exclusion': reg2.pvalues[3], 
                r"$R^{2}$ Exclusion": reg2.rsquared
            }
        )
        j += 1
        i += 1

    sys_risk = pd.DataFrame(sys_risk)
    sys_riskplus = sys_risk.copy()
    sys_risk = sys_risk.append(
            {
                'Stock': r"$\varnothing$",
                r"$\Delta$ Inclusion": sys_risk[r"$\Delta$ Inclusion"].mean(),
                r"$R^{2}$ Inclusion": sys_risk[r"$R^{2}$ Inclusion"].mean(),
                r"$\Delta$ Exclusion": sys_risk[r"$\Delta$ Exclusion"].mean(),
                r"$R^{2}$ Exclusion": sys_risk[r"$R^{2}$ Exclusion"].mean()
            }, ignore_index=True
        )
    return sys_risk, sys_riskplus

sys_risk, _ = betas(DAX_included, returns_daily_included, 365)
sys_risk
sys_risk, _ = betas(DAX_excluded, returns_daily_excluded, 365)
sys_risk
sys_risk, _ = betas(DAX_ticker_new, dax_new, 365)
sys_risk

'''Distribution of the shares with a higher unit share in the DAX and all those with a weighting of < 1 %. 
Parameters
----------
:des_stat:  df
    N: Number of stocks sorted after the index weight.
    Mean: Mean systematic risk. 
    R^2: Mean R-squared of the model.
-------
'''
_, sys_risk = betas(DAX_ticker_new, dax_new, 365)
des_stat = []
des_stat.append(
        {
            'N': '1-5',
            r"$\varnothing$ Inclusion": sys_risk[:5][r"$\Delta$ Inclusion"].mean(),
            r"$R^{2}$ Inclusion": sys_risk[:5][r"$R^{2}$ Inclusion"].mean(),
            r"$\varnothing$ Exclusion": sys_risk[:5][r"$\Delta$ Exclusion"].mean(),
            r"$R^{2}$ Exclusion": sys_risk[:5][r"$R^{2}$ Exclusion"].mean()
        }
    )
des_stat.append(
        {
            'N': '6-10',
            r"$\varnothing$ Inclusion": sys_risk[5:][r"$\Delta$ Inclusion"].mean(),
            r"$R^{2}$ Inclusion": sys_risk[5:][r"$R^{2}$ Inclusion"].mean(),
            r"$\varnothing$ Exclusion": sys_risk[5:][r"$\Delta$ Exclusion"].mean(),
            r"$R^{2}$ Exclusion": sys_risk[5:][r"$R^{2}$ Exclusion"].mean()
        }
    )
pd.DataFrame(des_stat)
