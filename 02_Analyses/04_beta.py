import pandas as pd
import numpy as np
import datetime
import statistics
import statsmodels.formula.api as smf

# @ Dennis: Ich lösche die Zeilen 12-51 noch raus... als ich das heute früh umgeändert habe, gab es die daily returns im df noch nicht.
# Ansonsten sollten die Werte unten, wie auf dem Foto sein.

info_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/info_df.csv')
stockdata_df = pd.read_csv('https://raw.githubusercontent.com/LarsWrede/GFSM/main/01_Data_and_Preprocessing/stockdata_df.csv')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'])
stockdata_df.set_index('Date', inplace=True)
unique_stocks = list(dict.fromkeys(list(info_df.loc[~info_df['Type'].isnull()]['Ticker'])))

# List with all stocks that got excluded from the DAX (2010-2021).
DAX_excluded = info_df[0:10].iloc[:,[1,2,3]]
DAX_excluded['Symbol'] = ['SZGG.DE Close', 'LXSG.DE Close', 'SDFGn.DE Close', 'PSMGn.DE Close', 'CBKG.DE Close',  'TKAG.DE Close', 'LHAG.DE Close', 'WDIG.H Close', 'BEIG.DE Close', 'DWNG.DE Close']
DAX_excluded['Date'] = pd.to_datetime(DAX_excluded['Date'], format='%Y-%m-%d')

#List with all stocks that got included in the DAX (2010-2021).
DAX_included = info_df[10:32].iloc[:,[1,2,3]]
DAX_included['Symbol'] = ['HEIG.DE Close', 'CONG.DE Close', 'LXSG.DE Close', 'VNAn.DE Close', 'PSMGn.DE Close', '1COV.DE Close', 'WDIG.H Close',
                          'MTXGn.DE Close', 'DWNG.DE Close', 'DHER.DE Close','ENR1n.DE Close', 'BEIG.DE Close', 'AIRG.DE Close', 'BNRGn.DE Close',
                          'HFGG.DE Close', 'PSHG_p.DE Close', 'PUMG.DE Close', 'QIA.DE Close', 'SATG.DE Close', 'SHLG.DE Close', 'SY1G.DE Close', 
                          'ZALG.DE Close']
DAX_included['Date'] = pd.to_datetime(DAX_included['Date'], format='%Y-%m-%d')

# Extending the stockdata_df with the Benchmark.
benchmark['Date'] = pd.to_datetime(benchmark['Umtauschdatum'], format='%d.%m.%y')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'], format='%Y-%m-%d')
stockdata_df = pd.merge(stockdata_df, benchmark, on ='Date')
stockdata_df['Date'] = pd.to_datetime(stockdata_df['Date'], format='%Y-%m-%d')
stockdata_df = stockdata_df.set_index('Date')

excluders = ['SZGG.DE Close', 'LXSG.DE Close', 'SDFGn.DE Close', 'PSMGn.DE Close', 'CBKG.DE Close',  'TKAG.DE Close', 'LHAG.DE Close', 'WDIG.H Close', 'BEIG.DE Close', 'DWNG.DE Close', 'Schlusskurs']
excluders = {new: stockdata_df[new] for new in excluders}

includers = ['HEIG.DE Close', 'CONG.DE Close', 'LXSG.DE Close', 'VNAn.DE Close', 'PSMGn.DE Close', '1COV.DE Close', 'WDIG.H Close',
                          'MTXGn.DE Close', 'DWNG.DE Close', 'DHER.DE Close','ENR1n.DE Close', 'BEIG.DE Close', 'AIRG.DE Close', 'BNRGn.DE Close',
                          'HFGG.DE Close', 'PSHG_p.DE Close', 'PUMG.DE Close', 'QIA.DE Close', 'SATG.DE Close', 'SHLG.DE Close', 'SY1G.DE Close', 
                          'ZALG.DE Close', 'Schlusskurs']
includers = {new: stockdata_df[new] for new in includers}

# Calculating daily returns
returns_daily_included = {}
for s in includers:
    includers[s] = includers[s].dropna().str.replace(',', '.').astype(float)
    returns_daily_included[s] = includers[s].pct_change()
    
returns_daily_excluded = {}
for s in excluders:
    #excluders[s] = excluders[s].dropna().str.replace(',', '.').astype(float)
    returns_daily_excluded[s] = excluders[s].pct_change()
benchmark = pd.DataFrame(returns_daily_excluded['Schlusskurs'])

