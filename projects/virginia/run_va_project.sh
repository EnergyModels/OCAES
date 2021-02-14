#!/bin/bash

# virginia project
cd preprocess_inputs
sbatch run_preprocess_inputs.sh

cd ../sample_run
sbatch run_sample.sh

cd ../capacity_sweep
sbatch run_capacity_sweep.sh
