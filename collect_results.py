import os
import argparse
import numpy as np
from ast import literal_eval
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Performance measures", prefix_chars='-')

parser.add_argument("-c", type = str, help = "Case to test", required=True)
args = parser.parse_args()

subdirs = [tup[0] for tup in os.walk(os.path.join('results', args.c))][1:]

jobs_data = []
boxplot_data = []
median_data = []

attrnames = []

for s in subdirs:
    with open(os.path.join(s, 'results_data.csv'), 'r') as f:
        attrnames = f.readline().replace('\n', '').split(';')
        for line in f.readlines():
            data_line = []
            for el in line.split(';'):
                if el[0] in ['(', '[']:
                    el = el[1:-1]
                    data_line.append([float(e) for e in el.replace(",", "").split()])
                else:
                    try:
                        data_line.append(int(el))
                    except ValueError:
                        data_line.append(el)
            jobs_data.append(data_line)
            boxplot_data.append(data_line[attrnames.index('computeTime')])
            median_data.append(np.median(boxplot_data[-1]))

# Plotting received data
fig = plt.figure(0, figsize=(9, 6))
ax = fig.add_subplot(111)
nSDD_X_index = attrnames.index('n_SDD_X')
nSDD_Y_index = attrnames.index('n_SDD_Y')
nThreads_index = attrnames.index('n_threads')
#ax.set_xticklabels([(dl[nSDD_X_index], dl[nSDD_Y_index]) for dl in
#    jobs_data])
ax.set_xticklabels([dl[nThreads_index] for dl in jobs_data])
ax.boxplot(boxplot_data)
ax.plot([i + 1 for i in range(len(median_data))],
        median_data, color='g')
plt.show()
