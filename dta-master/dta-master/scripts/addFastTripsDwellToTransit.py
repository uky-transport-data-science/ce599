__copyright__   = "Copyright 2012 SFCTA"
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
import datetime
import dta
import getopt
import itertools
import os
import sys

# requires pyproj for projecting lat,long to the SF network coordinate space
# requires transitfeed for parsing the GTFS


USAGE = r"""

 python addFastTripsDwellToTransit.py dynameq_net_dir dynameq_net_prefix fasttrips.dat output_dynameq_net_prefix
 
 e.g.
 
 python addFastTripsDwellToTransit.py . sf_final "Q:\Model Development\FastTrips\FAST_TrIPs Output\ft_output_loadProfile.dat" sf_iter1
 
 This script reads the given net files (including the ptrn file), adds the dwell from the fasttrips.dat file,
 and outputs [output_dynameq_net_prefix]_ptrn.dqt.  This output transit file is the same as the input version,
 but with the dwell times modified.
 
"""

def readFastTripsOutput(filename):
    """
    Reads the fasttrips output file, which is tab-delimited.
    Returns dictionary of { (tripid, stopid) -> dwelltime } where
    tripid and stopid are strings and dwelltime is a float.
    """
    tripstop_to_dwell = {}
    colname_to_colidx = {}

    input_stream = open(filename, 'r')
    for line in input_stream:
        line_parts = line.split("\t")
        
        # read the header
        if len(colname_to_colidx) == 0:
            for colidx in range(len(line_parts)):
                colname_to_colidx[line_parts[colidx]] = colidx
            # print colname_to_colidx
            continue
        
        # store the mapping
        tripstop_to_dwell[(line_parts[colname_to_colidx["tripId"]],
                           line_parts[colname_to_colidx["stopId"]])] = \
                                  float(line_parts[colname_to_colidx["dwellTime"]])
        
    input_stream.close()
    return tripstop_to_dwell
    
if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], "")

    if len(args) != 4:
        print USAGE
        sys.exit(2)
        
    INPUT_DYNAMEQ_NET_DIR         = args[0]
    INPUT_DYNAMEQ_NET_PREFIX      = args[1]
    INPUT_FASTTRIPS_FILE          = args[2]
    OUTPUT_DYNAMEQ_NET_PREFIX     = args[3]
    

    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("addFastTripsDwellToTransit.INFO.log", "addFastTripsDwellToTransit.DEBUG.log", logToConsole=True)

    scenario = dta.DynameqScenario()
    scenario.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX) 
    net = dta.DynameqNetwork(scenario)
    net.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX)
    
    # read the fasttrips file
    tripstop_to_dwell = readFastTripsOutput(INPUT_FASTTRIPS_FILE)
    
    # start the output file
    output_transit_filename = "%s_ptrn.dqt" % OUTPUT_DYNAMEQ_NET_PREFIX
    output_transit_file = open(output_transit_filename, mode='w')
    output_transit_file.write(dta.TransitLine.getDynameqFileHeaderStr())
    
    # read the transit file and output the update
    input_transit_filename = os.path.join(INPUT_DYNAMEQ_NET_DIR, "%s_ptrn.dqt" % INPUT_DYNAMEQ_NET_PREFIX)
    
    dwell_updated    = 0
    dwell_notupdated = 0
    transit_line_num = 0
    for transitline in dta.TransitLine.read(net, input_transit_filename):
        tripid = str(transitline.id)
        
        for transit_seg in transitline.iterSegments():
            # no stop
            if transit_seg.label == "nostop": continue
            if transit_seg.label.startswith("label"): 
                transit_seg.label = "nostop"
                continue
            
            # get stopid
            label_parts = transit_seg.label.split(",")
            if len(label_parts) != 2:
                dta.DtaLogger.error("Don't understand transit segment label %s for %s" % (transit_seg.label, str(transit_seg)))
                continue
            
            stopid = label_parts[0]

            if (tripid,stopid) not in tripstop_to_dwell:
                dta.DtaLogger.error("trip/stop (%10s, %10s) not found in FastTrips lookup for dwell; zeroing." %
                                    (tripid, stopid))
                transit_seg.dwell = 0
                dwell_notupdated += 1
                continue
            
            # update the dwell
            transit_seg.dwell = tripstop_to_dwell[(tripid, stopid)]
            dwell_updated += 1
        
        # output the line
        output_transit_file.write(transitline.getDynameqStr())
        transit_line_num += 1

    # we're all done
    output_transit_file.close()
    dta.DtaLogger.info("Wrote %8d %-16s to %s" % (transit_line_num, "TRANSIT LINES", output_transit_filename))
    dta.DtaLogger.info("Updated %d out of %d dwell times" % (dwell_updated, (dwell_updated+dwell_notupdated)))