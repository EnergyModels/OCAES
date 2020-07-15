from OCAES import ocaes, monteCarloInputs
import pandas as pd
import numpy as np
from joblib import Parallel, delayed, parallel_backend
import time
import os
from datetime import datetime


# =====================
# function to enable parameter sweep
# =====================
def parameter_sweep(sweep_input):
    # Record time to solve
    t0 = time.time()

    # create model
    data = pd.read_csv(sweep_input['timeseries_filename'])
    model_inputs = ocaes.get_default_inputs()

    # capacity inputs
    if sweep_input['scenario'] == 'wind_only':
        model_inputs['X_well'] = 0.0
        model_inputs['X_cmp'] = 0.0
        model_inputs['X_exp'] = 0.0
    else:
        model_inputs['X_well'] = sweep_input['capacity']
        model_inputs['X_cmp'] = sweep_input['capacity']
        model_inputs['X_exp'] = sweep_input['capacity']

    # scenario specific inputs
    model_inputs['pwr2energy'] = sweep_input['pwr2energy']
    model_inputs['eta_storage'] = sweep_input['eta_storage']
    model_inputs['C_well'] = sweep_input['C_well']
    model_inputs['C_cmp'] = sweep_input['C_cmp']
    model_inputs['C_exp'] = sweep_input['C_exp']
    model_inputs['V_cmp'] = sweep_input['V_cmp']
    model_inputs['V_exp'] = sweep_input['V_exp']
    model_inputs['F_well'] = sweep_input['F_well']
    model_inputs['F_cmp'] = sweep_input['F_cmp']
    model_inputs['F_exp'] = sweep_input['F_exp']
    model_inputs['L_well'] = sweep_input['L_well']
    model_inputs['L_cmp'] = sweep_input['L_cmp']
    model_inputs['L_exp'] = sweep_input['L_exp']

    # run model
    model = ocaes(data, model_inputs)
    df, s = model.get_full_results()
    revenue, LCOE, COVE, avoided_emissions = model.post_process(s)

    # save results
    results = pd.Series(index=('revenue', 'LCOE', 'COVE', 'avoided_emissions', 'solve_time'))
    results['revenue'] = revenue
    results['LCOE'] = LCOE
    results['COVE'] = COVE
    results['avoided_emissions'] = avoided_emissions
    results['solve_time'] = time.time() - start

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
    scenarios = ['wind_only', '4_hr_batt', '10_hr_batt', '10_hr_ocaes', '24_hr_ocaes']  # Excel sheet_names
    iterations = [1, 1, 1, 1, 1]  # number of runs per scenario per capacity (same order as scenarios)
    ncpus = 3  # int(os.getenv('NUM_PROCS'))  # number of cpus to use
    timeseries_filenames = ['timeseries_inputs_2019.csv']  # list of csv files
    capacities = np.arange(1, 501, 500)

    # ------------------
    # create sweep_inputs dataframe
    # ------------------
    sweep_inputs = pd.DataFrame()
    for timeseries_filename in timeseries_filenames:
        for scenario, n_iterations in zip(scenarios, iterations):
            df_scenario = monteCarloInputs(scenarios_filename, scenario, n_iterations)
            df_scenario.loc[:, 'scenario'] = scenario
            df_scenario.loc[:, 'timeseries_filename'] = timeseries_filename
            for capacity in capacities:
                df_scenario.loc[:, 'capacity'] = capacity
                sweep_inputs = sweep_inputs.append(df_scenario)

    # reset index (appending messes up indices)
    sweep_inputs = sweep_inputs.reset_index()

    # count number of cases
    n_cases = sweep_inputs.shape[0]

    # save inputs
    sweep_inputs.to_csv('sweep_inputs.csv')

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
    f = open("run_time_history.txt", "a")
    f.write('\n')
    f.write('Last run : ' + dt_string + '\n')
    f.write('Total run time [h]: ' + str(round(run_time, 3)) + '\n')
    f.write('\n')
    f.close()
