# This version is for Windows OS. The following modules are different in linux.
# 1) IPython, 2) matplotlib, 3) glpk solver.
# Updated 4/4/2014, based on OCAESv5.py 3/3/2014 version.
# 1) import part is refined. 2) Structure is optimized.

from OCAES_model import create_model
from pyomo.environ import *
import pandas as pd
import matplotlib.pyplot as plt

# ----------------
# Create model and solve
# ----------------
model = create_model()
instance = model.create_instance(report_timing=True)
instance.preprocess()
opt = SolverFactory("cplex")
results = opt.solve(instance)

# print status
print results.solver.status
print results.solver.termination_condition

# access and print results
LCOE = value(instance.LCOE)
N_WELLS = value(instance.N_WELLS)
X_OCAES = value(instance.X_OCAES)
N_WIND = value(instance.N_WIND)
X_WIND = value(instance.X_WIND)
print("LCOE    [$] : " + str(LCOE))
print("N_WELLS [-] : " + str(N_WELLS))
print("X_OCAES [MW]: " + str(X_OCAES))
print("N_WIND  [-] : " + str(N_WIND))
print("X_WIND  [MW]: " + str(X_WIND))

# return model


for v in instance.component_objects(Var, active=True):
    print("Variable",v)  # doctest: +SKIP
    for index in v:
        if index == None:
            print ("   ",index, value(v[index]))



N = 720  # TODO update to 8760

df = pd.DataFrame(columns=['E_WIND', 'E_CURTAIL', 'E_GRID', 'E_CMP', 'E_EXP', 'M_RES', 'M_CMP', 'M_EXP'], index=range(N))

for i in range(N):
    df.loc[i, "E_WIND"] = value(instance.E_WIND[i + 1])
    df.loc[i, "E_CURTAIL"] = value(instance.E_CURTAIL[i + 1])
    df.loc[i, "E_GRID"] = value(instance.E_GRID[i + 1])
    df.loc[i, "E_CMP"] = value(instance.E_CMP[i + 1])
    df.loc[i, "E_EXP"] = value(instance.E_EXP[i + 1])

    df.loc[i, "M_RES"] = value(instance.M_RES[i + 1])
    df.loc[i, "M_CMP"] = value(instance.M_CMP[i + 1])
    df.loc[i, "M_EXP"] = value(instance.M_EXP[i + 1])


df.to_csv("output.csv")
df.plot(y=['E_WIND', 'E_CURTAIL', 'E_GRID', 'E_CMP', 'E_EXP'])
plt.savefig('Energy_balance.png')

df.plot(y=['M_RES', 'M_CMP', 'M_EXP'])
plt.savefig('Mass_balance.png')