''' Calculating the systmatic risk after the inclusion of the Stocks in the DAX.
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
i = 0
j = 1
sys_risk = []
while i in range(0,10):
    d = []
    for date in benchmark.index:
        if str(date) < str(DAX_included.iloc[i][0]):
            d.append(0)
        else: d.append(1)
    benchmark['Dummy'] = d

    data = pd.DataFrame(returns_daily_included[DAX_included.iloc[i][1]][str(DAX_included.iloc[i][0] - datetime.timedelta(days=365)):str(DAX_included.iloc[i][0] + datetime.timedelta(days=365))])
    data['Benchmark'] = benchmark['Schlusskurs'][str(DAX_included.iloc[i][0] - datetime.timedelta(days=365)):str(DAX_included.iloc[i][0] + datetime.timedelta(days=365))]
    data['Dummy'] = benchmark['Dummy'][str(DAX_included.iloc[i][0] - datetime.timedelta(days=365)):str(DAX_included.iloc[i][0] + datetime.timedelta(days=365))]
    data = data.rename(columns = {DAX_included.iloc[i][1]: 'y', 'Dummy': 'D', 'Benchmark': 'x'})
    reg = smf.ols('y ~ x + D*x', data).fit(cov_type='HAC',cov_kwds={'maxlags':1})
    sys_risk.append(
        {
            'Stock': DAX_included.iloc[i][2],
            'Rank': j, 
            r"$\Delta$": reg.params[3], 
            'p_Value': reg.pvalues[3], 
            r"$R^{2}$": reg.rsquared
        }
    )
    j += 1
    i += 1
  
while i in range(10,len(returns_daily_included)-1):
    d = []
    for date in benchmark.index:
        if str(date) < str(DAX_included.iloc[i][0]):
            d.append(0)
        else: d.append(1)
    benchmark['Dummy'] = d

    data = pd.DataFrame(returns_daily_included[DAX_included.iloc[i][1]][str(DAX_included.iloc[i][0] - datetime.timedelta(days=365)):'2022-03-01'])
    data['Benchmark'] = benchmark['Schlusskurs'][str(DAX_included.iloc[i][0] - datetime.timedelta(days=365)):'2022-03-01']
    data['Dummy'] = benchmark['Dummy'][str(DAX_included.iloc[i][0] - datetime.timedelta(days=365)):'2022-03-01']
    data = data.rename(columns = {DAX_included.iloc[i][1]: 'y', 'Dummy': 'D', 'Benchmark': 'x'})
    reg = smf.ols('y ~ x + D*x', data).fit(cov_type='HAC',cov_kwds={'maxlags':1})
    sys_risk.append(
        {
            'Stock': DAX_included.iloc[i][2],
            'Rank': j, 
            r"$\Delta$": reg.params[3], 
            'p_Value': reg.pvalues[3], 
            r"$R^{2}$": reg.rsquared
        }
    )
    j += 1
    i += 1
sys_risk = pd.DataFrame(sys_risk)
sys_risk.append(
        {
            'Stock': r"$\varnothing$",
            r"$\Delta$": sys_risk[r"$\Delta$"].mean(),
            r"$R^{2}$": sys_risk[r"$R^{2}$"].mean()
        }, ignore_index=True
    )
    
    
    
''' Calculating the systmatic risk after the exclusion of the Stocks in the DAX.
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

i = 0
j = 1
sys_risk = []
while i in range(0,7):
    d = []
    for date in benchmark.index:
        if str(date) < str(DAX_excluded.iloc[i][0]):
            d.append(0)
        else: d.append(1)
    benchmark['Dummy'] = d

    data = pd.DataFrame(returns_daily_excluded[DAX_excluded.iloc[i][1]][str(DAX_excluded.iloc[i][0] - datetime.timedelta(days=365)):str(DAX_excluded.iloc[i][0] + datetime.timedelta(days=365))])
    data['Benchmark'] = benchmark['Schlusskurs'][str(DAX_excluded.iloc[i][0] - datetime.timedelta(days=365)):str(DAX_excluded.iloc[i][0] + datetime.timedelta(days=365))]
    data['Dummy'] = benchmark['Dummy'][str(DAX_excluded.iloc[i][0] - datetime.timedelta(days=365)):str(DAX_excluded.iloc[i][0] + datetime.timedelta(days=365))]   
    data = data.rename(columns = {DAX_excluded.iloc[i][1]: 'y', 'Dummy': 'D', 'Benchmark': 'x'})
    reg = smf.ols('y ~ x + D*x', data).fit(cov_type='HAC',cov_kwds={'maxlags':1})
    sys_risk.append(
        {
            'Stock': DAX_excluded.iloc[i][2],
            'Rank': j, 
            r"$\Delta$": reg.params[3], 
            'p_Value': reg.pvalues[3], 
            r"$R^{2}$": reg.rsquared
        }
    )
    j += 1
    i += 1
    
