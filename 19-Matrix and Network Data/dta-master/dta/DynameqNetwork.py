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
import shapefile
import pdb
import math
from itertools import izip, imap
import os
import sys, csv

from itertools import chain 
from .Centroid import Centroid
from .Connector import Connector
from .DtaError import DtaError
from .Logger import DtaLogger
from .Movement import Movement
from .Network import Network
from .Node import Node
from .RoadLink import RoadLink
from .RoadNode import RoadNode
from .TimePlan import TimePlan
from .VirtualLink import VirtualLink
from .VirtualNode import VirtualNode
from .VehicleClassGroup import VehicleClassGroup
from .Utils import Time

class DynameqNetwork(Network):
    """
    A Dynameq DTA Network.
    """
    
    #: Dynameq's Base Network File name
    BASE_FILE       = '%s_base.dqt'
    #: Dynameq's Advanced Network File name
    ADVANCED_FILE   = '%s_advn.dqt'
    #: Dynameq's Traffic Control Plan File name
    CONTROL_FILE    = '%s_ctrl.dqt'
    #: Dynameq's Transit Lines File name
    TRANSIT_FILE    = '%s_ptrn.dqt'
    #: Dynameq's Custom Priorities File name
    PRIORITIES_FILE = '%s_prio.dqt'
    #: Dynameq's Toll User Attribute File name
    TOLL_FILE = '%s_toll.dqt'
    
    #: Dynameq's Base file header
    BASE_HEADER          = """<DYNAMEQ>
<VERSION_1.8>
<BASE_NETWORK_FILE>
* CREATED by DTA Anyway http://code.google.com/p/dta/
"""
    #: Dynameq's Advanced file header
    ADVANCED_HEADER     = """<DYNAMEQ>
<VERSION_1.8>
<ADVN_NETWORK_FILE>
* CREATED by DTA Anyway http://code.google.com/p/dta/    
"""

    #: Dynameq's Traffic Control Plan file header
    CTRL_HEADER        = """<DYNAMEQ>
<VERSION_1.8>
<CONTROL_PLANS_FILE>
* CREATED by DTA Anyway http://code.google.com/p/dta/
"""

    #: Dynameq's Custom Priorities file header
    PRIORITIES_HEADER   = """<DYNAMEQ>
<VERSION_1.8>
<CUSTOM_PRIORITIES_FILE>
* CREATED by DTA Anyway http://code.google.com/p/dta/
"""

    MOVEMENT_FLOW_OUT   = 'movement_aflowo.dqt'
    MOVEMENT_FLOW_IN    = 'movement_aflowi.dqt'
    MOVEMENT_TIME_OUT   = 'movement_atime.dqt'
    MOVEMENT_SPEED_OUT  = "movement_aspeed.dqt"
    LINK_FLOW_OUT       = 'link_aflowo.dqt'
    LINK_TIME_OUT       = 'link_atime.dqt'
    LINK_SPEED_OUT      = "link_aspeed.dqt"
    
    def __init__(self, scenario):
        """
        Constructor.  Initializes to an empty network.
        
        Keeps a reference to the given dynameqScenario (a :py:class:`DynameqScenario` instance)
        for :py:class:`VehicleClassGroup` lookups        
        """ 
        Network.__init__(self, scenario)
        self._dir = None 
                
    def read(self, dir, file_prefix):
        """
        Reads the network in the given *dir* with the given *file_prefix*.

        """
        # base file processing
        basefile = os.path.join(dir, DynameqNetwork.BASE_FILE % file_prefix)
        if not os.path.exists(basefile):
            raise DtaError("Base network file %s does not exist" % basefile)
        
        self._dir = dir 
        count = 0
        for fields in self._readSectionFromFile(basefile, "NODES", "CENTROIDS"):
            self.addNode(self._parseNodeFromFields(fields))
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "NODES", basefile))

        count = 0
        for fields in self._readSectionFromFile(basefile, "CENTROIDS", "LINKS"):
            self.addNode(self._parseCentroidFromFields(fields))
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "CENTROIDS", basefile))
        
        count = 0
        for fields in self._readSectionFromFile(basefile, "LINKS", "LANE_PERMS"):
            self.addLink(self._parseLinkFromFields(fields))
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "LINKS", basefile))
        
        count = 0
        for fields in self._readSectionFromFile(basefile, "LANE_PERMS", "LINK_EVENTS"):
            self._addLanePermissionFromFields(fields)
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "LANE_PERMS", basefile))
        
        count = 0
        for fields in self._readSectionFromFile(basefile, "LINK_EVENTS", "LANE_EVENTS"):
            #TODO: do LINK_EVENTS have to correspond to scenario events?
            raise DtaError("LINK_EVENTS not implemented yet")
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "LINK_EVENTS", basefile))

        count = 0
        for fields in self._readSectionFromFile(basefile, "LANE_EVENTS", "VIRTUAL_LINKS"):
            #TODO: do LANE_EVENTS have to correspond to scenario events?
            #raise DtaError("LANE_EVENTS not implemented yet")
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "LANE_EVENTS", basefile))
            
        count = 0
        for fields in self._readSectionFromFile(basefile, "VIRTUAL_LINKS", "MOVEMENTS"):
            self.addLink(self._parseVirtualLinkFromFields(fields))
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "VIRTUAL_LINKS", basefile))
            
        count = 0                        
        for fields in self._readSectionFromFile(basefile, "MOVEMENTS", "MOVEMENT_EVENTS"):
            mov = self._parseMovementFromFields(fields)
            self.addMovement(self._parseMovementFromFields(fields))
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "MOVEMENTS", basefile))
        
        count = 0
        for fields in self._readSectionFromFile(basefile, "MOVEMENT_EVENTS", "ENDOFFILE"):
            #TODO: MOVEMENT_EVENTS
            #raise DtaError("MOVEMENT_EVENTS not implemented yet")            
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "MOVEMENT_EVENTS", basefile))
        
        # advanced file processing
        advancedfile = os.path.join(dir, DynameqNetwork.ADVANCED_FILE % file_prefix)
        if os.path.exists(advancedfile):
            
            count = 0
            for fields in self._readSectionFromFile(advancedfile, "SHIFTS", "VERTICES"):
                self._addShiftFromFields(fields)
                count += 1
            DtaLogger.info("Read  %8d %-16s from %s" % (count, "SHIFTS", advancedfile))
            
            count = 0
            for fields in self._readSectionFromFile(advancedfile, "VERTICES", "ENDOFFILE"):
                self._addShapePointsToLink(fields)
                count += 1
            DtaLogger.info("Read  %8d %-16s from %s" % (count, "VERTICES", advancedfile))

        # control file Processing
        controlfile = os.path.join(dir, DynameqNetwork.CONTROL_FILE % file_prefix)
        if os.path.exists(controlfile):
            
            count = 0
            for tp in TimePlan.readDynameqPlans(self, controlfile):
                tp.getNode().addTimePlan(tp)
                count += 1
            DtaLogger.info("Read  %8d %-16s from %s" % (count, "TIME PLANS", controlfile))
                        
        # custom priorities file
        custompriofile = os.path.join(dir, DynameqNetwork.PRIORITIES_FILE % file_prefix)
        if os.path.exists(custompriofile):
            
            count = 0
            for fields in self._readSectionFromFile(custompriofile, None, "ENDOFFILE"):
                self._addCustomPrioritiesFromFields(fields)
                count += 1
            DtaLogger.info("Read  %8d %-16s from %s" % (count, "CUSTOM PRIOS", custompriofile))
                       
        ## TODO - what about the public transit file?
        
    def write(self, dir, file_prefix):
        """
        Writes the network into the given *dir* with the given *file_prefix*
        """

        self._scenario.write(dir, file_prefix)
        basefile = os.path.join(dir, DynameqNetwork.BASE_FILE % file_prefix)
        
        basefile_object = open(basefile, "w")
        basefile_object.write(DynameqNetwork.BASE_HEADER)
        self._writeNodesToBaseFile(basefile_object)
        self._writeCentroidsToBaseFile(basefile_object)
        self._writeLinksToBasefile(basefile_object)
        self._writeLanePermissionsToBaseFile(basefile_object)
        self._writeLinkEventsToBaseFile(basefile_object)
        self._writeLaneEventsToBaseFile(basefile_object)
        self._writeVirtualLinksToBaseFile(basefile_object)
        self._writeMovementsToBaseFile(basefile_object)
        self._writeMovementEventsToBaseFile(basefile_object)
        basefile_object.close()
        
        advancedfile = os.path.join(dir, DynameqNetwork.ADVANCED_FILE % file_prefix)
        advancedfile_object = open(advancedfile, "w")
        advancedfile_object.write(DynameqNetwork.ADVANCED_HEADER)
        self._writeShiftsToAdvancedFile(advancedfile_object)
        self._writeShapePointsToAdvancedFile(advancedfile_object)
        advancedfile_object.close()

        ctrlfile = os.path.join(dir, DynameqNetwork.CONTROL_FILE % file_prefix)
        ctrl_object = open(ctrlfile, "w")
        ctrl_object.write(DynameqNetwork.CTRL_HEADER)
        self._writeControlFile(ctrl_object)
        ctrl_object.close() 
        
        if self.hasCustomPriorities():
            custompriofile = os.path.join(dir, DynameqNetwork.PRIORITIES_FILE % file_prefix)
            customprio_object = open(custompriofile, "w")
            customprio_object.write(DynameqNetwork.PRIORITIES_HEADER)
            self._writeCustomPriorities(customprio_object)
            customprio_object.close()

        tollfile = os.path.join(dir, DynameqNetwork.TOLL_FILE % file_prefix)
        toll_object = open(tollfile, "w")
        self._writeTollFile(toll_object)
        toll_object.close() 

    def _readSectionFromFile(self, filename, sectionName, nextSectionName):
        """
        Generator function, yields fields (array of strings) from the given section of the given file.
        
        If *sectionName* is None, starts reading after comments.
        
        """
        lines = open(filename, "r")
        curLine = ""
        if sectionName:
            try:
                # find the section
                while curLine != sectionName: curLine = lines.next().strip()
                
            except StopIteration:
                raise DtaError("DynameqNetwork _readSectionFromFile failed to find %s in %s" % 
                               (sectionName,filename))
        else:
            # find the first comment
            curLine = " "
            while curLine[0] != "*": curLine = lines.next().strip()
        
        # go past the section name
        curLine = lines.next().strip()
        # skip any comments
        while curLine[0] == "*":
            curLine = lines.next().strip()
        
        # these are the ones we want
        while not curLine == nextSectionName:
            fields  = curLine.split()
            yield fields
            
            curLine = lines.next().strip()
        lines.close()
        raise StopIteration

    def _parseNodeFromFields(self, fields):
        """
        Interprets fields and returns a RoadNode or a VirtualNode
        """
        id      = int(fields[0])
        x       = float(fields[1])
        y       = float(fields[2])
        control = int(fields[3])
        priority= int(fields[4])
        type    = int(fields[5])
        level   = int(fields[6])
        label   = fields[7]
        if label[0] == '"' and label[-1] ==  '"':
            label = label[1:-1]

        if type == Node.GEOMETRY_TYPE_INTERSECTION or \
           type == Node.GEOMETRY_TYPE_JUNCTION:
            return RoadNode(id, x, y, type, control, priority, label, level)
        
        if type == Node.GEOMETRY_TYPE_VIRTUAL:
            return VirtualNode(id, x, y, label, level)
        
        raise DtaError("DynameqNetwork _parseNodesFromBasefile: Found Node of unrecognized type %d" % type)

    def _writeNodesToBaseFile(self, basefile_object):
        """
        Write version of _parseNodesFromBaseFile().  *basefile_object* is the file object,
        ready for writing.
        """
        basefile_object.write("NODES\n")
        basefile_object.write("*%8s %20s %20s %8s %8s %4s %6s %12s\n" % 
                              ("id",
                               "x-coordinate",
                               "y-coordinate",
                               "control",
                               "priority",
                               "type",
                               "level",
                               "label"))


        count = 0

        roadNodes = sorted(self.iterRoadNodes(), key=lambda n:n.getId())
        virtualNodes = sorted(self.iterVirtualNodes(), key=lambda n:n.getId())

        for node in chain(roadNodes, virtualNodes):
            
            if isinstance(node, VirtualNode):
                control = VirtualNode.DEFAULT_CONTROL
                priority = VirtualNode.DEFAULT_PRIORITY
            else:
                control = node._control
                priority = node._priority

            basefile_object.write("%9d %20.6f %20.6f %8d %8d %4d %6d %12s\n" %
                                  (node.getId(),
                                   node.getX(),
                                   node.getY(),
                                   control,
                                   priority,
                                   node._geometryType,
                                   node._level,
                                   '"' + node._label + '"'))
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "NODES", basefile_object.name))
        DtaLogger.info("Wrote %8d %-16s to %s" % (self.getNumRoadNodes(), "ROAD NODES", basefile_object.name))
        DtaLogger.info("Wrote %8d %-16s to %s" % (self.getNumCentroids(), "CENTROIDS", basefile_object.name))
        DtaLogger.info("Wrote %8d %-16s to %s" % (self.getNumVirtualNodes(), "VIRTUAL NODES", basefile_object.name))
                
    def _parseCentroidFromFields(self, fields):
        """
        Interprets fields into a Centroid
        """
        id      = int(fields[0])
        x       = float(fields[1])
        y       = float(fields[2])
        level   = int(fields[3])
        label   = fields[4]
        if label[0] == '"' and label[-1] ==  '"':
            label = label[1:-1]
        
        return Centroid(id, x, y, label=label, level=level)
    
    def _writeCentroidsToBaseFile(self, basefile_object):
        """
        Write version of _parseCentroidsFromBaseFile().  *basefile_object* is the file object,
        ready for writing.
        """
        basefile_object.write("CENTROIDS\n")
        basefile_object.write("*%8s %20s %20s %6s %5s\n" % 
                              ("id",
                               "x-coordinate",
                               "y-coordinate",
                               "level",
                               "label"))
        
        count = 0
        for nodeId in sorted(self._nodes.keys()):
            centroid = self._nodes[nodeId]
            if not isinstance(centroid, Centroid): continue
            
            basefile_object.write("%9d %20.6f %20.6f %6d %s\n" % 
                                  (centroid.getId(),
                                   centroid.getX(),
                                   centroid.getY(),
                                   centroid._level,
                                   '"' + centroid._label + '"'))
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "CENTROIDS", basefile_object.name))

    def _parseLinkFromFields(self, fields):
        """
        Interprets fields into a Connector or a RoadLink
        """            
        id      = int(fields[0])
        startid = int(fields[1])
        endid   = int(fields[2])
        rev     = int(fields[3])
        faci    = int(fields[4])
        length  = float(fields[5])
        fspeed  = float(fields[6])
        lenfac  = float(fields[7])
        resfac  = float(fields[8])
        lanes   = int(fields[9])
        rabout  = int(fields[10])
        level   = int(fields[11])
        tmplabel= fields[12:len(fields) - 1]
        group = int(fields[len(fields) - 1])

        if tmplabel == '""':
            label = ""
        else:
            label = " ".join(tmplabel)[1:-1]

            
        startNode = self.getNodeForId(startid)
        endNode = self.getNodeForId(endid)
        
        if (isinstance(startNode, Centroid) or isinstance(endNode, Centroid) or
            isinstance(startNode, VirtualNode) or isinstance(endNode, VirtualNode)):
            
            # check faci == Connector.FACILITY_TYPE?
            
            return Connector(id, startNode, endNode, reverseAttachedLinkId=rev, 
                                length=(None if length==-1 else length),
                                freeflowSpeed=fspeed, effectiveLengthFactor=lenfac, 
                                responseTimeFactor=resfac, numLanes=lanes,
                                roundAbout=rabout, level=level, label=label, group=group)
        
        # are these all RoadLinks?  What about VirtualLinks?
        return RoadLink(id, startNode, endNode, reverseAttachedLinkId=rev, 
                           facilityType=faci, length=(None if length==-1 else length),
                           freeflowSpeed=fspeed, effectiveLengthFactor=lenfac, 
                           responseTimeFactor=resfac, numLanes=lanes,
                           roundAbout=rabout, level=level, label=label, group=group)

    def _writeLinksToBasefile(self, basefile_object):
        """
        Write version of _readLinksFromBaseFile().  *basefile_object* is the file object,
        ready for writing.
        """
        basefile_object.write("LINKS\n")
        basefile_object.write("*        id     start       end       rev faci         len      fspeed  lenfac  resfac lanes rabout level                          label                                  group       \n")

        count = 0

        roadLinks = sorted(self.iterRoadLinks() , key=lambda rl:rl.getId()) 
        connectors = sorted(self.iterConnectors(), key=lambda c:c.getId())

        for link in chain(roadLinks, connectors):

            basefile_object.write(" %10d %9d %9d %9d %4d %11s %11.3f %7.3f %7.3f %5d %6d %5d %30s %38d       \n" % 
                                  (link.getId(),
                                   link.getStartNode().getId(),
                                   link.getEndNode().getId(),
                                   link._reverseAttachedLinkId if link._reverseAttachedLinkId else -1,
                                   link._facilityType,
                                   ("%11.3f" % link._length),
                                   link._freeflowSpeed,
                                   link._effectiveLengthFactor,
                                   link._responseTimeFactor,
                                   link._numLanes,
                                   link._roundAbout,
                                   link._level,
                                   '"' + (link._label if link._label else "") + '"',
                                   link.getId() if link._group == -1 else link._group)) # -1 means no group so use link ID

            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "LINKS", basefile_object.name))
        DtaLogger.info("Wrote %8d %-16s to %s" % (self.getNumRoadLinks(), "ROAD LINKS", basefile_object.name))
        DtaLogger.info("Wrote %8d %-16s to %s" % (self.getNumConnectors(), "CONNECTORS", basefile_object.name))
        DtaLogger.info("Wrote %8d %-16s to %s" % (self.getNumVirtualLinks(), "VIRTUAL LINKS", basefile_object.name))
        
    def _addLanePermissionFromFields(self, fields):
        """
        Updates links by attaching permissions.
        """            
        linkId  = int(fields[0])
        laneId  = int(fields[1])
        perms   = fields[2]
        
        vehicleClassGroup = self._scenario.getVehicleClassGroup(perms)
        link = self.getLinkForId(linkId)
        link.addLanePermission(laneId, vehicleClassGroup)
            
    def _writeLanePermissionsToBaseFile(self, basefile_object):
        """
        Write version of _addLanePermissionsFromFields()
        *basefile_object* is the file object, ready for writing.        
        """
        basefile_object.write("LANE_PERMS\n")
        basefile_object.write("*    link  id                perms\n")
        
        count = 0
        for linkId in sorted(self._linksById.keys()):
            
            if (not isinstance(self._linksById[linkId], RoadLink) and
                not isinstance(self._linksById[linkId], Connector)):
                continue
            
            for laneId in range(self._linksById[linkId]._numLanes):
                if laneId not in self._linksById[linkId]._lanePermissions: continue # warn?
                basefile_object.write("%9d %3d %20s\n" % 
                                      (linkId,
                                       laneId,
                                       self._linksById[linkId]._lanePermissions[laneId].name))
                count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "LANE_PERMS", basefile_object.name))
    
    def _writeLinkEventsToBaseFile(self, basefile_object):
        """
        """
        basefile_object.write("LINK_EVENTS\n")
        basefile_object.write("*      id     time         std_att        value\n")
    
    def _writeLaneEventsToBaseFile(self, basefile_object):
        """
        """
        basefile_object.write("LANE_EVENTS\n")
        basefile_object.write("*    link  id     time                perms\n")
        
    def _parseVirtualLinkFromFields(self, fields):
        """
        Interprets fields into a VirtualLink
        """
        centroidId  = int(fields[0])
        linkId      = int(fields[1])
        
        centroid    = self._nodes[centroidId]
        connector   = self._linksById[linkId]

        if not isinstance(connector, Connector):
            raise DtaError("Virtual link specified with non-Connector link: %s" % str(connector))
        
        
        # no id -- make one up
        newId = self._maxLinkId + 1
        
        # if the connector is incoming to a virtual node, the the virtual link is incoming:
        # connector to centroid
        if connector._fromRoadNode:
            vlink = VirtualLink(id=newId,
                                startNode=connector.getEndNode(),
                                endNode=centroid,
                                label=None)
            # DtaLogger.debug("Creating virtual link from connector %d (node %d) to centroid %d" % 
            #                 (linkId, vlink.getStartNode().getId(), centroidId))            
        else:
            # the connector is outgoing to a virtual node, so the virtual link is outgoing:
            # connector to centroid
            vlink = VirtualLink(id=newId,
                            startNode=centroid,
                            endNode=connector.getStartNode(),
                            label=None)
            
            # DtaLogger.debug("Creating virtual link from centroid %d to connector %d (node %d)" % 
            #                 (centroidId, linkId, vlink.getEndNode().getId()))
     
        try:
            conn2 = vlink.getAdjacentConnector()
            assert(conn2 == connector)
        except DtaError:
            DtaLogger.warn(sys.exc_info()[1])
            raise
        except AssertionError:
            DtaLogger.warn("When creating Virtual Link from centroid %d to connector %d, different connector %d found" % 
                           (centroidId, linkId, conn2.getId()))
            raise
            
        return vlink
        
    def _writeVirtualLinksToBaseFile(self, basefile_object):
        """
        Write version of _parseVirtualLinkFromFields().  *basefile_object* is the file object,
        ready for writing.
        """
        basefile_object.write("VIRTUAL_LINKS\n")
        basefile_object.write("* centroid_id  link_id\n")
        
        count = 0
        for linkId in sorted(self._linksById.keys()):
            link = self._linksById[linkId]
            
            if not isinstance(link, VirtualLink): continue
            basefile_object.write("%13d %8d\n" %
                                  (link.getStartNode().getId() if isinstance(link.getStartNode(), Centroid) else link.getEndNode().getId(),
                                   link.getAdjacentConnector().getId()))
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "VIRTUAL_LINKS", basefile_object.name))

    def _parseMovementFromFields(self, fields):
        """
        Interprets fields into a Movement
        """
        nodeId          = int(fields[0])
        incomingLinkId  = int(fields[1])
        outgoingLinkId  = int(fields[2])
        freeflowSpeed   = float(fields[3])
        perms           = fields[4]
        numLanes        = int(fields[5])
        incomingLane    = int(fields[6])
        outgoingLane    = int(fields[7])
        followupTime    = float(fields[8])
        
        # use an int version if possible
        followupTime_i  = int(followupTime)
        if followupTime_i == followupTime:
            followupTime = followupTime_i
    
        node                = self.getNodeForId(nodeId)
        incomingLink        = self.getLinkForId(incomingLinkId)
        outgoingLink        = self.getLinkForId(outgoingLinkId)
        vehicleClassGroup   = self._scenario.getVehicleClassGroup(perms)
        
        return Movement(node, incomingLink, outgoingLink, freeflowSpeed,
                        vehicleClassGroup,
                        None if numLanes==-1 else numLanes,
                        None if incomingLane==-1 else incomingLane,
                        None if outgoingLane==-1 else outgoingLane,
                        followupTime)
        
    def _writeMovementsToBaseFile(self, basefile_object):
        """
        Write version of _parseMovementFromFields().
        *basefile_object* is the file object, ready for writing.        
        """
        basefile_object.write("MOVEMENTS\n")
        basefile_object.write("*   at_node   inc_link   out_link       fspeed                perms lanes inlane outlane  tfollow\n")
        
        count = 0
        for movement in self.iterMovements():
            
            basefile_object.write("%11d %10d %10d %12s %20s %5d %6d %7d %8s\n" %
                                  (movement._node.getId(),
                                   movement.getIncomingLink().getId(),
                                   movement._outgoingLink.getId(),
                                   str(-1 if not movement._freeflowSpeed else movement._freeflowSpeed),
                                   movement._permission.name,
                                   -1 if not movement._numLanes else movement._numLanes,
                                   -1 if not movement._incomingLane else movement._incomingLane,
                                   -1 if not movement._outgoingLane else movement._outgoingLane,
                                   str(movement._followupTime)))
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "MOVEMENTS", basefile_object.name))                                           
        
                    
    def writeCountListToFile(self, dir, starttime, period, number):
        """
        Writes counts to movements from CountDracula
        starttime = startitme for counts
        period = interval for each count
        number = total counts = (endtime-starttime)/period
        tolerance = tolerance for matching nodes in two databases in feet (5 ft is appropriate)        
        """
        movementcounter = 0
        countList2write = []

        for id in self._linksById:
            link = self._linksById[id]
            if not isinstance(link, VirtualLink):
                for movement in link.iterOutgoingMovements():
                    
                    movementcounter += 1
                    #print movementcounter
                    
                    
                    atNode = movement.getAtNode().getId()
                    fromNode = movement.getStartNode().getId()
                    toNode = movement.getEndNode().getId()
                    
                    movementcountsList = movement.getCountList()
                    
                    if not movementcountsList == []: 
                        countList2write.append([atNode,fromNode,toNode]+(movementcountsList))
        ## TODO Implement better csv file writer                  
        filewriter = csv.writer(open(dir+'\\movement_counts_user_attribute.csv', 'wb'),dialect = 'excel-tab', delimiter=' ',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow("*atNode FromNode toNode starttime="+str(starttime)+" period="+str(period)+" number="+str(number))
        filewriter.writerows(countList2write)
        
    def _writeMovementEventsToBaseFile(self, basefile_object):
        """
        *basefile_object* is the file object, ready for writing.
        """
        basefile_object.write("MOVEMENT_EVENTS\n")
        basefile_object.write("*   at_node  inc_link   out_link     time         std_att        value\n")
        
    def _addShiftFromFields(self, fields):
        """
        Updates links by attaching permissions.
        """            
        linkId      = int(fields[0])
        startShift  = int(fields[1])
        endShift    = int(fields[2])
        
        link = self.getLinkForId(linkId)
        link.addShifts(startShift, endShift)
    
    def _writeShiftsToAdvancedFile(self, advancedfile_object):
        """
        Write version of _addLanePermissionsFromFields().  
        *advancedfile_object* is the file object, ready for writing.
        """
        advancedfile_object.write("SHIFTS\n")
        advancedfile_object.write("*      id  start-shift    end-shift\n")
        
        count = 0
        for linkId in sorted(self._linksById.keys()):
            link = self._linksById[linkId]
            
            if isinstance(link, RoadLink):
                (startShift,endShift) = link.getShifts()
                if startShift != None or endShift != None:
                    advancedfile_object.write("%9d %12d %12d\n" % (linkId, startShift, endShift))
                    
                    count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "SHIFTS", advancedfile_object.name))
        
    def _addShapePointsToLink(self, fields):
        """
        Update links by attaching shape points
        """
        linkId      = int(fields[0])
        sequenceNum = int(fields[1])
        xcoord      = float(fields[2])
        ycoord      = float(fields[3])
        
        link = self.getLinkForId(linkId)
        link.addShapePoint(xcoord, ycoord)

    def _writeShapePointsToAdvancedFile(self, advancedfile_object):
        """
        Write version of _addShapePointsToLink().  
        *advancedfile_object* is the file object, ready for writing.
        """
        advancedfile_object.write("VERTICES\n")
        advancedfile_object.write("*      id   sequence_num                     x-coordinate                     y-coordinate\n")
        
        count = 0
        for linkId in sorted(self._linksById.keys()):
            link = self._linksById[linkId]
            
            if isinstance(link, RoadLink) or isinstance(link, Connector):
                for seqnum, (x,y) in enumerate(link._shapePoints):
                    advancedfile_object.write("%9d %14d %32f %32f\n" % 
                                              (linkId, 
                                               seqnum,
                                               x,
                                               y))
                    
                    count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "VERTICES", advancedfile_object.name))

    def _writeControlFile(self, ctrl_object):
        """
        Output the control plans to disk
        """
        count = 0        
        for planInfo in self.iterPlanCollectionInfo():
            ctrl_object.write(planInfo.getDynameqStr())
            for node in sorted(self.iterRoadNodes(), key=lambda node: node.getId()):
                if node.hasTimePlan(planInfo):
                    ctrl_object.write(node.getTimePlan(planInfo).getDynameqStr())
                    count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "TIME PLANS", ctrl_object.name))

            
    def _writeTollFile(self, toll_object):
        """
        Output the user attribute Toll field to disk
        """            
        toll_object.write("* link\n")

        count = 0

        roadLinks = sorted(self.iterRoadLinks() , key=lambda rl:rl.getId()) 
        for link in roadLinks:
            toll_object.write(" %10d %1d \n" % (link.getId(),link._tollLink))
            count += 1

        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "LINKS", toll_object.name))
        DtaLogger.info("Wrote %8d %-16s to %s" % (self.getNumRoadLinks(), "ROAD LINKS", toll_object.name))


    def _addCustomPrioritiesFromFields(self, fields):
        """
        Updates :py:class:`Movement` priorities by adding the information about their higher-priority movements.
        """
        at_node_id      = int(fields[0])
        inc_link_id     = int(fields[1])
        out_link_id     = int(fields[2])
        
        prio_inc_link_id= int(fields[3])
        prio_out_link_id= int(fields[4])
        cgap            = float(fields[5])
        cwait           = float(fields[6])
        
        at_node         = self.getNodeForId(at_node_id)
        movement        = at_node.getMovementForLinkIds(inc_link_id, out_link_id)
        prio_movement   = at_node.getMovementForLinkIds(prio_inc_link_id, prio_out_link_id)
        movement.addHigherPriorityMovement(prio_movement, cgap, cwait)
        
    def _writeCustomPriorities(self, customprio_object):
        """
        Output the custom priorities to disk
        """
        customprio_object.write("*        at       inc       out     inc_p     out_p        cgap       cwait\n")
        count = 0
        for movement in self.iterMovements():
            
            for (higherprio_movement, critical_gap, critical_wait) in movement.iterHigherPriorityMovements():
                customprio_object.write(" %10d %9d %9d %9d %9d %11.3f %11.3f\n" % \
                                        (movement.getAtNode().getId(),
                                         movement.getIncomingLink().getId(),
                                         movement.getOutgoingLink().getId(),
                                         higherprio_movement.getIncomingLink().getId(),
                                         higherprio_movement.getOutgoingLink().getId(),
                                         critical_gap,
                                         critical_wait))
                count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "CUSTOM PRIOS", customprio_object.name))
    
        
    def _readMovementOutFlowsAndTTs(self):
        """
        Read the movement travel times (in seconds) add assign them 
        to the corresponding movement
        """
        if not self._dir:
            raise DtaError("The network directory has not been defined")
        
        movementFlowFileName = os.path.join(self._dir, 
                                            DynameqNetwork.MOVEMENT_FLOW_OUT)
        movementTimeFileName = os.path.join(self._dir,
                                            DynameqNetwork.MOVEMENT_TIME_OUT)

        movementFlowInFileName = os.path.join(self._dir,
                                            DynameqNetwork.MOVEMENT_FLOW_IN)


        inputStream1 = open(movementFlowFileName, 'r')
        inputStream2 = open(movementTimeFileName, 'r')
        inputStream3 = open(movementFlowInFileName, 'r')        

        for i in range(9):
            inputStream1.next()
            inputStream2.next()

        for flowLine, timeLine, flowInLine in izip(inputStream1, inputStream2, inputStream3):
            
            flowFields = flowLine.strip().split()
            timeFields = timeLine.strip().split()
            flowInFields = flowLine.strip().split()            

            nodeBid, nodeAid, nodeCid = map(int, flowFields[:3])

            if [nodeBid, nodeAid, nodeCid] != map(int, timeFields[:3]):
                raise DtaError('The files %s and %s are not in sync. '
                                      'Movement through %s from %s to %s in the first file is not '
                                      'in the same line position in the second '
                                      'file' % (movementFlowFileName,
                                                movementTimeFileName,
                                                nodeBid, nodeAid, nodeCid))

            try:
                link = self.getLinkForNodeIdPair(nodeAid, nodeBid)
                movement = link.getOutgoingMovement(nodeCid)
            except DtaError, e:
                #if the movement does not exist. It could be a prohibited movement
                #perhaps you need to do more error checking there 
                if nodeAid == nodeCid:
                    continue
                continue

            simFlows = imap(int, flowFields[3:])
            simTTs = imap(float, timeFields[3:])
            simInFlows = imap(int, flowInFields[3:])
            
            timePeriodStart = self._simStartTimeInMin
                    
            for simFlow, simTT, simInFlow in izip(simFlows, simTTs, simInFlows):

                #TODO:Dynameq occasionaly reports negative times.
                if simTT < 0:
                    continue

                if simFlow == 0 and simTT > 0:
                    raise DtaError('Movement %s has zero flow in the '
                                   'time period begining %d and a '
                                   'positive travel time' % 
                                   (movement.getId(), timePeriodStart))
                elif simFlow > 0 and simTT == 0:
                    raise DtaError('Movement %s has positive flow in '
                                   'the time period begining %d and a '
                                   'zero travel time' % 
                                   (movement.getId(), timePeriodStart))
                
                elif simFlow == 0 and simTT == 0:
                    #simTT = movement.getFreeFlowTTInMin()
                    timePeriodStart += self._simTimeStepInMin
                    if timePeriodStart >= self._simEndTimeInMin:
                        break
                else:
                    movement.setSimOutVolume(timePeriodStart, timePeriodStart + 
                                        self._simTimeStepInMin, simFlow / (60 / self._simTimeStepInMin))
                    movement.setSimInVolume(timePeriodStart, timePeriodStart + 
                                        self._simTimeStepInMin, simInFlow / (60 / self._simTimeStepInMin))

                    movement.setSimTTInMin(timePeriodStart, timePeriodStart + 
                                          self._simTimeStepInMin, simTT / 60.0)

                                      
                    timePeriodStart += self._simTimeStepInMin
                    if timePeriodStart >= self._simEndTimeInMin:
                        break

        inputStream1.close()
        inputStream2.close()

                               
    def readSimResults(self, simStartTimeInMin, simEndTimeInMin, simTimeStepInMin):
        """
        Read the movement and link travel times and flows
        """
        self._simStartTimeInMin = simStartTimeInMin
        self._simEndTimeInMin = simEndTimeInMin
        self._simTimeStepInMin = simTimeStepInMin

        for link in self.iterLinks():
            if link.isVirtualLink():
                continue
            link.simTimeStepInMin = simTimeStepInMin
            link.simStartTimeInMin = simStartTimeInMin
            link.simEndTimeInMin = simEndTimeInMin
            for mov in link.iterOutgoingMovements():
                mov.simTimeStepInMin = simTimeStepInMin
                mov.simStartTimeInMin = simStartTimeInMin
                mov.simEndTimeInMin = simEndTimeInMin

        self._readMovementOutFlowsAndTTs()

    def readObsMovementCounts(self, countFileNameInDynameqDatFormat):
        """
        Assign the movement counts
        """

        startTimeInMin = 0
        endTimeInMin = 0
        timeStepInMin = 0
        for line in open(countFileNameInDynameqDatFormat, "r"):
            if "*" in line:
                # parse the times from this line
                if " at " in line:
                    times = line.strip().split()[4:]
                    startTimeInMin = Time.readFromString(times[0]).getMinutes()
                    endTimeInMin = Time.readFromString(times[-1]).getMinutes()
                    timeStepInMin = Time.readFromString(times[1]).getMinutes() - \
                                    startTimeInMin
                    continue

                # don't care about other comments
                continue
            
            # this is a data line -- all comment lines have been taken care of already
            fields = map(int, map(float, line.strip().split()))
            
            link1 = self.getLinkForNodeIdPair(fields[1],fields[0])
            link2 = self.getLinkForNodeIdPair(fields[0],fields[2])

            mov = link1.getOutgoingMovement(link2.getEndNodeId())
        

            for s, count in izip(range(startTimeInMin, endTimeInMin + 1, timeStepInMin), fields[3:]):
                if count < 0:
                    continue
                mov.setObsCount(s,s+timeStepInMin, count) 
            
            # next, aggregate to 15-minute and 60-minute bins if needed
            for aggregateTimeStep in [15, 60]: 
                if timeStepInMin<aggregateTimeStep: 
                    for s, count in izip(range(startTimeInMin, endTimeInMin + 1, timeStepInMin), fields[3:]):
                        if s == startTimeInMin: 
                            aggregateCount = 0            		
                        elif s % aggregateTimeStep == 0: 
        				    mov.setObsCount(s-aggregateTimeStep, s, aggregateCount)
        				    aggregateCount = 0
                        if count<0: continue
                        aggregateCount = aggregateCount + count
            
                        

    def readObsLinkCounts(self, countFileNameInDynameqDatFormat):
        """
        Assign the link counts
        """

        startTimeInMin = 0
        endTimeInMin = 0
        timeStepInMin = 0
        #lineNum = 0
        for line in open(countFileNameInDynameqDatFormat, "r"):
            #lineNum += 1
            #if lineNum == 0:
            if "*" in line:                    
                if "from" in line:
                    times = line.strip().split()[3:]
                    #startTimeInMin = Time.readFromStringWithoutColon(times[0]).getMinutes()
                    #endTimeInMin = Time.readFromStringWithoutColon(times[-1]).getMinutes()
                    #timeStepInMin = Time.readFromStringWithoutColon(times[1]).getMinutes() - \
                    #                startTimeInMin
                    startTimeInMin = Time.readFromString(times[0]).getMinutes()
                    endTimeInMin = Time.readFromString(times[-1]).getMinutes()
                    timeStepInMin = Time.readFromString(times[1]).getMinutes() - \
                                startTimeInMin
                    #lineNum += 1
                    continue
                else:
                    continue
                
            else:
                fields = map(int, map(float, line.strip().split()))
                
                #link = self.getLinkForId(fields[0])
                link = self.getLinkForNodeIdPair(fields[0],fields[1])
            
                for s, count in izip(range(startTimeInMin, endTimeInMin + 1, timeStepInMin), fields[2:]):
                    if count < 0:
                        continue
                    link.setObsCount(s,s+timeStepInMin, count) 
            
                # next, aggregate to 15-minute and 60-minute bins if needed
                for aggregateTimeStep in [15, 60]: 
                    if timeStepInMin<aggregateTimeStep: 
                        for s, count in izip(range(startTimeInMin, endTimeInMin + 1, timeStepInMin), fields[3:]):
                            if s == startTimeInMin: 
            				aggregateCount = 0            		
                            elif s % aggregateTimeStep == 0: 
                                link.setObsCount(s-aggregateTimeStep, s, aggregateCount)
                                aggregateCount = 0
                            if count<0: 
            				continue
                            aggregateCount = aggregateCount + count
            		
