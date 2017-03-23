__copyright__   = "Copyright 2011 SFCTA"
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

USAGE = r"""

 USAGE
 python prepareCorridorPlots.py INPUT_DYNAMEQ_NET_DIR 
                                INPUT_DYNAMEQ_NET_PREFIX 
                                REPORTING_START_TIME
                                REPORTING_END_TIME
                                ROUTE_DEFINITION_FILE
                                COUNT_DIR
                                LINK_COUNT_FILE_15MIN 
                                MOVEMENT_COUNT_FILE_15MIN 
                                MOVEMENT_COUNT_FILE_5MIN
                                REPORTS_ROUTE_TRAVEL_TIME_FILE 
 
 e.g.
 
 python createDTAResults.py X:/Projects/ModelDev/dtaAnyway/validation2010.1/Reports/Scenarios/sf_jun8_420p/export 
                               sf_jun8_420p 
                               16:00
                               17:00
                               2011_LOS_Monitoring.csv 
                               X:/Projects/ModelDev/dtaAnyway/validation2010.1/input/ 
                               counts_links_15min_1600_1830.dat 
                               counts_movements_15min_1600_1830.dat 
                               counts_movements_5min_1600_1800.dat
                               ObsVsSimulatedRouteTravelTimes.csv
 

 exports each of the routes defined in the 2011_LOS_Monitoring.csv file to an image 
 
 Before running this script, you must export the loaded Dynameq network by going to 
 Network->Export->Dynameq Network.
"""


import sys
import dta
import csv
import re
from dta.Logger import DtaLogger
from dta.Utils import Time
from dta.Path import Path
from dta.DtaError import DtaError


if __name__ == "__main__":
    
    if len(sys.argv) != 11:
        print USAGE
        sys.exit(2)

    INPUT_DYNAMEQ_NET_DIR                = sys.argv[1]
    INPUT_DYNAMEQ_NET_PREFIX             = sys.argv[2]
    REPORTING_START_TIME                 = sys.argv[3]
    REPORTING_END_TIME                   = sys.argv[4]
    ROUTE_DEFINITION_FILE                = sys.argv[5]
    COUNT_DIR                            = sys.argv[6]
    LINK_COUNT_FILE_15MIN                = sys.argv[7] 
    MOVEMENT_COUNT_FILE_15MIN            = sys.argv[8]
    MOVEMENT_COUNT_FILE_5MIN             = sys.argv[9]
    REPORTS_ROUTE_TRAVEL_TIME_FILE       = sys.argv[10]
    
    # The SanFrancisco network will use feet for vehicle lengths and coordinates, and miles for link lengths
    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("visualizeDTAResults.INFO.log", "visualizeDTAResults.DEBUG.log", logToConsole=True)

    scenario = dta.DynameqScenario()
    scenario.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX) 
    net = dta.DynameqNetwork(scenario)

    net.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX)

    #magic numbers here. This information may (or may not) be somewhere in the .dqt files 
    simStartTime = 14 * 60 + 30
    simEndTime = 21 * 60 + 30
    simTimeStep = 5
    net.readSimResults(simStartTime, simEndTime, 5)

    DtaLogger.info("Reading 15-minute link counts")
    net.readObsLinkCounts(COUNT_DIR + "/" + LINK_COUNT_FILE_15MIN)
    DtaLogger.info("Reading 15-minute movement counts")
    net.readObsMovementCounts(COUNT_DIR + "/" + MOVEMENT_COUNT_FILE_15MIN)
    DtaLogger.info("Reading 5-minute movement counts")
    net.readObsMovementCounts(COUNT_DIR + "/" + MOVEMENT_COUNT_FILE_5MIN)
    

    reportStartTime = Time.readFromString(REPORTING_START_TIME).getMinutes()
    reportEndTime = Time.readFromString(REPORTING_END_TIME).getMinutes()

    routeTTOuput = open(REPORTS_ROUTE_TRAVEL_TIME_FILE, "w") 

    routeTTOuput.write("%s,%s,%s,%s,%s\n" % ("RouteName", "SimTravelTimeInMin", "ObsTravelTimeInMin", "SimRouteLengthInMiles", "ObsRouteLengthInMiles"))

    allRoutes = []
    for record in csv.DictReader(open(ROUTE_DEFINITION_FILE, "r")):
        streetNames = []

        name = record["RouteName"].strip()
        regex = re.compile(r",| AND|\&|\@|\ AT|\/")
        streetNames = regex.split(name)
        #streetNames_cleaned = [net.cleanStreetName(nm) for nm in streetNames]

        #if "/" in name:
        #    DtaLogger.error("Please remove / character from path %s from %s to %s" % (name, start, end))
        #    continue

        avgTTInMin = float(record["totalAvgTT"]) / 60.0
        lengthInMiles = float(record["LengthFt"]) / 5280.0
        
        end = record["End"].strip()
        start = record["Start"].strip()

        end_clean = net.getCleanStreetName(end)
        start_clean = net.getCleanStreetName(start)
        for street in streetNames:
            street_clean = net.getCleanStreetName(street)
            error=0
            fullName = "%s from %s to %s" % (street_clean, start_clean, end_clean)
            name = street_clean
            try: 
                path = Path.createPath(net, fullName, [[street_clean, start_clean], [street_clean, end_clean]], cutoff=0.7)
                DtaLogger.info("CREATED path %s from %s to %s" % (street_clean, start_clean, end_clean))
                break
            except DtaError:
                DtaLogger.error("Failed to create path %s from %s to %s" % (street_clean, start_clean, end_clean))
                error=1
                continue

        if error == 0:
            allRoutes.append(path)
            print "%s,%f,%f,%f,%f\n" % ("%s from %s to %s" % (name, start, end), path.getSimTTInMin(reportStartTime, reportEndTime), avgTTInMin, path.getLengthInMiles(), lengthInMiles)
            routeTTOuput.write("%s,%f,%f,%f,%f\n" % ("%s from %s to %s" % (name, start, end), path.getSimTTInMin(17*60, 18*60), avgTTInMin, path.getLengthInMiles(), lengthInMiles))

            outfileStreets = []
            outfileStreets.append(name)
            outfileStreets.append(start_clean)
            outfileStreets.append(end_clean)
            #outfileName = name
            volumesVsCounts = dta.CorridorPlots.CountsVsVolumes(net, path, False)
            outfileName = "_".join(outfileStreets)
            volumesVsCounts.writeVolumesVsCounts(reportStartTime, reportEndTime, outfileName)

    Path.writePathsToShp(allRoutes, "allRoutes") 
    routeTTOuput.close()