while i in range(7,len(returns_daily_excluded)-1):
    d = []
    for date in benchmark.index:
        if str(date) < str(DAX_excluded.iloc[i][0]):
            d.append(0)
        else: d.append(1)
    benchmark['Dummy'] = d

    data = pd.DataFrame(returns_daily_excluded[DAX_excluded.iloc[i][1]][str(DAX_excluded.iloc[i][0] - datetime.timedelta(days=365)):'2022-03-01'])
    data['Benchmark'] = benchmark['Schlusskurs'][str(DAX_excluded.iloc[i][0] - datetime.timedelta(days=365)):'2022-03-01']
    data['Dummy'] = benchmark['Dummy'][str(DAX_excluded.iloc[i][0] - datetime.timedelta(days=365)):'2022-03-01']
    data = data.rename(columns = {DAX_excluded.iloc[i][1]: 'y', 'Dummy': 'D', 'Benchmark': 'x'})
    reg = smf.ols('y ~ x + D*x', data).fit(cov_type='HAC',cov_kwds={'maxlags':1})
    sys_risk.append(
        {
            'Stock': DAX_excluded.iloc[i][2],
            'Rank': j, 
            r"$\Delta$": reg.params[3], 
            'p_Value': reg.pvalues[3], 
            r"$R^{2}$": reg.rsquared
        }
    )
    j += 1
    i += 1
sys_risk = pd.DataFrame(sys_risk)
sys_risk.append(
        {
            'Stock': r"$\varnothing$",
            r"$\Delta$": sys_risk[r"$\Delta$"].mean(),
            r"$R^{2}$": sys_risk[r"$R^{2}$"].mean()            
        }, ignore_index=True
    )
    
    
''' Creating a list and dictionary with all 10 newly added DAX stocks.
Parameters
----------
:newcomers:  list
    Contains the names of the stocks.
:dax_new: dict
    Contains the daily returns of the 10 new stocks.
-------
'''
newcomers = ['AIRG.DE Close', 'SHLG.DE Close', 'ZALG.DE Close', 'SY1G. Volume', 'SATG.DE Close',  'PSHG_p.DE Close', 'HFGG.DE Close', 'BNRGn.DE Close', 'QIA.DE Close', 'PUMG.DE Close']
dax_new = {new: returns_daily_included[new] for new in newcomers}

''' Creating the dummy variable - 0 before the inclusion day (2021-09-20) and 1 thereafter.
Parameters
----------
:benchmark:  df
    Contains daily returns as well as the dummy variable.
-------
'''
d = []
for date in benchmark.index:
    if str(date) < '2021-09-20 00:00:00':
        d.append(0)
    else: d.append(1)
benchmark['Dummy'] = d


''' Calculating the systmatic risk.
To estimate the regression equations, OLS was used in conjunction with a correction procedure (Newey/West) 
for serially correlated error terms. 
This approach leads to test statistics that are robust against autocorrelated and 
heteroskedastic disturbance terms.

Time Horizon
----------
Start: 1 Year before the inclusion day (2020-09-20)
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
i = 1
sys_risk = []
for key in dax_new:
    data = pd.DataFrame(dax_new[key]['2020-09-20':'2022-03-01'])
    data['Benchmark'] = benchmark['Schlusskurs']['2020-09-20':'2022-03-01']
    data['Dummy'] = benchmark['Dummy']['2020-09-20':'2022-03-01']
    #stocks_as_df['Volume'][key]['2020-09-20':'2021-09-20']    
    data = data.rename(columns = {key: 'y', 'Dummy': 'D', 'Benchmark': 'x'})
    reg = smf.ols('y ~ x + D*x', data).fit(cov_type='HAC',cov_kwds={'maxlags':1})
    sys_risk.append(
        {
            'Stock': key,
            'Rank': i, 
            r"$\Delta$": reg.params[3], 
            'p_Value': reg.pvalues[3], 
            r"$R^{2}$": reg.rsquared
        }
    )
    i += 1
sys_risk = pd.DataFrame(sys_risk)
sys_risk.append(
        {
            'Stock': r"$\varnothing$",
            r"$\Delta$": sys_risk[r"$\Delta$"].mean(),
            r"$R^{2}$": sys_risk[r"$R^{2}$"].mean()
        }, ignore_index=True
    )
    
'''Distribution of the shares with a higher unit share in the DAX and all those with a weighting of < 1 %. 
Parameters
----------
:des_stat:  df
    N: Number of stocks sorted after the index weight.
    Mean: Mean systematic risk. 
    R^2: Mean R-squared of the model.
-------
'''
des_stat = []
des_stat.append(
        {
            'N': '1-5',
            r"$\varnothing$": sys_risk[:5][r"$\Delta$"].mean(),
            r"$R^{2}$": sys_risk[:5][r"$R^{2}$"].mean()
        }
    )
des_stat.append(
        {
            'N': '6-10',
            r"$\varnothing$": sys_risk[5:][r"$\Delta$"].mean(),
            r"$R^{2}$": sys_risk[5:][r"$R^{2}$"].mean()
        }
    )
pd.DataFrame(des_stat)
