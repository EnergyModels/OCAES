# Attention! In v1 ~ v3, CF is calculated at the collection point, while in this version
# CF is calculated at the grid-tied point. Methods are the same but there is a etaT0
# defference.

# Updated 3/24/14, "from Preprocessor import *"
# Updated 3/16/14, breakpoint added.

from os import getcwd, chdir, mkdir
from os.path import isdir
from coopr.pyomo import *
from coopr.opt import SolverFactory
from IPython import embed as II
from Preprocessor import *
from time import time
import csv
import matplotlib.pyplot as plt
from sys import argv

WindMode = True
WaveMode = False

model	= ConcreteModel()
opt		= SolverFactory("glpk")

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
Xt0		= int(Xt0) # Xt0 is the step length
steps	= int(200/Xt0)

model.T = Set(initialize = range(1, T + 1))

w = list()	
for i in range(0, T):
	w.append(WindMode*wind[i] + WaveMode*wave[i])

CF_up_1			= CF_natural_up(w, Xt0)
CF_up_2		 	= CF_OCAES_up(w, Xt0, etaC, etaE)
SCF_interval	= CF_interval_OCAES(CF_up_1, CF_up_2)

# This is the min and max capacity factor for a given number of transmission line.
# Should change all "CF_interval" into "SCF_interval"
# SCF_interval = {'1': [0.01*i for i in range(84, 100, 1)],
				# '2': [0.01*i for i in range(75, 100, 1)],
				# '3': [0.01*i for i in range(69, 100, 1)],
				# '4': [0.01*i for i in range(63, 86, 1)],
				# '5': [0.01*i for i in range(58, 72, 1)],
				# '6': [0.01*i for i in range(54, 61, 1)],
				# '7': [0.01*i for i in range(50, 53, 1)],
				# '8': [0.01*i for i in range(47, 48, 1)],
				# '9': [0.01*i for i in range(42, 43, 1)]}

# SCF_interval = {'1': [0.01*i for i in range(95, 100, 1)],
				# '2': [0.01*i for i in range(75, 95, 1)],
				# '3': [0.01*i for i in range(66, 75, 1)],
				# '4': [0.01*i for i in range(60, 66, 1)],
				# '5': [0.01*i for i in range(55, 60, 1)],
				# '6': [0.01*i for i in range(51, 55, 1)],
				# '7': [0.01*i for i in range(47, 51, 1)],
				# '8': [0.01*i for i in range(43, 47, 1)],
				# '9': [0.01*i for i in range(39, 43, 1)]}

# Power dispatched to the collecting point from wind & wave farms
w_ini = {i: WindMode*etaT1*wind[i - 1] + WaveMode*etaT2*wave[i - 1] for i in range(1, T + 1)}
model.w = Param(model.T, initialize = w_ini)

#-------------------------------------------------------------------------------
# Decision variables definition and initialization, with part of constraints
#-------------------------------------------------------------------------------

# model.n0		= Var(within = NonNegativeIntegers) # Amount of grid Transmission line, non-negative integer
model.Xgt		= Var(within = NonNegativeReals) # GT capacity.
model.drop		= Var(model.T, within = NonNegativeReals) # Operation drop(t), MWh/h, non-negative real
model.p			= Var(model.T, within = NonNegativeReals) # Hourly generated energy from gas plant, with constraint c - i

#-------------------------------------------------------------------------------
# Non-decision variable definition and initialization, with part of constraint
#-------------------------------------------------------------------------------

# w_s, energy sent to the point slightly ahead of the merging point
model.w_s		= Var(model.T, within = NonNegativeReals)

def wind_sent_rule(model,t):
	return model.w_s[t] == etaT0*(model.w[t] - model.drop[t])

#-------------------------------------------------------------------------------
# Constraints
#-------------------------------------------------------------------------------
# Constraint a, hourly wind energy sent to the merging point constraint
def CSTNa1_rule(model, t):
	return model.w_s[t] >= 0

def CSTNa2_rule(model, t):
	return model.w_s[t]/etaT0 <= Xt0*n0
	# return model.w_s[t]/etaT0 <= Xt0*model.n0

# Constraint b, hourly enregy sent to the grid constraint
def CSTNb_rule(model, t):
	return model.w_s[t] + model.p[t] <= Xt0*n0*etaT0
	# return model.w_s[t] + model.p[t] <= Xt0*model.n0*etaT0
	
# Constraint c, GT plant output energy constraint
def CSTNc2_rule(model, t):
	return model.p[t] <= model.Xgt

# Constraint d, TSE and CF constriant (optional)
def CSTNd1_rule(model):
	lhs = sum((model.p[t] + model.w_s[t]) for t in model.T)
	rhs = TSE
	return lhs >= rhs
	
def CSTNd2_rule(model):
	lhs = sum((model.p[t] + model.w_s[t]) for t in model.T) - SCF*etaT0*Xt0*T*n0
	# lhs = sum((model.p[t] + model.w_s[t]) for t in model.T) - SCF*etaT0*Xt0*T*model.n0
	rhs = 0
	return lhs >= rhs
#-------------------------------------------------------------------------------
# Objective funtion, not the real levelized revenue, but the simplified version
#-------------------------------------------------------------------------------

