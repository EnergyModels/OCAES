import pandas as pd
from OCAES import ocaes
import time
from joblib import Parallel, delayed, parallel_backend


# =====================
# Function to enable parameter sweep
# =====================
def parameterSweep(sweep_inputs, index):
    # Record time to solve
    t0 = time.time()

    # create and run model
    data = pd.read_csv('data_manual.csv')
    model_inputs = ocaes.get_default_inputs()
    model_inputs['eta_storage'] = sweep_inputs.loc[index, 'efficiency']
    model_inputs['X_well'] = sweep_inputs.loc[index, 'capacity']
    model_inputs['X_cmp'] = sweep_inputs.loc[index, 'capacity']
    model_inputs['X_exp'] = sweep_inputs.loc[index, 'capacity']
    model = ocaes(data, model_inputs)
    df, s = model.get_full_results()

    # Display Elapsed Time
    t1 = time.time()
    print("Time Elapsed: " + str(round(t1 - t0, 2)) + " s")

    # Combine inputs and results into output and then return
    return pd.concat([sweep_inputs.loc[index,:]], axis=0), s


# =====================
# Main Program
# =====================
if __name__ == '__main__':

    # ==============
    # User Inputs
    # ==============
    studyname = 'sweep_efficiency_capacity'

    # efficiencies to investigate
    efficiencies = [0.5, 0.6, 0.7, 0.8, 0.9]
    efficiencies = [ 0.9]

    # storage capacities to investigate
    capacities = [0, 100, 200, 300, 400, 500]
    capacities = [100,  500]

    # Number of cores to use
    ncpus = -1  # int(os.getenv('NUM_PROCS'))

    # ==============
    # Run Simulations
    # ==============

    # prepare inputs
    entries = ['efficiency', 'capacity']
    sweep_inputs = pd.DataFrame(columns=entries)
    for efficiency in efficiencies:
        for capacity in capacities:
            s = pd.Series(index=entries)
            s['efficiency'] = efficiency
            s['capacity'] = capacity
            sweep_inputs = sweep_inputs.append(s, ignore_index=True)
    iterations = len(sweep_inputs)

    # Perform Simulations (Run all plant variations in parallel)
    with parallel_backend('multiprocessing', n_jobs=ncpus):
        output, s = Parallel(n_jobs=ncpus, verbose=10)(
            delayed(parameterSweep)(sweep_inputs, index) for index in range(iterations))

    # Combine outputs into single dataframe and save
    df = pd.DataFrame(output)
    df.to_csv(studyname + '.csv')
