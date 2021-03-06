from OCAES import ocaes, monteCarloInputs
import pandas as pd
import numpy as np
from joblib import Parallel, delayed, parallel_backend
import time
import os
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt


# =====================
# function to enable parameter sweep
# =====================
def parameter_sweep(sweep_input):
    # Record time to solve
    t0 = time.time()

    # create model
    data = pd.read_csv(sweep_input['timeseries_filename'])
    model_inputs = ocaes.get_default_inputs()

    model_inputs['objective'] = sweep_input['objective']

    # scenario specific inputs
    model_inputs['pwr2energy'] = sweep_input['pwr2energy']
    model_inputs['eta_storage'] = sweep_input['eta_storage']
    model_inputs['CC_exp'] = sweep_input['CC_exp']
    model_inputs['C_well'] = 0.0
    model_inputs['C_cmp'] = 0.0
    model_inputs['C_exp'] = sweep_input['C_exp']
    model_inputs['V_cmp'] = 0.0
    model_inputs['V_exp'] = sweep_input['V_exp']
    model_inputs['F_well'] = 0.0
    model_inputs['F_cmp'] = 0.0
    model_inputs['F_exp'] = sweep_input['F_exp']
    model_inputs['L_well'] = sweep_input['L_well']
    model_inputs['L_cmp'] = sweep_input['L_cmp']
    model_inputs['L_exp'] = sweep_input['L_exp']

    # capacity inputs
    if sweep_input['scenario'] == 'wind_only':
        model_inputs['X_well'] = 0.0
        model_inputs['X_cmp'] = 0.0
        model_inputs['X_exp'] = 0.0
        model_inputs['eta_storage'] = 1.0
    else:
        model_inputs['X_well'] = sweep_input['capacity']
        model_inputs['X_cmp'] = sweep_input['capacity']
        model_inputs['X_exp'] = sweep_input['capacity']

    if model_inputs['objective'] == 'CONST_DISPATCH_OPT':
        model_inputs['X_dispatch'] = sweep_input['capacity']

    print('Scenario: ' + str(sweep_input['scenario']))
    print('X_wind:   ' + str(model_inputs['X_wind']))
    print('Capacity: ' + str(sweep_input['capacity']))
    print('Objective: ' + str(sweep_input['objective']))

    # run model
    model = ocaes(data, model_inputs)
    df, s = model.get_full_results()
    revenue, LCOE, COVE, avoided_emissions, ROI = model.post_process(s)

    # save results
    results = pd.Series(index=('revenue', 'LCOE', 'COVE', 'avoided_emissions', 'solve_time'), dtype='float64')
    results['revenue'] = revenue
    results['LCOE'] = LCOE
    results['COVE'] = COVE
    results['avoided_emissions'] = avoided_emissions
    results['ROI'] = ROI
    results['solve_time'] = time.time() - t0
    # additional outputs
    results['avoided_emissions_tonnes'] = s['avoided_emissions']
    results['yearly_electricity_MWh'] = s['yearly_electricity']
    results['yearly_electricity_generated_MWh'] = s['yearly_electricity_generated']
    results['yearly_electricity_purchased_MWh'] = s['yearly_electricity_purchased']
    results['yearly_exp_usage_MWh'] = s['yearly_exp_usage']
    results['yearly_cmp_usage_MWh'] = s['yearly_cmp_usage']
    results['yearly_curtailment_MWh'] = s['yearly_curtailment']
    results['yearly_curtailment_fr'] = s['yearly_curtailment'] / s['yearly_electricity_generated']
    results['yearly_electricity_revenue_dollars'] = s['yearly_electricity_revenue']
    results['yearly_capacity_credit_dollars'] = s['yearly_capacity_credit']
    results['yearly_total_revenue_dollars'] = s['yearly_total_revenue']
    results['yearly_costs_dollars'] = s['yearly_costs']
    results['yearly_profit_dollars'] = s['yearly_profit']
    results['yearly_electricity_value_dollars'] = s['yearly_electricity_value']
    results['price_grid_average_dollarsPerMWh'] = s['price_grid_average']

    results['X_wind'] = s['X_wind']
    results['X_well'] = s['X_well']
    results['X_exp'] = s['X_exp']
    results['X_cmp'] = s['X_cmp']
    results['X_dispatch'] = s['X_dispatch']
    results['storage_duration_hrs'] = s['E_well_duration']
    results['E_well_init_fr'] = s['E_well_init_fr']
    results['E_well_init'] = s['E_well_init']

    # combine inputs and results to return in single series
    single_output = pd.concat([sweep_input, results])
    return single_output


