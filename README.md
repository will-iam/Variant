Please fill in the config.py with your workspace directory, compiler commands and machine specifications.

// Does everything (build and start case)
python3 seek_optimal.py hydro4x1 --case n2dsod --core 2

// Order analysis
python3 seek_order.py eulerRuO1 --case nSedov --core 2 --fastref

// Some post-process script
python3 script/study/visualize.py eulerRuO1 --case nSedov256x256 --solver sedov
python3 script/study/plot.py eulerRuO1 --case nSedov256x256 --solver sedov --axis r --quant energy
python3 script/study/order.py eulerRuO1 --case nSedov --solver sedov
