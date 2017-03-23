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

  python generateWalkAccessLinksForFASTTrIPs.py dynameq_net_dir dynameq_net_prefix
  
  e.g. 
  
  python generateWalkAccessLinksForFASTTrIPs.py "Q:\Model Development\FastTrips\Transit.Dynameq\sf_gtfs_50pctdemand.iter0" sf_final

  Reads the dynameq network specified in dynameq_net_dir/dynameq_netprefix_*.dqt and generates walk access links from tazs to stops
  in the transit file, as well as walk transfer links between stops.
  
  Writes ft_input_accessLinks.dat and ft_input_transfers.dat into the current working directory.
  
"""

    
if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], "")

    if len(args) != 2:
        print USAGE
        sys.exit(2)
        
    INPUT_DYNAMEQ_NET_DIR         = args[0]
    INPUT_DYNAMEQ_NET_PREFIX      = args[1]
    OUTPUT_ACCESSLINKS_FILE       = "ft_input_accessLinks.dat"
    OUTPUT_TRANSFERLINKS_FILE     = "ft_input_transfers.dat"
    
    # these are the units of the dynameq input files
    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("generateWalkAccessLinksForFASTTrIPs.INFO.log", "generateWalkAccessLinksForFASTTrIPs.DEBUG.log", logToConsole=True)

    # reads the dynameq input (scenario, network)
    scenario = dta.DynameqScenario(dta.Time(0,0), dta.Time(23,0))
    scenario.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX) 
    net = dta.DynameqNetwork(scenario)
    net.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX)
    
    # { stopid -> (link, position) }
    stopid_to_linkpos = {}
    # { nodeid -> set( (stopids,dist) ) }
    nodeid_to_stopidset = {}
    
    # read the transit file
    input_transit_filename = os.path.join(INPUT_DYNAMEQ_NET_DIR, "%s_ptrn.dqt" % INPUT_DYNAMEQ_NET_PREFIX)
    for transitline in dta.TransitLine.read(net, input_transit_filename):
        tripid = str(transitline.id)
    
        for transit_seg in transitline.iterSegments():
            # we don't care about no stop links
            if transit_seg.label == "nostop": continue
            if transit_seg.label.startswith("label"): continue
            
            # get stopid
            label_parts = transit_seg.label.split(",")
            if len(label_parts) != 2:
                dta.DtaLogger.error("Don't understand transit segment label %s for %s" % (transit_seg.label, str(transit_seg)))
                continue
            
            stopid = label_parts[0]
            prop   = float(label_parts[1])
            linklen= transit_seg.link.euclideanLength(includeShape=True)
            
            stopid_to_linkpos[stopid] = (transit_seg.link, prop)
            
            # fill in nodeid_to_stopidset
            dist_from_start = prop*linklen
            dist_from_end   = (1.0-prop)*linklen
            
            startnodeid = transit_seg.link.getStartNode().getId()
            if startnodeid not in nodeid_to_stopidset:
                nodeid_to_stopidset[startnodeid] = set()
            nodeid_to_stopidset[startnodeid].add( (stopid,dist_from_start) )
            
            endnodeid = transit_seg.link.getEndNode().getId()
            if endnodeid not in nodeid_to_stopidset:
                nodeid_to_stopidset[endnodeid] = set()
            nodeid_to_stopidset[endnodeid].add( (stopid,dist_from_end) )
                        
    
    dta.DtaLogger.debug("nodeid_to_stopidset = %s" % str(nodeid_to_stopidset))
    # to use for cutoff
    stopid_to_coords = {}
    
    # here - add reverse links so people can walk backwards on one-way links
    new_id = 9500000
    # create roadlink list to iterate through since we'll be modifying the network
    roadlinks = []
    for roadlink in net.iterRoadLinks():
        roadlinks.append(roadlink)
        
    # iterate
    for roadlink in roadlinks:
        startid = roadlink.getStartNode().getId()
        endid   = roadlink.getEndNode().getId()
        
        try:
            revlink = net.getLinkForNodeIdPair(endid, startid)
        except:
            # no reverse link!  create one and add it
            revlink = roadlink.createReverseLink(new_id) 
            net.addLink(revlink)
            
            new_id += 1
    
#############################################################################################################################################
#Access/Egress Link Generation
    # generate the access link for each taz centroid to each walkable stop
    dta.DtaLogger.info("Generating the Access Links")
    # { (taz,stop) -> dist }
    access_links = {}
    for taz in range(1,982):
        # get the centroid
        try:
            centroid = net.getNodeForId(taz)
        except:
            dta.DtaLogger.info("No centroid for %d -- Skipping" % taz)
            continue
        
        vertices_set = dta.ShortestPaths.labelSettingWithLabelsOnNodes(net, sourceVertex=centroid, endVertex=None, sourceLabel=0.0, includeVirtual=True,
                                                                       maxLabel=5280.0/2.0, filterRoadLinkEvalStr="roadlink.getFacilityType() in [1,2,3,8]") #1,2,3,8

        dta.DtaLogger.debug("TAZ %d" % taz)
        if len(vertices_set) == 0:
            continue
        for node in vertices_set:
##            dta.DtaLogger.debug("  Node %7d  Dist %10.3f  PrevNode %7d  stopids? %s" % 
##                                (node.getId(), node.label, node.predVertex.getId() if node.predVertex else 0,
##                                str(nodeid_to_stopidset[node.getId()]) if (node and node.getId() in nodeid_to_stopidset) else ""))

            if (node and node.getId() in nodeid_to_stopidset):
                for nodestop in nodeid_to_stopidset[node.getId()]:
                    # ignore if further than a half mile
                    if (node.label + nodestop[1])/(5280.0) > 0.5: continue

                    if (taz, nodestop[0]) not in access_links:
                        access_links[(taz, nodestop[0])] = (node.label + nodestop[1])/(5280.0)
                    elif (node.label + nodestop[1])/(5280.0) < access_links[(taz, nodestop[0])]:
                        access_links[(taz, nodestop[0])] = (node.label + nodestop[1])/(5280.0)

        if taz%100==0:  dta.DtaLogger.info("Processed %4d tazs" % taz)
    dta.DtaLogger.info( "%d\tAccess Links were generated\n" % (len(access_links)))
    
    #writing the access links to the file
    output_access_links_file = open(os.path.join("",OUTPUT_ACCESSLINKS_FILE), mode="w")
    output_access_links_file.write("TAZ\tstop\tdist\ttime\n")
    keylist = access_links.keys()
    keylist.sort()
    for key in keylist:
        output_access_links_file.write( "%s\t%s\t%.3f\t%.3f\n" % (key[0], key[1], access_links[key], 60*access_links[key]/3.0) )
    output_access_links_file.close()
#############################################################################################################################################
#Transfer Link Generation
    dta.DtaLogger.info("Generating the Transfer Links")
   # { (fromstop,tostop) -> dist }
    transfer_links = {}
    counter = 0
    for from_stop in stopid_to_linkpos.keys():
        counter = counter + 1
        prop = stopid_to_linkpos[from_stop][1]
        from_stop_link = stopid_to_linkpos[from_stop][0]
        linklen= from_stop_link.euclideanLength(includeShape=True)

        start_node = stopid_to_linkpos[from_stop][0].getStartNode()
        end_node = stopid_to_linkpos[from_stop][0].getEndNode()

        dist_from_start = prop*linklen
        dist_from_end   = (1.0-prop)*linklen

        # find transfer links from the startnode
        vertices_set = dta.ShortestPaths.labelSettingWithLabelsOnNodes(net, sourceVertex=start_node, endVertex=None, sourceLabel=dist_from_start, includeVirtual=True,
                                                                       maxLabel=5280.0/4.0, filterRoadLinkEvalStr="roadlink.getFacilityType() in [1,2,3,8]") #1,2,3,8
        if len(vertices_set) != 0:
          for node in vertices_set:

            if (node and node.getId() in nodeid_to_stopidset):
                for nodestop in nodeid_to_stopidset[node.getId()]:

                    transfer_dist = (node.label + nodestop[1])/(5280.0)
                    if transfer_dist > 0.25:
                        continue
                    if (from_stop, nodestop[0]) not in transfer_links:
                        transfer_links[(from_stop, nodestop[0])] = transfer_dist
                    elif (node.label + nodestop[1])/(5280.0) < transfer_links[(from_stop, nodestop[0])]:
                        transfer_links[(from_stop, nodestop[0])] = transfer_dist

        # find transfer links from the endnode
        vertices_set = dta.ShortestPaths.labelSettingWithLabelsOnNodes(net, sourceVertex=end_node, endVertex=None, sourceLabel=dist_from_end, includeVirtual=True,
                                                                       maxLabel=5280.0/4.0, filterRoadLinkEvalStr="roadlink.getFacilityType() in [1,2,3,8]") #1,2,3,8
        if len(vertices_set) != 0:
          for node in vertices_set:

            if (node and node.getId() in nodeid_to_stopidset):
                for nodestop in nodeid_to_stopidset[node.getId()]:

                    transfer_dist = (node.label + nodestop[1])/(5280.0)
                    if transfer_dist > 0.25:
                        continue
                    if (from_stop, nodestop[0]) not in transfer_links:
                        transfer_links[(from_stop, nodestop[0])] = transfer_dist
                    elif transfer_dist < transfer_links[(from_stop, nodestop[0])]:
                        transfer_links[(from_stop, nodestop[0])] = transfer_dist

        # when both the from_stop and to_stop are on the same link, then simplify  the transfer distance to be based on the position of stops along the link
        for to_stop in stopid_to_linkpos.keys():
            to_stop_link = stopid_to_linkpos[to_stop][0]
            if to_stop_link == from_stop_link and to_stop!=from_stop:
                transfer_dist = abs(stopid_to_linkpos[to_stop][1]-stopid_to_linkpos[from_stop][1])
                if transfer_dist > 0.25:
                    continue
                if (from_stop, to_stop) not in transfer_links:
                    transfer_links[(from_stop, to_stop)] = transfer_dist
                elif transfer_dist < transfer_links[(from_stop, to_stop)]:
                    transfer_links[(from_stop, to_stop)] = transfer_dist
                

            
        if counter%100==0:  dta.DtaLogger.info("Processed %5d origin stops for transfer links" % counter)
    dta.DtaLogger.info( "%d\tTransfer Links were generated\n" % (len(transfer_links)) )
         
    #writing the transfer links to the file        
    output_transfer_links_file = open(os.path.join("",OUTPUT_TRANSFERLINKS_FILE), mode="w")
    output_transfer_links_file.write("fromSop\ttoStop\tdist\ttime\n")
    keylist = transfer_links.keys()
    keylist.sort()
    for key in keylist:
        output_transfer_links_file.write( "%s\t%s\t%.3f\t%.3f\n" % (key[0], key[1], transfer_links[key], 60*transfer_links[key]/3.0) )
    output_transfer_links_file.close()

#############################################################################################################################################            
    dta.DtaLogger.info("Wrote %d access links to %s" % (len(access_links), OUTPUT_ACCESSLINKS_FILE))
    dta.DtaLogger.info("Wrote %d access links to %s" % (len(transfer_links), OUTPUT_TRANSFERLINKS_FILE))












