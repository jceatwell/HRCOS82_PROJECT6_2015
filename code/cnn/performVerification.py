#!/usr/bin/env python2

import argparse
import sys
import datasetConfigParser as dcp
import os
import subprocess
import re
import collections
import math
import timeit

import numpy as np
from scipy.integrate import simps
from numpy import trapz


from subprocess import PIPE
# from theano.compile.io import Out
from os.path import join

# For debugging
import pickle

# class RocMatrix():
#     def __init__(self,label):
#         self.label = label  # Used to define points
#         
#         # These are running counts
#         self.TPCount = 0  # predicted == actual
#         self.FPCount = 0  # predicted != actual
#         self.TNCount = 0
#         self.FNCount = 0  # predicted == unknown
#         self.total   = 0  # running total (zeroed when Total == INS_COUNT
#         self.INS_COUNT = 100    # Calculate TPRates and FPRates per INS_COUNT
#                 
#         # Calculations: 
#         #    FPRate = FP/FP+TN
#         #    TPRate = TP/TP+FN
#         self.fpTpData = []   # Data stored in the form (TP at some interval, FP at some interval) 
#         self.rocMetrics = []
#         
#     def csvFormat(self):
#         result = []
#         
#         # sort by x axis
# #         self.rocMetrics.sort(key = lambda tup: tup[0])
#         
#         # output for print / write to file
#         for (fpRate, tpRate) in self.rocMetrics:
#             result.append( "%0.4f,%0.4f" %(fpRate, tpRate))
#             
#         return '\n'.join(result)
#             
#     def calculateROCMetrics(self):
#         # Calculate ROC metrics
#         allPositiveCount = self.TPCount + self.FNCount
#         allNegativeCount = self.FPCount + self.TNCount
#         self.rocMetrics = []
#         
#         if (allPositiveCount > 0) and (allNegativeCount > 0):
#             for (fpCount, tpCount) in self.fpTpData:
#                 fpRate = float(fpCount) / float(allNegativeCount)
#                 tpRate = float(tpCount) / float(allPositiveCount)
#         
#                 self.rocMetrics.append( (fpRate, tpRate) )
#                 
# #         
# #             tpRate = (self.TPCount) / float(self.TPCount + self.FNCount)
# #             fpRate = (self.FPCount) / float(self.FPCount + self.TNCount)
# #             self.rocMetrics.append( (fpRate, tpRate) )
#             
#     def update(self, predicted, actual):
#         if predicted == '1' and actual == '1':
#             self.TPCount += 1
#         elif predicted == '0' and actual == '0':
#             self.TNCount += 1
#         elif predicted == '1' and actual == '0':
#             self.FPCount += 1
#         elif predicted == '0' and actual == '1':
#             self.FNCount += 1
#         self.total += 1
#         
#         if (self.total % self.INS_COUNT) == 0:
#             self.fpTpData.append( (self.FPCount, self.TPCount) )
            
    
class ConfusionMatrix():
    def __init__(self,trueValue, TPCount, FPCount, TNCount, FNCount,total):
        self.trueValue = trueValue
        self.TPCount = TPCount  # predicted == actual
        self.FPCount = FPCount  # predicted != actual
        self.TNCount = TNCount
        self.FNCount = FNCount  # predicted == unknown
        self.total = total
    
    def updateTotal(self):
        self.total = self.TPCount + self.FPCount + self.TNCount + self.FNCount
        
    # For debugging if required
    def printMe(self):
        attrs = vars(self)
        print ', '.join("%s: %s" % item for item in attrs.items())
    
    def update(self, predicted, actual):
        if predicted == '1' and actual == '1':
            self.TPCount += 1
        elif predicted == '0' and actual == '0':
            self.TNCount += 1
        elif predicted == '1' and actual == '0':
            self.FPCount += 1
        elif predicted == '0' and actual == '1':
            self.FNCount += 1
        self.total += 1

    def calculateArea(self, points, rule="Simpson"):
        totalArea = 0    
        lastPoint = (0,0) 
        for ind, point in enumerate(points):
            if ind > 0:
                y = np.array([lastPoint[1], point[1]])
                
                if (rule == "Simpson"):
                    # To Compute the area under graph using composite Simpson's rule.
                    totalArea  += simps(y, dx=(point[0] - lastPoint[0]))
                else:
                    # To Compute the area under graph using composite Trapezoidal rule.
                    totalArea  += trapz(y, dx=(point[0] - lastPoint[0]))
                    
            lastPoint = point
        return totalArea
    
    def performCalculations(self):
        result = PerfamanceMeasures()
        result.total = self.total
        
        # Calculate F-Score (FERA Paper equation (1))
        if ((self.TPCount + self.FPCount) != 0):
            result.precision = self.TPCount / float(self.TPCount + self.FPCount)
        
        if ((self.TPCount + self.FNCount) != 0):
            result.recall = self.TPCount / float(self.TPCount + self.FNCount)
        
        if ((result.precision + result.recall) > 0):
            result.fScore = (2 * result.precision * result.recall) / float(result.precision + result.recall)
        
        # Calculate Accuracy
        if (self.total != 0):
            result.accuracy = (self.TPCount + self.TNCount) / float(self.total);
            
        # FERA Paper equation (4)        
        # Essentially a value is either 0 or 1 depending on classification
        # Since 1 squared = 1 the greatest (and smallest) an error can be is 1
        # The sum of the errors is thus self.FPCount + self.FNCount
        if (self.total != 0):
            result.meanSquareError = (1/float(self.total)) * (float(self.FPCount) + float(self.FNCount))
            
        result.rootMeanSquareError = math.sqrt(result.meanSquareError)
        
        # Calculate ROC metrics
        allPositiveCount = self.TPCount + self.FNCount
        if allPositiveCount > 0:
            result.TPRate = float(self.TPCount) / float(self.TPCount + self.FNCount)
        
        allNegativeCount = self.FPCount + self.TNCount
        if allNegativeCount > 0:
            result.FPRate = float(self.FPCount) / float(allNegativeCount)
            result.specificity = float(self.TNCount) / float(allNegativeCount)
        
        # Calculate AUCROC
        result.AUC = self.calculateArea([(0,0), (result.FPRate, result.TPRate), (1,1) ])
        return result;
    
