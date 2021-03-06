import pandas as pd
from pyomo.environ import *
import matplotlib.pyplot as plt
import seaborn as sns
from OCAES import OCAES_rules as rules


class ocaes:
    def get_default_inputs(storage_type='OCAES'):
        attributes = ['debug', 'delta_t',
                      'X_wind', 'X_well', 'X_cmp', 'X_exp',
                      'pwr2energy', 'eta_storage',
                      'C_wind', 'C_well', 'C_cmp', 'C_exp',
                      'V_wind', 'V_cmp', 'V_exp',
                      'F_wind', 'F_well', 'F_cmp', 'F_exp',
                      'wt_cutin', 'wt_rated', 'wt_cutout',
                      'wt_A', 'wt_B', 'wt_C', 'wt_D']
        inputs = pd.Series(index=attributes)

        inputs['debug'] = False  # debug
        inputs['delta_t'] = 1  # [hr]
        inputs['objective'] = 'REVENUE'  # objective function
        # options are COVE, REVENUE, REVENUE_ARBITRAGE, PROFIT,
        # CD_FIX_DISP, CD_FIX_WIND_STOR, or CD_FIX_DISP_STOR

        # Constant dispatch (CD) - power output is held constant for entire time series
        # CD_FIX_DISP - dispatch is fixed, wind and storage capacities optimized (variable)
        # CD_FIX_DISP_WIND_STOR - dispatch, wind and stoarge capacities are fixed
        # CD_FIX_DISP_STOR - dispatch and storage fixed, wind is optimzied (variable)
        # CD_FIX_WIND_STOR - wind and stoarge are fixed, dispatch is optimized (variable)

        # Power capacity [MW]
        inputs['X_wind'] = 500.0  # wind farm
        inputs['X_well'] = 500.0  # well
        inputs['X_cmp'] = 500.0  # compressor
        inputs['X_exp'] = 500.0  # expander
        inputs['X_dispatch'] = 200.0  # constant dispatch (output to electric grid)

        # Storage performance
        inputs['pwr2energy'] = 10.0  # relation between power and energy (duration) [-]
        inputs['eta_storage'] = 0.75  # round trip efficiency [-]
        inputs['min_storage_fr'] = 0.0  # minimum storage level, fraction of max [-]

        # Capital costs [$/MW]
        inputs['C_wind'] = 4444.0 * 1000.0
        inputs['C_well'] = 144.986 * 1000.0
        inputs['C_cmp'] = 0.0
        inputs['C_exp'] = 930.438 * 1000.0

        # Variable costs [$/MWh]
        inputs['V_wind'] = 0.0
        inputs['V_cmp'] = 0.0
        inputs['V_exp'] = 4.62

        # Fixed costs [$/MW-y]
        inputs['F_wind'] = 129.0 * 1000.0
        inputs['F_well'] = 0.0
        inputs['F_cmp'] = 0.0
        inputs['F_exp'] = 0.0

        # Interest rate and inflation
        inputs['interest'] = 0.05  # interest rate [fr]
        inputs['inflation'] = 0.025  # inflation rate [fr]

        # Loan lifetime [y]
        inputs['L_wind'] = 25.0
        inputs['L_well'] = 25.0
        inputs['L_cmp'] = 25.0
        inputs['L_exp'] = 25.0

        # Capacity credits
        inputs['CC_value'] = 140  # $/MW-day
        inputs['CC_wind'] = 0.2  # [fr]
        inputs['CC_exp'] = 1.0  # [fr]

        # wind farm performance characteristics
        inputs['wt_cutin'] = 3.16  # Cut-in wind speed [m/s]
        inputs['wt_rated'] = 11.42  # Rated wind speed [m/s]
        inputs['wt_cutout'] = 25.0  # Cut-out wind speed [m/s]

        # wind farm power curve Ax^3 + Bx^2 + Cx + D, Based on NREL 5MW wind turbine
        # outputs should be 0 to 1 in range of wt_cutin to wt_rated
        inputs['wt_A'] = 0.0003659862  # A
        inputs['wt_B'] = 0.006094302  # B
        inputs['wt_C'] = -0.0337523  # C
        inputs['wt_D'] = 0.05317015  # D

        if storage_type == 'battery':
            # place all costs on expander
            inputs['C_exp'] = 5038.0 * 1000.0  # $/MW
            inputs['F_exp'] = 10.0 * 1000.0
            inputs['V_exp'] = 0.03 / 100.0 * 1000.0

            # remove all costs from compressor and well
            inputs['C_cmp'] = 0.0
            inputs['F_cmp'] = 0.0
            inputs['V_cmp'] = 0.0
            inputs['C_well'] = 0.0
            inputs['F_well'] = 0.0
            inputs['V_well'] = 0.0

            # battery lifetime
            inputs['L_well'] = 10.0
            inputs['L_exp'] = 10.0
            inputs['L_cmp'] = 10.0

            # Storage performance
            inputs['pwr2energy'] = 10.0  # relation between power and energy [-]
            inputs['eta_storage'] = 0.86  # round trip efficiency [-]

        if storage_type == 'wind_only':
            inputs['X_well'] = 0
            inputs['X_cmp'] = 0
            inputs['X_exp'] = 0

        return inputs

    def __init__(self, data, inputs=get_default_inputs()):
        # store data and inputs
        self.data = data
        self.inputs = inputs
        self.results = []

        # ================================
        # check for proper inputs
        # ================================
        if inputs['L_wind'] < 1.0:
            inputs['L_wind'] = 1.0
        if inputs['L_well'] < 1.0:
            inputs['L_well'] = 1.0
        if inputs['L_cmp'] < 1.0:
            inputs['L_cmp'] = 1.0
        if inputs['L_exp'] < 1.0:
            inputs['L_exp'] = 1.0

        # ================================
        # Calculate wind power generated (fraction of rated)
        # wind farm power curve Ax^3 + Bx^2 + Cx + D (min = 0.0, max = 1.0
        # ================================
        data.loc[:, 'P_wind_fr'] = 0.0
        data.P_wind_fr = inputs['wt_A'] * data.windspeed_ms ** 3 + inputs['wt_B'] * data.windspeed_ms ** 2 + inputs[
            'wt_C'] * data.windspeed_ms + inputs['wt_D']
        data.loc[data.windspeed_ms < inputs['wt_cutin'], 'P_wind_fr'] = 0.0  # Cut-in
        data.loc[data.windspeed_ms >= inputs['wt_rated'], 'P_wind_fr'] = 1.0  # Rated
        data.loc[data.windspeed_ms >= inputs['wt_cutout'], 'P_wind_fr'] = 0.0  # cut-out
        # data.loc[:, 'P_wind_fr'] = data.loc[:, 'P_wind_fr'] * inputs['X_wind']

        # COVE calculations
        data.loc[:, 'R'] = data.price_dollarsPerMWh / data.price_dollarsPerMWh.mean()  # normalized price

        # ================================
        # Process data
        # Move time series data to dictionaries to be compatible with pyomo indexed format
        # ================================
        T = len(data) + 1  # number of time steps
        P_wind_dict = {i: data.P_wind_fr[i - 1] for i in range(1, T)}  # wind power (fraction of capacity)
        price_dict = {i: data.price_dollarsPerMWh[i - 1] for i in range(1, T)}  # electricity price in $/MWh
        emissions_dict = {i: data.emissions_tonCO2PerMWh[i - 1] for i in range(1, T)}  # emissions [ton/MWh]

        # Constraints do not work if the RTE<=0
        if inputs['eta_storage'] <= 0.0:
            inputs['eta_storage'] = 0.01  # Replace with a very low efficiency

        # ================================
        # Create Pyomo model
        # ================================
        model = AbstractModel()
        # ----------------
        # Sets (fixed)
        # ----------------
        model.t = Set(initialize=range(1, T))

        # ----------------
        # Parameters (fixed inputs)
        # ----------------
        # calculated inputs based on data
        model.P_wind_fr = Param(model.t, initialize=P_wind_dict)  # Fraction of wind power generated by farm
        model.price_grid = Param(model.t,
                                 initialize=price_dict)  # Grid locational marginal price (LMP) of electricity by hour
        model.emissions_grid = Param(model.t, initialize=emissions_dict)  # Grid emissions by hour
        model.price_grid_average = Param(initialize=data.price_dollarsPerMWh.mean())

        # general
        model.delta_t = Param(initialize=inputs['delta_t'])  # time step [hr]
        model.T = Param(initialize=T)  # number of time steps

        # power capacity - wind [MW]
        if not (inputs['objective'] == 'CD_FIX_DISP' or inputs['objective'] == 'CD_FIX_DISP_STOR'):
            model.X_wind = Param(initialize=float(inputs['X_wind']))

        # power capacity -storage [MW]
        if not (inputs['objective'] == 'CD_FIX_DISP'):
            model.X_well = Param(initialize=float(inputs['X_well']))
            model.X_cmp = Param(initialize=float(inputs['X_cmp']))
            model.X_exp = Param(initialize=float(inputs['X_exp']))
            model.X_storage = Param(initialize=float(inputs['X_exp']))

        # power capacity - dispatch [MW]
        if not(inputs['objective'] == 'CD_FIX_WIND_STOR'):
            model.X_dispatch = Param(initialize=float(inputs['X_dispatch']))

        # storage performance
        model.E_well_duration = Param(initialize=float(inputs['pwr2energy']))
        model.E_well_min_fr = Param(initialize=float(inputs['min_storage_fr']))  # minimum energy storage fraction [MWh]
        model.E_well_max_fr = Param(initialize=1.0)  # maximum energy storage fraction [MWh]
        model.eta_storage_roundtrip = Param(initialize=inputs['eta_storage'])  # Storage round trip efficiency [-]
        model.eta_storage_single = Param(initialize=inputs['eta_storage'] ** 0.5)  # Storage single direction eff. [-]

        # capital costs [$/MW]
        model.C_wind = Param(initialize=float(inputs['C_wind']))
        model.C_well = Param(initialize=float(inputs['C_well']))
        model.C_cmp = Param(initialize=float(inputs['C_cmp']))
        model.C_exp = Param(initialize=float(inputs['C_exp']))

        # variable costs [$/MWh]
        model.V_wind = Param(initialize=inputs['V_wind'])
        model.V_cmp = Param(initialize=inputs['V_cmp'])
        model.V_exp = Param(initialize=inputs['V_exp'])

        # fixed costs [$/MW-y]
        model.F_wind = Param(initialize=inputs['F_wind'])
        model.F_well = Param(initialize=inputs['F_well'])
        model.F_cmp = Param(initialize=inputs['F_cmp'])
        model.F_exp = Param(initialize=inputs['F_exp'])

        # Real discount rate [fr]
        i = inputs['interest'] - inputs['inflation']
        model.i = Param(initialize=i)

        # Loan lifetime [y]
        model.L_wind = Param(initialize=inputs['L_wind'])
        model.L_well = Param(initialize=inputs['L_well'])
        model.L_cmp = Param(initialize=inputs['L_cmp'])
        model.L_exp = Param(initialize=inputs['L_exp'])

        # Capacity credits
        model.CC_value = Param(initialize=float(inputs['CC_value']))
        model.CC_wind = Param(initialize=float(inputs['CC_wind']))
        model.CC_exp = Param(initialize=float(inputs['CC_exp']))

        # Capital Recovery Factor, real [fr]
        model.CRF_wind = Param(initialize=float(i + (i / ((1 + i) ** inputs['L_wind'] - 1.0))))
        model.CRF_well = Param(initialize=float(i + (i / ((1 + i) ** inputs['L_well'] - 1.0))))
        model.CRF_cmp = Param(initialize=float(i + (i / ((1 + i) ** inputs['L_cmp'] - 1.0))))
        model.CRF_exp = Param(initialize=float(i + (i / ((1 + i) ** inputs['L_exp'] - 1.0))))

        # ----------------
        # Variables (upper case)
        # ----------------
        # power capacity - wind [MW]
        if inputs['objective'] == 'CD_FIX_DISP' or inputs['objective'] == 'CD_FIX_DISP_STOR':
            model.X_wind = Var(within=NonNegativeReals, initialize=float(inputs['X_wind']))

        # power capacity -storage [MW]
        if inputs['objective'] == 'CD_FIX_DISP':
            model.X_well = Var(within=NonNegativeReals, initialize=float(inputs['X_well']))
            model.X_cmp = Var(within=NonNegativeReals, initialize=float(inputs['X_cmp']))
            model.X_exp = Var(within=NonNegativeReals, initialize=float(inputs['X_exp']))
            model.X_storage = Var(within=NonNegativeReals, initialize=float(inputs['X_exp']))

        # power capacity - dispatch [MW]
        if inputs['objective'] == 'CD_FIX_WIND_STOR':
            model.X_dispatch = Var(within=NonNegativeReals, initialize=float(inputs['X_dispatch']))

        # Decision variables - energy flows
        model.P_wind = Var(model.t, within=NonNegativeReals, initialize=0.0)  # OCAES compressor power in (>0, MW)
        model.P_cmp = Var(model.t, within=NonNegativeReals, initialize=0.0)  # OCAES compressor power in (>0, MW)
        model.P_exp = Var(model.t, within=NonNegativeReals, initialize=0.0)  # OCAES expander power out (>0, MW)
        model.P_curtail = Var(model.t, within=NonNegativeReals, initialize=0.0)  # Curtailed power (>0, MW)
        model.P_grid_sell = Var(model.t, within=NonNegativeReals, initialize=0.0)  # Power sold to the grid (>0, MW)
        model.P_grid_buy = Var(model.t, within=NonNegativeReals, initialize=0.0)  # Power bought from the grid (>0, MW)

        # Energy stored
        model.E_well = Var(model.t, within=NonNegativeReals, initialize=0.0)  # OCAES compressor power in (>0, MW)
        model.E_well_init_fr = Var(within=NonNegativeReals, initialize=0.5,
                                   bounds=(0.0, 1.0))  # Initial energy storage fraction
        model.E_well_init = Var(within=NonNegativeReals, initialize=0.0)  # Initial energy storage (MWh)

        # Avoided emissions
        model.avoided_emissions = Var(within=Reals, initialize=0.0)  # within reservoir (>0, $)

        # electricity (delivered to the grid and generated)
        model.yearly_electricity = Var(within=Reals, initialize=0.0)  # scaled for one year
        model.yearly_electricity_generated = Var(within=Reals, initialize=0.0)  # scaled for one year
        model.yearly_electricity_purchased = Var(within=Reals, initialize=0.0)  # scaled for one year
        model.yearly_curtailment = Var(within=Reals, initialize=0.0)  # scaled for one year
        model.yearly_exp_usage = Var(within=Reals, initialize=0.0)  # scaled for one year
        model.yearly_cmp_usage = Var(within=Reals, initialize=0.0)  # scaled for one year

        # Economics
        model.electricity_revenue = Var(model.t, within=Reals, initialize=0.0)
        model.yearly_electricity_revenue = Var(within=Reals, initialize=0.0)
        model.yearly_capacity_credit = Var(within=Reals, initialize=0.0)
        model.yearly_total_revenue = Var(within=Reals, initialize=0.0)
        model.yearly_costs = Var(within=Reals, initialize=0.0)
        model.yearly_profit = Var(within=Reals, initialize=0.0)

        # COVE
        model.yearly_electricity_value = Var(within=Reals, initialize=0.0)

        # ----------------
        # Constraints (prefixed with cnst)
        # ----------------
        # wind power
        model.cnst_pwr_wind = Constraint(model.t, rule=rules.pwr_wind)

        # capacity
        if inputs['objective'] == 'CD_FIX_DISP':
            model.cnst_cap_well_var = Constraint(rule=rules.capacity_well_var)
            model.cnst_cap_cmp_var = Constraint(rule=rules.capacity_cmp_var)
            model.cnst_cap_exp_var = Constraint(rule=rules.capacity_exp_var)

        # capacity - power
        model.cnst_pwr_capacity_cmp = Constraint(model.t, rule=rules.pwr_capacity_cmp)
        model.cnst_pwr_capacity_exp = Constraint(model.t, rule=rules.pwr_capacity_exp)
        model.cnst_pwr_capacity_well_in = Constraint(model.t, rule=rules.pwr_capacity_well_in)
        model.cnst_pwr_capacity_well_out = Constraint(model.t, rule=rules.pwr_capacity_well_out)
        model.cnst_pwr_grid_sell = Constraint(model.t, rule=rules.pwr_grid_sell)
        model.cnst_pwr_grid_limit = Constraint(model.t, rule=rules.pwr_grid_limit)
        if inputs['objective'] == 'REVENUE_ARBITRAGE':
            model.cnst_pwr_grid_buy = Constraint(model.t, rule=rules.pwr_grid_buy_enabled)
        else:
            model.cnst_pwr_grid_buy = Constraint(model.t, rule=rules.pwr_grid_buy_disabled)

        # capacity - energy
        model.cnst_energy_capacity_well_min = Constraint(model.t, rule=rules.energy_capacity_well_min)
        model.cnst_energy_capacity_well_max = Constraint(model.t, rule=rules.energy_capacity_well_max)

        # power balance
        model.cnst_power_balance = Constraint(model.t, rule=rules.power_balance)

        # energy stored
        model.cnst_energy_stored_init = Constraint(rule=rules.energy_stored_init)
        model.cnst_energy_stored = Constraint(model.t, rule=rules.energy_stored)
        model.cnst_energy_stored_final = Constraint(rule=rules.energy_stored_final)

        # emissions
        model.cnst_emissions = Constraint(rule=rules.emissions)

        # electricity
        model.cnst_yearly_electricity = Constraint(rule=rules.yearly_electricity)
        model.cnst_yearly_electricity_generated = Constraint(rule=rules.yearly_electricity_generated)
        model.cnst_yearly_electricity_purchased = Constraint(rule=rules.yearly_electricity_purchased)
        model.cnst_yearly_curtailment = Constraint(rule=rules.yearly_curtailment)
        model.cnst_yearly_exp_usage = Constraint(rule=rules.yearly_exp_usage)
        model.cnst_yearly_cmp_usage = Constraint(rule=rules.yearly_cmp_usage)

        # economics
        model.cnst_electricity_revenue = Constraint(model.t, rule=rules.electricity_revenue)
        model.cnst_yearly_electricity_revenue = Constraint(rule=rules.yearly_electricity_revenue)
        if inputs['objective'] == 'CD_FIX_DISP' or inputs['objective'] == 'CD_FIX_WIND_STOR' or \
                inputs['objective'] == 'CD_FIX_DISP_STOR' or inputs['objective'] == 'CD_FIX_DISP_WIND_STOR':
            model.cnst_yearly_capacity_credit_simple = Constraint(rule=rules.yearly_capacity_credit_simple)
        else:
            model.cnst_yearly_capacity_credit = Constraint(rule=rules.yearly_capacity_credit)
        model.cnst_yearly_total_revenue = Constraint(rule=rules.yearly_total_revenue)
        model.cnst_yearly_costs = Constraint(rule=rules.yearly_costs)
        model.cnst_yearly_profit = Constraint(rule=rules.yearly_profit)

        # COVE
        model.cnst_yearly_electricity_value = Constraint(rule=rules.yearly_electricity_value)

        # Constant Dispatch
        if inputs['objective'] == 'CD_FIX_DISP' or inputs['objective'] == 'CD_FIX_WIND_STOR' or \
                inputs['objective'] == 'CD_FIX_DISP_STOR' or inputs['objective'] == 'CD_FIX_DISP_WIND_STOR':
            model.cnst_pwr_dispatch_const = Constraint(model.t, rule=rules.pwr_dispatch_const)

        # ----------------
        # Objective
        # ----------------
        if inputs['objective'] == 'COVE' or inputs['objective'] == 'CD_FIX_WIND_STOR':
            model.objective = Objective(sense=maximize, rule=rules.objective_COVE)
        elif inputs['objective'] == 'PROFIT':
            model.objective = Objective(sense=maximize, rule=rules.objective_PROFIT)
        elif inputs['objective'] == 'CD_FIX_DISP' or inputs['objective'] == 'CD_FIX_DISP_STOR' or \
                inputs['objective'] == 'CD_FIX_DISP_WIND_STOR':
            model.objective = Objective(sense=minimize, rule=rules.objective_COST)
        else:  # REVENUE, REVENUE_ARBITRAGE
            model.objective = Objective(sense=maximize, rule=rules.objective_revenue)

        # ----------------
        # Run
        # ----------------

        # create instance
        if inputs['debug']:
            instance = model.create_instance(report_timing=True)
        else:
            instance = model.create_instance(report_timing=False)
        instance.preprocess()

        # set solver
        if SolverFactory('gurobi').available():
            opt = SolverFactory("gurobi")
        elif SolverFactory('cplex').available():
            opt = SolverFactory("cplex")
        elif SolverFactory('glpk').available():
            opt = SolverFactory("glpk")
        elif SolverFactory('cbc').available():
            opt = SolverFactory("cbc")
        else:
            print('Warning could not find a suitable solver')

        # solve
        results = opt.solve(instance)
        print("Solver status               : " + str(results.solver.status))
        print("Solver termination condition: " + str(results.solver.termination_condition))

        # Store model, instance and results
        self.model = model
        self.instance = instance
        self.results = results

    def get_full_results(self):

        s = pd.Series(dtype='float64')
        df = pd.DataFrame()

        # Variable values
        for v in self.instance.component_objects(Var, active=True):
            value_dict = v.extract_values()
            if len(value_dict) == 1:  # single value
                s[v.name] = value_dict[None]
                # if single value, put in series
            else:
                df = pd.concat([df, pd.DataFrame.from_dict(value_dict, orient='index', columns=[v.name])], axis=1,
                               sort=False)

        # Parameter values
        for v in self.instance.component_objects(Param, active=True):
            value_dict = v.extract_values()
            if len(value_dict) == 1:  # single value
                s[v.name] = value_dict[None]
                # if single value, put in series
            else:
                df = pd.concat([df, pd.DataFrame.from_dict(value_dict, orient='index', columns=[v.name])],
                               axis=1, sort=False)
        return df, s

    def calculate_LCOE(self, s):
        return s['yearly_costs'] / s['yearly_electricity']

    def post_process(self, s):
        revenue = s['yearly_total_revenue'] / s['yearly_electricity'] * 1e-3  # $/kWh
        LCOE = s['yearly_costs'] / s['yearly_electricity'] * 1e-3  # $/kWh
        COVE = s['yearly_costs'] / s['yearly_electricity_value'] * 1e-3  # $/kWh
        avoided_emissions = s['avoided_emissions'] / s['yearly_electricity']  # ton/MWh
        ROI = s['yearly_total_revenue'] / s['yearly_costs']
        return revenue, LCOE, COVE, avoided_emissions, ROI

    def plot_overview(self, start=1, stop=168, dpi=300, savename='results_overview'):
        # get results
        df, s = self.get_full_results()

        # ----------------------
        # check and process inputs
        # ----------------------
        if start < 1:
            start = 1
        if stop > len(df):
            stop = len(df)
        savename = savename + '.png'

        n_plots = 4

        # Column width guidelines
        # https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
        # Single column: 90mm = 3.54 in
        # 1.5 column: 140 mm = 5.51 in
        # 2 column: 190 mm = 7.48 i
        width = 7.48  # inches
        height = 5.5  # inches

        # create subplots
        f, axes = plt.subplots(n_plots, 1, sharex='col')  # ,constrained_layout=True)

        # style
        sns.set_style("white", {"font.family": "serif", "font.serif": ["Times", "Palatino", "serif"]})
        sns.set_context("paper")
        sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
        colors = sns.color_palette("Paired")

        # x variable
        x_convert = 1.0
        x_label = 'Timestep [-]'

        for i, ax in enumerate(axes):
            if i == 0:
                y_vars = ['P_cmp', 'P_exp', 'P_curtail', 'P_grid_sell', 'P_grid_buy', 'P_wind']
                y_var_names = ['Compressor', 'Expander', 'Curtail', 'Grid - Sell', 'Grid - Buy', 'Wind']
                y_colors = [colors[0], colors[1], colors[2], colors[3], colors[4]]
                y_convert = 1.0
                y_label = 'Power [MW]'

            elif i == 1:
                y_vars = ['E_well']
                y_var_names = ['Energy stored']
                y_colors = [colors[0]]
                y_convert = 1.0
                y_label = 'Energy [MWh]'

            elif i == 2:  # if i == 2:
                y_vars = ['price_grid']
                y_var_names = ['Electricity price']
                y_colors = [colors[0]]
                y_convert = 1.0
                y_label = 'Price [$/MWh]'

            else:  # if i == 3:
                y_vars = ['electricity_revenue']
                y_var_names = ['Revenue']
                y_colors = [colors[0]]
                y_convert = 1.0
                y_label = 'Revenue [$]'

            for y_var, y_color, y_var_name in zip(y_vars, y_colors, y_var_names):
                data = df.loc[start:stop, y_var]
                x = data.index * x_convert
                y = data.values * y_convert
                ax.plot(x, y, color=y_color, label=y_var_name)

            # add legend
            ax.legend()

            # Despine and remove ticks
            sns.despine(ax=ax, )
            ax.tick_params(top=False, right=False)

            # Labels
            if i == n_plots - 1:
                ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)

        # Set size
        f = plt.gcf()
        f.set_size_inches(width, height)

        # save and close plot
        plt.savefig(savename, dpi=dpi)
        plt.close()

    def plot_power_energy(self, start=1, stop=168, dpi=300, savename='results_power_energy'):
        # get results
        df, s = self.get_full_results()

        # ----------------------
        # check and process inputs
        # ----------------------
        if start < 1:
            start = 1
        if stop > len(df):
            stop = len(df)
        savename = savename + '.png'

        # Column width guidelines
        # https://www.elsevier.com/authors/author-schemas/artwork-and-media-instructions/artwork-sizing
        # Single column: 90mm = 3.54 in
        # 1.5 column: 140 mm = 5.51 in
        # 2 column: 190 mm = 7.48 i
        width = 7.48  # inches
        height = 5.5  # inches

        # create subplots
        f, axes = plt.subplots(3, 2, sharex='all')
        a = axes.ravel()

        # style
        sns.set_style("white", {"font.family": "serif", "font.serif": ["Times", "Palatino", "serif"]})
        sns.set_context("paper")
        sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
        colors = sns.color_palette("Paired")

        # x variable
        x_convert = 1.0
        x_label = 'Timestep [-]'

        # y variables
        y_vars = ['P_wind', 'P_cmp', 'P_grid_sell', 'P_grid_buy', 'P_exp', 'P_curtail', 'E_well']
        y_colors = [colors[0], colors[1], colors[2], colors[3], colors[4], colors[5], colors[6]]
        y_converts = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        y_labels = ['Wind power [MW]', 'Compressor [MW]', 'Delivered to grid [MW]', 'Purchased from grid [MW]',
                    'Expander [MW]', 'Curtailment [MW]', 'Energy stored [MWh]']

        for i, (ax, y_var, y_color, y_convert, y_label) in enumerate(zip(a, y_vars, y_colors, y_converts, y_labels)):
            data = df.loc[start:stop, y_var]
            x = data.index * x_convert
            y = data.values * y_convert
            ax.plot(x, y, color=y_color)

            # Labels
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)

            # Despine and remove ticks
            sns.despine(ax=ax, )
            ax.tick_params(top=False, right=False)

        # Set size
        f = plt.gcf()
        f.set_size_inches(width, height)

        # save and close plot
        plt.savefig(savename, dpi=dpi)
        plt.close()
