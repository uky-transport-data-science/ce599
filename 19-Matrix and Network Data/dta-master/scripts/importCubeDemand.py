__copyright__   = "Copyright 2011-2012 SFCTA"
__license__     = """
    This file is part of DTA.

    DTA is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    DTA is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with DTA.  If not, see <http://www.gnu.org/licenses/>.
"""

import getopt
import pdb 
import dta
import os
import sys
import datetime
import csv




USAGE = r"""

 python importCubeDemand.py [-f demand_profile_file] dynameq_net_dir dynameq_net_prefix 
        cubeVehicleClass output_demand_table startTime endTime 
        cube_demand_table1 startTime1 endTime1 timeStep1 demand_portion1 
        [cube_demand_table2 startTime2 endTime2 timeStep2 demand_portion2]
        [cube_demand_table3 startTime3 endTime3 timeStep3 demand_portion3]
        ...
 
 e.g.
python %DTA_CODE_DIR%\scripts\importCubeDemand.py -f Y:\dta\SanFrancisco\2010\demand\DemandProfile.csv . sf_stops 
        Car_NoToll demand_Car_NoToll.dat 14:30 19:30 
        Y:\dta\SanFrancisco\2010\demand\SanFranciscoSubArea_2010_MD.csv 14:30 15:30 01:00 0.13364
        Y:\dta\SanFrancisco\2010\demand\SanFranciscoSubArea_2010_PM.csv 15:30 18:30 03:00 1.00
        Y:\dta\SanFrancisco\2010\demand\SanFranciscoSubArea_2010_EV.csv 18:30 19:30 01:00 0.22594

 ****IMPORTANT****
 Input Demand tables must be input in chronological order with the earliest start time first,
 and they must have non-overlapping time periods.
 *****************
 
 The example command above will construct a output a Dynameq ascii demand file, demand_Car_NoToll.dat,
 covering 14:30-19:30 for the vehicle class "Car_NoToll". 
 
 The DTA network and scenario for this table will be read from the current directory and have the
 prefix "sf_stops".
 
 The demand will derived from three different input (Cube) demand files:
    0.13364 of the demand from SanFranciscoSubArea_2010_MD.csv will be used for the 14:30-15:30 period,
    1.0     of the demand from SanFranciscoSubArea_2010_PM.csv will be used for the 15:30-18:30 period, and
    0.22594 of the demand from SanFranciscoSubArea_2010_EV.csv will be used for the 18:30-19:30 period.
    
 Further, if a demand_profile_file is passed, then any portion of the demand can be further peaked or
 distributed non-uniformly. The demand_profile_file is a csv file with the following columns:
 Start Time, End Time, Factor 1, Factor 2, Factor 3,...
 
 If a row is specified matching the start and end time of one of the input demand files, then the demand
 will be distributed according to the factors.  The sum of the factors must add to 1.  When this is
 included, then the timeStep specified with the input demand file will be ignored, and the timeStep for
 this demand period will instead be the timeperiod for the demand period divided by the number of time
 factors.  So in the given example, the contents of the DemandProfile.csv are:
 
 Start Time,End Time,Factor 1,Factor 2,Factor 3,Factor 4,Factor 5,Factor 6
 15:30,18:30,0.15173,0.15772,0.1679,0.17848,0.17492,0.16925

 So the timestep for the 15:30-16:30 period will be (3 hours / 6 periods) = 30 minutes, and
 not 3 hours as specified by timeStep2=03:00.
 
 """

               


if __name__ == "__main__":

    optlist, args = getopt.getopt(sys.argv[1:], "f:")

    if len(args) < 11:
        print USAGE
        sys.exit(2)
    

    INPUT_DYNAMEQ_NET_DIR         = args[0]
    INPUT_DYNAMEQ_NET_PREFIX      = args[1]
    CUBE_VEH_CLASS                = args[2]
    OUTPUT_DYNAMEQ_TABLE          = args[3]
    START_TIME                    = args[4]
    END_TIME                      = args[5]

    if optlist:
        for (opt,arg) in optlist:
            if opt=="-f":
                DEMAND_PROFILE_FILE   = arg
    else:
        DEMAND_PROFILE_FILE = None
    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("importCubeDemand.INFO.log", "importCubeDemand.DEBUG.log", logToConsole=True)

    outputStream = open(OUTPUT_DYNAMEQ_TABLE, "w")
        
    scenario = dta.DynameqScenario()
    scenario.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX) 
    net = dta.DynameqNetwork(scenario)
    net.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX)

    startTime = dta.Utils.Time.readFromString(START_TIME)
    endTime   = dta.Utils.Time.readFromString(END_TIME)

  