class PerfamanceMeasures():
    def __init__(self):
        # For standard Mesurements
        self.precision = 0
        self.recall = 0
        self.fScore = 0
        self.accuracy = 0
        self.meanSquareError = 0
        self.rootMeanSquareError = 0
        self.total = 0
        # Receiver Operating Characteristic
        self.TPRate = 0
        self.FPRate = 0
        self.specificity = 0
        self.AUC = 0
        
#     def printMeasurements(self, au, auLabel):
#         print "%s: %4s Precision: %0.4f Recall: %0.4f F-Score: %0.4f MSE: %0.4f RMSE: %0.4f Accuracy: %0.4f Total: %d" \
#         %(auLabel, au, self.precision, self.recall, self.fScore, self.meanSquareError, self.rootMeanSquareError, self.accuracy, self.total)

    def formatMeasurements(self, cls, clsLabel):
        if clsLabel == "Emotion":
            labelSize = 8
        else:
            labelSize = 4
            
        return "%s: %*s Precision: %0.4f Recall: %0.4f F-Score: %0.4f MSE: %0.4f RMSE: %0.4f Accuracy: %0.4f TPR: %0.4f FPR: %0.4f spc: %0.4f AUC: %0.4f Records: %d" \
        %(clsLabel, labelSize, cls, self.precision, self.recall, self.fScore, self.meanSquareError, self.rootMeanSquareError, self.accuracy, self.TPRate, self.FPRate, self.specificity, self.AUC, self.total)

    def formatCsvMeasurements(self, cls, clsLabel):
        return "%s,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%0.4f,%d" \
        %(cls, self.precision, self.recall, self.fScore, self.meanSquareError, self.rootMeanSquareError, self.accuracy, self.TPRate, self.FPRate, self.specificity, self.AUC, self.total)
            
def processPrediction(dsfolder, config, mode, eye_detection):
    results = doPrediction(dsfolder, config, mode, eye_detection)
    dataset_process_results(dsfolder, config, results)

