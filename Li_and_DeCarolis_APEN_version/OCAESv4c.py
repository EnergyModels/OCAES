# This script is aimed at seeking for the break-even social cost of carbon (SCC)
# by looping from 10 $/tC to 1000$/tC, while keeping X0 and CF the same in the optimal OCAES.

from os import getcwd, chdir, mkdir
from os.path import isdir
from pyomo.environ import *
from pyomo.opt import SolverFactory
from IPython import embed as IP
from Preprocessor import data_generator, wind_generator, wave_generator, CF_natural_up, CF_OCAES_up, CF_interval_noOCAES, CF_interval_OCAES
from time import time
from csv import reader, writer
from matplotlib import pyplot as plt
from sys import argv
from decimal import Decimal

# # Return n0 corresponding to CF in csvname
# def CF2n0(CF, csvname):
	# from csv import reader
	# from decimal import Decimal
	# with open(csvname, 'rb') as f:
		# csv_reader = reader(f)
		# for row in csv_reader:
			# if int(100*Decimal(row[1])) == int(round(100*(CF))):
				# return int(Decimal(row[0]))
			# else:
				# continue

def wind_sent_rule(model,t):
	return model.w_s[t] == etaT0*(model.w[t] - model.drop[t])

def CSTNa1_rule(model, t):
	return model.w_s[t] >= 0

def CSTNa2_rule(model, t):
	return model.w_s[t]/etaT0 <= Xt0*model.n0

def CSTNb_rule(model, t):
	return model.w_s[t] + model.p[t] <= Xt0*model.n0*etaT0

def CSTNc2_rule(model, t):
	return model.p[t] <= model.Xgt

def CSTNd2_rule(model):
	lhs = sum((model.p[t] + model.w_s[t]) for t in model.T) - model.SCF*etaT0*Xt0*T*model.n0
	rhs = 0
	return lhs >= rhs

def OBJ_rule(model):
	return (Cgt*CCRgt + Fgt)*model.Xgt + 8760.0/T*sum(model.p[t]/etagt for t in model.T)*\
               (Vgt + 3.6*Cng/etagt + 3.6/etagt/1.055*14.47*model.tx/1000.0)

WindMode = True
WaveMode = False

model	= AbstractModel()
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
Xt0		= int(Xt0) # Xt0 is the step length
steps	= int(200/Xt0)

model.T = Set(initialize = range(1, T + 1))

w = list()	
for i in range(0, T):
	w.append(WindMode*wind[i] + WaveMode*wave[i])

# Power dispatched to the collecting point from wind & wave farms
w_ini = {i: WindMode*etaT1*wind[i - 1] + WaveMode*etaT2*wave[i - 1] for i in range(1, T + 1)}
model.w		= Param(model.T, initialize = w_ini)

model.n0	= Param(initialize = 0, mutable = True)
model.SCF	= Param(initialize = 0, mutable = True)
model.tx	= Param(initialize = 0, mutable = True)

model.Xgt	= Var(within = NonNegativeReals) # GT capacity.
model.drop	= Var(model.T, within = NonNegativeReals) # Operation drop(t), MWh/h, non-negative real
model.p		= Var(model.T, within = NonNegativeReals) # Hourly generated energy from gas plant, with constraint c - i
model.w_s	= Var(model.T, within = NonNegativeReals)

model.wind_sent	= Constraint(model.T, rule = wind_sent_rule)
model.CSTNa1	= Constraint(model.T, rule = CSTNa1_rule)
model.CSTNa2	= Constraint(model.T, rule = CSTNa2_rule)
model.CSTNb		= Constraint(model.T, rule = CSTNb_rule)
model.CSTNc2	= Constraint(model.T, rule = CSTNc2_rule)
model.CSTNd2	= Constraint(rule = CSTNd2_rule)

model.OBJ		= Objective(sense = minimize, rule = OBJ_rule)

