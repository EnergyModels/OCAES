# OCAES
Technoeconomic performance of offshore compressed air energy storage (OCAES) systems. 

Model inputs are generalized and can be used to assess the technoeconomic performance of energy storage system co-located with offshore wind.

Original methodology forked from https://github.com/binghui89/OCAES and builds on the approach by Li and DeCarolis 2015
https://doi.org/10.1016/j.apenergy.2015.05.111

## Installation
Sample Linux installion based on Rivanna, the UVA High Performance Computer https://www.rc.virginia.edu/
  - clone from github
      > git clone https://www.github.com/EnergyModels/caes
  - move to OCAES directory
      > cd OCAES
  - load Anaconda (may need to update to latest python version)
      > module load anaconda/2019.10-py3.7
  - create environment
      > conda env create
  - activate environment
      > source activate ocaes-py3
  - install caes module
      > pip install .

## Operation
To run (from a new terminal) on Rivanna
- load Anaconda (may need to update to latest python vversion)
    > module load anaconda/2019.10-py3.7
- activate environment
    > source activate ocaes-py3
- move to directory
    > cd ~/OCAES/examples/sample_runs/COVE
- run file
    > python run_sample_COVE.py

## Projects

### Techno-economic analysis of offshore isothermal compressed air energy storage in saline aquifers co-located with wind power

  Bennett, J.A., Simpson, J.G., Qin, C., Fittro, R., Koenig, G.M., Clarens, A.F., Loth, E. (in review). Techno-economic 
  analysis of offshore isothermal compressed air energy storage in saline aquifers co-located with wind power.

    cd OCAES\projects\virginia 
    sbatch run_va_project.sh

## Acknowledgement

Special thank you to Binghui Li and Joe DeCarolis for making their code open-source and publicly available. For more 
information on their project please see:

    Li, B., and DeCarolis, J.F., (2015). A techno-economic assessment of offshore wind coupled to offshore compressed 
    air energy storage. Applied Energy, 155, 1, 315-322. https://doi.org/10.1016/j.apenergy.2015.05.111