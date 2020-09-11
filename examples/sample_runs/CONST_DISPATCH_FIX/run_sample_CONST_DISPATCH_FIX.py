import pandas as pd
from OCAES import ocaes

# ----------------------
# create and run model
# ----------------------
dispatch = 10  # MW
duration = 24.0  # hours

data = pd.read_csv('timeseries_inputs_2019_72_hours.csv')
inputs = ocaes.get_default_inputs()
inputs['X_dispatch'] = dispatch
inputs['pwr2energy'] = duration
inputs['objective'] = 'CONST_DISPATCH_FIX'
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
