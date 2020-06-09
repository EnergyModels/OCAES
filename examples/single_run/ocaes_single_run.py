import pandas as pd
from OCAES import ocaes

# ----------------------
# create and run model
# ----------------------
data = pd.read_csv('data_manual.csv')
inputs = ocaes.get_default_inputs()
model = ocaes(data, inputs)
df, s = model.get_full_results()

df.to_csv('results.csv')

# ----------------------
# create plots using built-in functions
# ----------------------
model.plot_overview()
model.plot_power_energy()
