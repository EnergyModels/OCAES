import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------------------
# inputs
# ----------------------------------------
data_folders = ['2019_NYISO']
price_files = ['2019_OASIS_Day-Ahead_Market_Zonal_LBMP.csv']
price_types = ['da']  # da - day ahead
wind_speed_files = ['Clean_1yr_90m_Windspeeds.txt']
output_filenames = ['NYISO_timeseries_inputs_2019.csv']
zones = ['LONGIL']

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
    df_price = pd.read_csv(price_file)  # $/MWh

    # set index
    df_price.loc[:, 'Eastern Date Hour'] = pd.to_datetime(df_price.loc[:, 'Eastern Date Hour'])
    df_price = df_price.set_index('Eastern Date Hour')

    # only select entries from the correct zone
    df_price = df_price[df_price.loc[:, 'Zone Name'] == zone]

    if price_type == 'da':

        # create columns to store generation, VRE and emissions
        df_price['price_dollarsPerMWh'] = df_price.loc[:, 'DAM Zonal LBMP']

        # drop columns that we don't need
        df_price = df_price.drop(
            columns=['Eastern Date Hour Time Zone', 'Zone Name', 'Zone PTID', 'DAM Zonal LBMP', 'DAM Zonal Losses',
                     'DAM Zonal Congestion', 'DAM Zonal Price Version'])

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
    df_ws = pd.read_csv(wind_speed_file, delimiter=' ')

    # set year to be the same as price file
    df_ws.year = df_price.index[0].year

    # create new column in datetime format and set as index
    daytime = pd.to_datetime(df_ws[['year', 'month', 'day', 'hour', 'minute', 'second']])
    df_ws['daytime'] = daytime
    df_ws = df_ws.set_index('daytime')

    # resample on hourly basis
    df_ws = df_ws.resample('H').mean()

    # drop columns that we no longer need
    df_ws = df_ws.drop(columns=['year', 'month', 'day', 'hour', 'minute', 'second'])

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
