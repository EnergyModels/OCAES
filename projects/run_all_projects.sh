#!/bin/bash

# virginia project
cd virginia/3yr_combined
sbatch run_capacity_sweep_3yr.sh

cd ../2015
sbatch run_capacity_sweep_2015.sh

cd ../2017
sbatch run_capacity_sweep_2017.sh

cd ../2019
sbatch run_capacity_sweep_2019.sh