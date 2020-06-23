import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------------------
# inputs
# ----------------------------------------
data_folder = 'raw_data'
price_file = 'rt_hrl_lmps_DOM_19.csv'
generation_by_fuel_file = '2019_gen_by_fuel.csv'  # must be the same year as price_file
wind_speed_file = 'Clean_1yr_90m_Windspeeds.txt'  # data is set to be the same year as price_file

# ----------------------------------------
# begin processing
# ----------------------------------------
wrk_dir = os.getcwd()
os.chdir(data_folder)
data_dir = os.getcwd()

# ----------------------------------------
# Emission factors (kg CO2/million btu)
# ----------------------------------------
# Source: 	Table A.3. Carbon Dioxide Uncontrolled Emission Factors
# 			https://www.eia.gov/electricity/annual/html/epa_a_03.html
# 			accessed 1/21/2020
# Coal - Bituminous coal, Gas - Natural gas, Multiple Fuels - Residual fuel oil, Oil - Residual fuel oil
emission_factors = {'Coal': 93.3, 'Gas': 53.07, 'Hydro': 0.0, 'Multiple Fuels': 78.79, 'Nuclear': 0.0, 'Oil': 78.79,
                    'Other': 0.0, 'Other Renewables': 0.0, 'Solar': 0.0, 'Storage': 0.0, 'Wind': 0.0}

# ----------------------------------------
# Heat rate (btu / kWh) - 2018
# ----------------------------------------
# Source: 	Table 8.2. Average Tested Heat Rates by Prime Mover and Energy Source, 2008 - 2018
#			https://www.eia.gov/electricity/annual/html/epa_08_02.html
# 			accessed 1/21/2020
# Coal - Coal + Steam Generator, Gas - Natural gas + Gas Turbine,
# Multiple Fuels - Petroleum + Gas Turbine, Oil - Petroleum + Gas Turbine
heat_rates = {'Coal': 10015, 'Gas': 11138, 'Hydro': 0.0, 'Multiple Fuels': 13352.0, 'Nuclear': 0.0, 'Oil': 13352.0,
              'Other': 0.0, 'Other Renewables': 0.0, 'Solar': 0.0, 'Storage': 0.0, 'Wind': 0.0}

# ----------------------------------------
# Pricing
# ----------------------------------------
os.chdir(data_dir)
df_price = pd.read_csv(price_file)  # $/MWh
os.chdir(wrk_dir)

# set index
df_price.datetime_beginning_ept = pd.to_datetime(df_price.datetime_beginning_ept)
df_price = df_price.set_index('datetime_beginning_ept')

# create columns to store generation, VRE and emissions
df_price['price_dollarsPerMWh'] = df_price.loc[:, 'system_energy_price_rt']

# drop columns that we don't need
df_price = df_price.drop(
    columns=['system_energy_price_rt', 'datetime_beginning_utc', 'pnode_id', 'pnode_name', 'voltage', 'equipment',
             'type', 'zone', 'total_lmp_rt',
             'congestion_price_rt', 'marginal_loss_price_rt', 'row_is_current', 'version_nbr'])

# save and plot
df_price.to_csv('price.csv')
df_price.plot()
plt.tight_layout()
plt.savefig('price.png')

# ----------------------------------------
# Generation by fuel ->
#   total generation
#   emissions
#   generation by VRE (variable renewable energy)
# ----------------------------------------
os.chdir(data_dir)
df_gen = pd.read_csv(generation_by_fuel_file)
os.chdir(wrk_dir)

# convert to datetime and set as index
df_gen.datetime_beginning_ept = pd.to_datetime(df_gen.datetime_beginning_ept)
df_gen = df_gen.set_index('datetime_beginning_ept')

# drop columns that we don't need
df_gen = df_gen.drop(columns=['datetime_beginning_utc', 'is_renewable'])

# create columns to store generation, VRE and emissions
df_gen['generation_MW'] = np.nan
df_gen['VRE_MW'] = np.nan
df_gen['emissions_tonCO2PerMWh'] = np.nan

# calculate emissions (kg CO2/ kWh) per fuel and VRE
for fuel_type in emission_factors.keys():
    # select indices
    ind = df_gen['fuel_type'] == fuel_type

    # generation
    df_gen.loc[ind, 'generation_MW'] = df_gen.loc[ind, 'mw']

    # VRE
    if fuel_type == 'Solar' or fuel_type == 'Wind':
        df_gen.loc[ind, 'VRE_MW'] = df_gen.loc[ind, 'mw']

    # emissions
    df_gen.loc[ind, 'emissions_tonCO2PerMWh'] = df_gen.loc[ind, 'fuel_percentage_of_total'] * heat_rates[fuel_type] * \
                                                emission_factors[fuel_type] / 1E6

# resample to an hourly basis, sum values
df_gen = df_gen.resample('H').sum()

# drop columns that we don't need
df_gen = df_gen.drop(columns=['mw', 'fuel_percentage_of_total'])

# replace 0 generation with average values
ind = df_gen.loc[:, 'generation_MW'] == 0.0
df_gen.loc[ind, 'generation_MW'] = df_gen.loc[:, 'generation_MW'].mean()
df_gen.loc[ind, 'VRE_MW'] = df_gen.loc[:, 'VRE_MW'].mean()
df_gen.loc[ind, 'emissions_tonCO2PerMWh'] = df_gen.loc[:, 'emissions_tonCO2PerMWh'].mean()

# save and plot
df_gen.to_csv('generation.csv')

df_gen.plot(y='generation_MW')
plt.tight_layout()
plt.savefig('generation_MW.png')

df_gen.plot(y='VRE_MW')
plt.tight_layout()
plt.savefig('VRE.png')

df_gen.plot(y='emissions_tonCO2PerMWh')
plt.tight_layout()
plt.savefig('emissions_tonCO2PerMWh.png')

# ----------------------------------------
# Wind speed
# ----------------------------------------
os.chdir(data_dir)
df_ws = pd.read_csv(wind_speed_file, delimiter=' ')
os.chdir(wrk_dir)

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
df_ws.to_csv('wind_speed.csv')
df_ws.plot()
plt.tight_layout()
plt.savefig('wind_speed.png')

# ----------------------------------------
# Combine into a single results file
# ----------------------------------------
df = df_gen.join(df_price)
df = df.join(df_ws)
df = df.fillna(method='ffill')  # replace nan with next valid value

df.to_csv('model_inputs.csv')