# =====================
# main program
# =====================
if __name__ == '__main__':
    start = time.time()
    # ==============
    # user inputs
    # ==============
    scenarios_filename = 'scenarios.xlsx'  # Excel file with scenario inputs
    costs_filename = 'cost_study_results.csv'  # CSV file with scenario inputs
    sizing_filename = 'sizing_study_results.csv'  # CSV file with sizing study results
    scenarios = ['wind_only', '4_hr_batt', '10_hr_batt',
                 '10_hr_ocaes', '24_hr_ocaes', '168_hr_ocaes']  # Excel sheet_names
    iterations = [1, 1, 1,
                  1, 1, 1, 1, 1]  # number of runs per scenario per capacity (same order as scenarios)
    ncpus = 6  # int(os.getenv('NUM_PROCS'))  # number of cpus to use
    timeseries_filenames = ['da_timeseries_inputs_2019.csv']  # list of csv files
    capacities = np.arange(10.0, 501, 10)
    objectives = ['COVE', 'CD_FIX_WIND_STOR']

    # ------------------
    # create sweep_inputs dataframe
    # ------------------
    sweep_inputs = pd.DataFrame()
    for objective in objectives:
        for timeseries_filename in timeseries_filenames:
            for scenario, n_iterations in zip(scenarios, iterations):
                if not (scenario == 'wind_only' and objective == 'CD_FIX_WIND_STOR'):
                    df_scenario = monteCarloInputs(scenarios_filename, scenario, n_iterations)
                    df_scenario.loc[:, 'scenario'] = scenario
                    df_scenario.loc[:, 'timeseries_filename'] = timeseries_filename
                    df_scenario.loc[:, 'objective'] = objective
                    for capacity in capacities:
                        df_scenario.loc[:, 'capacity'] = capacity
                        sweep_inputs = sweep_inputs.append(df_scenario)

    # reset index (appending messes up indices)
    sweep_inputs = sweep_inputs.reset_index()

    # ------------------
    # import costs and sizing study results
    # ------------------
    costs = pd.read_csv(costs_filename)
    sizing = pd.read_csv(sizing_filename)

    # remove bad entries from sizing
    sizing = sizing[sizing.errors == False]

    # only use expected permeability results
    sizing = sizing[sizing.loc[:, 'k_type'] == 'expected']

    # Overwrite OCAES CAPEX with inputs
    for sheetname, duration_hr in zip(['10_hr_ocaes', '24_hr_ocaes', '48_hr_ocaes', '72_hr_ocaes', '168_hr_ocaes'],
                                      [10, 24, 48, 72, 168]):
        ind = sweep_inputs.sheetname == sheetname
        # costs
        sweep_inputs.loc[ind, 'C_exp'] = np.interp(sweep_inputs.loc[ind, 'capacity'], costs.capacity_MW,
                                                   costs.CAPEX_dollars_per_kW) * 1000.0

        ind2 = sizing.duration_hr == duration_hr
        # efficiency
        sweep_inputs.loc[ind, 'eta_storage'] = np.interp(sweep_inputs.loc[ind, 'capacity'],
                                                         sizing.loc[ind2, 'capacity_MW'],
                                                         sizing.loc[ind2, 'RTE'], right=-1)

    # Remove any entries with bad values (RTE = -1)
    sweep_inputs = sweep_inputs[sweep_inputs.loc[:, 'eta_storage'] != -1]

    # reset index (appending messes up indices)
    sweep_inputs = sweep_inputs.reset_index()

    # plot overview of inputs for a visual check
    sns.scatterplot(x='capacity', y='C_exp', hue='sheetname', style='sheetname', data=sweep_inputs)
    plt.savefig('sweep_inputs_C_exp.png')
    plt.close()
    sns.scatterplot(x='capacity', y='eta_storage', hue='sheetname', style='sheetname', data=sweep_inputs)
    plt.savefig('sweep_inputs_eta_storage.png')
    plt.close()
    sns.scatterplot(x='capacity', y='V_exp', hue='sheetname', style='sheetname', data=sweep_inputs)
    plt.savefig('sweep_inputs_V_exp.png')
    plt.close()
    sns.scatterplot(x='capacity', y='F_exp', hue='sheetname', style='sheetname', data=sweep_inputs)
    plt.savefig('sweep_inputs_F_exp.png')
    plt.close()
    sns.scatterplot(x='capacity', y='pwr2energy', hue='sheetname', style='sheetname', data=sweep_inputs)
    plt.savefig('sweep_inputs_pwr2energy.png')
    plt.close()

    # count number of cases
    n_cases = sweep_inputs.shape[0]

    # save inputs
    sweep_inputs.to_csv('sweep_inputs.csv')

    try:
        ncpus = int(os.getenv('NUM_PROCS'))  # try to use variable defined in sbatch script
    except:
        ncpus = ncpus  # otherwise default to this number of cores

    # run each case using parallelization
    with parallel_backend('multiprocessing', n_jobs=ncpus):
        output = Parallel(n_jobs=ncpus, verbose=5)(
            delayed(parameter_sweep)(sweep_inputs.loc[index])
            for index in
            range(n_cases))
    df = pd.DataFrame(output)

    # save results
    df.to_csv('sweep_results.csv')

    # save total study time
    end = time.time()
    run_time = (end - start) / 3600.0
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    f = open("history_runtime.txt", "a")
    f.write('\n')
    f.write('Last run : ' + dt_string + '\n')
    f.write('Total run time [h]: ' + str(round(run_time, 3)) + '\n')
    f.write('\n')
    f.close()
