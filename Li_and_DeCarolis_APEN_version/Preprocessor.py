################################################################################
# data_generator() returns a dictionary where the key is the name of the 
# variable, which is the value of the item. The data is read from a csv file.
# 
# Both of wind_generator and wave_generator return a list with data read from 
# csv files.
#
# CF_natural_up() seeks for the upperbound of the wind farm's output CF by
# manipulating the # of TLs only, in %.
#
# CF_OCAES_up() seeks for the upperbound of the output CF by assuming infinite 
# capacities of compressor, expander and storage reservoir are installed, in %.
#
# CF_interval_noOCAES() returns a dictionary in which the CF interval from the 
# lowest natural upperbound to the natural upperbound for a certain # of TLs are 
# stored.
#
# CF_interval_OCAES() returns a dictionary in which the CF interval from the 
# natural upperbound to the upperbound with OCAES incorporated for each # of 
# TLs are stored.
################################################################################
def data_generator():
	from os import chdir
	from os import getcwd
	from csv import reader
	
	default = getcwd()
	chdir('data')
	
	data = dict()
	with open('data.csv', 'rb') as f: # 1st column: name, 2nd column: value
		csv_reader = reader(f, dialect = 'excel')
		for row in csv_reader:
			data[row[0]] = float(row[1])
	
	chdir(default)
	return data

def wind_generator():
	from os import chdir
	from os import getcwd
	from csv import reader
	
	default = getcwd()
	chdir('data')
	
	wind = list()
	with open('wind.csv', 'rb') as f:
		csv_reader = reader(f, dialect = 'excel')
		for row in csv_reader:
			wind.append(float(row[0]))
	
	chdir(default)
	return wind

def wave_generator():
	from os import chdir
	from os import getcwd
	from csv import reader
	
	default = getcwd()
	chdir('data')
	
	wave = list()
	with open('wave.csv', 'rb') as f:
		csv_reader = reader(f, dialect = 'excel')
		for row in csv_reader:
			wave.append(float(row[0]))
	
	chdir(default)
	return wave

def CF_natural_up(w, Xt0):
	from copy import copy
	from math import floor
	CF_up = dict()
	steps = int(200.0/Xt0)
	for n0 in range(1, steps):
		temp = copy(w)
		for i in range(0, len(w)):
			if temp[i] > n0*Xt0:
				temp[i] = n0*Xt0
		CF_up[str(n0)] = int(floor(100*sum(temp)/(n0*Xt0*len(w))))
	return CF_up # Attention! returned value is 100*CF.

def CF_OCAES_up(w, Xt0, etaC, etaE):
	from copy import copy
	from math import floor
	CF_up = dict()
	steps = int(200.0/Xt0)
	for n0 in range(1, steps):
		temp = copy(w)
		reservoir = 0.0
		for i in range(0, len(temp)):
			if temp[i] >= n0*Xt0:
				reservoir = reservoir + etaC*(temp[i] - n0*Xt0)
				temp[i] = n0*Xt0
			elif reservoir > 0:
				deltaS = min(reservoir, (n0*Xt0 - temp[i])/etaE)
				reservoir = reservoir - deltaS
				temp[i] = temp[i] + deltaS*etaE
		CF_up[str(n0)] = int(floor(100*sum(temp)/(n0*Xt0*len(w))))
	return CF_up # Attention! returned value is 100*CF.

def CF_interval_noOCAES(CF_natural_up):
	SCF_interval_noOCAES = dict()
	lb = CF_natural_up[str(len(CF_natural_up))]
	for i in range(1, len(CF_natural_up) + 1):
		SCF_interval_noOCAES[str(i)] = [0.01*j for j in range(lb, CF_natural_up[str(i)] + 1)]
	# SCF_interval_noOCAES = {'1': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['1'] + 1)],
							# '2': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['2'] + 1)],
							# '3': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['3'] + 1)],
							# '4': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['4'] + 1)],
							# '5': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['5'] + 1)],
							# '6': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['6'] + 1)],
							# '7': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['7'] + 1)],
							# '8': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['8'] + 1)],
							# '9': [0.01*i for i in range(CF_natural_up['9'], CF_natural_up['9'] + 1)]}
	return SCF_interval_noOCAES # Attention! returned value is exact CF.

