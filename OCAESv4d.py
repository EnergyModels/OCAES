# Updated 7/19/2014
# structure optimized based on OCAESv5.py, breakpoint added, modules not contained in Cygnus are commented out.

# 7/18/2014
# Study the LCOE as the function of X0 at a fixed CF in the wind-GT scenario
# CF = 0.38 ~ 1.00, n0 is a function of CF

from os import getcwd, chdir, mkdir
from os.path import isdir
from pyomo.environ import *
from pyomo.opt import SolverFactory
from IPython import embed as IP
from Preprocessor import *
from time import time
import csv
# import matplotlib.pyplot as plt
from sys import argv
from copy import copy

def wind_sent_rule(model,t):
	return model.w_s[t] == etaT0*(model.w[t] - model.drop[t])

#-------------------------------------------------------------------------------
# Constraints
#-------------------------------------------------------------------------------
# Constraint a, hourly wind energy sent to the merging point constraint
def CSTNa1_rule(model, t):
	return model.w_s[t] >= 0

def CSTNa2_rule(model, t):
	return model.w_s[t]/etaT0 <= Xt0*model.n0

# Constraint b, hourly enregy sent to the grid constraint
def CSTNb_rule(model, t):
	return model.w_s[t] + model.p[t] <= Xt0*model.n0*etaT0
	
# Constraint c, GT plant output energy constraint
def CSTNc2_rule(model, t):
	return model.p[t] <= model.Xgt

# Constraint d, TSE and CF constriant (optional)
def CSTNd1_rule(model):
	lhs = sum((model.p[t] + model.w_s[t]) for t in model.T)
	rhs = TSE
	return lhs >= rhs
	
def CSTNd2_rule(model):
	lhs = sum((model.p[t] + model.w_s[t]) for t in model.T) - model.SCF*etaT0*Xt0*T*model.n0
	rhs = 0
	return lhs >= rhs
#-------------------------------------------------------------------------------
# Objective funtion, not the real levelized revenue, but the simplified version
#-------------------------------------------------------------------------------
def OBJ_rule(model):
	return (Cgt*CCRgt + Fgt)*model.Xgt + Vgt*8760.0/T*sum(model.p[t] for t in model.T) + 3.6*Cng*8760.0/T*sum(model.p[t]/etagt for t in model.T)

WindMode = True
WaveMode = False

model	= ConcreteModel()
opt		= SolverFactory("cplex")

#-------------------------------------------------------------------------------
# Data input from csv files, 'data.csv', 'wind.csv' and 'wave.csv'
#--------------------------------------------------------------------------------

data = data_generator() # 1st column: name, 2nd column: value
wind = wind_generator()
wave = wave_generator()

Xw1 	= data['Xw1']
etaT1 	= data['etaT1']
C1 		= data['C1']
F1 		= data['F1']
V1 		= data['V1']
Xw2 	= data['Xw2']
etaT2 	= data['etaT2']
C2 		= data['C2']
F2 		= data['F2']
V2 		= data['V2']
etaC 	= data['etaC']
etaE 	= data['etaE']
Cgt		= data['Cgt']
Fgt		= data['Fgt']
Vgt		= data['Vgt']
etagt 	= data['etagt']
Cng		= data['Cng']
Xt0 	= data['Xt0']
etaT0 	= data['etaT0']
T 		= data['T']
r	 	= data['r']
rgt	 	= data['rgt']
L	 	= data['L']
s0 		= data['s0']

CCR		= r*(1 + r)**L/((1 + r)**L - 1)
CCRgt	= rgt*(1 + rgt)**L/((1 + rgt)**L - 1)

T		= int(T)
Xt0		= int(Xt0) # Xt0 is the step size
steps	= int(200/Xt0)

model.T = Set(initialize = range(1, T + 1))

w = list()	
for i in range(0, T):
	w.append(WindMode*wind[i] + WaveMode*wave[i])

# Power dispatched to the collecting point from wind & wave farms
w_ini = {i: WindMode*etaT1*wind[i - 1] + WaveMode*etaT2*wave[i - 1] for i in range(1, T + 1)}
model.w			= Param(model.T, initialize = w_ini)
model.n0		= Param(initialize = 0, mutable = True)
model.SCF		= Param(initialize = 0, mutable = True)
model.w_s		= Var(model.T, within = NonNegativeReals) # w_s, energy sent to the point slightly ahead of the merging point
model.Xgt		= Var(within = NonNegativeReals) # GT capacity.
model.drop		= Var(model.T, within = NonNegativeReals) # Operation drop(t), MWh/h, non-negative real
model.p			= Var(model.T, within = NonNegativeReals) # Hourly generated energy from gas plant, with constraint c - i
model.wind_sent	= Constraint(model.T, rule = wind_sent_rule)
model.CSTNa1	= Constraint(model.T, rule = CSTNa1_rule)
model.CSTNa2	= Constraint(model.T, rule = CSTNa2_rule)
model.CSTNb		= Constraint(model.T, rule = CSTNb_rule)
model.CSTNc2	= Constraint(model.T, rule = CSTNc2_rule)
model.CSTNd2	= Constraint(rule = CSTNd2_rule)
model.OBJ		= Objective(sense = minimize, rule = OBJ_rule)
################################################################################
# Solve the model.
################################################################################

