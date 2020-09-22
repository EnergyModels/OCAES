import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------------------
# inputs
# ----------------------------------------
data_folders = ['2019_ISO_New_England']
price_files = ['2019_smd_hourly.xlsx']
price_types = ['da']  # da - day ahead
wind_speed_files = ['2405366_41.15_-70.84_2012.csv']
output_filenames = ['ISONE_timeseries_inputs_2019.csv']
zones = ['SEMA']

# option to output individual column data (good for troubleshooting)
write_all_data = False
# ----------------------------------------
# begin script
# ----------------------------------------
wrk_dir = os.getcwd()

for data_folder, price_file, price_type, wind_speed_file, output_filename, zone in \
        zip(data_folders, price_files, price_types, wind_speed_files, output_filenames, zones):
    # ----------------------------------------
    # begin processing
    # ----------------------------------------
    os.chdir(data_folder)

    # ----------------------------------------
    # Pricing
    # ----------------------------------------
    df_price = pd.read_excel(price_file, sheet_name=zone)  # $/MWh

    # set index
    df_price.Date = pd.to_datetime(df_price.Date)
    df_price.loc[:, 'year'] = pd.DatetimeIndex(df_price.Date).year
    df_price.loc[:, 'month'] = pd.DatetimeIndex(df_price.Date).month
    df_price.loc[:, 'day'] = pd.DatetimeIndex(df_price.Date).day
    df_price.loc[:, 'hour'] = df_price.Hr_End - 1
    df_price.loc[:, 'datetime'] = pd.to_datetime(df_price[['year', 'month', 'day', 'hour']])
    df_price = df_price.set_index('datetime')

    if price_type == 'da':
        # create columns to store generation, VRE and emissions
        df_price['price_dollarsPerMWh'] = df_price.loc[:, 'DA_LMP']

        # drop columns that we don't need
        df_price = df_price.drop(
            columns=['Date', 'Hr_End', 'DA_Demand', 'RT_Demand', 'DA_LMP', 'DA_EC', 'DA_CC', 'DA_MLC', 'RT_LMP',
                     'RT_EC', 'RT_CC', 'RT_MLC', 'Dry_Bulb', 'Dew_Point', 'year', 'month', 'day', 'hour'])

    else:
        print('Warning - price file type not recognized')

    # save and plot
    if write_all_data:
        df_price.to_csv('price.csv')
    df_price.plot()
    plt.tight_layout()
    plt.savefig('price.png')

    # ----------------------------------------
    # Wind speed
    # ----------------------------------------
    df_ws = pd.read_csv(wind_speed_file, skiprows=1)

    df_ws = df_ws.drop(columns=['power - DEPRECATED'])

    # set year to be the same as price file
    df_ws.Year = df_price.index[0].year

    # create new column in datetime format and set as index
    daytime = pd.to_datetime(df_ws[['Year', 'Month', 'Day', 'Hour', 'Minute']])
    df_ws['daytime'] = daytime
    df_ws = df_ws.set_index('daytime')
    df_ws.loc[:, 'windspeed_ms'] = df_ws.loc[:, 'wind speed at 100m (m/s)']

    # resample on hourly basis
    df_ws = df_ws.resample('H').mean()

    # drop columns that we no longer need
    df_ws = df_ws.drop(
        columns=['Year', 'Month', 'Day', 'Hour', 'Minute', 'wind speed at 100m (m/s)',
                 'air temperature at 100m (C)'])

    # save and plot
    if write_all_data:
        df_ws.to_csv('wind_speed.csv')
    df_ws.plot()
    plt.tight_layout()
    plt.savefig('wind_speed.png')

    # return to main directory
    os.chdir(wrk_dir)

    # ----------------------------------------
    # Combine into a single results file
    # ----------------------------------------
    df = df_price.join(df_ws)
    df.loc[:, 'generation_MW'] = 0.0
    df.loc[:, 'VRE_MW'] = 0.0
    df.loc[:, 'emissions_tonCO2PerMWh'] = 0.0
    df = df.fillna(method='ffill')  # replace nan with next valid value
    df.to_csv(output_filename)
