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
    

USAGE = r"""

 python attachCountsFromCountDracula.py [-l links.shp] [-m movements.shp] [-n nodes.shp] dynameq_net_dir dynameq_net_prefix
 
 e.g.
 
 python attachCountsFromCountDracula.py . sf
 

 Checks the CountDracula counts database for movement and turn counts for a few different
 timeslice specifications, and writes the data files for Dynameq into the current dir.
"""


import dta
import datetime
import getopt
import os
import sys
import xlwt

# global
STYLE_REG  = xlwt.easyxf('font: name Calibri')
STYLE_BOLD = xlwt.easyxf('font: name Calibri, bold on')
STYLE_TIME = xlwt.easyxf('font: name Calibri', num_format_str='hh:mm')
STYLE_DATE = xlwt.easyxf('font: name Calibri', num_format_str='yyyy-mm-dd hh:mm ddd')
STYLE_DATE.alignment = xlwt.Alignment()
STYLE_DATE.alignment.horz = xlwt.Alignment.HORZ_LEFT

def findDtaMovementForTurnCountLocation(sanfranciscoDynameqNet, turn_count_location):
    """
    Finds the DTA Movement for the given turn_count_location (a CountDracula TurnCountLocation instance).
    
    Returns None on failure; returns the Movement instance on success.
    """

    try:
        movement = sanfranciscoDynameqNet.findMovementForRoadLabels(incoming_street_label   = turn_count_location.from_street.nospace_name,
                                                                    incoming_direction      = turn_count_location.from_dir,
                                                                    outgoing_street_label   = turn_count_location.to_street.nospace_name,
                                                                    outgoing_direction      = turn_count_location.to_dir,
                                                                    intersection_street_label=turn_count_location.intersection_street.nospace_name,
                                                                    roadnode_id             = turn_count_location.intersection.id,
                                                                    remove_label_spaces     = True,
                                                                    use_dir_for_movement    = False, # use labels
                                                                    dir_need_not_be_primary = True)
        dta.DtaLogger.debug("Found movement %8d %8d" % (movement.getIncomingLink().getId(), movement.getOutgoingLink().getId()))
        return movement
    
    except dta.DtaError, e:
        dta.DtaLogger.warn("Failed to find movement @ %s: %s" % (str(turn_count_location), str(e))) 
      

    try:
        movement = sanfranciscoDynameqNet.findMovementForRoadLabels(incoming_street_label   = turn_count_location.from_street.nospace_name,
                                                                    incoming_direction      = turn_count_location.from_dir,
                                                                    outgoing_street_label   = turn_count_location.to_street.nospace_name,
                                                                    outgoing_direction      = turn_count_location.to_dir,
                                                                    intersection_street_label=turn_count_location.intersection_street.nospace_name,
                                                                    roadnode_id             = turn_count_location.intersection.id,
                                                                    remove_label_spaces     = True,
                                                                    use_dir_for_movement    = True,  # use directions over labels
                                                                    dir_need_not_be_primary = False) # keep it tighter tho

        dta.DtaLogger.warn("Found movement by loosening label constraints: %s %s to %s %s" % 
                           (movement.getIncomingLink().getLabel(), movement.getIncomingLink().getDirection(),
                            movement.getOutgoingLink().getLabel(), movement.getOutgoingLink().getDirection()))
        dta.DtaLogger.debug(" %8d %8d" % (movement.getIncomingLink().getId(), movement.getOutgoingLink().getId()))
        return movement
        
    except dta.DtaError, e:
        dta.DtaLogger.error("Failed to find movement @ %s: %s" % (str(turn_count_location), str(e)))                  

    return None
                