def CF_interval_OCAES(CF_natural_up, CF_OCAES_up):
	SCF_interval = dict()
	for i in range(1, len(CF_natural_up) + 1):
		SCF_interval[str(i)] = [0.01*j for j in range(CF_natural_up[str(i)] + 1, CF_OCAES_up[str(i)] + 1)]
		# SCF_interval = {'1': [0.01*i for i in range(CF_natural_up['1'] + 1, CF_OCAES_up['1'] + 1)],
						# '2': [0.01*i for i in range(CF_natural_up['2'] + 1, CF_OCAES_up['2'] + 1)],
						# '3': [0.01*i for i in range(CF_natural_up['3'] + 1, CF_OCAES_up['3'] + 1)],
						# '4': [0.01*i for i in range(CF_natural_up['4'] + 1, CF_OCAES_up['4'] + 1)],
						# '5': [0.01*i for i in range(CF_natural_up['5'] + 1, CF_OCAES_up['5'] + 1)],
						# '6': [0.01*i for i in range(CF_natural_up['6'] + 1, CF_OCAES_up['6'] + 1)],
						# '7': [0.01*i for i in range(CF_natural_up['7'] + 1, CF_OCAES_up['7'] + 1)],
						# '8': [0.01*i for i in range(CF_natural_up['8'] + 1, CF_OCAES_up['8'] + 1)],
						# '9': [0.01*i for i in range(CF_natural_up['9'] + 1, CF_OCAES_up['9'] + 1)]}
	return SCF_interval # Attention! returned value is exact CF.


if __name__ == '__main__':
	import csv
	from IPython import embed as II
	from os import getcwd
	from sys import argv
	
	data	= data_generator()
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
	Xc 		= data['Xc']
	Xe 		= data['Xe']
	etaC 	= data['etaC']
	etaE 	= data['etaE']
	Cl		= data['Cl']/1.0
	Cs	 	= data['Cs']/1.0
	Xt0 	= data['Xt0']
	etaT0 	= data['etaT0']
	T 		= data['T']
	r	 	= data['r']
	L	 	= data['L']
	Ls	 	= data['Ls']
	s0 		= data['s0']

	CCR		= r*(1 + r)**L/((1 + r)**L - 1)
	T		= int(T)
	Xt0		= int(Xt0)
	steps	= 200/Xt0

	WindMode	= True
	WaveMode	= False
	if argv[1] == 'W':
		write_flag = True
		linux_flag = False
	elif argv[1] == 'L':
		write_flag = False
		linux_flag = True
	else:
		write_flag = False
		linux_flag = False
	
	wind = wind_generator()
	
	wave = wave_generator()
	
	w = list()	
	for i in range(0, T):
		w.append(WindMode*wind[i] + WaveMode*wave[i])
	
	CF_up_1	= CF_natural_up(w, Xt0)
	CF_up_2	= CF_OCAES_up(w, Xt0, etaC, etaE)
	print T
	for i in range(1, steps):
		print '%3i%3i%4i\n' % (i, CF_up_1[str(i)], CF_up_2[str(i)])
	
	if write_flag is True:
		from csv import writer
		from math import exp
		LC	= dict()
		TSE	= dict()
		for n0 in range(1, steps):
			CF = CF_up_1[str(n0)]/100.0
			C0 = 16.59*(1.971E6 + 0.209E6*exp(1.66*n0*Xt0*1E6/1E8))*1.6*0.15 +\
				 16.59*2400*1600*0.15 +\
				 0.03327*(n0*Xt0)**0.7513*1E6*1.35
			AnnualCapital		= CCR*(C0 + C1 + C2)
			AnnualFixed			= F1 + F2
			# AnnualVariable		= 8760.0/T*(V1*sum(wind[0: T]) + V2*sum(wave[0: T]))
			AnnualVariable		= 0
			AnnualProduced		= 8760.0/T*CF*n0*Xt0*T
			TSE[str(n0)]	= AnnualProduced
			LC[str(n0)]		= (AnnualCapital + AnnualFixed + AnnualVariable)/AnnualProduced
		
		csvname = 'preprocess_' + str(T) + '_' + str(steps) + 'x' + str(Xt0) + 'MW.csv'
		with open(csvname, 'wb') as f:
			csv_writer = writer(f)
			# csv_writer.writerow(['n0', 'CF', 'CF_withOCAES', 'LC', 'TSE'])
			for i in range(1, steps):
				csv_writer.writerow([i, CF_up_1[str(i)]/100.0, CF_up_2[str(i)]/100.0, LC[str(i)], TSE[str(i)]])
		print 'File written successfully: preprocessing .csv log!'
	
	if linux_flag is True:
		to_be_written = list()
		SCF_interval	= CF_interval_OCAES(CF_up_1, CF_up_2)
		for i in SCF_interval:
			for j in range(0, len(SCF_interval[i])):
				to_be_written.append([int(i), int(100*SCF_interval[i][j])])
		sh = 'node2runs.sh'
		with open(sh, 'wb') as f:
			f.write('#!/bin/bash\n\n')
			for i in range(0, len(to_be_written)):
				line = 'coopr_python OCAESv5.py ' + str(to_be_written[i][0]) + ' ' + str(to_be_written[i][1]) + ' &\n'
				f.write(line)
				if (i + 1)%8 == 0:
					f.write('wait\n\n')
		print 'File written successfully: linux script!'
	# II()