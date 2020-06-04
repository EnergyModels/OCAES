import pandas as pd
from OCAES import ocaes

data = pd.read_csv('data_manual.csv')
inputs = ocaes.get_default_inputs()
model = ocaes(data, inputs)
DF = model.get_full_results()

# df = model.get_full_results()
# df.plot()


# import pyomo.environ as pyo
# for v in model.instance.component_data_objects(pyo.Var, active=True):
#     print(v, pyo.value(v))
