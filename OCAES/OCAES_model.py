# imports
from pyomo.environ import *

from OCAES import OCAES_rules as rules
from CoolProp.CoolProp import PropsSI
import os
import pandas as pd

def create_model():
    # ================================
    # import data
    # ================================
    work_dir = os.getcwd()
    os.chdir("../data")

    # power generated by one 5.5 MW wind turbine
    E_WT = pd.read_csv("wind_power_5MW.csv")

    if E_WT.isnull().values.any():
        print "Remove null values from wind_power_5MW.csv"
        exit()

    # grid price of electricity
    grid_price = pd.read_csv("COE.csv")

    if grid_price.isnull().values.any():
        print "Remove null values from COE.csv"
        exit()

    # grid price of electricity
    generation = pd.read_csv("generation.csv")

    if generation.isnull().values.any():
        print "Remove null values from generation.csv"
        exit()

    # grid emissions
    # grid_emi = pd.read_csv("emissions.csv")

    # other data
    # data = pd.read_csv("data.csv")

    os.chdir(work_dir)

    # ================================
    # process data
    # ================================

    # financing
    R = 0.05  # discount rate (%)
    L = 25  # lifetime (years)

    # Wind farm
    # X_WIND = 600  # capacity (MW)
    C_WIND = 4444.0 * 1000.0  # capital cost ($/kW) to ($/MW)
    F_WIND = 129.0 * 1000.0  # fixed O&M cost ($/kW-y) to ($/MW-y)
    V_WIND = 0.0  # variable O&M cost ($/kWh) to ($/MWh)

    # OCAES costs
    C_WELL = 15.0 * 1E6  # capital cost (million pounds) to ($)
    C_MACHINE = 953000.0  # capital cost to ($/MW) # TODO add intercept, 953000 MW + 57400
    F_OCAES = 11 * 1000.0  # fixed O&M cost ($/kW-y) to ($/MW-y)
    V_OCAES = 3.0  # variable O&M cost ($/MWh)

    # OCAES performance
    M_DOT_WELL = 15.0*3600.0  # maximum well flow rate (kg/s) to (kg/h)
    M_WELL = 158.0E6  # maximum well storage (kg)
    M_RES0 = 0.0  # initial reservoir storage level (kg)
    eta_CMP = 0.9  # compressor efficiency (fraction)
    eta_EXP = 0.9  # expander efficiency (fraction)

    # pressure/temperature conditions
    T_amb = 25.0 + 273.15  # ambient temperature (deg C to K)
    P_amb = 101325.0  # ambient pressure (Pa)
    P_res = 250.0 * 1E5  # reservoir pressure (bar to Pa)

    # time steps
    delta_t = 1  # (1 hour)
    T = 8760  # number of hours # TODO Update to 8760

    # ================================
    # Pre-calculations
    # ================================
    # capital charging rate
    CCR = R * (1 + R) ** L / ((1 + R) ** L - 1)  # TODO Need to verify usage

    # Scale power production from a single 5 MW turbine to the capacity of the wind farm
    # E_WIND = E_WT.power.values * X_WIND / 5.0

    # Move time series data to dictionaries to be compatible with pyomo indexed format
    # E_WIND_dict = {i: E_WIND[i - 1] for i in range(1, T + 1)}
    grid_price_dict = {i:  grid_price.system_energy_price_rt[i - 1] for i in
                       range(1, T + 1)}

    E_WT_dict = {i: E_WT.power[i - 1] for i in range(1, T + 1)}
    E_GRID_dict = {i: generation.mw[i - 1] for i in range(1, T + 1)}
    # ------------
    # Thermodynamics TODO
    # ------------
    # Enthalpy change during expansion/compression
    H_amb = PropsSI('H', 'T', T_amb, 'P', P_amb, 'Air')  # J/kg
    H_res = PropsSI('H', 'T', T_amb, 'P', P_res, 'Air')  # J/kg
    delta_H = (H_amb - H_res) * 2.78E-10  # convert from J/kg to MWh/kg
    print("delta_H : " + str(delta_H) )

    # Mouli-Castillo methodology
    s = 3 # number of stages (Qin & Loth 2014)
    k = 1.4 # dimensionless gas constant
    R_const = 8.314 # kJ/kmol-K
    R_air = R_const / 28.97 # kJ/kg-K
    W_CMP = s*k*R_air*T_amb/(k-1) * ((P_res/P_amb)**((k-1)/(eta_CMP*s*k))-1.0)*2.78e-7 # Specific work (MWh/kg)
    W_EXP = s*k*R_air*T_amb/(k-1) * ((P_res/P_amb)**(eta_EXP*(k-1)/(s*k))-1.0)*2.78e-7 # Specific work (MWh/kg)
    print("W_CMP []" + str(W_CMP))
    print("W_EXP []" + str(W_EXP))

    # ================================
    # Create Pyomo model
    # ================================
    model = AbstractModel()
    # ----------------
    # Sets (fixed)
    # ----------------
    model.t = Set(initialize=range(1, T + 1))

    # ----------------
    # Parameters (fixed inputs)
    # ----------------
    # model.E_WIND = Param(model.t, initialize=E_WIND_dict)  # Wind power generated by farm
    # model.P = Param(model.t, initialize=grid_price_dict)  # grid price of electricity
    model.E_GRID = Param(model.t, initialize=E_GRID_dict)  # electricity demand
    model.E_WT = Param(model.t, initialize=E_WT_dict)  # electricity production from a single wind turbine
    model.delta_t = Param(initialize=delta_t)
    model.delta_H = Param(initialize=delta_H)
    model.M_WELL = Param(initialize=M_WELL)
    model.M_DOT_WELL = Param(initialize=M_DOT_WELL)
    # model.M_RES0 = Param(initialize=M_RES0)
    model.eta_CMP = Param(initialize=eta_CMP)
    model.eta_EXP = Param(initialize=eta_EXP)

    model.W_CMP = Param(initialize=W_CMP)
    model.W_EXP = Param(initialize=W_EXP)

    X_WT = 5.0 # Capacity of a single wind turbine
    model.X_WT = Param(initialize=X_WT)

    model.C_WIND = Param(initialize=C_WIND)
    model.F_WIND = Param(initialize=F_WIND)
    model.V_WIND = Param(initialize=V_WIND)
    model.C_WELL = Param(initialize=C_WELL, mutable = True)
    model.C_MACHINE = Param(initialize=C_MACHINE, mutable = True)
    model.F_OCAES = Param(initialize=F_OCAES)
    model.V_OCAES = Param(initialize=V_OCAES)
    model.CCR = Param(initialize=CCR)
    # GRID_RAMP_RATE = 300
    # model.GRID_RAMP_RATE = Param(initialize=GRID_RAMP_RATE, mutable = True)
    # PRICE_MULTIPLIER = 1.0
    # model.PRICE_MULTIPLIER = Param(initialize=PRICE_MULTIPLIER, mutable = True)


    # ----------------
    # Variables (upper case)
    # ----------------
    # Decision variables - OCAES system
    model.N_WELLS = Var(within=NonNegativeIntegers, initialize=1)  # Number of wells (>0, integer)
    model.X_OCAES = Var(within=NonNegativeReals, initialize=1.0)  # The machinery rating (>0, MW)
    model.N_WIND = Var(within=NonNegativeIntegers, initialize=125) # Number of wind turbines (>0, integer)
    # Result of decision variable
    model.X_WIND = Var(within=NonNegativeReals, initialize=600)  # Wind capacity (>0, MW)

    # Energy flows
    model.E_CMP = Var(model.t, within=NonNegativeReals, initialize=0.0)  # OCAES compressor (>0, MWh)
    model.E_EXP = Var(model.t, within=NonNegativeReals, initialize=0.0)  # OCAES expander (>0, MWh)
    model.E_CURTAIL = Var(model.t, within=NonNegativeReals, initialize=0.0)  # Curtailed energy (>0, MWh)
    model.E_WIND = Var(model.t, within=NonNegativeReals, initialize=0.0)  # Wind energy generated (>0, MWh)

    # Air stored
    model.M_RES0 = Var(within=NonNegativeReals, initialize=M_RES0) # initial energy stored, needs to overcome initial period without wind energy
    model.M_RES = Var(model.t, within=NonNegativeReals, initialize=0.0)  # within reservoir (>0, kg)
    model.M_CMP = Var(model.t, within=NonNegativeReals, initialize=0.0)  # from compressor (>0, kg)
    model.M_EXP = Var(model.t, within=NonNegativeReals, initialize=0.0)  # to expander (>0, kg)

    # Economics
    # model.REVENUE = Var(within=Reals, initialize=0.0)  # within reservoir (>0, $)
    model.COSTS = Var(within=Reals, initialize=0.0)  # from compressor (>0, $)
    # model.PROFIT = Var(within=Reals, initialize=0.0)  # to expander (>0, $)

    # ----------------
    # Constraints (lower case)
    # ----------------
    # Wind farm
    # model.capacity_trans = Constraint(model.t, rule=rules.capacity_trans)  # Transmission line capacity
    model.energy_wind = Constraint(model.t, rule=rules.energy_wind)  # Compressor capacity limit
    model.capacity_wind = Constraint(model.t, rule=rules.capacity_wind)  # Compressor capacity limit

    # Machinery
    model.capacity_cmp = Constraint(model.t, rule=rules.capacity_cmp)  # Compressor capacity limit
    model.capacity_exp = Constraint(model.t, rule=rules.capacity_exp)  # Expander capacity limit
    model.work_cmp = Constraint(model.t, rule=rules.work_cmp)  # Compressor work (per time step)
    model.work_exp = Constraint(model.t, rule=rules.work_exp)  # Expander work (per time step)
    # model.grid_ramp_rate_limit1 = Constraint(model.t, rule=rules.grid_ramp_rate_limit1)  # Expander capacity limit
    # model.grid_ramp_rate_limit2 = Constraint(model.t, rule=rules.grid_ramp_rate_limit2)  # Expander capacity limit

    # Reservoir
    model.initial_storage = Constraint(rule=rules.initial_storage)  # Initial mass stored
    model.reservoir_rate_limit_in = Constraint(model.t, rule=rules.reservoir_rate_limit_in)  # Reservoir mass limit
    model.reservoir_rate_limit_out = Constraint(model.t, rule=rules.reservoir_rate_limit_out)  # Reservoir mass limit
    model.reservoir_capacity_limit = Constraint(model.t, rule=rules.reservoir_capacity_limit)  # Reservoir mass limit

    # Energy and mass balances
    model.energy_balance = Constraint(model.t, rule=rules.energy_balance)  # Hourly energy balance
    model.mass_balance = Constraint(model.t, rule=rules.mass_balance)  # Hourly mass balance

    # Economics
    # model.revenue = Constraint(rule=rules.revenue)  # Total revenue
    model.costs = Constraint(rule=rules.costs)  # Total costs
    # model.profit = Constraint(rule=rules.profit)  # Profit

    # ----------------
    # Objective
    # ----------------
    model.LCOE = Objective(sense=minimize, rule=rules.objective)

    return model