import pandas as pd
from OCAES import ocaes

# ----------------------
# wind only
# ----------------------
data = pd.read_csv('data_manual.csv')
inputs = ocaes.get_default_inputs()
inputs['X_well'] = 0
inputs['X_cmp'] = 0
inputs['X_exp'] = 0
model = ocaes(data, inputs)
df, s_wind = model.get_full_results()
s_wind = model.calculate_LCOE(s_wind)

# ----------------------
# OCAES
# ----------------------
data = pd.read_csv('data_manual.csv')
inputs = ocaes.get_default_inputs()
inputs['X_cmp'] = 500
inputs['X_exp'] = 500
model = ocaes(data, inputs)
df, s_ocaes = model.get_full_results()
s_ocaes = model.calculate_LCOE(s_ocaes)

# ----------------------
# battery
# ----------------------
data = pd.read_csv('data_manual.csv')
inputs = ocaes.get_default_inputs()

# Set capacity
inputs['X_well'] = 0
inputs['X_cmp'] = 500
inputs['X_exp'] = 500

# place all costs on expander
inputs['C_exp'] = 1876.0 * 1000.0 # $/MW
inputs['F_exp'] = 10.0*1000.0
inputs['V_exp'] = 0.03/100.0*1000.0

# remove all costs from compressor and well
inputs['C_cmp'] = 0.0
inputs['F_cmp'] = 0.0
inputs['V_cmp'] = 0.0
inputs['C_well'] = 0.0
inputs['F_well'] = 0.0
inputs['V_well'] = 0.0

# battery lifetime
inputs['L_exp'] = 15.0
inputs['L_cmp'] = 15.0

# Storage performance
inputs['pwr2energy'] = 2.0  # relation between power and energy [-]
inputs['eta_storage'] = 0.90  # round trip efficiency [-]
model = ocaes(data, inputs)
df, s_batt = model.get_full_results()
s_batt2 = model.calculate_LCOE(s_batt)

# ----------------------
# print results
# ----------------------
# print(s_wind['LCOE'])
# print(s_ocaes['LCOE'])
# print(s_batt['LCOE'])