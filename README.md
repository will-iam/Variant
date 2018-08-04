Please fill in the config.py with your workspace directory and compiler commands.

// Does everything (build and start case)
python3 seek_optimal.py hydro4x1 -c n2dsod --core_per_node 1 --max_core_number 1
python3 seek_order.py hydro4x1 -c nSod --core_per_node 2 --max_core_number 2 --fastref

// Some post-process script
python3 script/study/visualize.py hydro4x1 --case n2dsod256x32
python3 script/study/precision.py hydro4x1 --case n2dsod256x32
python3 script/study/order.py hydro4x1 --case nSod