if __name__ == '__main__':
	instance = model.create()
	
	list_SCC = range(100, 1100, 100)
	list_SCF = list()
	list_n0 = list()
	csvname = 'minimum_' + str(T) + '_' + str(steps) + 'x' + str(Xt0) + 'MW.csv'
	with open(csvname, 'rb') as f:
		csv_reader = reader(f)
		for row in csv_reader:
			list_n0.append(int(Decimal(row[0])))
			list_SCF.append(Decimal(row[1]))

	total_run = len(list_SCC)*len(list_n0)
	counter	= 0  # Counter indicates the progress.
	
	dir_result = 'Result_' + str(T) + 'h' + '_' + str(steps) + 'x' + str(Xt0) + 'MW' + '_P' # P indicates prescriptive analysis
	if not isdir(dir_result):
		mkdir(dir_result)
	chdir(dir_result)
	print 'Entering result directory...Done!\n'
	
	for SCC in list_SCC:
		instance.tx.set_value(SCC)
		R_n0	= list()
		R_Xgt	= list()
		R_LC	= list()
		R_SCF	= list()
		R_CF	= list()
		R_LT	= list()
		R_AE	= list() # Actual Energy Production
		for i in range(0, len(list_n0)):
			counter += 1
			tic = time()
			input_SCF = float(list_SCF[i])
			input_n0 = list_n0[i]
			
			instance.n0.set_value(input_n0)
			instance.SCF.set_value(input_SCF)
			instance.preprocess()
			results = opt.solve(instance)
			if instance.load(results) == False:
				IP()
			
			x = range(1, T + 1)
			output_n0		= value(instance.n0)
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
			csvname = 'result' + '_' + str(SCC) + '_' + str(input_n0) + '_' + str(round(100*(input_SCF))) + '.csv'
			with open(csvname, 'wb') as f:
				csv_writer = writer(f)
				zipped = zip(x, output_w, output_w_s, output_drop, output_p)
				zipped[:0] = [('Time', 'Input Power by wind', 'Output Power by wind', 'Drop', 'GT output')]
				csv_writer.writerows(zipped)
			
			C0 = 16.59*(1.971E6 + 0.209E6*exp(1.66*output_n0*Xt0*1E6/1E8))*1.6*0.15 +\
				 16.59*2400*1600*0.15 +\
				 0.03327*(output_n0*Xt0)**0.7513*1E6*1.35
			
			AnnualCapital		= CCR*(C1 + C2 + C0) + CCRgt*Cgt*output_Xgt
			AnnualFixed			= F1 + F2 + Fgt*output_Xgt
			AnnualVariable		= 8760.0/T*(V1*sum(wind[0: T]) + V2*sum(wave[0: T]) + sum(output_p)*\
                                                            (Vgt + 3.6/etagt*Cng/etagt + 3.6/1.055*14.47*SCC/1000.0))
			AnnualProduced		= 8760.0/T*(sum(output_w_s) + sum(output_p))
			
			R_n0.append(output_n0)
			R_SCF.append(input_SCF)
			R_Xgt.append(output_Xgt)
			R_LC.append((AnnualCapital + AnnualFixed + AnnualVariable)/AnnualProduced)
			R_CF.append((AnnualProduced)/(output_n0*Xt0*8760*etaT0))
			R_LT.append(time() - tic)
			
			print '\n%s\t%i' % ('Social C cost ($/tC):', int(SCC))
			print '%s\t%i' % ('Multiple of step:', R_n0[-1])
			print '%s\t%f' % ('Capacity Factor >=', input_SCF)
			print '%s\t%f' % ('Capacity Factor:', R_CF[-1])
			print '%s\t%f' % ('Capacity of GT (MW):', R_Xgt[-1])
			print '%s\t%f' % ('Levelized Cost ($/MWh):', R_LC[-1])
			print '%s\t%f' % ('Time elapsed (s):', R_LT[-1])
			
			print '%s\t%i%s%i' % ('Completed/Total:', counter, '/', total_run)
		csvname = 'tax' + '_' + str(SCC) + '_' + str(T) + 'h' + '.csv'
		with open(csvname, 'wb') as f:
			csv_writer = writer(f)
			rows = list()
			for i in range(0, len(R_SCF)):
					rows.append((R_n0[i], R_SCF[i], R_CF[i], R_Xgt[i], R_LC[i], R_LT[i]))
			rows[:0] = [('n0', 'Target CF', 'CF', 'Xgt (MW)', 'Lev. Cost ($/MWh)', 'Time (s)')]
			csv_writer.writerows(rows)

