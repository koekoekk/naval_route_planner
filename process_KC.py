import indicators
import os
import pickle
import main
import numpy as np
import pandas as pd

from datetime import datetime
from deap import tools
from pathlib import Path


def create_raw_dicts():
    loadDir = Path('C:/Users/JobS/Dropbox/EUR/Afstuderen/Ortec - Jumbo/5. Thesis/Current results/KC')
    rawDir = loadDir / 'raws_8_10'
    os.chdir(loadDir)

    refFiles = [file for file in os.listdir(rawDir) if 'R' in file]
    print('refFiles', refFiles)
    planner = main.RoutePlanner(bathymetry=False, fuelPrice=1., ecaFactor=1, vesselName='Tanaka')
    planner.evaluator.set_classes(inclCurr=True, inclWeather=False, nDays=7, startDate=datetime(2014, 11, 15))
    evaluate = planner.evaluator.evaluate

    refFrontsDict = {}
    for refFile in refFiles:
        split = refFile.split('_')
        pair = split[-1]
        with open(rawDir / refFile, 'rb') as fh:
            refRawList = pickle.load(fh)
        refFronts = [refRaw['fronts'][0][0] for refRaw in refRawList]
        newRefFronts = []
        for oldFront in refFronts:
            fits = [evaluate(ind, revert=False, includePenalty=False) for ind in oldFront]
            for fit, ind in zip(fits, oldFront.items):
                ind.fitness.values = fit
            newFront = tools.ParetoFront()
            newFront.update(oldFront.items)
            newRefFronts.append(newFront)
        refFrontsDict[pair] = newRefFronts

    files = [file for file in os.listdir(rawDir) if 'R' not in file]
    print('files', files)

    frontsDict = {}
    for file in files:
        split = file.split('_')
        pair = split[-1]
        with open(rawDir / file, 'rb') as fh:
            rawList = pickle.load(fh)
        fronts = [raw['fronts'][0][0] for raw in rawList]
        frontsDict[pair] = (fronts, refFrontsDict[pair])

    return frontsDict, planner


writer = pd.ExcelWriter('output.xlsx')


def compute_metrics(name, frontsDict):
    pairs = list(frontsDict.keys())
    dfBinaryHV = pd.DataFrame(columns=pairs)
    dfCoverage = pd.DataFrame(columns=pairs)

    for pair, (fronts, refFronts) in frontsDict.items():
        print('\r', pair, end='')

        for front, refFront in zip(fronts, refFronts):
            biHV = indicators.binary_hypervolume(front, refFront)
            coverage = indicators.two_sets_coverage(front, refFront)
            dfBinaryHV = dfBinaryHV.append({pair: biHV}, ignore_index=True)
            dfCoverage = dfCoverage.append({pair: coverage}, ignore_index=True)

    for df in [dfBinaryHV, dfCoverage]:
        mean, std, minn, maxx = df.mean(), df.std(), df.min(), df.max()
        df.loc['mean'] = mean
        df.loc['std'] = std
        df.loc['min'] = minn
        df.loc['max'] = maxx

    dfCoverage.to_excel(writer, sheet_name='{}_C'.format(name))
    dfBinaryHV.to_excel(writer, sheet_name='{}_B'.format(name))


def save_fronts(frontsDict, planner):
    evaluate2 = planner.evaluator.evaluate2
    for pair, frontTup in frontsDict.items():
        print('\r', pair, end='')
        fronts, refFronts = frontTup
        dfPairList, refDFPairList = [], []
        for run, (front, refFront) in enumerate(zip(fronts, refFronts)):
            dataFrames = []
            # Do for front and ref front
            for idx, f in enumerate([front, refFront]):
                # (Objective) values
                days, cost, dist, _, avgSpeed = zip(*map(evaluate2, f.items))
                cost = np.array(cost) * 1000.
                hours = np.array(days) * 24.
                currentSpeed = np.array(dist) / np.array(hours) - np.array(avgSpeed)
                df0 = pd.DataFrame(np.transpose(np.stack([hours, cost, dist, avgSpeed, currentSpeed])),
                                   columns=['T', 'C', 'D', 'V', 'S'])

                # Statistics
                dfStat = pd.DataFrame([df0.mean(), df0.std(), df0.min(), df0.max()],
                                      index=['mean', 'std', 'min', 'max'],
                                      columns=['T', 'C', 'D', 'V', 'S'])
                dfStatPairList = dfPairList if idx == 0 else refDFPairList
                dfStatPairList.append(dfStat)

                # Append dataframes
                df0 = dfStat.append(df0, ignore_index=False)
                dataFrames.append(df0)

            # Write to Excel sheet
            dfFronts, dfRefFronts = dataFrames
            dfRefFronts.to_excel(writer, sheet_name='{}_R{}'.format(pair, run))
            dfFronts.to_excel(writer, sheet_name='{}_{}'.format(pair, run))

        dfPair = pd.concat(dfPairList).groupby(level=0).mean()
        dfRefPair = pd.concat(refDFPairList).groupby(level=0).mean()
        dfPair.to_excel(writer, sheet_name='S_{}'.format(pair))
        dfRefPair.to_excel(writer, sheet_name='S_{}_R'.format(pair))


# compute_metrics(key, _fronts)
save_fronts(*create_raw_dicts())

writer.close()
