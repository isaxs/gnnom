#!/usr/bin/python
import argparse

parser = argparse.ArgumentParser(description='Compare NN predictions.')
parser.add_argument('csv1',  metavar='csv1',   type=str, help='path to the template csv file')
parser.add_argument('csv2',  metavar='csv2',   type=str, help='path to the csv file for comparison')

parser.add_argument('-o', '--output', type=str, default="", help='save output in CSV format')
parser.add_argument('-m', '--metric', type=str, default="", help='options: ad(absolute diff); rd(relative diff); h (histo); l (csv1 vs csv2)')

args = parser.parse_args()

import csv
import numpy as np
import os
import matplotlib.pyplot as plt
csv1 = args.csv1
csv2 = args.csv2

outCsvPath    = args.output
metric        = args.metric
ms = ['ad', 'rd', 'h', 'l']
if metric not in ms:
    print("wrong metric! dying...")
    os._exit(0)

#convert to dictionaries
with open(csv1, mode='r', newline = '') as infile1:
    reader = csv.reader(infile1)
    dict1 = {rows[0]:rows[1] for rows in reader}

with open(csv2, mode='r', newline = '') as infile2:
    reader = csv.reader(infile2)
    dict2 = {rows[0]:rows[1] for rows in reader}



# find intersecions
fSet   = set(dict1)
sSet   = set(dict2)
sameId   = []
for name in fSet.intersection(sSet):
    sameId.append(name)
print(str(len(sameId)) + " out of " + str(max(len(dict1), len(dict2))) + " ids are identical")

# write output csv
with open(outCsvPath, mode='w') as outfile:
    writer  = csv.writer(outfile)
    ad       = []
    rd      = []
    linGT   = []
    linC    = []
    for num, n in enumerate(sameId, start = 1):
        diff = round(float(dict1[n]) - float(dict2[n]), 4)
        if metric == "l":
            #writer.writerow(["#Standart deviation: ", np.std(diff)])
            linGT.append(round(float(dict1[n]),4))
            linC.append(round(float(dict2[n]), 4))
            writer.writerow([round(float(dict1[n]),4),round(float(dict2[n]),4)])
        if metric == "ad":
            writer.writerow([str(num), str(diff), n])
            ad.append(diff)
        if metric in ["rd", "h"]:
            rDiff = diff/float(dict1[n])
            writer.writerow([str(num), str(rDiff), n])
            rd.append(rDiff)

outfile.close()

# if metric == 'ad' --> plot absolute differences
if metric == "ad":
    plt.scatter(range(len(ad)), ad, c = 'tab:blue', alpha = 0.3, edgecolors='none')
    plt.xlabel('Number of curve')
    plt.ylabel('Absolute difference')
    std = np.std(ad)
    med = np.median(ad)
    plt.title("std = " + str(std*100) + " %\nmedian = " + str(med*100) + " %")
    plt.grid(True)
    plt.show()

# if metric == 'rd' --> plot relative differences
if metric == "rd":
    plt.scatter(range(len(rd)), rd, c = 'tab:blue', alpha = 0.3, edgecolors='none')
    plt.xlabel('Number of curve')
    plt.ylabel('Relative difference')
    std = np.std(rd)
    med = np.median(rd)
    plt.title("std = " + str(std*100) + " %\nmedian = " + str(med*100) + " %")
    plt.grid(True)
    plt.show()

# if metric == 'l' --> plot linear regression
if metric == "l":
    plt.scatter(linGT, linC, c = 'tab:blue', alpha = 0.3, edgecolors='none')
    plt.xlabel('Ground truth')
    plt.ylabel('Predicted')
    linGT = np.array(linGT)
    linC = np.array(linC)
    rd  = (linGT - linC)/linGT
    std = np.std(rd)
    med = np.median(rd)
    plt.title("std = " + str(std*100) + " %\nmedian = " + str(med*100) + " %")
    plt.grid(True)
    plt.show()

# if metric == 'h' --> plot histogram
if metric == "h":
    # the histogram of the data
    n, bins, patches = plt.hist(rd, 50, density=True, facecolor='g', alpha=0.75)

    plt.xlabel('Bins')
    plt.ylabel('Probability')
    std = np.std(rd)
    med = np.median(rd)
    plt.title("std = " + str(std*100) + " %\nmedian = " + str(med*100) + " %")
    plt.grid(True)
    plt.show()
