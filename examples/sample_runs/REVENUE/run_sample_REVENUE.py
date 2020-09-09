import pandas as pd
from OCAES import ocaes

# ----------------------
# create and run model
# ----------------------
capacity = 130  # MW
duration = 24  # hours

data = pd.read_csv('timeseries_inputs_2019_72_hours.csv')
inputs = ocaes.get_default_inputs()
inputs['X_well'] = capacity
inputs['X_cmp'] = capacity
inputs['X_exp'] = capacity
inputs['pwr2energy'] = duration
inputs['objective'] = 'REVENUE'
model = ocaes(data, inputs)
df, s = model.get_full_results()

df.to_csv('results_timeseries.csv')
s.to_csv('results_values.csv')
print(model.calculate_LCOE(s))

# ----------------------
# create plots using built-in functions
# ----------------------
model.plot_overview()
model.plot_power_energy()
