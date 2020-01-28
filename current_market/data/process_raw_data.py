import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import numpy as np

# save working directory
wrkdir = os.getcwd()

# ----------------------------------------
# From EIA (used in processing PJM data)
# ----------------------------------------
# emission factors (kg CO2/million btu)
# Coal - Bituminous coal, Gas - Natural gas, Multiple Fuels - Residual fuel oil, Oil - Residual fuel oil
emission_factors = {'Coal': 93.3, 'Gas': 53.07, 'Hydro': 0.0, 'Multiple Fuels': 78.79, 'Nuclear': 0.0, 'Oil': 78.79,
                    'Other': 0.0, 'Other Renewables': 0.0, 'Solar': 0.0, 'Storage': 0.0, 'Wind': 0.0}

# heat rate (btu / kWh) - 2018
# Coal - Coal + Steam Generator, Gas - Natural gas + Gas Turbine,
# Multiple Fuels - Petroleum + Gas Turbine, Oil - Petroleum + Gas Turbine
heat_rates = {'Coal': 10015, 'Gas': 11138, 'Hydro': 0.0, 'Multiple Fuels': 13352.0, 'Nuclear': 0.0, 'Oil': 13352.0,
              'Other': 0.0, 'Other Renewables': 0.0, 'Solar': 0.0, 'Storage': 0.0, 'Wind': 0.0}

# ----------------------------------------
# PJM
# ----------------------------------------
os.chdir(".//raw_data//PJM")
df_price = pd.read_csv('2019_rt_hrl_lmps.csv')  # $/MWh
df_gen = pd.read_csv('2019_gen_by_fuel.csv')
os.chdir(wrkdir)

# ----------------------------------------
# Pricing
# ----------------------------------------
# set index
df_price = df_price.set_index('datetime_beginning_ept')

# drop columns that we don't need
df_price = df_price.drop(
    columns=['datetime_beginning_utc', 'pnode_id', 'pnode_name', 'voltage', 'equipment', 'type', 'zone', 'total_lmp_rt',
             'congestion_price_rt', 'marginal_loss_price_rt', 'row_is_current', 'version_nbr'])

# save and plot
df_price.to_csv('COE.csv')
df_price.plot()
plt.savefig('COE.png')

# ----------------------------------------
# Generation type -> emissions
# ----------------------------------------

# convert to datetime and set as index
df_gen.datetime_beginning_ept = pd.to_datetime(df_gen.datetime_beginning_ept)
df_gen = df_gen.set_index('datetime_beginning_ept')

# drop columns that we don't need
df_gen = df_gen.drop(columns=['datetime_beginning_utc', 'is_renewable', 'mw'])

# create column to store emissions
df_gen['emissions'] = 0.0

# calculate emissions (kg CO2/ kWh) per fuel
for fuel_type in emission_factors.keys():
    ind = df_gen['fuel_type'] == fuel_type
    df_gen.loc[ind, 'emissions'] = df_gen.loc[ind, 'fuel_percentage_of_total'] * heat_rates[fuel_type] * \
                                   emission_factors[fuel_type] / 1E6

# resample to an hourly basis, sum values (total emissions)
df_gen = df_gen.resample('H').sum()

# drop columns that we don't need
df_gen = df_gen.drop(columns=['fuel_percentage_of_total'])

# save and plot
df_gen.to_csv('emissions.csv')
df_gen.plot()
plt.savefig('emissions.png')

# ----------------------------------------
# Wind speed
# ----------------------------------------
os.chdir(".//raw_data//wind_speed")
df_ws = pd.read_csv('buoy.z01.00.20141213.000000.6nb00120_lidar_20141213_20160530.txt')
os.chdir(wrkdir)

# only keep the hub height of interest
df_ws = df_ws[df_ws[' height(m)'] == 86.9]

# only keep the year of interest (2015)
df_ws = df_ws[df_ws['year'] == 2015]

# rename columns to remove spacing in day/time columns
df_ws = df_ws.rename(
    columns={" month": "month", " day": "day", " hour": "hour", " minute": "minute", " second": "second"})

# create new column in datetime format and set as inde
daytime = pd.to_datetime(df_ws[['year', 'month', 'day', 'hour', 'minute', 'second']])
df_ws['daytime'] = daytime
df_ws = df_ws.set_index('daytime')

# drop columns that we don't need
df_ws = df_ws.drop(columns=[' range(m)', ' wind speed standard deviation (m/s)', ' wind direction (deg)',
                            ' wind direction standard deviation (deg)', ' attitude flag', '  signal strength',
                            ' signal strength threshold'])

# drop na values
df_ws = df_ws.dropna()

# upsample to minute basis to account for missing values
df_ws = df_ws.resample('T').fillna('pad')

# downsample to an hourly basis
df_ws = df_ws.resample('H').mean()

# drop columns that we no longer need
df_ws = df_ws.drop(columns=['year', 'month', 'day', 'hour', 'minute', 'second', ' height(m)'])

# save and plot
df_ws.to_csv('wind_speed.csv')
df_ws.plot()
plt.savefig('wind_speed.png')

#----------------------------------------
# Wind turbine
#----------------------------------------
# read data
os.chdir(".//raw_data//wind_turbine")
df_wt = pd.read_csv('power_curve_NREL5MW.csv')
os.chdir(wrkdir)

#  wind turbine rating
rating = 5.0 # MW

# apply interpolation function of the power curve to wind speed data and convert from kW to MW
pwr = np.interp(df_ws.values, df_wt.windspeed_ms, df_wt.power_kW, left= 0.0, right = rating)/ 1000.0
# save to df_ws and drop wind speed column
df_ws['power'] = pwr
df_ws = df_ws.drop(columns = [' wind speed (m/s)'])

# save and plot
df_ws.to_csv('wind_power_5MW.csv')
df_ws.plot()
plt.savefig('wind_power_5MW.png')