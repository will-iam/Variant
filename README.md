# Variant

## Install

Please fill in the config.py with your workspace directory, compiler commands and machine specifications.

The verrou option will require [Verrou on GitHub](https://github.com/edf-hpc/verrou) which requires Valgrind.

Requires:
1. morden C++ compilers
2. python 3
3. and other stuff I don't have in mind presently

## Start your first hydrodynamics simulation

Variant comes with two helper scripts that compile, build and run cases.

```
python3 seek_optimal.py hydro4x1 --case nSod --core 2
python3 seek_order.py eulerRuO1 --case nSedov --core 2 --fastre
```

## Read the results

And finally to visualize the results.

```
python3 script/study/visualize.py eulerRuO1 --case nSedov256x256 --solver sedov
python3 script/study/plot.py eulerRuO1 --case nSedov256x256 --solver sedov --axis r --quant energy
python3 script/study/order.py eulerRuO1 --case nSedov --solver sedov
```
