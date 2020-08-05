import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =====================================
# user inputs
# =====================================
# data input
results_filename = "sweep_results.csv"

series = ['wind_only', '4_hr_batt', '10_hr_batt', '10_hr_ocaes', '24_hr_ocaes']
series_dict = {'wind_only': 'Wind only', '4_hr_batt': 'Battery (4 hr)', '10_hr_batt': 'Battery (10 hr)',
               '10_hr_ocaes': 'OCAES (10 hr)', '24_hr_ocaes': 'OCAES (24 hr)'}

# =====================================
# process data
# =====================================

# Import results
df = pd.read_csv(results_filename)

# create dataframe to hold results summary
df_smry = pd.DataFrame()

# create dataframe to hold results summary by
columns = ['2015', '2017', '2019', 'combined']
index = ['Capacity']
for val in series_dict.values():
    index.append(val)
COVE = pd.DataFrame(index=index, columns=columns)
COVE_pct = pd.DataFrame(index=index, columns=columns)
revenue = pd.DataFrame(index=index, columns=columns)
revenue_pct = pd.DataFrame(index=index, columns=columns)

for timeseries_filename in df.timeseries_filename.unique():

    if timeseries_filename == "timeseries_inputs_2015.csv":
        year = "2015"
    elif timeseries_filename == "timeseries_inputs_2017.csv":
        year = "2017"
    elif timeseries_filename == "timeseries_inputs_2019.csv":
        year = "2019"
    elif timeseries_filename == "timeseries_inputs_multiyear.csv":
        year = "combined"

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

    # # find lowest COVE
    low = df2.COVE.min()
    ind = df2.loc[:, 'COVE'] == low

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

    # save into metric specifc dataframes
    COVE.loc['Capacity', year] = capacity
    COVE_pct.loc['Capacity', year] = capacity
    revenue.loc['Capacity', year] = capacity
    revenue_pct.loc['Capacity', year] = capacity

    for key, val in zip(series_dict.keys(), series_dict.values()):
        ind = df3.loc[:, 'sheetname'] == key
        COVE.loc[val, year] = float(df3.loc[ind, 'COVE'])
        COVE_pct.loc[val, year] = float(df3.loc[ind, 'COVE_pct_diff'])
        revenue.loc[val, year] = float(df3.loc[ind, 'revenue'])
        revenue_pct.loc[val, year] = float(df3.loc[ind, 'revenue_pct_diff'])

# create formatted table
COVE_format = pd.concat([COVE.loc[:, '2015'], COVE_pct.loc[:, '2015'],
                         COVE.loc[:, '2017'], COVE_pct.loc[:, '2017'],
                         COVE.loc[:, '2019'], COVE_pct.loc[:, '2019'],
                         COVE.loc[:, 'combined'], COVE_pct.loc[:, 'combined']]
                        , axis=1)

revenue_format = pd.concat([revenue.loc[:, '2015'], revenue_pct.loc[:, '2015'],
                         revenue.loc[:, '2017'], revenue_pct.loc[:, '2017'],
                         revenue.loc[:, '2019'], revenue_pct.loc[:, '2019'],
                         revenue.loc[:, 'combined'], revenue_pct.loc[:, 'combined']]
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


