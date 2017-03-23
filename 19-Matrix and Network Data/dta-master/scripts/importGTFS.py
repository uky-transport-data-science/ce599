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

 python importGTFS.py [-s sf_gtfs_stops.shp] [-l sf_gtfs_links.shp] dynameq_net_dir dynameq_net_prefix gtfs_file.zip
 
 e.g.
 
 python importGTFS.py . sf Y:\dta\SanFrancisco\2010\transit\google_transit_sfmta_20120609_20120914.zip
 
 This script reads the `General Transit Feed Specification <https://developers.google.com/transit/gtfs/>`_
 and converts the transit lines into DTA transit lines, outputting them in Dynameq format as 
 [dynameq_net_dir]\[dynameq_net_prefix]_ptrn.dqt
 
 Each trip is input as a separate line with a large headway, so it runs once.  This is because
 future development will modify dwell times based on the ridership of that particular trip.
 
 The script also optionally outputs a stops shapefile and a links shapefile for debugging.
"""
 
def convertLongitudeLatitudeToXY(longitude,latitude):
    from pyproj import Proj
    """
    Converts longitude and latitude to an x,y coordinate pair in
    NAD83 Datum (most of our GIS and CUBE files)
    
    Returns (x,y) in feet.
    """
    FEET_TO_METERS = 0.3048006096012192

    p = Proj(proj  = 'lcc',
             datum = "NAD83",
             lon_0 = "-120.5",
             lat_1 = "38.43333333333",
             lat_2 = "37.066666666667",
             lat_0 = "36.5",
             ellps = "GRS80",
             units = "m",
             x_0   = 2000000,
             y_0   = 500000) #use kwargs
    x_meters,y_meters = p(longitude,latitude,inverse=False,errcheck=True)

    return (x_meters/FEET_TO_METERS,y_meters/FEET_TO_METERS)

def stopOnWrongSide(roadlink, x, y, portion_along_link):
    """
    Returns True if the stop at (*x*, *y*) is on the left side of the street.
    
    Uses *portion_along_link* if there are shape points.
    """
    # for no shape points, this is simple
    if roadlink.getNumShapePoints() == 0:
        s = (((roadlink.getEndNode().getX() - roadlink.getStartNode().getX())*(y-roadlink.getStartNode().getY())) -
             ((roadlink.getEndNode().getY() - roadlink.getStartNode().getY())*(x-roadlink.getStartNode().getX())))

    else:
        # find relevant sub-segment
        (close_x, close_y, close_idx) = roadlink.coordinatesAndShapePointIdxAlongLink(fromStart=True, 
                                        distance=portion_along_link*roadlink.getLengthInCoordinateUnits(), goPastEnd=True)
        
        shapepoints = roadlink.getShapePoints()
        
        if close_idx == 0:
            start_point = (roadlink.getStartNode().getX(), roadlink.getStartNode().getY())
        else:
            start_point = (shapepoints[close_idx-1][0], shapepoints[close_idx-1][1])
        if close_idx == len(shapepoints):
            end_point   = (roadlink.getEndNode().getX(), roadlink.getEndNode().getY())
        else:
            end_point   = (shapepoints[close_idx][0], shapepoints[close_idx][1])
            
        s = (((end_point[0] - start_point[0])*(y-start_point[1])) -
             ((end_point[1] - start_point[1])*(x-start_point[0])))
            
    return (True if s>0 else False)
    
    

def addStopIdToLinkToDict(stop, network, stopid_to_link):
    """
    Maps the given *stop* (a :py:class:`transitfeed.stop` instance) to a link in 
    the given *network* (a :py:class:`Network` instance).
    
    Sets the 6-tuple: ``(x, y, stopname, roadlink, distance, portion_along_link)`` into the 
    *stopid_to_link* dictionary for the stop id key.  If something is already there, then this does nothing.
    
    The last three values will be None if no roadlink is found.
    """
    stop_id = stop['stop_id']
    if stop_id in stopid_to_link: return
    
    QUICK_DIST = 200 # feet
            
    (x,y) = convertLongitudeLatitudeToXY(stop['stop_lon'], stop['stop_lat'])

    closest_tuples = network.findNRoadLinksNearestCoords(x,y, n=6, quick_dist=QUICK_DIST)
    
    # none found - bummer!
    if len(closest_tuples) == 0:
        stopid_to_link[stop_id] = (x, y, stop['stop_name'], None, None, None)
    else:
        # check if the stop name changes things
        stop_name_parts = stop['stop_name'].split(" ")
        stop_str = stop_name_parts[0].upper()
        stop_str = stop_str.replace("MCALLISTER", "MC ALLISTER")
        
        # score best matches
        scores = []
        
        for close_tuple in closest_tuples:
            # 1 point for right side of the street
            alt_wrong_side = stopOnWrongSide(close_tuple[0], x, y, close_tuple[2])
            score = (1 if not alt_wrong_side else 0)
            
            # 2 points for matching name
            score += (2 if close_tuple[0].getLabel().startswith(stop_str) else 0)
    
            # points for distance?
            # score += 0.5 if close_tuple[1] < 50 else 0.0
            
            # todo: make this cleaner
            # score -10 for geary tunnel
            start_end_ids = (close_tuple[0].getStartNode().getId(), close_tuple[0].getEndNode().getId())
            score += (-10 if start_end_ids==(26811,26908) else 0)
            score += (-10 if start_end_ids==(26908,26811) else 0)
            
            # hack: stop 7334 goes to the wrong side of the street.  it appears to have coords slightly off?
            score += (-10 if (stop_id=='7334' and close_tuple[0].getDirection() == dta.RoadLink.DIR_WB) else 0)
            # ? score += (-10 if start_end_ids==(20296,20299) else 0)
            
            # hack: stop 7073 goes to the wrong side of the street.  it should be NB not SB
            score += (-10 if (stop_id=='7073' and close_tuple[0].getDirection() == dta.RoadLink.DIR_SB) else 0)
            
            # hack: stop 3255 goes to the wrong side of the street.  it should be EB not WB
            score += (-10 if (stop_id=='3255' and close_tuple[0].getDirection() == dta.RoadLink.DIR_WB) else 0)
            
            # hack: stop 5486 is on the border but goes to the wrong one
            score += (-10 if (stop_id=='5486' and start_end_ids==(20197,20208)) else 0)
            
            # hack: stop 3670 goes to the wrong side of the street.  it should be EB not WB
            score += (-10 if (stop_id=='3670' and close_tuple[0].getDirection() == dta.RoadLink.DIR_WB) else 0)
            
            # hack: stop 7554 goes to the wrong side of the street.  it should be EB not WB
            score += (-10 if (stop_id=='7554' and close_tuple[0].getDirection() == dta.RoadLink.DIR_WB) else 0)
            
            # hack: stop 5247 goes to the wrong side of the street.  it should be SB not NB
            score += (-10 if (stop_id=='5247' and close_tuple[0].getDirection() == dta.RoadLink.DIR_NB) else 0)
            
            # hack: stop 7269 goes to the wrong side of the street.  it should be EB not WB
            score += (-10 if (stop_id=='7269' and close_tuple[0].getDirection() == dta.RoadLink.DIR_NB) else 0)            

            # hack: stop 2026 goes to the wrong side of the street.  it should be NB not SB
            score += (-10 if (stop_id=='2026' and close_tuple[0].getDirection() == dta.RoadLink.DIR_SB) else 0)            

            # hack: stop 3210 goes to the wrong side of the street.  it should be SB not NB
            score += (-10 if (stop_id=='3210' and close_tuple[0].getDirection() == dta.RoadLink.DIR_NB) else 0)     
                        
            # hack: stop 6781 goes to the wrong side of the street.  it should be WB not EB
            score += (-10 if (stop_id=='6781' and close_tuple[0].getDirection() == dta.RoadLink.DIR_EB) else 0)     

            # hack: stop 5878 goes to the wrong side of the street.  it should be EB not WB
            score += (-10 if (stop_id=='5878' and close_tuple[0].getDirection() == dta.RoadLink.DIR_WB) else 0)  
            
            scores.append(score)
        
        # select best score
        max_score = max(scores)
        max_score_idx = scores.index(max_score)
        
        # debug
        dta.DtaLogger.debug("stop %s %s" % (stop['stop_id'], stop['stop_name']))
        if max_score_idx > 0:
            dta.DtaLogger.debug(" -> Falling back to secondary link %d" % closest_tuples[max_score_idx][0].getId())
        
        # this is noisy
        for idx in range(len(scores)):
            dta.DtaLogger.debug("  link %7d (-30%s) score=%d" % (closest_tuples[idx][0].getId(),
                                                                 closest_tuples[idx][0].getLabel(),
                                                                 scores[idx]))

        stopid_to_link[stop['stop_id']] = (x,y,stop['stop_name'],
                                           closest_tuples[max_score_idx][0],
                                           closest_tuples[max_score_idx][1],
                                           closest_tuples[max_score_idx][2])
        
    if len(stopid_to_link) % 500 == 0:
        dta.DtaLogger.info("%5d stop ids mapped" % len(stopid_to_link))

def writeStopsShpFile(stopid_to_link, shapefilename):
    """
    Write stops to *shapefilename* for debugging.
    
    * *stoplist* is a list of transitfeed stops
    * *stopid_to_link* is a map of { stopid -> (x, y, roadlink, distance, portion_along_link) }
       from :py:func:`mapStopIdToLink`
    
    """
    import shapefile
    shp = shapefile.Writer(shapefile.POINT)
    shp.field("stop_id",     "N", 10)
    shp.field("stop_name",   "C", 30)
    shp.field("nearlink",    "N", 10)
    shp.field("linkdist",    "N", 15, 4)
    shp.field("linkt",       "N", 12, 8)
    
    for stopid in stopid_to_link.keys():
        
        # (x, y, stopname, roadlink, distance, portion_along_link)
        shp.point(stopid_to_link[stopid][0], stopid_to_link[stopid][1])
        shp.record(stopid, stopid_to_link[stopid][2],
                   stopid_to_link[stopid][3].getId() if stopid_to_link[stopid][3] else -1,
                   "%15.4f" % stopid_to_link[stopid][4] if stopid_to_link[stopid][3] else 0,
                   "%12.8f" % stopid_to_link[stopid][5] if stopid_to_link[stopid][3] else 0)
        
    shp.save(shapefilename)
    dta.DtaLogger.info("Wrote GTFS stops to shapefile %s" % shapefilename)

def defineLinesShpFile():
    """
    Defines the fields in the transit line shapefile.  For use with :py:func:`writeLineToShapefile`.
    """
    import shapefile
    shp = shapefile.Writer(shapefile.POLYLINE)
    shp.field("route", "C", 50) # label + headsign
    shp.field("lineid","N", 10)
    return shp

def writeLineToShapefile(shp, transitline):
    """
    *shp* is the shapefile object from :py:func:`defineLinesShpFile`
    *transitline* is an instance of :py:class:`TransitLine`.
    """
    
    seg_points = []
    for segment in transitline.iterSegments():
        seg_points.extend(segment.link.getCenterLine(wholeLineShapePoints=True))
    shp.line(parts=[seg_points])
    
    label_parts = transitline.label.split("_")
    label_parts.pop() # forget the route id, trip id
    label_parts.pop()
    shp.record("_".join(label_parts), transitline.id)
    
    
if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], "l:s:")

    if len(args) != 3:
        print USAGE
        sys.exit(2)

    import transitfeed

    INPUT_DYNAMEQ_NET_DIR         = args[0]
    INPUT_DYNAMEQ_NET_PREFIX      = args[1]
    GTFS_ZIP                      = args[2]

    OUTPUT_STOP_SHAPEFILE       = None
    OUTPUT_LINK_SHAPEFILE       = None    
    for (opt,arg) in optlist:
        if opt=="-s":
            OUTPUT_STOP_SHAPEFILE  = arg
        if opt=="-l":
            OUTPUT_LINK_SHAPEFILE  = arg

    GTFS_ROUTE_TYPE_TO_LINE_TYPE = \
    {"Bus":         dta.TransitLine.LINE_TYPE_BUS,
     "Cable Car":   dta.TransitLine.LINE_TYPE_TRAM,
     "Tram":        dta.TransitLine.LINE_TYPE_TRAM
     }
    GTFS_ROUTE_TYPE_TO_VTYPE = \
    {"Bus":         "Motor_Std",
     "Cable Car":   "CableCar",
     "Tram":        "LRT2"
    }
    

    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"

    dta.setupLogging("importGTFS.INFO.log", "importGTFS.DEBUG.log", logToConsole=True)

    scenario = dta.DynameqScenario()
    scenario.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX) 
    net = dta.DynameqNetwork(scenario)
    net.read(INPUT_DYNAMEQ_NET_DIR, INPUT_DYNAMEQ_NET_PREFIX)
    
    tfl = transitfeed.Loader(feed_path=GTFS_ZIP)
    schedule = tfl.Load()
    dta.DtaLogger.info("Read %s" % GTFS_ZIP)
            
    # Get the ServicePeriod we're interested in - we want weekday service
    service_period_tuples = schedule.GetServicePeriodsActiveEachDate(datetime.date(2012,7,10), datetime.date(2012,7,12))
    service_period = service_period_tuples[0][1][0]
    # for now, we only support one
    for (date,sps) in service_period_tuples:
        assert(len(sps) == 1)
        assert(sps[0] == service_period)
    dta.DtaLogger.info("Filtering trips to those with service id %s" % service_period.service_id)
    
    # open the output file for writing
    output_filename = os.path.join(INPUT_DYNAMEQ_NET_DIR, "sf_trn_ptrn.dqt")
    output_file = open(output_filename,mode="w+")
    output_file.write(dta.TransitLine.getDynameqFileHeaderStr())

    # iterate through the routes -- first, determine a sort order
    route_list = schedule.GetRouteList()
    route_labels = []
    for route in route_list:
        route_label = route['route_short_name'].strip() + " " + route['route_long_name'].strip()
        route_labels.append(route_label)
    

    # We could read the override file but we need this one
    #              rom Dir, From,        Over,        To Dir,    To St,          desig,    [permission],[lanes]
    overrides = [ ["EB",    "Market St","Sansome St","NB",      "Sansome St",   "LT",      "Transit"] ]
    net.setMovementTurnTypeOverrides(overrides)
    
    # Do this in a two-phase way -- first, we have to do all of our split links
    # Then, we actually create the transit lines
    # If we create the transit lines as we go along, a line that causes a split link later in the
    # list will invalidate the transit lines that traversed that link already
    for phase in ["splitlink", "createtransit"]:
        
        # iterate through the routes
        stopid_to_link = {}  # we'll fill this twice. it feels wasteful but splitting links could invalidate some

        if phase == "createtransit":
            line_shp = defineLinesShpFile()  # do the shapefile during the createtransit phase
            line_shp_done = set()            # (route_label, trip_headsign)        

        for route_label in sorted(route_labels):
            
            # iterate through the trips and find those for this route
            trip_list = schedule.GetTripList()
            for trip in trip_list:
                            
                # skip if irrelevant service period
                if trip['service_id'] != service_period.service_id: continue
                route_id = trip['route_id']
                route = schedule.GetRoute(route_id)
                
                # only do the trips for the given route_label
                trip_route_label = route['route_short_name'].strip() + " " + route['route_long_name'].strip()
                if trip_route_label != route_label: continue
        
                # create the transit line
                label = "%s_%s_route%s_trip%s" % (route_label, trip['trip_headsign'], route_id, trip['trip_id'])
                transit_line_id = int(trip['trip_id']) # try this even though they're not sequential
                stoptimes = trip.GetStopTimes()
                line_departure = dta.Time.fromSeconds(stoptimes[0].GetTimeSecs())
                
                # Skip if it's not running during simulation time
                if line_departure > scenario.endTime: continue
                if line_departure < scenario.startTime: continue
                
                route_type_str = transitfeed.Route._ROUTE_TYPES[int(route['route_type'])]['name']
                # for now, skip LRT because they run off-street and we don't handle that yet
                if route_type_str == "Tram": continue
                                        
                dta.DtaLogger.debug("Processing %s (%s)" % (label, route_type_str))
                
                if phase == "createtransit":
                    dta_transit_line = dta.TransitLine(net, id=transit_line_id,
                                                       label=label,
                                                       litype=GTFS_ROUTE_TYPE_TO_LINE_TYPE[route_type_str],
                                                       vtype=GTFS_ROUTE_TYPE_TO_VTYPE[route_type_str],
                                                       stime=line_departure,
                                                       level=0,
                                                       active=dta.TransitLine.LINE_ACTIVE,
                                                       hway=60*6, #run once -- make this cleaner
                                                       dep=1)
                                                               
                prev_roadlink = None
                prev_stopid   = None
                for stoptime in stoptimes:
                    
                    stopid = stoptime.stop['stop_id']
                    
                    # curious - not sure why this should happen but it does with Trip 5141123 Stop 5245
                    if stopid == prev_stopid: continue
                    
                    addStopIdToLinkToDict(stoptime.stop, net, stopid_to_link) # lazy updating
                    stop_roadlink = stopid_to_link[stopid][3]
                    
                    if stop_roadlink == None:
                        # todo handle this better
                        continue
                    
                    # split link phase: split if the previous stop's roadlink is the same as
                    # this stop's road link
                    if phase == "splitlink" and prev_roadlink == stop_roadlink:
                        fraction = 0.5*(stopid_to_link[prev_stopid][5] + stopid_to_link[stopid][5])
                        dta.DtaLogger.debug("Two stops (%s %s) on trip %s on link %d (%d-%d)! splitting @ %f  shapepoints=%d" % 
                                            (prev_stopid, stopid, label,
                                             prev_roadlink.getId(), 
                                             prev_roadlink.getStartNode().getId(), 
                                             prev_roadlink.getEndNode().getId(),
                                             fraction, prev_roadlink.getNumShapePoints()))
                        dta.DtaLogger.debug("Old link centerline = %s" % str(stop_roadlink.getCenterLine(wholeLineShapePoints = True)))
                        
                        # split the link
                        start_node  = stop_roadlink.getStartNode()
                        end_node    = stop_roadlink.getEndNode()
                        midnode     = net.splitLink(linkToSplit=stop_roadlink,splitReverseLink=True, fraction=fraction)
                        # the prev_roadlink is now the first half - update that one
                        prev_roadlink = net.getLinkForNodeIdPair(start_node.getId(), midnode.getId())
                        old_tuple     = stopid_to_link[prev_stopid]
                        new_distinfo  = prev_roadlink.getDistanceFromPoint(old_tuple[0], old_tuple[1])
                        # update (x, y, stopname, roadlink, distance, portion_along_link)
                        stopid_to_link[prev_stopid] = (old_tuple[0], old_tuple[1], old_tuple[2],
                                                       prev_roadlink, new_distinfo[0], new_distinfo[1])
                        
                        # associate this one to the second half
                        stop_roadlink = net.getLinkForNodeIdPair(midnode.getId(), end_node.getId())
                        old_tuple     = stopid_to_link[stopid]
                        new_distinfo  = stop_roadlink.getDistanceFromPoint(old_tuple[0], old_tuple[1])
                        stopid_to_link[stopid] = (old_tuple[0], old_tuple[1], old_tuple[2],
                                                  stop_roadlink, new_distinfo[0], new_distinfo[1])
                        
                        dta.DtaLogger.debug("New links are %d and %d" % (prev_roadlink.getId(), stop_roadlink.getId()))
                        dta.DtaLogger.debug("  centerline for %d (%d): %s" %
                                            (prev_roadlink.getId(), prev_roadlink.getNumShapePoints(),
                                             str(prev_roadlink.getCenterLine(wholeLineShapePoints = True))))
                        dta.DtaLogger.debug("  centerline for %d (%d): %s" %
                                            (stop_roadlink.getId(), stop_roadlink.getNumShapePoints(),
                                             str(stop_roadlink.getCenterLine(wholeLineShapePoints = True))))
                        
                    # createtransit phase: connect this stoplink from previous stoplink
                    if phase == "createtransit" and prev_roadlink:
                        
                        if prev_roadlink == stop_roadlink:
                            error = "create transit but two stops (%s %s) on trip %s are still on the same link %d (%d-%d)" % \
                                    (prev_stopid, stopid, label,
                                     prev_roadlink.getId(), prev_roadlink.getStartNode().getId(), prev_roadlink.getEndNode().getId())
                            dta.DtaLogger.fatal(error)
                            raise dta.DtaError(error)
                        
                        # shortest path connecting stop links
                        try:
                            dta.ShortestPaths.labelSettingWithLabelsOnNodes(net, 
                                                                            prev_roadlink.getEndNode(), 
                                                                            stop_roadlink.getStartNode())
                            path_nodes = dta.ShortestPaths.getShortestPathBetweenNodes(prev_roadlink.getEndNode(), 
                                                                                       stop_roadlink.getStartNode())
            
                        except:
                            dta.DtaLogger.error("Error: %s" % str(sys.exc_info()))
                            dta.DtaLogger.error("route %-25s No shortest path found from %d to %d" %
                                               (label, prev_roadlink.getEndNode().getId(), stop_roadlink.getStartNode().getId()))
                            continue
                        
                        node_num_list = [ prev_roadlink.getEndNode().getId() ]
                        for path_node_A, path_node_B in itertools.izip(path_nodes, path_nodes[1:]):
                            node_num_list.append(path_node_B.getId())
                            newlink = net.getLinkForNodeIdPair(path_node_A.getId(), path_node_B.getId())
                            newseg  = dta_transit_line.addSegment(newlink, 0, label="nostop")
        
                    # add this link
                    if phase == 'createtransit':
                        dta_transit_line.addSegment(stop_roadlink,
                                                    label="%s,%5.4f" % (stopid, stopid_to_link[stopid][5]),
                                                    lane=dta.TransitSegment.TRANSIT_LANE_UNSPECIFIED,
                                                    dwell=15, # todo: put in a better default
                                                    stopside=dta.TransitSegment.STOP_OUTSIDE)
                    prev_roadlink = stop_roadlink
                    prev_stopid   = stopid
        
                # check if the movements are allowed
                if phase=="createtransit":
                    dta_transit_line.checkMovementsAreAllowed(enableMovement=True)
                    
                    output_file.write(dta_transit_line.getDynameqStr())
                
                    # only once per (route_label, trip_headsign)
                    if (route_label, trip['trip_headsign']) not in line_shp_done:
                        writeLineToShapefile(line_shp, dta_transit_line)
                        line_shp_done.add( (route_label, trip['trip_headsign']) )

        if phase=="splitlink" and OUTPUT_LINK_SHAPEFILE:
            net.writeLinksToShp(OUTPUT_LINK_SHAPEFILE)
            
    output_file.close()

    net.write(".", "sf_trn")

    dta.DtaLogger.info("Wrote %8d %-16s to %s" % (transit_line_id-1, "TRANSIT LINES", output_filename))
 
    # write the lines shapefile
    line_shp.save("sf_gtfs_lines")
    dta.DtaLogger.info("Wrote GTFS lines to shapefile sf_gtfs_lines.shp")
    
    if OUTPUT_STOP_SHAPEFILE:
        writeStopsShpFile(stopid_to_link, OUTPUT_STOP_SHAPEFILE)
