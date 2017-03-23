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
import dta
import os
import sys


USAGE = r"""

 python importTPPlusTransitRoutes.py dynameq_net_dir dynameq_net_prefix [tpplus_transit1.lin tpplus_transit2.lin ...]
 
 e.g.
 
 python importTPPlusTransitRoutes.py . sf Y:\dta\SanFrancisco\2010\transit\sfmuni.lin Y:\dta\SanFrancisco\2010\transit\bus.lin
 
 This script reads the dynameq network in the given directory, as well as the given Cube TPPlus transit line file,
 and converts the transit lines into DTA transit lines, outputting them in Dynameq format as 
 [dynameq_net_dir]\sf_trn_ptrn.dqt
 
 """
 

if __name__ == "__main__":

    INPUT_DYNAMEQ_NET_DIR         = sys.argv[1]
    INPUT_DYNAMEQ_NET_PREFIX      = sys.argv[2]
    TRANSIT_LINES                 = sys.argv[3:]

    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("importTPPlusTransitRoutes.INFO.log", "importTPPlusTransitRoutes.DEBUG.log", logToConsole=True)
    
    scenario = dta.DynameqScenario()
    scenario.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX) 
    net = dta.DynameqNetwork(scenario)
    net.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX)


    MODE_TO_LITYPE = {'11':dta.TransitLine.LINE_TYPE_BUS,  # Muni Local
                      '12':dta.TransitLine.LINE_TYPE_BUS,  # Muni Express
                      '13':dta.TransitLine.LINE_TYPE_BUS,  # Muni BRT
                      '14':dta.TransitLine.LINE_TYPE_TRAM, # Muni CableCar
                      '15':dta.TransitLine.LINE_TYPE_TRAM, # Muni LRT
                      }
    
    # For now, assume motor standard and LRV1
    MODE_TO_VTYPE = {'11':"Motor_Std",
                     '12':"Motor_Std",
                     '13':"Motor_Std",
                     '14':"CableCar",
                     '15':"LRT2"
                     }
    # others are buses
    for modenum in range(1,30):
        key = "%d" % modenum
        if key not in MODE_TO_LITYPE:
            MODE_TO_LITYPE["%d" % modenum] = dta.TransitLine.LINE_TYPE_BUS
            MODE_TO_VTYPE["%d" % modenum]  = "Motor_Std"

    # write the output file
    output_filename = os.path.join(INPUT_DYNAMEQ_NET_DIR, "sf_trn_ptrn.dqt")
    output_file = open(output_filename,mode="w+")
    output_file.write(dta.TransitLine.getDynameqFileHeaderStr())
    
    dtaTransitLineId = 1
    for transit_file in TRANSIT_LINES:
        dta.DtaLogger.info("===== Processing %s ======" % transit_file)
        
        for tpplusRoute in dta.TPPlusTransitRoute.read(net, transit_file):
            # ignore if there's no frequency for this time period
            if tpplusRoute.getHeadway(3) == 0: continue
            
            dtaTransitLines = tpplusRoute.toTransitLine(net, dtaTransitLineId, MODE_TO_LITYPE, MODE_TO_VTYPE,
                                                        headwayIndex=3, startTime=dta.Time(15,30), demandDurationInMin=3*60)

            for dtaTransitLine in dtaTransitLines:
                # ignore if no segments for the DTA network
                if dtaTransitLine.getNumSegments() == 0: continue
            
                # check if the movements are allowed
                dtaTransitLine.checkMovementsAreAllowed(enableMovement=True)
            
                output_file.write(dtaTransitLine.getDynameqStr())
                dtaTransitLineId += 1

    output_file.close()

    net.write(".", "sf_trn")

    dta.DtaLogger.info("Output %d transit lines into %s" % (dtaTransitLineId-1, output_filename))

    
    

    
                
