from pyomo.environ import *
import matplotlib.pyplot as plt

import OCAES_rules as rules
from CoolProp.CoolProp import PropsSI
import os
import pandas as pd

def create_model():
    # ================================
    # import data
    # ================================
    work_dir = os.getcwd()
    os.chdir("data")

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
    X_WIND = 600  # capacity (MW)
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
    E_WIND = E_WT.power.values * X_WIND / 5.0

    # Move time series data to dictionaries to be compatible with pyomo indexed format
    E_WIND_dict = {i: E_WIND[i - 1] for i in range(1, T + 1)}
    grid_price_dict = {i:  grid_price.system_energy_price_rt[i - 1] for i in
                       range(1, T + 1)}
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
    W_CMP = s*k*R*T_amb/(k-1) * ((P_res/P_amb)**((k-1)/(eta_CMP*s*k))-1.0)*2.78e-7 # Specific work (MWh/kg)
    W_EXP = s*k*R*T_amb/(k-1) * ((P_res/P_amb)**(eta_EXP*(k-1)/(s*k))-1.0)*2.78e-7 # Specific work (MWh/kg)
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
    model.E_WIND = Param(model.t, initialize=E_WIND_dict)  # Wind power generated by farm
    model.P = Param(model.t, initialize=grid_price_dict)  # grid price of electricity
    model.delta_t = Param(initialize=delta_t)
    model.delta_H = Param(initialize=delta_H)
    model.M_WELL = Param(initialize=M_WELL)
    model.M_DOT_WELL = Param(initialize=M_DOT_WELL)
    model.M_RES0 = Param(initialize=M_RES0)
    model.eta_CMP = Param(initialize=eta_CMP)
    model.eta_EXP = Param(initialize=eta_EXP)

    model.W_CMP = Param(initialize=W_CMP)
    model.W_EXP = Param(initialize=W_EXP)

    model.X_WIND = Param(initialize=X_WIND)
    model.C_WIND = Param(initialize=C_WIND)
    model.F_WIND = Param(initialize=F_WIND)
    model.V_WIND = Param(initialize=V_WIND)
    model.C_WELL = Param(initialize=C_WELL, mutable = True)
    model.C_MACHINE = Param(initialize=C_MACHINE)
    model.F_OCAES = Param(initialize=F_OCAES)
    model.V_OCAES = Param(initialize=V_OCAES)
    model.CCR = Param(initialize=CCR)
    GRID_RAMP_RATE = 300
    model.GRID_RAMP_RATE = Param(initialize=GRID_RAMP_RATE, mutable = True)
    PRICE_MULTIPLIER = 1.0
    model.PRICE_MULTIPLIER = Param(initialize=PRICE_MULTIPLIER, mutable = True)


    # ----------------
    # Variables (upper case)
    # ----------------
    # Decision variables - OCAES system
    model.N_WELLS = Var(within=NonNegativeIntegers, initialize=1)  # Number of wells (>0, integer)
    model.X_OCAES = Var(within=NonNegativeReals, initialize=1.0)  # The machinery rating (>0, MW)

    # Energy flows
    model.E_CMP = Var(model.t, within=NonNegativeReals, initialize=0.0)  # OCAES compressor (>0, MWh)
    model.E_EXP = Var(model.t, within=NonNegativeReals, initialize=0.0)  # OCAES expander (>0, MWh)
    model.E_CURTAIL = Var(model.t, within=NonNegativeReals, initialize=0.0)  # Curtailed energy (>0, MWh)
    model.E_GRID = Var(model.t, within=NonNegativeReals, initialize=0.0)  # Grid delivered (>0, MWh)

    # Air stored
    model.M_RES = Var(model.t, within=NonNegativeReals, initialize=0.0)  # within reservoir (>0, kg)
    model.M_CMP = Var(model.t, within=NonNegativeReals, initialize=0.0)  # from compressor (>0, kg)
    model.M_EXP = Var(model.t, within=NonNegativeReals, initialize=0.0)  # to expander (>0, kg)

    # Economics
    model.REVENUE = Var(within=Reals, initialize=0.0)  # within reservoir (>0, $)
    model.COSTS = Var(within=Reals, initialize=0.0)  # from compressor (>0, $)
    model.PROFIT = Var(within=Reals, initialize=0.0)  # to expander (>0, $)

    # ----------------
    # Constraints (lower case)
    # ----------------
    model.energy_balance = Constraint(model.t, rule=rules.energy_balance)  # Hourly energy balance
    model.capacity_trans = Constraint(model.t, rule=rules.capacity_trans)  # Transmission line capacity
    model.capacity_cmp = Constraint(model.t, rule=rules.capacity_cmp)  # Compressor capacity limit
    model.capacity_exp = Constraint(model.t, rule=rules.capacity_exp)  # Expander capacity limit
    model.grid_ramp_rate_limit1 = Constraint(model.t, rule=rules.grid_ramp_rate_limit1)  # Expander capacity limit
    model.grid_ramp_rate_limit2 = Constraint(model.t, rule=rules.grid_ramp_rate_limit2)  # Expander capacity limit

    model.mass_balance = Constraint(model.t, rule=rules.mass_balance)  # Hourly mass balance
    model.reservoir_rate_limit = Constraint(model.t, rule=rules.reservoir_rate_limit)  # Reservoir mass limit
    model.reservoir_capacity_limit = Constraint(model.t, rule=rules.reservoir_capacity_limit)  # Reservoir mass limit

    model.work_cmp = Constraint(model.t, rule=rules.work_cmp)  # Compressor work (per time step)
    model.work_exp = Constraint(model.t, rule=rules.work_exp)  # Expander work (per time step)

    model.revenue = Constraint(rule=rules.revenue)  # Total revenue
    model.costs = Constraint(rule=rules.costs)  # Total costs
    model.profit = Constraint(rule=rules.profit)  # Profit

    # ----------------
    # Objective
    # ----------------
    model.OBJ = Objective(sense=maximize, rule=rules.objective)

    return model

    # ----------------
    # Create model and solve
    # ----------------
    instance = model.create_instance(report_timing=True)


    instance.preprocess()
    opt = SolverFactory("cplex")
    results = opt.solve(instance)

    print results.solver.status
    print results.solver.termination_condition

    # Print results
    print("PROFIT [M$] : " + str(value(instance.PROFIT) / 1E6))
    print("N_WELLS [-] : " + str(value(instance.N_WELLS)))
    print("X_OCAES [MW]: " + str(value(instance.X_OCAES)))  # TODO Add constraint for max E_GRID to be wind turbine capacity
    # TODO add rate of change constraint to E_GRID

    # return model

    N = 200  # TODO update to 8760

    df = pd.DataFrame(columns=['E_WIND', 'E_CURTAIL', 'E_GRID', 'E_CMP', 'E_EXP'], index=range(N))

    for i in range(N):
        df.loc[i, "E_WIND"] = value(instance.E_WIND[i + 1])
        df.loc[i, "E_CURTAIL"] = value(instance.E_CURTAIL[i + 1])
        df.loc[i, "E_GRID"] = value(instance.E_GRID[i + 1])
        df.loc[i, "E_CMP"] = value(instance.E_CMP[i + 1])
        df.loc[i, "E_EXP"] = value(instance.E_EXP[i + 1])

    df.plot()
    df.to_csv("output.csv")
    plt.savefig('Energy_balance.png')