if __name__ == '__main__':
	instance = model.create()
	
	if len(argv) > 1:
		breakpoint = float(argv[1])
	else:
		breakpoint = 0
		
	dir_result = 'Result_' + str(T) + 'h' + '_' + str(steps) + 'x' + str(Xt0) + 'MW_GT_full'
	if not isdir(dir_result):
		mkdir(dir_result)
	chdir(dir_result)

	CF_interval	= [0.01*i for i in range(38, 101)]
	n0_interval = dict()
	for i in [0.01*j for j in range(38, 101)]:
		for n in range(1, 201):
			temp = copy(w)
			for j in range(0, len(w)):
				if temp[j] > n*Xt0:
					temp[j] = n*Xt0
			CF = sum(temp)/(n*Xt0*len(w))
			if CF < i:
				n0_interval[str(int(round(i*100)))] = range(n, 201)
				break
			elif n == 200:
				n0_interval[str(int(round(i*100)))] = []
	
	counter		= 0  # Counter indicates the progress.
	total_run	= sum(len(n0_interval[i]) for i in n0_interval)
	# IP()
	for SCF in CF_interval:
		if SCF < breakpoint:
			counter = counter + len(n0_interval[str(int(round(SCF*100)))])
			continue
		# Results containers
		List_n0		= list()
		List_Xgt	= list()
		List_LC		= list()
		List_CF		= list()
		List_LT		= list()
		List_AE		= list() # Actual Energy Production
		
		for n0 in n0_interval[str(int(round(SCF*100)))]:
			counter += 1
			# Given n0 (# of 20 MW), the capital cost in $ can be calculated.
			# Cable and installation & transport go with Lundberg (2003),
			# Transformer goes with Lazaridis (2005).
			C0 = 16.59*(1.971E6 + 0.209E6*exp(1.66*n0*Xt0*1E6/1E8))*1.6*0.15 +\
				 16.59*2400*1600*0.15 +\
				 0.03327*(n0*Xt0)**0.7513*1E6*1.35
			t1 = time()
			
			instance.n0.set_value(n0)
			instance.SCF.set_value(SCF)
			instance.preprocess()
			
			results	= opt.solve(instance)
			if instance.load(results) == False:
				print '\n%s\t%i' % ('Simulation Hours:', int(T))
				print '%s\t%i' % ('Multiple of 20 MW:', n0)
				print '%s\t%f' % ('Capacity Factor >=', SCF)
				print 'This iteration is infeasible\n'
				# IP()
				continue
			
			x = range(1, T + 1)
			output_n0		= n0
			# output_n0		= value(instance.n0)
			output_Xgt		= value(instance.Xgt)
			output_w		= list()
			output_drop		= list()
			output_p		= list()
			output_w_s		= list() # w_s is the energy received at the grid side slightly before the merging point
			threshold		= list() # The grid transmission line capacity, i.e.: X0
			for i in range(1, T + 1):
				output_w.append(value(instance.w[i]))
				output_drop.append(value(instance.drop[i]))
				output_p.append(value(instance.p[i]))
				output_w_s.append(value(instance.w_s[i]))
				threshold.append(output_n0*Xt0)
			
			# Resulting operation rules recording
			csvname = 'result' + '_' + str(n0) + '_' + str(int(100*SCF)) + '.csv'
			with open(csvname, 'wb') as f:
				writer = csv.writer(f)
				zipped = zip(x, output_w, output_w_s, output_drop, output_p)
				zipped[:0] = [('Time', 'Input Power by wind', 'Output Power by wind', 'Drop', 'GT output')]
				writer.writerows(zipped)
			
			AnnualCapital		= CCR*(C1 + C2 + C0) + CCRgt*Cgt*output_Xgt
			AnnualFixed			= F1 + F2 + Fgt*output_Xgt
			AnnualVariable		= 8760.0/T*(V1*sum(wind[0: T]) + V2*sum(wave[0: T]) + Vgt*sum(output_p) + 3.6*Cng*sum(output_p)/etagt)
			AnnualProduced		= 8760.0/T*(sum(output_w_s) + sum(output_p))
			
			List_n0.append(output_n0)
			List_Xgt.append(output_Xgt)
			List_LC.append((AnnualCapital + AnnualFixed + AnnualVariable)/AnnualProduced)
			List_CF.append((AnnualProduced)/(output_n0*Xt0*8760*etaT0))
			List_LT.append(time() - t1)
			List_AE.append(sum(output_w_s) + sum(output_p))
			
			print '\n%s\t%i' % ('Simulation Hours:', int(T))
			print '%s\t%i' % ('Multiple of step:', List_n0[-1])
			print '%s\t%f' % ('Capacity Factor >=', SCF)
			print '%s\t%f' % ('Capacity Factor:', List_CF[-1])
			print '%s\t%f' % ('Capacity of GT (MW):', List_Xgt[-1])
			print '%s\t%f' % ('Levelized Cost ($/MWh):', List_LC[-1])
			print '%s\t%f' % ('Time elapsed (s):', List_LT[-1])
			
			print '%s\t%i%s%i' % ('Completed/Total:', counter, '/', total_run)
		
		csvname = 'CF' + '_' + str(int(round(SCF*100))) + '_' + str(T) + 'h' + '.csv'
		with open(csvname, 'wb') as f:
			writer = csv.writer(f)
			rows = list()
			for i in range(0, len(n0_interval[str(int(round(SCF*100)))])):
					rows.append((List_n0[i], SCF, List_CF[i], List_Xgt[i], List_LC[i], List_LT[i]))
					# rows.append((List_n0[i], List_TSE[i], List_AE[i], List_Xgt[i], List_LC[i], List_CF[i], List_LT[i]))
			rows[:0] = [('n0', 'Target CF', 'CF', 'Xgt (MW)', 'Lev. Cost ($/MWh)', 'Time (s)')]
			writer.writerows(rows)