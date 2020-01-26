# This version is for Windows OS. The following modules are different in linux.
# 1) IPython, 2) matplotlib, 3) glpk solver.
# Updated 4/4/2014, based on OCAESv5.py 3/3/2014 version.
# 1) import part is refined. 2) Structure is optimized.

import os
from OCAES_model import create_model
from pyomo.environ import *
from joblib import Parallel, delayed, parallel_backend
import pandas as pd


def parameterSweep(model, inputs):
    # Create model
    instance = model.create_instance(report_timing=True)

    # set values
    instance.PRICE_MULTIPLIER.set_value(inputs['PRICE_MULTIPLIER'])
    instance.GRID_RAMP_RATE.set_value(inputs['GRID_RAMP_RATE'])
    instance.C_WELL.set_value(inputs['C_WELL'])
    instance.C_MACHINE.set_value(inputs['C_MACHINE'])

    # Solve
    instance.preprocess()
    opt = SolverFactory("cplex")
    results = opt.solve(instance)

    # print status
    print results.solver.status
    print results.solver.termination_condition

    # access and print results
    PROFIT = value(instance.PROFIT)
    N_WELLS = value(instance.N_WELLS)
    X_OCAES = value(instance.X_OCAES)
    print("PROFIT [M$] : " + str(PROFIT / 1E6))
    print("N_WELLS [-] : " + str(N_WELLS))
    print("X_OCAES [MW]: " + str(X_OCAES))

    results = pd.Series([PROFIT, N_WELLS, X_OCAES],
              index=['PROFIT', 'N_WELLS', 'X_OCAES'])

    output = pd.concat([inputs,results])

    return output


if __name__ == '__main__':
    # inputs
    mulitpliers = [1]
    ramp_rates = [1000]
    well_cost = [1E6, 5E6, 10E6, 15E6]
    machine_cost = [953000]

    # prepare inputs
    n1 = len(mulitpliers)
    n2 = len(ramp_rates)
    n3 = len(well_cost)
    n4 = len(machine_cost)
    n_cases = n1 * n2
    inputs = pd.DataFrame(index=range(n_cases),columns=['PRICE_MULTIPLIER','GRID_RAMP_RATE','C_WELL','C_MACHINE'])
    count = 0
    for i in range(n1):
        for j in range(n2):
            for k in range(n3):
                for l in range(n4):
                    inputs.loc[count, 'PRICE_MULTIPLIER'] = mulitpliers[i]
                    inputs.loc[count, 'GRID_RAMP_RATE'] = ramp_rates[j]
                    inputs.loc[count, 'C_WELL'] = well_cost[k]
                    inputs.loc[count, 'C_MACHINE'] = machine_cost[l]
                    count = count + 1

    # create baseline model
    model = create_model()

    # inputs, results = parameterSweep(model, inputs.loc[0,:])

    # Perform Simulations (Run all plant variations in parallel)
    with parallel_backend('multiprocessing', n_jobs=-1): # -1 uses all processors
        output = Parallel(verbose=10)(
            delayed(parameterSweep)(model, inputs.loc[index,:]) for index in
            range(n_cases))

    # Combine outputs into single dataframe and save
    df = pd.DataFrame(output)
    # df = df.transpose()
    os.chdir('results')
    df.to_csv('results.csv')
