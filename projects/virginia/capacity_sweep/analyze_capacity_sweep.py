import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =====================================
# user inputs
# =====================================
# data input
results_filename = "sweep_results.csv"

series = ['wind_only', '4_hr_batt', '10_hr_batt',
          '10_hr_ocaes', '24_hr_ocaes', '48_hr_ocaes', '72_hr_ocaes', '168_hr_ocaes']
series_dict = {'wind_only': 'Wind only', '4_hr_batt': 'Battery (4 hr)', '10_hr_batt': 'Battery (10 hr)',
               '10_hr_ocaes': 'OCAES (10 hr)', '24_hr_ocaes': 'OCAES (24 hr)',
               '48_hr_ocaes': 'OCAES (48 hr)', '72_hr_ocaes': 'OCAES (72 hr)', '168_hr_ocaes': 'OCAES (168 hr)'}

# =====================================
# process data
# =====================================

# Import results
df = pd.read_csv(results_filename)


df = df.loc[df.loc[:, 'objective'] == 'COVE']

# create dataframe to hold results summary
df_smry = pd.DataFrame()

# create dataframe to hold results summary by
columns = ['2015_da', '2015_rt', '2017_da', '2017_rt', '2019_da', '2019_rt']
index = ['Year','Market','Capacity']
for val in series_dict.values():
    index.append(val)
COVE = pd.DataFrame(index=index, columns=columns)
COVE_pct = pd.DataFrame(index=index, columns=columns)
revenue = pd.DataFrame(index=index, columns=columns)
revenue_pct = pd.DataFrame(index=index, columns=columns)

for timeseries_filename in df.timeseries_filename.unique():

    if timeseries_filename == "da_timeseries_inputs_2015.csv":
        col = "2015_da"
        year = "2015"
        market = 'Day Ahead'
    elif timeseries_filename == "rt_timeseries_inputs_2015.csv":
        col = "2015_rt"
        year = "2015"
        market = 'Real time'
    elif timeseries_filename == "da_timeseries_inputs_2017.csv":
        col = "2017_da"
        year = "2017"
        market = 'Day Ahead'
    elif timeseries_filename == "rt_timeseries_inputs_2017.csv":
        col = "2017_rt"
        year = "2017"
        market = 'Real time'
    elif timeseries_filename == "da_timeseries_inputs_2019.csv":
        col = "2019_da"
        year = "2019"
        market = 'Day Ahead'
    elif timeseries_filename == "rt_timeseries_inputs_2019.csv":
        col = "2019_rt"
        year = "2019"
        market = 'Real time'

    # save year and market into metric specific dataframes
    COVE.loc['Year', col] = year
    COVE.loc['Market', col] = market
    COVE_pct.loc['Year', col] = year
    COVE_pct.loc['Market', col] = market
    revenue.loc['Year', col] = year
    revenue.loc['Market', col] = market
    revenue_pct.loc['Year', col] = year
    revenue_pct.loc['Market', col] = market

    # -----------
    # summary of results at lowest COVE
    # -----------
    # select only entries from current year
    ind = df.loc[:, 'timeseries_filename'] == timeseries_filename
    df2 = df.loc[ind, :]

    # average groups by sheetname and capacity
    df2 = df2.groupby(['sheetname', 'capacity']).mean()

    # reset index
    df2 = df2.reset_index()

    # # find lowest COVE for capacity > 0 and not wind_only
    low = df2[(df2.loc[:, 'sheetname'] != 'wind_only') & (df2.loc[:, 'capacity'] > 0.0)].COVE.min()
    ind = (df2.loc[:, 'COVE'] == low)

    # get capacity for lowest COVE
    capacity = float(df2.loc[ind, 'capacity'].values)

    # select all indices at that capacity
    ind2 = df2.loc[:, 'capacity'] == capacity
    df3 = df2.loc[ind2, :]

    # calculate % diff from wind_only
    ind = df3.loc[:, 'sheetname'] == 'wind_only'
    df3.loc[:, 'COVE_basis'] = float(df3.loc[ind, 'COVE'].values)
    df3.loc[:, 'COVE_pct_diff'] = (df3.COVE - df3.COVE_basis) / df3.COVE_basis * 100
    df3.loc[:, 'revenue_basis'] = float(df3.loc[ind, 'revenue'].values)
    df3.loc[:, 'revenue_pct_diff'] = (df3.revenue - df3.revenue_basis) / df3.revenue_basis * 100

    # save into df_smry
    df3.loc[:, 'timeseries_filename'] = timeseries_filename
    df_smry = df_smry.append(df3, ignore_index=True)

    # save into metric specific dataframes
    COVE.loc['Capacity', col] = capacity
    COVE_pct.loc['Capacity', col] = capacity
    revenue.loc['Capacity', col] = capacity
    revenue_pct.loc['Capacity', col] = capacity

    for key, val in zip(series_dict.keys(), series_dict.values()):
        ind = df3.loc[:, 'sheetname'] == key
        COVE.loc[val, col] = float(df3.loc[ind, 'COVE'])
        COVE_pct.loc[val, col] = float(df3.loc[ind, 'COVE_pct_diff'])
        revenue.loc[val, col] = float(df3.loc[ind, 'revenue'])
        revenue_pct.loc[val, col] = float(df3.loc[ind, 'revenue_pct_diff'])

# create formatted table
COVE_format = pd.concat([COVE.loc[:, '2015_da'], COVE_pct.loc[:, '2015_da'],
                         COVE.loc[:, '2015_rt'], COVE_pct.loc[:, '2015_rt'],
                         COVE.loc[:, '2017_da'], COVE_pct.loc[:, '2017_da'],
                         COVE.loc[:, '2017_rt'], COVE_pct.loc[:, '2017_rt'],
                         COVE.loc[:, '2019_da'], COVE_pct.loc[:, '2019_da'],
                         COVE.loc[:, '2019_rt'], COVE_pct.loc[:, '2019_rt']]
                        , axis=1)

revenue_format = pd.concat([revenue.loc[:, '2015_da'], revenue_pct.loc[:, '2015_da'],
                            revenue.loc[:, '2015_rt'], revenue_pct.loc[:, '2015_rt'],
                            revenue.loc[:, '2017_da'], revenue_pct.loc[:, '2017_da'],
                            revenue.loc[:, '2017_rt'], revenue_pct.loc[:, '2017_rt'],
                            revenue.loc[:, '2019_da'], revenue_pct.loc[:, '2019_da'],
                            revenue.loc[:, '2019_rt'], revenue_pct.loc[:, '2019_rt'], ]
                           , axis=1)

# save results
writer = pd.ExcelWriter('analysis_results.xls')
COVE_format.to_excel(writer, sheet_name='COVE_formatted')
COVE.to_excel(writer, sheet_name='COVE')
COVE_pct.to_excel(writer, sheet_name='COVE_pct')
revenue_format.to_excel(writer, sheet_name='revenue_formatted')
revenue.to_excel(writer, sheet_name='revenue')
revenue_pct.to_excel(writer, sheet_name='revenue_pct')
df_smry.to_excel(writer, sheet_name='raw')
writer.close()
