import SSDataObject as SSDO
import numpy as NUM
import ErrorUtils as ERROR
import arcpy as ARCPY
import WeightsUtilities as WU
import SSUtilities as UTILS
import os as OS
import arcpy.management as DM
import gapy as GAPY
import arcpy.da as DA

#### Two New Field in Collected Feature ####
countFieldName = "ICOUNT"
timeFieldName = "START_TIME"

def stCollectByKNN(ssdo, timeField, outputFC, inSpan, inDistance):
    """
    This method applied Jacquez Space-Time K-NN to convert event data into weighted
    point data by dissolving all coincident points in space and time into unique
    points with a new count field that contains the number of original features
    at that location and time span.

    INPUTS:
        ssdo (obj): SSDataObject from input
        timeField (str): Date/Time field name in input feature
        outputFC (str): path to the output feature class
        inSpan (int): value of temporal units within the same time bin
        inDistance (int): value of spatial units considered as spatial neighbors
    OUTPUTS:
        Create new collected point feature

    """
    #### Read raw time data ####
    timeData = ssdo.fields[timeField].data
    #### Convert temporal unit ####
    time = NUM.array(timeData, dtype = 'datetime64[s]').astype('datetime64[D]')
    #### Find Start Time ####
    startTime = time.min()
    #### Create Bin for Space and Time ####
    timeBin = (time - startTime) / inSpan

    numObs = ssdo.numObs
    #### Create Sudo-fid to Find K-NN in Space and Time
    fid = [i for i in xrange(numObs)]

    #### Validate Output Workspace ####
    ERROR.checkOutputPath(outputFC)

    #### True Centroid Warning For Non-Point FCs ####
    if ssdo.shapeType.upper() != "POINT":
        ARCPY/AddIDMessage("WARNING", 1021)

    #### Create GA Data Structure ####
    gaTable, gaInfo = WU.gaTable(ssdo.inputFC, spatRef = ssdo.spatialRefString)

    #### Assure Enough Observations ####
    cnt = UTILS.getCount(ssdo.inputFC)
    ERROR.errorNumberOfObs(cnt, minNumObs = 4)
    N = gaInfo[0]
    ERROR.errorNumberOfObs(N, minNumObs = 4)

    #### Process Any Bad Records Encountered ####
    numBadRecs = cnt -N
    if numBadRecs:
        badRecs = WU.parseGAWarnings(gaTable.warnings)
        if not ssdo.silentWarnings:
            ERROR.reportBadRecords(cnt, numBadRecs, badRecs, label = ssdo.oidName)

    #### Create Output Feature Class ####
    outPath, outName = OS.path.split(outputFC)
    try:
        DM.CreateFeatureclass(outPath, outName, "POINT", "", ssdo.mFlag,
                              ssdo.zFlag, ssdo.spatialRefString)
    except:
        ARCPY.AddIDMessage("ERROR", 210, outputFC)
        raise SystemExit()

    #### Create k-Nearest Neighbor Search Type ####
    gaSearch = GAPY.ga_nsearch(gaTable)
    gaSearch.init_nearest(inDistance, 0, "euclidean")

    #### Add Count Field ####
    countFieldNameOut = ARCPY.ValidateFieldName(countFieldName, outPath)
    timeFieldNameOut = ARCPY.ValidateFieldName(timeFieldName, outPath)
    UTILS.addEmptyField(outputFC, countFieldNameOut, "LONG")
    UTILS.addEmptyField(outputFC, timeFieldNameOut, "DATE")
    fieldList = ["SHAPE@", countFieldNameOut, timeFieldNameOut]

    #### Set Insert Cursor ####
    rowsOut = DA.InsertCursor(outputFC, fieldList)

    #### Detect S-T K-NN by Space and Time Bin ####
    duplicateList = []
    for record in fid:
        kNNList = [record]
        if record not in duplicateList:
            for pair in fid:
                if pair != record :
                    gaSearch.search_by_idx(record)
                    for nh in gaSearch:
                        if timeBin[record] == timeBin[pair]:
                            kNNList.append(nh.idx)
                            duplicateList.append(nh.idx)
            #### Create and Populate New Feature ####
            kNNList = list(set(kNNList))
            count = len(kNNList)
            dt = time[record]
            x0 = ssdo.xyCoords[kNNList, 0].mean()
            y0 = ssdo.xyCoords[kNNList, 1].mean()
            pnt =(x0, y0, ssdo.defaultZ)
            rowResult = [pnt, count, dt]
            rowsOut.insertRow(rowResult)
            ARCPY.SetProgressorPosition()

    #### Clean Up ####
    del rowsOut, timeBin, kNNList, duplicateList

    return countFieldNameOut

if __name__ == '__main__':
    ARCPY.env.overwriteOutput = True

    inputFC = r"C:\Data\time\starbucks.shp"
    timeField = "DATE"
    outputFC = r"C:\Data\time\collectedStarbucks.shp"
    inSpan = 7
    inDistance = 1000.
    #### Create SSDataObject ####
    ssdo = SSDO.SSDataObject(inputFC)
    ssdo.obtainData(ssdo.oidName, [timeField], dateStr = True)
    #### Call stCollectByKnn to Carry Out Collect Event ####
    stCollectByKNN(ssdo, timeField, outputFC, inSpan, inDistance)