def exportTurnCountsToDynameqUserDataFile(sanfranciscoDynameqNet, starttime, period, num_intervals,
                                               suffix, from_year=None, to_year=None, weekdays=None,
                                               all_count_workbook=None):
    """
    Exports turn counts from CountDracula database and exports them to a Dynameq movement user data file.
    
    * *cd_reader* is a CountDraculaReader instance where the counts are stored
    * *sanfranciscoDynameqNet* is a :py:class:`Network` instance for looking up the relevant nodes for the output file
    * *starttime* is a datetime.time instance defining the start time for the counts we'll extract
    * *period* is a datetime.timedelta instance defining the duration of each time slice (e.g. 15-minute counts)
    * *num_intervals* is an integer defining how many intervals we'll export
    * *suffix* is an optional suffix for the file name (something descriptive)
    * *from_year* is a datetime.date instance defining the start date (inclusive) of acceptable count dates
    * *to_year* is a datetime.date instance defining the end date (inclusive) of acceptable count dates
    * If *weekdays* is passed (a list of integers, where Sunday is 1 and Saturday is 7), then counts will
      only include the given weekdays.
    * If *all_count_workbook* is passed (it should be an xlwt.Workbook) then the raw data will be added
      to a sheet there as well.
            
    Writes to a file called ``counts_movements_Xmin_Y_Z_suffix.dat`` where X is the number of minutes in the period, Y is the starttime and Z is
    the endtime; e.g. counts_movements_15min_1600_1830_suffix.dat
    """    
    endtime         = datetime.datetime.combine(datetime.date(2000,1,1), starttime) + (num_intervals*period)
    filename        = "counts_movements_%dmin_%s_%s%s.dat" % (period.seconds/60, 
                                                              starttime.strftime("%H%M"), endtime.strftime("%H%M"),
                                                              "_%s" % suffix if suffix else "")
    
    kwargs = {'period_minutes': int(period.total_seconds()/60)}
    if from_year: 
        kwargs['count_year__gte'] = from_year
    if to_year:
        kwargs['count_year__lte'] = to_year
    # I don't know why this one fails
    # I get django.core.exceptions.FieldError: Join on field 'count_date' not permitted. Did you misspell 'week_day' for the lookup type?
    #if weekdays:
    #    kwargs['count_date__week_day__in'] = weekdays
    
    # file header (comments)
    outfile         = open(filename, "w")
    outfile.write("* mainline_counts\n")
    outfile.write("* domain: Movements\n")
    outfile.write("* script: %s\n" % sys.argv[0])
    outfile.write("* starttime: %s\n" % starttime.strftime("%H:%M"))
    outfile.write("* period: %d min\n" % (period.seconds/60))
    outfile.write("* num_intervals: %d\n" % num_intervals)
    outfile.write("* date_range: %s - %s\n" % (str(from_year), str(to_year)))
    outfile.write("* weekdays: %s\n" % str(weekdays))
    outfile.write("* CREATED %s\n" % datetime.datetime.now().ctime())
    outfile.write("*%8s %8s %8s" % ("at","start","end"))

    if all_count_workbook:
        sheet = all_count_workbook.add_sheet("movavg_%s_%d" % (suffix, period.seconds/60))
        # header row
        row_num = 0
        sheet.write(row_num,0, "from-at-to",    STYLE_BOLD) # for joins
        sheet.write(row_num,1, "fromstreet",    STYLE_BOLD)
        sheet.write(row_num,2, "fromdir",       STYLE_BOLD)
        sheet.write(row_num,3, "tostreet",      STYLE_BOLD)
        sheet.write(row_num,4, "todir",         STYLE_BOLD)

        sheet.panes_frozen      = True
        sheet.horz_split_pos    = 1
        sheet.col(0).width      = 23*256
        sheet.col(1).width      = 15*256
        sheet.col(3).width      = 15*256

    for interval in range(num_intervals):
        curtime     = datetime.datetime.combine(datetime.date(2000,1,1), starttime) + (interval*period)
        outfile.write("  %s" % curtime.strftime("%H:%M"))
        if all_count_workbook: sheet.write(row_num, 5+interval, curtime, STYLE_TIME)
        
    outfile.write("\n")

    # For each movement count, see if we can find the right place for it in the sanfranciscoDynameqNet    
    location_id_to_movement = {} # CountDracula location id to dta.Movement
    location_ids            = [] # list of location ids in the worksheet/output file
    movement_counts         = [] # query sets from count dracula, indexed by interval
    
    # first, build out location_id_to_movement, location_ids and movement_counts
    for interval in range(num_intervals):

        # query
        kwargs['start_time'] = datetime.datetime.combine(datetime.date(2000,1,1), starttime) + (interval*period)
        
        qs = TurnCount.objects.filter(**kwargs).order_by('location')
        if weekdays:
            for weekday in range(1,8):
                if weekday not in weekdays: qs = qs.exclude(count_date__week_day=weekday)
        movement_counts.append(qs)
        
        for count in movement_counts[-1]:
            
            # find the DTA movement for this location, if we haven't done so already
            if count.location.id not in location_id_to_movement:
                location_id_to_movement[count.location.id] = findDtaMovementForTurnCountLocation(sanfranciscoDynameqNet, count.location)

            # don't include the ones we couldn't map
            if location_id_to_movement[count.location.id] != None and count.location.id not in location_ids:
                location_ids.append(count.location.id)

    # now we're ready for output
    for location_id in location_ids:

        # movement found -- write it out
        outfile.write(" %8d %8d %8d" % (location_id_to_movement[location_id].getAtNode().getId(), 
                                        location_id_to_movement[location_id].getStartNode().getId(),
                                        location_id_to_movement[location_id].getEndNode().getId()))

        # workbook version
        if all_count_workbook:
            row_num += 1
            sheet.write(row_num, 0, "%d %d %d" % (location_id_to_movement[location_id].getStartNode().getId(),
                                                  location_id_to_movement[location_id].getAtNode().getId(),
                                                  location_id_to_movement[location_id].getEndNode().getId()), STYLE_REG)
            sheet.write(row_num, 1, location_id_to_movement[location_id].getIncomingLink().getLabel(),      STYLE_REG) # from street
            sheet.write(row_num, 2, location_id_to_movement[location_id].getIncomingLink().getDirection(),  STYLE_REG) # from dir
            sheet.write(row_num, 3, location_id_to_movement[location_id].getOutgoingLink().getLabel(),      STYLE_REG) # to street
            sheet.write(row_num, 4, location_id_to_movement[location_id].getOutgoingLink().getDirection(),  STYLE_REG) # to dir
            
        for interval in range(num_intervals):
            agg_count_dict = movement_counts[interval].filter(location__id=location_id).aggregate(Avg('count'), Count('count'))
            if 'count__avg' in agg_count_dict and agg_count_dict['count__avg'] != None:
                avg_count = agg_count_dict['count__avg']
            elif agg_count_dict['count__count'] > 0:
                avg_count = 0.0
            else:
                avg_count = -1.0
            
            outfile.write(" %6.1f" % avg_count)
            
            # workbook version
            if all_count_workbook: sheet.write(row_num, 5+interval, avg_count, STYLE_REG)

        outfile.write("\n")
            
    outfile.close()
    dta.DtaLogger.info("Wrote movement counts for %d movements to %s; failed to find %d movements." % 
                       (len(location_ids), filename, len(location_id_to_movement)-len(location_ids)))
    
    # if we're not doing the raw workbook then we're done
    if not all_count_workbook: return
    
    # write raw data into workbook
    sheet = all_count_workbook.add_sheet("movements_%s_%d" % (suffix, period.seconds/60))

    # header row
    row_num = 0
    # dta location data        
    sheet.write(row_num,0, "from-at-to",    STYLE_BOLD) # for joins
    sheet.write(row_num,1, "at-node",       STYLE_BOLD)
    sheet.write(row_num,2, "from-node",     STYLE_BOLD)
    sheet.write(row_num,3, "to-node",       STYLE_BOLD)
    sheet.write(row_num,4, "from_link",     STYLE_BOLD)
    sheet.write(row_num,5, "to_link",       STYLE_BOLD)
    # count dracula location data - fromstreet, fromdir, tostreet, todir
    sheet.write(row_num,6, "fromstreet",    STYLE_BOLD)
    sheet.write(row_num,7, "fromdir",       STYLE_BOLD)
    sheet.write(row_num,8, "tostreet",      STYLE_BOLD)
    sheet.write(row_num,9, "todir",         STYLE_BOLD)
    # count data, count = [ count, starttime, period, vtype, sourcefile, project ]
    sheet.write(row_num,10,"count",         STYLE_BOLD)
    sheet.write(row_num,11,"starttime",     STYLE_BOLD)
    sheet.write(row_num,12,"year",          STYLE_BOLD) # for ease of trends analysis
    sheet.write(row_num,13,"allyears",      STYLE_BOLD) # for ease of trends analysis        
    sheet.write(row_num,14,"time",          STYLE_BOLD) # for ease of trends analysis
    sheet.write(row_num,15,"period (min)",  STYLE_BOLD)
    sheet.write(row_num,16,"vtype",         STYLE_BOLD)
    sheet.write(row_num,17,"sourcefile",    STYLE_BOLD)
    sheet.write(row_num,18,"project",       STYLE_BOLD)

    sheet.panes_frozen      = True
    sheet.horz_split_pos    = 1
    sheet.col(0).width      = 23*256
    sheet.col(11).width     = 23*256
    
    for location_id in location_ids:

        for interval in range(num_intervals):

            movement_counts_for_location = movement_counts[interval].filter(location__id=location_id)

            # figure out multiyear
            count_years = set()
            for movement_count in movement_counts_for_location: count_years.add(movement_count.count_year)
            
            for movement_count in movement_counts_for_location:
                # data row
                row_num += 1
                # dta location data                        
                sheet.write(row_num,0, "%d %d %d" % (location_id_to_movement[location_id].getStartNode().getId(), 
                                                     location_id_to_movement[location_id].getAtNode().getId(),
                                                     location_id_to_movement[location_id].getEndNode().getId()), STYLE_REG)
                sheet.write(row_num,1, location_id_to_movement[location_id].getAtNode().getId(),        STYLE_REG)
                sheet.write(row_num,2, location_id_to_movement[location_id].getStartNode().getId(),     STYLE_REG)
                sheet.write(row_num,3, location_id_to_movement[location_id].getEndNode().getId(),       STYLE_REG)
                sheet.write(row_num,4, location_id_to_movement[location_id].getIncomingLink().getId(),  STYLE_REG)
                sheet.write(row_num,5, location_id_to_movement[location_id].getOutgoingLink().getId(),  STYLE_REG)
                # count dracula location data - fromstreet, fromdir, tostreet, todir
                sheet.write(row_num,6, location_id_to_movement[location_id].getIncomingLink().getLabel(),       STYLE_REG)
                sheet.write(row_num,7, location_id_to_movement[location_id].getIncomingLink().getDirection(),   STYLE_REG)
                sheet.write(row_num,8, location_id_to_movement[location_id].getOutgoingLink().getLabel(),       STYLE_REG)
                sheet.write(row_num,9, location_id_to_movement[location_id].getOutgoingLink().getDirection(),   STYLE_REG)
                # count, starttime, year, allyears, time, period (min), vtype, sourcefile, project   
                sheet.write(row_num,10, movement_count.count,               STYLE_REG)
                sheet.write(row_num,11, datetime.datetime.combine(movement_count.count_date, movement_count.start_time), STYLE_DATE)
                sheet.write(row_num,12, movement_count.count_date.year,     STYLE_REG)
                sheet.write(row_num,13, str(sorted(count_years)),           STYLE_REG)                
                sheet.write(row_num,14, movement_count.start_time,          STYLE_TIME)
                sheet.write(row_num,15, movement_count.period_minutes,      STYLE_REG)
                sheet.write(row_num,16, movement_count.vehicle_type,        STYLE_REG)
                sheet.write(row_num,17, movement_count.sourcefile,          STYLE_REG)
                sheet.write(row_num,18, movement_count.project,             STYLE_REG)

