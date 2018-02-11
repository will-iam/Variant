Please fill in the config.py with your workspace directory and compiler
commands.

It's not fully parallel yet. Plan to move to the top:
- quantities must be Array of Structures.
- overlap (in and out) cells are aligned in memory (no copy in temporary buffer to communicate data,
    no need to multithread this part, needed to split the computation overlapcells, then purely internal cells).
- communication must be split MPI_Isend/MPI_Irecv then after computation MPI_Waitall

Discovered issue:
- Pb in periodic cases


python2 seek_optimal.py hydro2dAoS4x1 -c n2dsod --core_per_node 4 --max_core_number 4
