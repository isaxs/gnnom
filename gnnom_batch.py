#!/usr/bin/python
import argparse

parser = argparse.ArgumentParser(description='Apply NN model in batch regime.')
parser.add_argument('architecture',  metavar='json',   type=str, help='path to the json file with architecture')
parser.add_argument('weights', metavar='h5',   type=str, help='path to the hdf5 file with weights')
parser.add_argument('dataPath',   metavar='path', type=str, help='path to the folder with data')
parser.add_argument('-o', '--output', type=str, default="", help='save output in CSV format')

args = parser.parse_args()

from keras.models import model_from_json
import saxsdocument
import numpy as np
import os
import json

jsonFilename  = args.architecture
h5Filename    = args.weights
inputFolder   = args.dataPath
outCsvPath    = args.output
stdpddf       = 1.0

try:
    # load json and create model
    jsonFile = open(jsonFilename, 'r')
    loadedModelJson = jsonFile.read()
    json_data = json.loads(loadedModelJson)
    if('Normalization coefficient' in json_data):
        stdpddf = (float)(json_data['Normalization coefficient'])
    smin          = (float)(json_data['smin'])
    smax          = (float)(json_data['smax'])
    firstPointIndex = (int)(json_data['firstPointIndex'])
    lastPointIndex  = (int)(json_data['lastPointIndex'])
    
    jsonFile.close()
    loadedModel = model_from_json(loadedModelJson)
    # load weights into new model
    loadedModel.load_weights(h5Filename)
    inputLength = loadedModel.input_shape[1]  # I(s) points
    print("Expected input: " + str(inputLength) + " points.")
    #outputLength = loadedModel.output_shape[1]  # p(r) points

    print("Model loaded. Yeah!")

except KeyError as e:
    print(f"Error: Oops, model cannot be loaded! Missing value: {e}")
    exit()

except:
    print("Error: Oops, model cannot be loaded for unknown reasons.")
    exit()

Rg = 20.0 # Angstroms

# output csv
outCsv = []
for inputFilename in os.listdir(inputFolder):
    try:
        doc  = saxsdocument.read(os.path.join(inputFolder, inputFilename))
        dat  = np.transpose(np.array(doc.curve[0]))
        s  = dat[0]
        Is = dat[1]

    except Exception as e:
        print(f"Error: Could not read {inputFilename}:")
        print(e)

    if s[0] != 0:
        # sew missing head
        step = s[1] - s[0]
        # find number of missing points
        head_number = (int)(np.rint((s[0] )/step))
        ss = 0.0
        s_head  = np.full(head_number, 0.0)
        Is_head = np.full(head_number, 0.0)
        for i in range(head_number):
            s_head[i]  = ss
            Is_head[i] = np.exp(ss*ss*Rg*Rg/-3.0)
            ss += step
        s  = np.hstack((s_head, s))
        Is = np.hstack((Is_head, Is))

    if len(Is[firstPointIndex:lastPointIndex]) != inputLength:
        print(f"{inputFilename} too short, skipping.")
        continue

    if round(s[firstPointIndex], 3) != round(smin, 3):
        print(f"{inputFilename}: point {firstPointIndex} has s={s[firstPointIndex]}, expected s={smin}")
        exit()

    if round(s[lastPointIndex - 1], 3) != round(smax, 3):
        print(f"{inputFilename}: point {lastPointIndex - 1} has s={s[lastPointIndex]}, expected s={smax}")
        exit()

    test = np.array([Is[firstPointIndex:lastPointIndex], ])
    pred = loadedModel.predict(test)

    #TODO: instead of checking output number of points > 10 read model type (scalar/pddf)
    if len(pred[0]) > 10:
        # Find Dmax: first negative point after max(p(r))
        max_pddf = np.argmax(pred)
        negIndex = np.argmax(pred[:,max_pddf:] < 0)
        # Crop p(r > Dmax), nullify last point
        pred = pred[:, 0: (negIndex + max_pddf + 1)]
        pred[:,-1] = 0.0

        r = np.arange(0.0, len(pred[0]) * 0.25, 0.25)
        outCsv.append(inputFilename + ', ' + str(round(r[-1], 3)))
        # print(f"{len(r)} - {len(pred[0])} - {r[-1]}") # DEBUG
        pddf_predicted = np.vstack((r, stdpddf * pred[0]))
        np.savetxt(inputFilename, np.transpose(pddf_predicted), fmt = "%.8e")

    else:
        for number in pred[0]:
            outCsv.append(inputFilename + ', ' + str(round(number, 3)))

if outCsvPath != "":
    np.savetxt(outCsvPath, outCsv, delimiter=",", fmt='%s')
    print(outCsvPath + " is written.")
else:
    print ("\n".join(outCsv))