def findDtaLinkForMainlineCountLocation(sanfranciscoDynameqNet, mainline_count_location):
    """
    Finds the DTA RoadLink for the given mainline_count_location (a CountDracula MainlineCountLocation instance).
    
    Returns None on failure; returns the RoadLink instance on success.
    """
    try:
        links = sanfranciscoDynameqNet.findLinksForRoadLabels(on_street_label       = mainline_count_location.on_street.nospace_name,
                                                              on_direction          = mainline_count_location.on_dir,
                                                              from_street_label     = mainline_count_location.from_street.nospace_name,
                                                              to_street_label       = mainline_count_location.to_street.nospace_name,
                                                              remove_label_spaces   = True)
        dta.DtaLogger.debug("Found %d links: %s" % (len(links), str(links)))
        # return the first
        return links[0]
    except dta.DtaError, e:
        dta.DtaLogger.error("Failed to find links for %s: %s" % (str(e), str(mainline_count_location)))
        return None
    
    

def exportMainlineCountsToDynameUserDataFile(sanfranciscoDynameqNet, starttime, period, num_intervals,
                                                   suffix=None, from_year=None, to_year=None, weekdays=None,
                                                   all_count_workbook=None):
    """
    Exports mainline counts from CountDracula database and exports them to a Dynameq link user data file.
    
    * *cd_reader* is a CountDraculaReader instance where the counts are stored
    * *sanfranciscoDynameqNet* is a :py:class:`Network` instance for looking up the relevant nodes for the output file    
    * *starttime* is a datetime.time instance defining the start time for the counts we'll extract
    * *period* is a datetime.timedelta instance defining the duration of each time slice (e.g. 15-minute counts)
    * *num_intervals* is an integer defining how many intervals we'll export
    * *suffix* is an optional suffix for the file name (something descriptive)
    * *from_year* is a datetime.date instance defining the start date (inclusive) of acceptable count dates
    * *to_year* is a datetime.date instance defining the end date (inclusive) of acceptable count dates
    * If *weekdays* is passed (a list of integers, where Monday is 0 and Sunday is 6), then counts will
      only include the given weekdays.
    * If *all_count_workbook* is passed (it should be an xlwt.Workbook) then the raw data will be added
      to a sheet there as well.
          
    Writes to a file called ``counts_links_Xmin_Y_Z.dat`` where X is the number of minutes in the period, Y is the starttime and Z is
    the endtime; e.g. counts_links_15min_1600_1830.dat
    """
    endtime         = datetime.datetime.combine(datetime.date(2000,1,1), starttime) + (num_intervals*period)
    filename        = "counts_links_%dmin_%s_%s%s.dat" % (period.seconds/60, 
                                                          starttime.strftime("%H%M"), 
                                                          endtime.strftime("%H%M"),
                                                          "_%s" % suffix if suffix else "")
    kwargs = {'period_minutes': int(period.total_seconds()/60)}
    if from_year: 
        kwargs['count_year__gte'] = from_year
    if to_year:
        kwargs['count_year__lte'] = to_year    
    
    # file header (comments)
    outfile         = open(filename, "w")
    outfile.write("* mainline_counts\n")
    outfile.write("* domain: Links\n")
    outfile.write("* script: %s\n" % sys.argv[0])
    outfile.write("* starttime: %s\n" % starttime.strftime("%H:%M"))
    outfile.write("* period: %d min\n" % (period.seconds/60))
    outfile.write("* num_intervals: %d\n" % num_intervals)
    outfile.write("* date_range: %s - %s\n" % (str(from_year), str(to_year)))
    outfile.write("* weekdays: %s\n" % str(weekdays))
    outfile.write("* CREATED %s\n" % datetime.datetime.now().ctime())
    outfile.write("*%8s %8s" % ("from","to"))
    
    if all_count_workbook:
        sheet = all_count_workbook.add_sheet("linkavg_%s_%d" % (suffix, period.seconds/60))
        # header row
        row_num = 0
        sheet.write(row_num,0, "from-to",       STYLE_BOLD) # for joins
        sheet.write(row_num,1, "onstreet",      STYLE_BOLD)
        sheet.write(row_num,2, "ondir",         STYLE_BOLD)
        sheet.write(row_num,3, "fromstreet",    STYLE_BOLD)
        sheet.write(row_num,4, "tostreet",      STYLE_BOLD)

        sheet.panes_frozen      = True
        sheet.horz_split_pos    = 1
        sheet.col(0).width      = 15*256
        sheet.col(1).width      = 15*256
        sheet.col(3).width      = 15*256
        
    for interval in range(num_intervals):
        curtime     = datetime.datetime.combine(datetime.date(2000,1,1), starttime) + (interval*period)
        outfile.write("  %s" % curtime.strftime("%H:%M"))
        if all_count_workbook: sheet.write(row_num, 5+interval, curtime, STYLE_TIME)
    outfile.write("\n")

    # For each movement count, see if we can find the right place for it in the sanfranciscoDynameqNet    
    location_id_to_link     = {} # CountDracula location id to dta.Link
    location_id_to_location = {} # CountDracula location id to CountDracula location
    location_ids            = [] # list of location ids in the worksheet/output file
    link_counts             = [] # query sets from CountDracula, indexed by interval

    # first, build out location_id_to_link, location_ids and link_counts
    for interval in range(num_intervals):

        # query
        kwargs['start_time'] =  datetime.datetime.combine(datetime.date(2000,1,1), starttime) + (interval*period)
        
        qs = MainlineCount.objects.filter(**kwargs).order_by('location')
        if weekdays:
            for weekday in range(1,8):
                if weekday not in weekdays: qs = qs.exclude(count_date__week_day=weekday)
        link_counts.append(qs)
        
        for count in link_counts[-1]:
            
            # find the DTA link for this location, if we haven't done so already
            if count.location.id not in location_id_to_link:
                location_id_to_link[count.location.id] = findDtaLinkForMainlineCountLocation(sanfranciscoDynameqNet, count.location)
                location_id_to_location[count.location.id] = count.location
                
            # don't include the ones we couldn't map
            if location_id_to_link[count.location.id] != None and count.location.id not in location_ids:
                location_ids.append(count.location.id)

    # now we're ready for output
    for location_id in location_ids:
    
        # link found -- write it out
        outfile.write(" %8d %8d" % (location_id_to_link[location_id].getStartNode().getId(), location_id_to_link[location_id].getEndNode().getId()))

        # workbook version
        if all_count_workbook:
            row_num += 1
            sheet.write(row_num, 0, "%d %d" % (location_id_to_link[location_id].getStartNode().getId(), location_id_to_link[location_id].getEndNode().getId()), STYLE_REG)
            sheet.write(row_num, 1, location_id_to_link[location_id].getLabel(),     STYLE_REG) # onstreet        
            sheet.write(row_num, 2, location_id_to_link[location_id].getDirection(), STYLE_REG) # ondir
            sheet.write(row_num, 3, location_id_to_location[location_id].from_street.street_name, STYLE_REG) # fromstreet
            sheet.write(row_num, 4, location_id_to_location[location_id].to_street.street_name,   STYLE_REG) # tostreet
           
        for interval in range(num_intervals):
            
            agg_count_dict = link_counts[interval].filter(location__id=location_id).aggregate(Avg('count'), Count('count'))

            if 'count__avg' in agg_count_dict and agg_count_dict['count__avg'] != None:
                avg_count = agg_count_dict['count__avg']
            elif agg_count_dict['count__count'] > 0:
                avg_count = 0.0
            else:
                avg_count = -1.0
            
            outfile.write(" %6.1f" % avg_count)
            # workbook version
            if all_count_workbook:
                sheet.write(row_num, 5+interval, avg_count, STYLE_REG)
                            
        outfile.write("\n")
            
    outfile.close()
    dta.DtaLogger.info("Wrote link counts for %d links to %s; failed to find %d links." % 
                       (len(location_ids), filename, len(location_id_to_link)-len(location_ids)))

    # if we're not doing the raw workbook then we're done
    if not all_count_workbook: return
    
    # write raw data into workbook
    sheet = all_count_workbook.add_sheet("links_%s_%d" % (suffix, period.seconds/60))

    # header row
    row_num = 0
    # dta location data
    sheet.write(row_num,0, "from-to",       STYLE_BOLD)
    sheet.write(row_num,1, "from-node",     STYLE_BOLD)
    sheet.write(row_num,2, "to-node",       STYLE_BOLD)
    sheet.write(row_num,3, "linkid",        STYLE_BOLD)
    # count dracula location data
    sheet.write(row_num,4, "onstreet",      STYLE_BOLD)
    sheet.write(row_num,5, "ondir",         STYLE_BOLD)
    sheet.write(row_num,6, "fromstreet",    STYLE_BOLD)
    sheet.write(row_num,7, "tostreet",      STYLE_BOLD)
    # count data, count = [ count, starttime, period, vtype, refpos, sourcefile, project ]
    sheet.write(row_num,8, "count",         STYLE_BOLD)
    sheet.write(row_num,9, "starttime",     STYLE_BOLD)
    sheet.write(row_num,10,"year",          STYLE_BOLD) # for ease of trends analysis
    sheet.write(row_num,11,"allyears",      STYLE_BOLD) # for ease of trends analysis
    sheet.write(row_num,12,"time",          STYLE_BOLD) # for ease of trends analysis
    sheet.write(row_num,13,"period (min)",  STYLE_BOLD)
    sheet.write(row_num,14,"vtype",         STYLE_BOLD)
    sheet.write(row_num,15,"refpos",        STYLE_BOLD)
    sheet.write(row_num,16,"sourcefile",    STYLE_BOLD)
    sheet.write(row_num,17,"project",       STYLE_BOLD)

    sheet.panes_frozen      = True
    sheet.horz_split_pos    = 1
    sheet.col(0).width      = 15*256
    sheet.col(9).width      = 23*256

    for location_id in location_ids:

        for interval in range(num_intervals):

            link_counts_for_location = link_counts[interval].filter(location__id=location_id)

            # figure out multiyear
            count_years = set()
            for link_count in link_counts_for_location: count_years.add(link_count.count_year)
            
            for link_count in link_counts_for_location:
                # data row
                row_num += 1
                # dta location data
                sheet.write(row_num,0, "%d %d" % (location_id_to_link[location_id].getStartNode().getId(), location_id_to_link[location_id].getEndNode().getId()), STYLE_REG)
                sheet.write(row_num,1, location_id_to_link[location_id].getStartNode().getId(),                 STYLE_REG)
                sheet.write(row_num,2, location_id_to_link[location_id].getEndNode().getId(),                   STYLE_REG)
                sheet.write(row_num,3, location_id_to_link[location_id].getId(),                                STYLE_REG)
                # count dracula location data - onstreet, ondir, fromstreet, tostreet
                sheet.write(row_num,4, location_id_to_link[location_id].getLabel(),                  STYLE_REG)
                sheet.write(row_num,5, location_id_to_link[location_id].getDirection(),              STYLE_REG)
                sheet.write(row_num,6, location_id_to_location[location_id].from_street.street_name, STYLE_REG)
                sheet.write(row_num,7, location_id_to_location[location_id].to_street.street_name,   STYLE_REG)
                # count data, starttime, year, allyears, time, period (min), vtype, refpos, sourcefile, project
                sheet.write(row_num,8,  link_count.count,                           STYLE_REG)
                if link_count.count_date == None:
                    sheet.write(row_num,9,  link_count.start_time, STYLE_TIME)
                else:
                    sheet.write(row_num,9,  datetime.datetime.combine(link_count.count_date, link_count.start_time), STYLE_DATE)
                sheet.write(row_num,10, link_count.count_year,                 STYLE_REG)
                sheet.write(row_num,11, str(sorted(count_years)),                   STYLE_REG)
                sheet.write(row_num,12, link_count.start_time,                      STYLE_TIME)
                sheet.write(row_num,13, link_count.period_minutes,                  STYLE_REG)
                sheet.write(row_num,14, link_count.vehicle_type,                    STYLE_REG)
                sheet.write(row_num,15, link_count.reference_position,              STYLE_REG)
                sheet.write(row_num,16, link_count.sourcefile,                      STYLE_REG)
                sheet.write(row_num,17, link_count.project,                         STYLE_REG)

