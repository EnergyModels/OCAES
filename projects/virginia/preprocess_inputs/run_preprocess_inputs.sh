#!/bin/bash
#SBATCH -N 1
#SBATCH --cpus-per-task=1
#SBATCH -t 1:00:00
#SBATCH -p standard

module purge
module load anaconda/2019.10-py3.7

# activate environment
source activate ocaes-py3

# if gurobi is available
module load gurobi/9.0.1

# set the NUM_PROCS env variable for the Python script
export NUM_PROCS=$SLURM_CPUS_PER_TASK

# run
python preprocess_inputs.py
python move_input_files.py