# Read in the demand profile(s) if an input file was provided
    factorsStart = []
    if DEMAND_PROFILE_FILE:
        factorsEnd   = []
        factorsList = []
        factorsLists = []
        factorNum = 0
        inputStream = open(DEMAND_PROFILE_FILE, "r")
        for record in csv.DictReader(inputStream):
            factorsList = []
            factorsStart.append(dta.Utils.Time.readFromString(record["Start Time"]))
            factorsEnd.append(dta.Utils.Time.readFromString(record["End Time"]))
            ii = 1
            factorNum = record["Factor %d" % ii]
            while factorNum:
                factorsList.append(factorNum)
                ii += 1
                factorNum = record["Factor %d" % ii]
            factorsLists.append(factorsList)

# Check to make sure that demand is within the scenario time.  Exit if not.  

    if startTime < scenario.startTime:
        dta.DtaLogger.error("Demand cannot start before scenario start time.")
        dta.DtaLogger.error("Demand start = %s, Scenario start = %s" % 
                            (startTime.strftime("%H:%M"), scenario.startTime.strftime("%H:%M")))
        sys.exit(2)
    if endTime > scenario.endTime:
        dta.DtaLogger.error("Demand cannot end after scenario end time.")
        dta.DtaLogger.error("Demand end = %s, Scenario end = %s" %
                            (endTime.strftime("%H:%M"), scenario.endTime.strftime("%H:%M")))
        sys.exit(2)

    # Create and write out demand for each table in the correct order (earliest first and getting continualy later.)
    dta.Demand.writeDynameqDemandHeader(outputStream, startTime, endTime, CUBE_VEH_CLASS)
    numDemandTables = (len(args)-5)/5
    for ii in range(0,numDemandTables):
        CUBE_TABLE            = args[6+(ii*5)]
        START_TIME_N          = args[7+(ii*5)]
        END_TIME_N            = args[8+(ii*5)]
        TIME_STEP             = args[9+(ii*5)]
        DEMAND_PORTION        = args[10+(ii*5)]

    # Check to be sure time is continuous
        if ii == 0:
            if dta.Utils.Time.readFromString(START_TIME_N) != startTime:
                dta.DtaLogger.error("Start time of first demand period (%s) must equal demand start time %s." % 
                                    (START_TIME_N, startTime.strftime("%H:%M")))
                sys.exit(2)
        elif ii > 0 and ii < numDemandTables-1:
            if dta.Utils.Time.readFromString(START_TIME_N) != endTime_n:
                dta.DtaLogger.error("Start time of demand period %d does not equal end time of demand period %d." % (ii+1, ii))
                sys.exit(2)
        elif ii > 0 and ii == numDemandTables-1:
            if dta.Utils.Time.readFromString(END_TIME_N) != endTime:
                dta.DtaLogger.error("End time of last demand period (%s) must equal demand end time %s." % 
                                    (END_TIME_N, endTime.strftime("%H:%M")))
                sys.exit(2)

    # Set start time, end time, and time step for the demand period
        startTime_n = dta.Utils.Time.readFromString(START_TIME_N)
        endTime_n   = dta.Utils.Time.readFromString(END_TIME_N)
        timeStep    = dta.Utils.Time.readFromString(TIME_STEP)

    # Check to see if demand period has a demand profile

        demProf = 0
        for jj in range(0,len(factorsStart)):
            if startTime_n == factorsStart[jj] and endTime_n == factorsEnd[jj]:
                demProf = 1
                FactorsList = factorsLists[jj]

    # Read in cube demand table, apply time of day factors (if applicable) and write demand out to OUTPUT_DYNAMEQ_TABLE

        if demProf == 1:
            timeStep = endTime_n - startTime_n
            demand = dta.Demand.readCubeODTable(CUBE_TABLE, net, CUBE_VEH_CLASS, 
                                                startTime_n, endTime_n, timeStep, float(DEMAND_PORTION))
            demand = demand.applyTimeOfDayFactors(FactorsList)
        else:
            demand = dta.Demand.readCubeODTable(CUBE_TABLE, net, CUBE_VEH_CLASS, 
                                                startTime_n, endTime_n, timeStep, float(DEMAND_PORTION))
            
        demand.writeDynameqTable(outputStream)
        dta.DtaLogger.info("Wrote %10.2f %-10s to %s" % (demand.getTotalNumTrips(), "TRIPS", OUTPUT_DYNAMEQ_TABLE))

    outputStream.close()


    
    


    
    
        
        








