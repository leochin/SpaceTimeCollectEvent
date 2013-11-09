import SSDataObject as SSDO
import arcpy as ARCPY
import datetime as DT
import SSTimeUtilities as TUTIL
import numpy as NUM

def daysInMonth(month, year):
    return TUTIL.monthConvert(month, year)

def daysInYear(year):
    import calendar as CAL
    if CAL.isleap(year):
        return 366
    else:
        return 365

if __name__ == '__main__':
    ARCPY.env.overwriteOutput = True
    inputFC = r"C:\Data\time\starbucks.shp"
    timeField = "DATE"
    #### Create SSDataObject ####
    ssdo = SSDO.SSDataObject(inputFC)
    #### Retrive time data from ssdo ####
    ssdo.obtainData(ssdo.oidName, [timeField], dateStr = True)
    timeData = ssdo.fields[timeField].data
    ## print timeData
    #### Convert string to datetime64 object ####
    # method A
    dt = NUM.array([DT.datetime.strptime(dtString, "%Y-%m-%d %H:%M:%S") for dtString in timeData])

    # method B
    dt = NUM.array([TUTIL.iso2DateTime(dtString) for dtString in timeData])
    ## print dt
    '''
    After converted to datetime64 object, you can have property as second, minute, hour...
    For example:
        print dt[0].year
        print dt[0].second
    '''

    #### Find how many days in the month ####
    days1 = daysInMonth(dt[0].month, dt[0].year)
    print "There are {0} days in this {1}-{2}".format(days1, dt[0].year, dt[0].month)

    #### Find how many days in the year ####
    days2 = daysInYear(dt[0].year)
    print "There are {0} days in {1}".format(days2, dt[0].year)

    #### Convert string to datetime64 string ####
    timeData = NUM.array(timeData, dtype = 'datetime64[s]')
    ## print timeData
    '''
    When converted to datetime64 string, use .astype() to change the date/time unit
    s: second -> ex: 2013-11-01 01:12:13
    m: minute -> ex: 2013-11-01 01:12
    h: hour   -> ex: 2013-11-01 01
    D: day    -> ex: 2013-11-01
    M: month  -> ex: 2013-11
    Y: year   -> ex: 2013

    After converted to datetime64 string, it's able to do the Arithmetic
    '''
    day = timeData.astype('datetime64[D]')
    diff = day[1] - day[0]
    print diff

    #### Find startTime and endTime ####
    startTime = NUM.min(day)
    endTime = NUM.max(day)
    print startTime

    #### Assign temporal index ####
    binSize = 3
    timeBin = NUM.array((day - startTime) / binSize, dtype = 'int32')
    print timeBin