def OBJ_rule(model):
	return (Cgt*CCRgt + Fgt)*model.Xgt + Vgt*8760.0/T*sum(model.p[t] for t in model.T) + 3.6*Cng*8760.0/T*sum(model.p[t]/etagt for t in model.T)
	# return CCR*C0*n0 + (Cgt*CCRgt + Fgt)*model.Xgt + Vgt*8760.0/T*sum(model.p[t] for t in model.T) + 3.6*Cng*8760.0/T*sum(model.p[t]/etagt for t in model.T)
	# return CCR*C0*model.n0 + (Cgt*CCRgt + Fgt)*model.Xgt + Vgt*8760.0/T*sum(model.p[t] for t in model.T) + 3.6*Cng*8760.0/T*sum(model.p[t]/etagt for t in model.T)
	
################################################################################
# Solve the model.
################################################################################

if __name__ == '__main__':
	if len(argv) > 1:
		breakpoint = int(argv[1])
	else:
		breakpoint = 0
	
	dir_result = 'Result_' + str(T) + 'h' + '_' + str(steps) + 'x' + str(Xt0) + 'MW' + '_GT'
	if not isdir(dir_result):
		mkdir(dir_result)
	chdir(dir_result)
	# try:
		# chdir(dir_result)
	# except WindowsError:
		# mkdir(dir_result)
		# chdir(dir_result)

	counter		= 0  # Counter indicates the progress.
	total_run	= sum(len(SCF_interval[i]) for i in SCF_interval)
	
	for n0 in range(1, steps):
		if n0 < breakpoint:
			counter = counter + len(SCF_interval[str(n0)])
			continue
		# Given n0 (# of 20 MW), the capital cost in $ can be calculated.
		# Cable and installation & transport go with Lundberg (2003),
		# Transformer goes with Lazaridis (2005).
		C0 = 16.59*(1.971E6 + 0.209E6*exp(1.66*n0*Xt0*1E6/1E8))*1.6*0.15 +\
		     16.59*2400*1600*0.15 +\
		     0.03327*(n0*Xt0)**0.7513*1E6*1.35
		
		# Results containers
		List_n0		= list()
		List_Xgt	= list()
		List_LC		= list()
		List_CF		= list()
		List_LT		= list()
		List_AE		= list() # Actual Energy Production
		
		List_SCF	= SCF_interval[str(n0)]
		# List_TSE	= range(145489, 673370, 5000)
		for SCF in List_SCF:
			counter = counter + 1
			t1 = time()
			
			# model.n0.reset()
			model.Xgt.reset()
			model.drop.reset()
			model.p.reset()
			model.w_s.reset()
			
			model.wind_sent	= Constraint(model.T, rule = wind_sent_rule)
			model.CSTNa1	= Constraint(model.T, rule = CSTNa1_rule)
			model.CSTNa2	= Constraint(model.T, rule = CSTNa2_rule)
			model.CSTNb		= Constraint(model.T, rule = CSTNb_rule)
			model.CSTNc2	= Constraint(model.T, rule = CSTNc2_rule)
			model.CSTNd2	= Constraint(rule = CSTNd2_rule)
			# model.CSTNd1	= Constraint(rule = CSTNd1_rule)
			
			model.OBJ		= Objective(sense = minimize, rule = OBJ_rule)
			
			instance	= model.create()
			results		= opt.solve(instance)
			if instance.load(results) == False:
				II()
			
			x = range(1, T + 1)
			output_n0		= n0
			# output_n0		= value(instance.n0)
			output_Xgt		= value(instance.Xgt)
			output_w		= list()
			output_drop		= list()
			output_p		= list()
			output_w_s		= list() # w_s is the energy received at the grid side slightly before the merging point
			threshold		= list() # The grid transmission line capacity
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
			# print '%s\t%f' % ('Total Energy (MWh) >=', TSE)
			print '%s\t%f' % ('Capacity Factor:', List_CF[-1])
			# print '%s\t%f' % ('Actual Energy (MWh):', List_AE[-1])
			print '%s\t%f' % ('Capacity of GT (MW):', List_Xgt[-1])
			print '%s\t%f' % ('Levelized Cost ($/MWh):', List_LC[-1])
			print '%s\t%f' % ('Time elapsed (s):', List_LT[-1])
			
			print '%s\t%i%s%i' % ('Completed/Total:', counter, '/', total_run)
		
		csvname = 'n0' + '_' + str(n0) + '_' + str(T) + 'h' + '.csv'
		# csvname = 'TSE' + '_' + str(TSE) + '_' + str(T) + 'h' + '.csv'
		with open(csvname, 'wb') as f:
			writer = csv.writer(f)
			rows = list()
			for i in range(0, len(List_SCF)):
			# for i in range(0, len(List_TSE)):
					rows.append((List_n0[i], List_SCF[i], List_CF[i], List_Xgt[i], List_LC[i], List_LT[i]))
					# rows.append((List_n0[i], List_TSE[i], List_AE[i], List_Xgt[i], List_LC[i], List_CF[i], List_LT[i]))
			rows[:0] = [('n0', 'Target CF', 'CF', 'Xgt (MW)', 'Lev. Cost ($/MWh)', 'Time (s)')]
			writer.writerows(rows)
