import pandas as pd
from OCAES import ocaes

# ----------------------
# create and run model
# ----------------------
data = pd.read_csv('timeseries_inputs_2019.csv')
inputs = ocaes.get_default_inputs()
# inputs['C_well'] = 5000.0
# inputs['X_well'] = 50.0
# inputs['L_well'] = 50.0
# inputs['X_cmp'] = 0
# inputs['X_exp'] = 0
model = ocaes(data, inputs)
df, s = model.get_full_results()

revenue, LCOE, COVE, avoided_emissions = model.post_process(s)
s['revenue'] = revenue
s['LCOE'] = LCOE
s['COVE'] = COVE
s['avoided_emissions'] = avoided_emissions


df.to_csv('results_timeseries.csv')
s.to_csv('results_values.csv')
print(model.calculate_LCOE(s))

# ----------------------
# create plots using built-in functions
# ----------------------
model.plot_overview()
model.plot_power_energy()
