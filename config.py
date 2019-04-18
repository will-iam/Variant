import os

workspace = os.getcwd()

gnu_CC = 'gcc'
gnu_CXX = 'g++'

clang_CC = 'clang'
clang_CXX = 'clang++'

intel_CC = 'icc'
intel_CXX = 'icpc'

mpi_CC = 'mpicc'
mpi_CXX = 'mpic++'

# keywords are: $mpi_nprocs, $ncores
mpi_RUN = 'mpirun -hostfile hostfile -np $mpi_nprocs'

core_per_node = 2
# tmp dir to launch a run.
tmp_dir = os.path.join(workspace, 'tmp')
# tmp dir to store results after a run.
results_dir = os.path.join(workspace, 'results')

## Cases directory, makes life easier when they're distinct.
case_ic = os.path.join(workspace, 'casepy') # Where the python scripts to build initial condition are.
case_input = os.path.join(workspace, 'caseinput') # Where the built initial conditions are (heady) 
case_ref = os.path.join(workspace, 'caseref') # Where the references (results to compare with) are

#What you can add in your hostfile for mpirun.
#localhost slots=4
