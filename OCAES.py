# This version is for Windows OS. The following modules are different in linux.
# 1) IPython, 2) matplotlib, 3) glpk solver.
# Updated 4/4/2014, based on OCAESv5.py 3/3/2014 version.
# 1) import part is refined. 2) Structure is optimized.

from os import getcwd, chdir, mkdir
from os.path import isdir
from pyomo.environ import *
from pyomo.opt import SolverFactory
# from IPython import embed as II
import Preprocessor as pre
from time import time
import csv
import matplotlib.pyplot as plt





# ================================
# Import data
# ================================










# -------------------------------------------------------------------------------
# Data input from csv files, 'data.csv', 'wind.csv' and 'wave.csv'
# --------------------------------------------------------------------------------

# Read-in data
data = pre.data_generator()  # 1st column: name, 2nd column: value
wind = pre.wind_generator()
wave = pre.wave_generator()

# Assign data to local variables
Xw1 = data['Xw1']
etaT1 = data['etaT1']
C1 = data['C1']
F1 = data['F1']
V1 = data['V1']
Xw2 = data['Xw2']
etaT2 = data['etaT2']
C2 = data['C2']
F2 = data['F2']
V2 = data['V2']
Xc = data['Xc']
Xe = data['Xe']
etaC = data['etaC']
etaE = data['etaE']
Cl = data['Cl'] / 1.0
Cs = data['Cs'] / 1.0
Xt0 = data['Xt0']
etaT0 = data['etaT0']
T = data['T']
r = data['r']
L = data['L']
Ls = data['Ls']
s0 = data['s0']



T = int(T)
Xt0 = int(Xt0)  # Xt0 is the step length
steps = int(200 / Xt0)













if __name__ == '__main__':
    instance = model.create()

    # Put the results recording file in a subdirectory.
    dir_result = 'Result_' + str(T) + 'h' + '_' + str(steps) + 'x' + str(Xt0) + 'MW'
    if not isdir(dir_result):
        mkdir(dir_result)
    chdir(dir_result)

    counter = 0  # Counter indicates the progress.
    total_run = sum(len(SCF_interval[i]) for i in SCF_interval)

    for n0 in range(1, steps):  # No need to do the last step, i.e. the 200MW TL
        if n0 < breakpoint:
            counter = counter + len(SCF_interval[str(n0)])
            continue
        # Given n0 (# of 20 MW), the capital cost in $ can be calculated.
        # Cable and installation & transport go with Lundberg (2003),
        # Transformer goes with Lazaridis (2005).
        C0 = 16.59 * (1.971E6 + 0.209E6 * exp(
            1.66 * n0 * Xt0 * 1E6 / 1E8)) * 1.6 * 0.15 + 16.59 * 2400 * 1600 * 0.15 + 0.03327 * (
                     n0 * Xt0) ** 0.7513 * 1E6 * 1.35

        List_n0 = list()
        List_nl = list()
        List_Xs = list()
        List_LC = list()
        List_CF = list()
        List_LT = list()

        List_SCF = list()

        for SCF in SCF_interval[str(n0)]:
            counter = counter + 1
            tic = time()

            instance.n0.set_value(n0)
            instance.SCF.set_value(SCF)
            instance.preprocess()

            results = opt.solve(instance)
            if instance.load(results) == False:
                print '\n%s\t%i' % ('Simulation Hours:', int(T))
                print '%s\t%i' % ('Multiple of 20 MW:', n0)
                print '%s\t%f' % ('Capacity Factor >=', SCF)
                print 'This iteration is infeasible\n'
                # II()
                continue
            ####################################################################

            x = range(1, T + 1)
            output_n0 = n0
            output_nl = value(instance.nl)
            output_Xs = value(instance.Xs)
            output_w = list()
            output_store = list()
            output_dispatch = list()
            output_drop = list()
            output_w_s = list()
            threshold = list()  # The grid transmission line capacity
            for i in range(1, T + 1):
                output_w.append(value(instance.w[i]))
                output_store.append(value(instance.store[i]))
                output_dispatch.append(value(instance.dispatch[i]))
                output_drop.append(value(instance.drop[i]))
                output_w_s.append(value(instance.w_s[i]))
                threshold.append(output_n0 * Xt0)

            # Resulting operation rules recording, temporarily commented out
            csvname = 'result' + '_' + str(n0) + '_' + str(int(100 * SCF)) + '.csv'
            with open(csvname, 'wb') as f:
                writer = csv.writer(f)
                zipped = zip(x, output_w, output_w_s, output_store, output_dispatch, output_drop)
                zipped[:0] = [('Time', 'Input Power', 'Power to grid', 'Store', 'Dispatch', 'Drop')]
                writer.writerows(zipped)

            # Cost/Revenue calculation
            AnnualCapital = CCR * (C0 + C1 + C2 + output_nl * Cl) + CCRs * (output_Xs * Cs)
            AnnualFixed = F1 + F2
            AnnualVariable = 8760.0 / T * (V1 * sum(wind[0: T]) + V2 * sum(wave[0: T]))
            AnnualProduced = 8760.0 / T * sum(output_w_s)

            List_n0.append(output_n0)
            List_nl.append(output_nl)
            List_Xs.append(output_Xs)
            List_LC.append((AnnualCapital + AnnualFixed + AnnualVariable) / AnnualProduced)
            List_SCF.append(SCF)
            List_CF.append((AnnualProduced) / (output_n0 * Xt0 * 8760))  # This is real CF
            List_LT.append(time() - tic)

            print '\n%s\t%i' % ('Simulation Hours:', int(T))
            print '%s\t%i' % ('Multiple of step:', List_n0[-1])
            print '%s\t%f' % ('Capacity Factor >=', SCF)
            print '%s\t%f' % ('Capacity Factor:', List_CF[-1])
            print '%s\t%i' % ('Numbers of pistons:', List_nl[-1])
            print '%s\t%f' % ('Storage capacity (MW):', List_Xs[-1])
            print '%s\t%f' % ('Levelized Cost ($/MWh):', List_LC[-1])
            print '%s\t%f' % ('Time elapsed (s):', List_LT[-1])

            print '%s\t%i%s%i' % ('Completed/Total:', counter, '/', total_run)

        csvname = 'n0' + '_' + str(n0) + '_' + str(T) + 'h' + '.csv'
        with open(csvname, 'wb') as f:
            writer = csv.writer(f)
            rows = list()
            for i in range(0, len(List_SCF)):
                rows.append((List_n0[i], List_SCF[i], List_CF[i], List_nl[i], List_Xs[i], List_LC[i], List_LT[i]))
            rows[:0] = [('n0', 'Target CF', 'CF', 'nl', 'Xs', 'Lev. Cost ($/MWh)', 'Time (s)')]
            writer.writerows(rows)  # II()