#     # write state
#     fileObject = open("state.out",'wb')
#     pickle.dump(results,fileObject) 
#     fileObject.close()
    
    # read state
#    fileObject = open("state.out",'r')
#    results = pickle.load(fileObject)
     

def readActualDataValues(dataFilePath):
    results = []
    try:
        dataFile = open(dataFilePath, "r")
        for line in dataFile:
            if (len(line) > 1):
                results.append(line.split()[0])
        dataFile.close()
    except IOError as e:
        print "I/O error({0}): writing file {1}".format(e.strerror, dataFilePath)
    return results


def fixClass(cls):
    '''
        Corrects Class to be more readable (e.g. AU1 becomes AU01)
    '''
    if cls.startswith("AU") and len(cls) == 3:
        return "AU0{}".format(cls[-1:])
    else:
        return cls
    
def dataset_process_results(dsfolder, config, results):
    ''' 
        Results in format: [('AU14/S067_003_00021006.png', 'AU10:1,AU12:0,AU14:0,AU17:1,AU6:0'), ('AU14/S067_004_00021628.png', 'AU10:0,AU12:0,AU14:0,AU17:0,AU6:0')]
        where
            AU14/S067_003_00021006.png := file which was fed in for evaluation
            'AU10:0,AU12:0,AU14:0,AU17:0,AU6:0' := Predictions made
    '''
    
    # Prepare Matrix
    classConfusionMatrix = {}
#     rocFullMatrix = RocMatrix("full")
    rocMatrix = {}
    classConfusionMatrix["full"] = ConfusionMatrix("full", 0, 0, 0, 0)
    for cls in config["CLSLIST"]:
        clsRef = fixClass(cls)
        classConfusionMatrix[clsRef] = ConfusionMatrix(cls, 0, 0, 0, 0)
#         rocMatrix[cls] = RocMatrix(cls)
        
    resultCount = len( results.items() )
    idx = 1
    for (prediction, result) in results.items():
        sys.stdout.write("Processing prediction ........................... [%3d / %3d]\r" %(idx, resultCount))
        sys.stdout.flush()
        idx += 1
        
#         print "Processing prediction: {}".format(prediction)
        for data in result:
            # Read in actual results
            inputImage = data[0]
            validationDataPath = join(dsfolder, join(config['VALIDATION_DATA'], inputImage))
            validationDataPath = "{}.txt".format( validationDataPath )
#             validationDataPath = "{}.txt".format( validationDataPath[:-4] )
            actualValues = readActualDataValues(validationDataPath)

            # Populate confusion Matrix
            predictions = dict(item.split(":") for item in data[1].split(","))
            for predictedClass in predictions.keys():
                # is this a positive or negative example
                if predictedClass in actualValues:
                    actualValue = '1'
                else:
                    actualValue = '0'
                
                # Update Confusion Matrix with reflection of predictions (Not the input prediction)
                # For specific AU
                clsRef = fixClass(predictedClass)
                classConfusionMatrix[clsRef].update(predictions[predictedClass], actualValue);
                
                # Update Confusion Matrix for complete set
                classConfusionMatrix["full"].update(predictions[predictedClass], actualValue);
                
    print ""
    print ""
    print "------------------------ {} ------------------------".format(config["RECOG_TITLE"])
    print "Classifier Performance:"
    for cmKey in collections.OrderedDict(sorted(classConfusionMatrix.items())):
        perfMeasurements = classConfusionMatrix[cmKey].performCalculations()
        print perfMeasurements.formatMeasurements(cmKey, config["RECOG_TYPE"])
    
    outputFile = "{}_{}.csv".format( config["RECOG_TYPE"], config["RECOG_TITLE"])
    writeOutput(classConfusionMatrix, outputFile, config["RECOG_TYPE"])
    
def writeOutput(classConfusionMatrix, outputFile, label):
    try:
        with open(outputFile, 'w+') as f:
            # Headings
            f.write ( "%s,Precision,Recall,F1-Score,MSE,RMSE,Accuracy,TPR,FPR,specificity,AUC,Records\n" %(label) )
            
            # Details
            for cmKey in collections.OrderedDict(sorted(classConfusionMatrix.items())):
                perfMeasurements = classConfusionMatrix[cmKey].performCalculations()
                f.write( perfMeasurements.formatCsvMeasurements(cmKey, label) + "\n")
    except IOError as e:
        print "I/O error({0}): writing file {1}".format(e.strerror, outputFile)
        