#: this_is_main
if __name__ == '__main__':
    
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geodjango.settings'
    from django.core.management import setup_environ
    from geodjango import settings
    from django.db.models import Avg, Count    
    from countdracula.models import Node, StreetName, MainlineCountLocation, MainlineCount, TurnCountLocation, TurnCount

    optlist, args = getopt.getopt(sys.argv[1:], "l:m:n:")
    
    if len(args) != 2:
        print USAGE
        sys.exit(2)
    
    SF_DYNAMEQ_NET_DIR          = args[0] 
    SF_DYNAMEQ_NET_PREFIX       = args[1]
    
    OUTPUT_LINK_SHAPEFILE       = None
    OUTPUT_MOVE_SHAPEFILE       = None
    OUTPUT_NODE_SHAPEFILE       = None
    
    for (opt,arg) in optlist:
        if opt=="-m":
            OUTPUT_MOVE_SHAPEFILE  = arg
        elif opt=="-l":
            OUTPUT_LINK_SHAPEFILE  = arg
        elif opt=="-n":
            OUTPUT_NODE_SHAPEFILE  = arg
                
    dta.setupLogging("attachCountsFromCountDracula.INFO.log", "attachCountsFromCountDracula.DEBUG.log", logToConsole=True)
    
    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"
        
    # Read the SF scenario and DTA network
    sanfranciscoScenario = dta.DynameqScenario()
    sanfranciscoScenario.read(dir=SF_DYNAMEQ_NET_DIR, file_prefix=SF_DYNAMEQ_NET_PREFIX)
    
    sanfranciscoDynameqNet = dta.DynameqNetwork(scenario=sanfranciscoScenario)
    sanfranciscoDynameqNet.read(dir=SF_DYNAMEQ_NET_DIR, file_prefix=SF_DYNAMEQ_NET_PREFIX)
    
    counts_wb = xlwt.Workbook()
    
    # Instantiate the count dracula reader and do the exports
    # Time slices here are based on what we have available (according to CountDracula's querySanFranciscoCounts.py)
    
    for suffix in ["all", "all_midweek", "recent", "recent_midweek"]:
        from_year   = None
        to_year     = None
        weekdays    = None
        
        # year range
        if suffix.find("recent") >= 0:
            from_year   = 2009
            to_year     = 2014
            
        # weekdays
        if suffix.find("midweek") >= 0:
            weekdays    = [3,4,5] # Tues, Wed, Thurs
            
        dta.DtaLogger.info("Processing %s" % suffix)
        exportTurnCountsToDynameqUserDataFile   (sanfranciscoDynameqNet, starttime=datetime.time(07,00), 
                                                 period=datetime.timedelta(minutes=15), num_intervals=10, 
                                                 suffix=suffix, from_year=from_year, to_year=to_year, weekdays=weekdays,
                                                 all_count_workbook=counts_wb)
        exportTurnCountsToDynameqUserDataFile   (sanfranciscoDynameqNet, starttime=datetime.time(07,00),
                                                 period=datetime.timedelta(minutes= 5), num_intervals=24,
                                                 suffix=suffix, from_year=from_year, to_year=to_year, weekdays=weekdays,
                                                 all_count_workbook=counts_wb)
        exportMainlineCountsToDynameUserDataFile(sanfranciscoDynameqNet, starttime=datetime.time(07,00),
                                                 period=datetime.timedelta(minutes=60), num_intervals=2,
                                                 suffix=suffix, from_year=from_year, to_year=to_year, weekdays=weekdays,
                                                 all_count_workbook=counts_wb)
        exportMainlineCountsToDynameUserDataFile(sanfranciscoDynameqNet, starttime=datetime.time(07,00),
                                                 period=datetime.timedelta(minutes=15), num_intervals=10,
                                                 suffix=suffix, from_year=from_year, to_year=to_year, weekdays=weekdays,
                                                 all_count_workbook=counts_wb)
        # static counts - PM period
        
        if weekdays: continue  # no notion of weekdays...
        
        exportMainlineCountsToDynameUserDataFile(sanfranciscoDynameqNet, starttime=datetime.time(06,30),
                                                 period=datetime.timedelta(minutes=60*3), num_intervals=1,
                                                 suffix=suffix, from_year=from_year, to_year=to_year, weekdays=weekdays,
                                                 all_count_workbook=counts_wb)

    counts_wb.save("counts_generated_%s.xls" % str(datetime.date.today()))
    
    if OUTPUT_LINK_SHAPEFILE: sanfranciscoDynameqNet.writeLinksToShp(OUTPUT_LINK_SHAPEFILE)
    if OUTPUT_MOVE_SHAPEFILE: sanfranciscoDynameqNet.writeMovementsToShp(OUTPUT_MOVE_SHAPEFILE)
    if OUTPUT_NODE_SHAPEFILE: sanfranciscoDynameqNet.writeNodesToShp(OUTPUT_NODE_SHAPEFILE)
    
