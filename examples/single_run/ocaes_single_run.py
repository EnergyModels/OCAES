import pandas as pd
from OCAES import ocaes

# ----------------------
# create and run model
# ----------------------
data = pd.read_csv('data_manual.csv')
inputs = ocaes.get_default_inputs(storage_type='battery')
# inputs['X_well'] = 0
# inputs['X_cmp'] = 0
# inputs['X_exp'] = 0
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