# def writeROC(rocMatrix, outputFile):
#     try:
# #         if (rocMatrix.total % rocMatrix.INS_COUNT) > 0:
# #             rocMatrix.updateROCMetrics()
#         
#         with open(outputFile, 'a+') as f:
#             f.write( rocMatrix.csvFormat() )
#     except IOError as e:
#         print "I/O error({0}): writing file {1}".format(e.strerror, outputFile)
        
def doPrediction(dsfolder, config, mode, eye_detection, do_prints=True):
    faces_dir = os.path.join(dsfolder, config['VALIDATION_IMAGES'])

    if mode == 'svm':
        class_dir = os.path.join(dsfolder, config['CLASSIFIER_SVM_FOLDER'])
        mode_s = 'svm'
    else:
        class_dir = os.path.join(dsfolder, config['CLASSIFIER_ADA_FOLDER'])
        mode_s = 'ada'

    execut = config['DETECTION_TOOL']
    print "INFO: detector tool '%s %s', eye detection: %r"%(execut, mode_s, eye_detection)

    classificators = []
    for f in os.listdir(class_dir):
        abs_f = os.path.join(class_dir, f)
        if os.path.isfile(abs_f):
            classificators.append(abs_f)

    print "INFO: classifiers %s"%str(classificators)

    results = {}
    args = [execut, mode_s, config['FACECROP_FACE_DETECTOR_CFG']]
    if eye_detection:
        args.append(config['FACECROP_EYE_DETECTOR_CFG'])
    else:
        args.append('none')
    args += [config['SIZE']['width'], config['SIZE']['height'],
        config['GABOR_NWIDTHS'], config['GABOR_NLAMBDAS'],
        config['GABOR_NTHETAS']] + classificators

    #new (with confusion matrix)
    res_reg = re.compile("Input File: (.*) Predicted Values: (.*) Finished Prediction")
    
    groupings = 2
    
    referenceFilePath = join(faces_dir, "images.txt")
    useReferenceFile = False
    if os.path.exists(referenceFilePath):
        facesList = [line.strip() for line in open(referenceFilePath, "r") if len(line) > 1]
        useReferenceFile = True
    else:
        facesList = [os.path.join(faces_dir, f) for f in os.listdir(faces_dir) if not f.endswith(".txt")]
        
    subList = [facesList[n:n+groupings] for n in range(0, len(facesList), groupings)]
    lenList = len(subList)
    
    try:
        for idx, faces_list in enumerate(subList):
            sys.stdout.write("processing prediction group ..................... [%3d / %3d]\r" %(idx+1, lenList))
            sys.stdout.flush()
            
            faces = '\n'.join(faces_list)
            p = subprocess.Popen(args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
            out = p.communicate(input=faces)   
            results["PR{}".format(idx)] = re.findall(res_reg, out[0])
        print ""
    except Exception as e:
        print "ERR: something wrong HERE1 (%s)" % str(e)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", default="dataset.cfg", help="Dataset config file name")
#    parser.add_argument("--ctx", default="context", help="Validation Context used to distinguish ROC csv saves")
    parser.add_argument("dsFolder", help="Dataset base folder")
    parser.add_argument("-v", "--verbose", action='store_true', help="verbosity")
    parser.add_argument("--mode", default="adaboost", choices=['adaboost', 'svm'], help="training mode: adaboost or svm")
#     parser.add_argument("--output", default="output.csv", help="Output File")
    parser.add_argument("--eye-correction", action="store_true", help="Perform eye correction on images")
    args = parser.parse_args()

    try:
        config = {}
        config = dcp.parse_ini_config(args.cfg)
        
        start_time = timeit.default_timer()
        processPrediction(args.dsFolder, config, args.mode, args.eye_correction)
        print "Validation Time Taken: {}".format(timeit.default_timer() - start_time)
    except Exception as e:
        print "ERR: something wrong (%s)" % str(e)
        sys.exit(1)
