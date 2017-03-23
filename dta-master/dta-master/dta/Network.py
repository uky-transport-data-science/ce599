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
import pdb 
import collections
import copy
import random
import difflib
import operator
import shapefile
import sys 

from .Centroid import Centroid
from .Connector import Connector
from .DtaError import DtaError
from .Link import Link
from .RoadLink import RoadLink
from .Logger import DtaLogger
from .Node import Node
from .RoadNode import RoadNode
from .TimePlan import PlanCollectionInfo
from .Scenario import Scenario
from .VirtualLink import VirtualLink
from .VirtualNode import VirtualNode
from .VehicleType import VehicleType
from .VehicleClassGroup import VehicleClassGroup
from .Movement import Movement
from .Algorithms import *
from .Utils import Time

class Network(object):
    """
    Base class that represents a DTA Network.  Networks exist on a continuum between
    macro- and micro-simulation, and this network is meant to represent something
    "typical" for a mesosimulation.  Something to be aware of in case it becomes too complicated.
    
    Subclasses will be used to represent networks for different frameworks (Dynameq, Cube, etc)
    so this class should have no code to deal with any particular file formats.
    
    """
    
    def __init__(self, scenario):
        """
        Constructor.  Initializes to an empty network, stores reference to given
        scenario (a :py:class:`Scenario` instance).
        """
        if (not VehicleType.LENGTH_UNITS) or (not Node.COORDINATE_UNITS) or not (RoadLink.LENGTH_UNITS):
            raise DtaError("Network __init__ failed; Please set VehicleType.LENGTH_UNITS, Node.COORDINATE_UNITS and RoadLink.LENGTH_UNITS.")
        
        # node id -> node; these can be instances of :py:class:`RoadNode` :py:class:`VirtualNode` or
        # :py:class:`Centroid`
        self._nodes         = {}
        # link id -> :py:class:`Link` (these are :py:class:`RoadLink`s and :py:class:`Connector`s)
        self._linksById     = {}
        # (nodeA id, nodeB id) -> :py:class:`Link` (these are :py:class:`RoadLink`s and :py:class:`Connector`s)
        self._linksByNodeIdPair = {}
        
        # maximum link id
        self._maxLinkId     = 0
        # maximum node id
        self._maxNodeId     = 0
        
        # the relevant :py:class:`Scenario` instance
        if not isinstance(scenario, Scenario):
            raise DtaError("Network __init__ received invalid scenario %s (not Scenario instance)" %
                           str(scenario))
            
        self._scenario = scenario
        self._planInfo = {}
        
        self._nodeType = random.randint(0, 100000)
        self._linkType = random.randint(0, 100000)
        
    def __del__(self):
        pass
    
    def deepcopy(self, originNetwork):
        """
        Copies the contents of the originNetwork by creating copies of all its 
        constituent elements into self (Nodes and Links and Movements, 
        not the scenario). If the originNetwork contains an element 
        with an already existing id this method will throw an exception. 
        """
        self._maxLinkId = originNetwork._maxLinkId
        self._maxNodeId = originNetwork._maxNodeId
        
        for node in originNetwork.iterNodes():            
            cNode = copy.copy(node) 
            cNode._incomingLinks = []
            cNode._outgoingLinks = []
            self.addNode(cNode)

        for link in originNetwork.iterLinks():
            cLink = copy.copy(link)
            cLink._startNode = self.getNodeForId(link._startNode.getId())
            cLink._endNode = self.getNodeForId(link._endNode.getId())
            if isinstance(link, RoadLink):                
                cLink._outgoingMovements = []
                cLink._incomingMovements = [] 
            self.addLink(cLink) 

        for link in originNetwork.iterLinks():
            if isinstance(link, RoadLink):                
                for mov in link.iterOutgoingMovements():
                    cLink = self.getLinkForId(link.getId())
                    cMov = copy.copy(mov)
                    cMov._node = self.getNodeForId(mov._node.getId())
                    cMov._incomingLink = self.getLinkForId(mov._incomingLink.getId())
                    cMov._outgoingLink = self.getLinkForId(mov._outgoingLink.getId())

                    cLink.addOutgoingMovement(cMov)

    def addPlanCollectionInfo(self, startTime, endTime, name, description):
        """
        Instantiates a new :py:class:`PlanCollectionInfo` for this network with the given attributes and returns it.
        See :py:meth:`PlanCollectionInfo.__init__` for arguments.
        """
        if not (isinstance(startTime, Time) and isinstance(startTime, Time)):
            raise DtaError("Start time and End Time should be instances of `Utils.Time` objects") 
        
        if self.hasPlanCollectionInfo(startTime, endTime):
            raise DtaError("The network already has a plan collection info from %d to %d"
                           % (startTime, endTime))
        planInfo = PlanCollectionInfo(startTime, endTime, name, description)   
        self._planInfo[startTime, endTime] = planInfo
        return planInfo

    def hasPlanCollectionInfo(self, startTime, endTime):
        """
        Return True if the network has a time plan connection for the given
        start and end times
        startTime :py:class:`Utils.Time` instance 
        endTime :py:class:`Utils.Time` instance         
        """
        if not (isinstance(startTime, Time) and isinstance(startTime, Time)):
            raise DtaError("Start time and End Time should be instances of `Utils.Time` objects") 
        
        return True if (startTime, endTime) in self._planInfo else False

    def getPlanCollectionInfo(self, startTime, endTime):
        """
        Return the plan collection info for the given input times
        startTime :py:class:`Utils.Time` instance 
        endTime :py:class:`Utils.Time` instance                 
        """
        if not (isinstance(startTime, Time) and isinstance(startTime, Time)):
            raise DtaError("Start time and End Time should be instances of `Utils.Time` objects") 
        
        if self.hasPlanCollectionInfo(startTime, endTime):
            return self._planInfo[startTime, endTime]
        else:
            raise DtaError("The network does not have a plan collection from %d to %d"
                           % (startTime, endTime))

    def iterPlanCollectionInfo(self):
        """
        Return an iterator to the planInfo objects
        """
        for sTime, eTime in sorted(self._planInfo.keys()):
            yield self.getPlanCollectionInfo(sTime, eTime)

        #return iter(sorted(self._planInfo.values(), key=lambda pi:pi._startTime))
                        
    def addNode(self, newNode):
        """
        Verifies that *newNode* is a :py:class:`RoadNode`, :py:class:`VirtualNode` or :py:class:`Centroid`
        and that the id is not already used; stores it.
        """
        if (not isinstance(newNode, RoadNode) and 
            not isinstance(newNode, VirtualNode) and 
            not isinstance(newNode, Centroid)):
            raise DtaError("Network.addNode called on non-RoadNode/VirtualNode/Centroid: %s" % str(newNode))

        if newNode.getId() in self._nodes:
            raise DtaError("Network.addNode called on node with id %d already in the network (for a node)" % newNode.getId())

        self._nodes[newNode.getId()] = newNode
        
        if newNode.getId() > self._maxNodeId: self._maxNodeId = newNode.getId()

    def getNumNodes(self):
        """
        Returns the number of nodes in the network
        """
        return len(self._nodes)

    def getNumRoadNodes(self):
        """
        Returns the number of roadnodes in the network
        """
        return sum(1 for node in self.iterNodes() if isinstance(node, RoadNode))

    def getNumCentroids(self):
        """
        Returns the number of centroids in the network
        """
        return sum(1 for node in self.iterNodes() if isinstance(node, Centroid))

    def getNumVirtualNodes(self):
        """
        Returns the number of virtual nodes in the network
        """
        return sum(1 for node in self.iterNodes() if isinstance(node, VirtualNode))
        
    def getNumLinks(self):
        """
        Returns the number of links in the network
        """
        return len(self._linksById)

    def getNodeForId(self, nodeId):
        """
        Accessor for node given the *nodeId*.
        Raises :py:class:`DtaError` if not found.
        """
        if nodeId in self._nodes:
            return self._nodes[nodeId]
        
        raise DtaError("Network getNodeForId: none found for id %d" % nodeId)
    
    def addAllMovements(self, vehicleClassGroup, includeUTurns=False):
        """
        For each :py:class:`RoadNode` and each :py:class:`VirtualNode`, 
        makes a movement for the given *vehicleClassGroup* (a :py:class:`VehicleClassGroup` instance)
        from each incoming link to each outgoing link 
        (not including :py:class:`VirtualLink` instances).
        
        If *includeUTurns*, includes U-Turn movements for each link as well, otherwise omits these.
        
        If either the incoming link or the outgoing link returns false for :py:meth:`RoadLink.allowsAll`,
        then uses the lane permission from that link instead.
        
        .. todo:: This last bit is somewhat arbitrary, could be refined further.
         
        """
        
        movements_added = 0
        
        for node in self.iterNodes():
            if node.isCentroid(): continue
            
            for incomingLink in node.iterIncomingLinks():

                if incomingLink.isVirtualLink(): continue
                
                for outgoingLink in node.iterOutgoingLinks():
                    if outgoingLink.isVirtualLink(): continue
                
                    # it already exists
                    if incomingLink.hasOutgoingMovement(outgoingLink.getEndNodeId()): continue
                
                    # one of incoming or outgoing link doesn't allow all
                    vcg = None
                    if not incomingLink.allowsAll():
                        DtaLogger.warn("addAllMovements: incoming link %d-%d %s %s does not allow all" % (incomingLink.getStartNode().getId(),
                                                                                                          incomingLink.getEndNode().getId(),
                                                                                                          incomingLink.getLabel(), incomingLink.getDirection()))
                        vcg = incomingLink._lanePermissions[0]
                        
                    if not outgoingLink.allowsAll():
                        DtaLogger.warn("addAllMovements: outgoing link %d-%d %s %s does not allow all" % (outgoingLink.getStartNode().getId(),
                                                                                                          outgoingLink.getEndNode().getId(),
                                                                                                          outgoingLink.getLabel(), outgoingLink.getDirection()))
                        # this should really be more like an intersection between the incoming vcg and the outgoing
                        vcg = outgoingLink._lanePermissions[0]

                    mov = Movement.simpleMovementFactory(incomingLink, outgoingLink, vcg if vcg else vehicleClassGroup)
                
                    # if it's a U-Turn and we don't want it, set the movement to prohibited
                    if mov.isUTurn() and not includeUTurns:
                        mov.prohibitAllVehicleClassGroups()
                
                    incomingLink.addOutgoingMovement(mov)
                    movements_added += 1
        
        DtaLogger.info("addAllMovements() added %d movements" % movements_added)
    
    def setMovementTurnTypeOverrides(self, overrides):
        """
        Sets movement turn type overrides.  *overrides* is specified as a list of overrides, where each override
        is a tuple containing ( *from_dir*, *from_street*, *cross_street*, *to_dir*, *to_street*, *turn_type*, [*perm_type*], [*lanes*] ).
        
        *from_dir* and *to_dir* should be one of :py:attr:`RoadLink.DIR_EB`, :py:attr:`RoadLink.DIR_WB`, :py:attr:`RoadLink.DIR_NB`, 
        and :py:attr:`RoadLink.DIR_SB`.
        
        *from_street*, *cross_street* and *to_street* should be labels (corresponding to :py:meth:`Link.getLabel`)
        
        *turn_type* should be one of :py:attr:`Movement.DIR_UTURN`, :py:attr:`Movement.DIR_RT`, :py:attr:`Movement.DIR_RT2`,
        :py:attr:`Movement.DIR_LT2`, :py:attr:`Movement.DIR_LT`, :py:attr:`Movement.DIR_TH`.
        """
        overrides_applied = 0
        permissions_applied = 0
        lanes_applied = 0
        
        for override in overrides:
            if len(override) < 6:
                DtaLogger.warn("Override incomplete: %s " % str(override))
                continue

            if override[0] not in [RoadLink.DIR_EB, RoadLink.DIR_WB, RoadLink.DIR_SB, RoadLink.DIR_NB]:
                DtaLogger.warn("Invalid override from_dir: %s -- skipping" % str(override[0]))
                continue

            if override[3] not in [RoadLink.DIR_EB, RoadLink.DIR_WB, RoadLink.DIR_SB, RoadLink.DIR_NB]:
                DtaLogger.warn("Invalid override to_dir: %s -- skipping" % str(override[3]))
                continue

            movement = None
            try:
                movement = self.findMovementForRoadLabels(incoming_street_label=override[1].upper(),
                                                          incoming_direction=override[0],
                                                          outgoing_street_label=override[4].upper(), 
                                                          outgoing_direction=override[3],
                                                          intersection_street_label=override[2].upper(),
                                                          roadnode_id=None,
                                                          remove_label_spaces=False,
                                                          use_dir_for_movement=False,
                                                          dir_need_not_be_primary=True)
                movement.setOverrideTurnType(override[5])
                overrides_applied += 1
                
                DtaLogger.debug("Set override turntype: %s for %s-%s (@%d) %s-%s" % (str(override),
                                                                                  movement.getIncomingLink().getLabel(),
                                                                                  movement.getIncomingLink().getDirection(),
                                                                                  movement.getAtNode().getId(), 
                                                                                  movement.getOutgoingLink().getLabel(),
                                                                                  movement.getOutgoingLink().getDirection()))

            except dta.DtaError, e:
                DtaLogger.warn("Failed to set movement override %s: %s -- skipping" % (str(override), str(e)))
                continue
            
            # handle permission
            if movement and len(override) >= 7:
                movement.setVehicleClassGroup(self._scenario.getVehicleClassGroup(override[6]))
                DtaLogger.debug("Set override permission: %s for %s-%s (@%d) %s-%s"  % (str(override),
                                                                                  movement.getIncomingLink().getLabel(),
                                                                                  movement.getIncomingLink().getDirection(),
                                                                                  movement.getAtNode().getId(), 
                                                                                  movement.getOutgoingLink().getLabel(),
                                                                                  movement.getOutgoingLink().getDirection()))
                permissions_applied += 1
                
            # handle lanes
            if movement and len(override) >= 8:
                movement.setNumLanes(int(override[7]))
                DtaLogger.debug("Set override lanes: %d for %s-%s (@%d) %s-%s" % (movement.getNumLanes(),
                                                                                  movement.getIncomingLink().getLabel(),
                                                                                  movement.getIncomingLink().getDirection(),
                                                                                  movement.getAtNode().getId(), 
                                                                                  movement.getOutgoingLink().getLabel(),
                                                                                  movement.getOutgoingLink().getDirection()))
                lanes_applied += 1        
        DtaLogger.info("Network.setMovementTurnTypeOverrides successfully applied %d out of %d turn type overrides" % (overrides_applied, len(overrides)))
        DtaLogger.info("Network.setMovementTurnTypeOverrides successfully applied %d vehicle class group permissions" % permissions_applied)
        DtaLogger.info("Network.setMovementTurnTypeOverrides successfully applied %d lane overrides" % lanes_applied)

    def addLink(self, newLink):
        """
        Verifies that:
        
         * the *newLink* is a Link
         * that the id is not already used
         * the nodepair is not already used
         
        Stores it.
        
        """ 

        if not isinstance(newLink, Link):
            raise DtaError("Network.addLink called on a non-Link: %s" % str(newLink))

        if newLink.getId() in self._linksById:
            raise DtaError("Link with id %s already exists in the network" % newLink.getId())
        if (newLink.getStartNode().getId(), newLink.getEndNode().getId()) in self._linksByNodeIdPair:
            raise DtaError("Link for nodes (%d,%d) already exists in the network" % 
                           (newLink.getStartNode().getId(), newLink.getEndNode().getId()))
        
        self._linksById[newLink.getId()] = newLink
        self._linksByNodeIdPair[(newLink.getStartNode().getId(), newLink.getEndNode().getId())] = newLink
        
        if newLink.getId() > self._maxLinkId:
            self._maxLinkId = newLink.getId()
        
        newLink.getStartNode()._addOutgoingLink(newLink)
        newLink.getEndNode()._addIncomingLink(newLink)

    
    def getLinkForId(self, linkId):
        """
        Accessor for link given the *linkId*.
        Raises :py:class:`DtaError` if not found.
        """
        if linkId in self._linksById:
            return self._linksById[linkId]
        
        raise DtaError("Network getLinkForId: none found for id %d" % linkId)
    
    def getLinkForNodeIdPair(self, nodeAId, nodeBId):
        """
        Accessor for the link given the link nodes.
        Raises :py:class:`DtaError` if not found.        
        """
        if (nodeAId,nodeBId) in self._linksByNodeIdPair:
            return self._linksByNodeIdPair[(nodeAId,nodeBId)]
        
        raise DtaError("Network getLinkForNodeIdPair: none found for (%d,%d)" % (nodeAId,nodeBId))
    
    def addMovement(self, newMovement):
        """
        Adds the movement by adding it to the movement's incomingLink
        """
        newMovement.getIncomingLink().addOutgoingMovement(newMovement)
        
    def _switchConnectorNode(self, connector, switchStart, newNode):
        """
        Helper function for insertVirtualNodeBetweenCentroidsAndRoadNodes().
         * *switchStart* is a boolean
         * *newNode* is the new node to use
        """
        if switchStart:
            oldStartNode = connector.getStartNode()
            
            # the connector should go from the newNode
            connector.setStartNode(newNode)
                
            # fix _linksByNodeIdPair
            del self._linksByNodeIdPair[(oldStartNode.getId(), connector.getEndNode().getId())]
            self._linksByNodeIdPair[(newNode.getId(), connector.getEndNode().getId())] = connector
            
        else:
            oldEndNode = connector.getEndNode()
            
            # the connector should go from the newNode
            connector.setEndNode(newNode)
                
            # fix _linksByNodeIdPair
            del self._linksByNodeIdPair[(connector.getStartNode().getId(), oldEndNode.getId())]
            self._linksByNodeIdPair[(connector.getStartNode().getId(), newNode.getId())] = connector

    def _removeDuplicateConnectors(self):
        """
        Remove duplicate connectors that connect from the
        same centroid to the same road node
        """
        vNodesToDelete = set()
        for node in self.iterCentroids():
            # this will map roadnode -> [ virtual nodes IDs ]
            result = collections.defaultdict(list)
            for vNode in node.iterAdjacentNodes():
                if not vNode.isVirtualNode(): continue
                rNode = vNode.getConnectedRoadNode()
                result[rNode.getId()].append(vNode.getId())
            
            for rNodeId in sorted(result.keys()):
                vNodes = result[rNodeId]
                if len(vNodes) == 1: continue
                # keep the virtual node with the lowest node number
                for vNodeToRemove in sorted(vNodes)[1:]:
                    vNodesToDelete.add(vNodeToRemove)

        for vNodeToDelete in vNodesToDelete:
            self.removeNode(self.getNodeForId(vNodeToDelete))
            
    def moveCentroidConnectorsFromIntersectionsToMidblocks(self, splitReverseLinks=False, moveVirtualNodeDist=None, 
                                                                  externalNodeIds=[], disallowConnectorEvalStr=None):
        """
        Remove centroid connectors from intersections and attach them to midblock locations.
        If there is not a node defining a midblock location the algorithm will split the 
        relevant links (in both directions) and attach the connector to the newly 
        created node.
        
        If *moveVirtualNodeDist* is not None, if no candidate links are found, the method will 
        try moving the :py:class:`VirtualNode` instance around to find a candidate link. 
        *moveVirtualNodeDist* is in :py:attr:`Node.COORDINATE_UNITS`

        Pass *disallowConnectorEvalStr* for a :py:class:`RoadLink` to evaluate
        whether or not it should be available for splitting for a Connector.  For example,
        *disallowConnectorEvalStr* could be ``True if self.getFacilityType() in [1,8] else False`` if links with
        facility types 1 and 8 are not splittable, say if they are freeways or ramps.
                
        Before:
        
        .. image:: /images/removeCentroidConnectors1.png
           :height: 300px
        
        After:
        
        .. image:: /images/removeCentroidConnectors2.png
           :height: 300px


        This method also adjusts the number of lanes for :py:class:`Connector` instances.  If the
        connector is a boundary connector (according to :py:meth:`Connector.isBoundaryConnector`, then
        it will adjust the number of lanes to be the sum of the incoming road links if it's an outgoing connector,
        or the sum of the outgoing road links if it's an incoming connector.  If it's not a boundary
        connector, then the number of lanes is set to match one of the incoming (if the connector is outgoing)
        or outgoing (if the connector is incoming) links.

        .. todo:: Move this last functionality to its own method and don't iterate over movements.
        
        """

        allRoadNodes = [node for node in self.iterNodes() if isinstance(node, RoadNode)]
        for node in allRoadNodes: 

            if not node.hasConnector():
                continue 
            
            if node.isJunction(countRoadNodesOnly=True):
                continue

            if node.getId() in externalNodeIds:
                continue
            
            connectors = [link for link in node.iterAdjacentLinks() if isinstance(link, Connector)]
                        
            for con in connectors:
                try:
                    self.moveCentroidConnectorFromIntersectionToMidblock(node, con, splitReverseLink=splitReverseLinks, 
                                                                         moveVirtualNodeDist=moveVirtualNodeDist,
                                                                         disallowConnectorEvalStr=disallowConnectorEvalStr) 
                    #DtaLogger.info("Removed centroid connectors from intersection %d" % node.getId())
                except DtaError, e:
                    DtaLogger.error("moveCentroidConnectorFromIntersectionToMidblock(node=%d, con=%d) errored: %s" % 
                                    (node.getId(), con.getId(), str(e)))


        self._removeDuplicateConnectors()

        #fix the number of lanes on the new connectors
        for node in self.iterNodes():

            if not node.isRoadNode():   continue 
            if not node.hasConnector(): continue
            
            # node is a roadnode with a connector
             
            if node.isIntersection():                
                for link in node.iterAdjacentLinks():
                    if link.isConnector():
                        link.setNumLanes(1) 

            movementsToDelete = []
            
            for ilink in node.iterIncomingLinks():                
                for olink in node.iterOutgoingLinks():

                    #prohibit the connector to connector movements
                    if ilink.isConnector() and olink.isConnector():
                        if ilink.hasOutgoingMovement(olink.getEndNodeId()):
                            mov = ilink.getOutgoingMovement(olink.getEndNodeId())
                            ilink.prohibitOutgoingMovement(mov)
                            #ilink.removeOutgoingMovement(mov)
                        else:
                            prohibitedMovement = Movement.simpleMovementFactory(ilink, olink,
                                 self.getScenario().getVehicleClassGroup(VehicleClassGroup.CLASSDEFINITION_PROHIBITED))
                            ilink.addOutgoingMovement(prohibitedMovement)
                        continue
                    
                    # movement already exists, continue
                    if ilink.hasOutgoingMovement(olink.getEndNode().getId()): continue

                    # fill in missing movements
                    # one of incoming or outgoing link doesn't allow all
                    vcg = self.getScenario().getVehicleClassGroup(VehicleClassGroup.CLASSDEFINITION_ALL)
                    if not ilink.allowsAll():
                        DtaLogger.warn("moveCentroidConnectorsFromIntersectionsToMidblocks: incoming link %d-%d %s %s does not allow all" % 
                                       (ilink.getStartNode().getId(), ilink.getEndNode().getId(),
                                        ilink.getLabel(), ilink.getDirection()))
                        vcg = ilink._lanePermissions[0]
                        
                    if not olink.allowsAll():
                        DtaLogger.warn("moveCentroidConnectorsFromIntersectionsToMidblocks: outgoing link %d-%d %s %s does not allow all" % 
                                       (olink.getStartNode().getId(), olink.getEndNode().getId(),
                                        olink.getLabel(), olink.getDirection()))
                        # this should really be more like an intersection between the incoming vcg and the outgoing
                        vcg = olink._lanePermissions[0]
                    
                    allowedMovement = Movement.simpleMovementFactory(ilink, olink,vcg)
                    ilink.addOutgoingMovement(allowedMovement)

            # why iterate through movements?  why not just iterate through connectors?
            # also why is this in this method and not in its own method?  for non-boundary connectors,
            # won't it just set lanes to the last movement it happens to hit on?!
            for mov in node.iterMovements():
                if not mov.isThruTurn():
                    continue
                    
                if mov.getIncomingLink().isConnector() and mov.getOutgoingLink().isRoadLink():
                    if mov.getIncomingLink().isBoundaryConnector():
                        mov.getIncomingLink().setNumLanes(sum([link.getNumLanes() for link in node.iterOutgoingLinks() if link.isRoadLink()]))
                    else:
                        mov.getIncomingLink().setNumLanes(mov.getOutgoingLink().getNumLanes())
                
                if mov.getIncomingLink().isRoadLink() and mov.getOutgoingLink().isConnector():
                    if mov.getOutgoingLink().isBoundaryConnector():
                        mov.getOutgoingLink().setNumLanes(sum([link.getNumLanes() for link in node.iterIncomingLinks() if link.isRoadLink()]))
                    else:
                        mov.getOutgoingLink().setNumLanes(mov.getIncomingLink().getNumLanes())
                            

                    
    def moveCentroidConnectorFromIntersectionToMidblock(self, roadNode, connector, splitReverseLink=False, 
                                                               moveVirtualNodeDist=None, disallowConnectorEvalStr=None):
        """
        Remove the input connector for an intersection and attach it to a midblock 
        location. If a midblock location does does not exist a RoadLink close
        to the connector is split in half and the connector is attached to the new 
        midblock location.  
        
        Pass *disallowConnectorEvalStr* for a :py:class:`RoadLink` to evaluate
        whether or not it should be available for splitting for a Connector.  For example,
        *disallowConnectorEvalStr* could be ``True if self._facilitype in [1,8]`` if links with
        facility types 1 and 8 are not splittable, say if they are freeways or ramps.
        
        If *moveVirtualNodeDist* is not None, if no candidate links are found, the method will 
        try moving the :py:class:`VirtualNode` instance around to find a candidate link. 
        *moveVirtualNodeDist* is in :py:attr:`Node.COORDINATE_UNITS`
        
        .. todo:: I would like more detail about this.  How are movements handled for VehicleClassGroups?

        """
        if not isinstance(roadNode, RoadNode):
            raise DtaError("Input Node %d is not a RoadNode" % roadNode.getId())
        if not isinstance(connector, Connector):
            raise DtaError("Input Link %s is not a Connector" % connector.getId())
        
        if not roadNode.hasConnector():
            raise DtaError("RoadNode %d does not have a connector attached to it"
                           % roadNode.getId())

        virtualNode     = connector.getVirtualNode()
        original_loc    = (virtualNode.getX(), virtualNode.getY())
        try_locs        = [original_loc]
        
        if moveVirtualNodeDist:
            try_locs.extend([(original_loc[0],                     original_loc[1]+moveVirtualNodeDist),
                             (original_loc[0]+moveVirtualNodeDist, original_loc[1]),
                             (original_loc[0],                     original_loc[1]-moveVirtualNodeDist),
                             (original_loc[0]-moveVirtualNodeDist, original_loc[1]),
                             (original_loc[0]+moveVirtualNodeDist, original_loc[1]-moveVirtualNodeDist),
                             (original_loc[0]+moveVirtualNodeDist, original_loc[1]+moveVirtualNodeDist),
                             (original_loc[0]-moveVirtualNodeDist, original_loc[1]+moveVirtualNodeDist),
                             (original_loc[0]-moveVirtualNodeDist, original_loc[1]-moveVirtualNodeDist)])
        
        for try_loc in try_locs:
            virtualNode._x = try_loc[0]
            virtualNode._y = try_loc[1]
            
            candidateLinks = roadNode.getCandidateLinksForSplitting(connector, disallowConnectorEvalStr)
            
            # no candidate links found -- try moving the virtual node
            if len(candidateLinks) == 0:
                continue
            
            nodeToAttachConnector = None

            # see if any of the candidate links already terminate in a midblock node
            for candidateLink in candidateLinks:
                
                otherNode = candidateLink.getOtherEnd(roadNode)
                if otherNode.isMidblockNode(countRoadNodesOnly=True):
                    nodeToAttachConnector = otherNode
                    break
            
            # if not, split the first candidate link
            if nodeToAttachConnector == None:
                nodeToAttachConnector = self.splitLink(candidateLinks[0], splitReverseLink=splitReverseLink)
    
            # this node is now an intersection, not a junction
            nodeToAttachConnector.geometryType = Node.GEOMETRY_TYPE_INTERSECTION 
            
            if connector.startIsRoadNode():
    
                newConnector = Connector(connector.getId(),
                                         nodeToAttachConnector,
                                         virtualNode,
                                         None,
                                         -1,  # don't assign a length
                                         connector._freeflowSpeed,
                                         connector._effectiveLengthFactor,
                                         connector._responseTimeFactor,
                                         connector._numLanes,
                                         connector._roundAbout,
                                         connector._level, 
                                         connector._label, connector.getId())
            else:
    
                newConnector = Connector(connector.getId(),
                                         virtualNode,
                                         nodeToAttachConnector,
                                         None,
                                         -1, # don't assign a length 
                                         connector._freeflowSpeed,
                                         connector._effectiveLengthFactor,
                                         connector._responseTimeFactor,
                                         connector._numLanes,
                                         connector._roundAbout,
                                         connector._level, 
                                         connector._label, connector.getId())
    
            self.removeLink(connector)
            self.addLink(newConnector)
            #TODO: do the movements 
            return newConnector
    
        # if we got here, we failed to find any candidate links
        if moveVirtualNodeDist:
            # put it back
            virtualNode._x = original_loc[0]
            virtualNode._y = original_loc[1]
            
        raise DtaError("No candidate links found for roadNode %d" % roadNode.getId())

    def addTwoWayStopControlToConnectorsAtRoadlinks(self):
        """
        Add two way stop control to :py:class:`Connector` instances when they are incoming into an intersection
        with an incoming :py:class:`RoadLink`.

        This way, vehicles on the :py:class:`Connector` will yield to vehicles on the incoming :py:class:`RoadLink`.
        If the stop is uncontrolled, vehicles will take turns from all incoming links.
        """
        two_way_stops_count = 0
        done = set()
        
        for connector in self.iterConnectors():
            # we only care about those that end at road nodes
            if not connector.endIsRoadNode(): continue
            
            roadnode = connector.getEndNode()
            
            # skip if we've already done this one
            if roadnode in done: continue
            
            # we only care if there are incoming roadlinks here
            incoming_roadlinks = False
            for inlink in roadnode.iterIncomingLinks():
                if inlink.isRoadLink():
                    incoming_roadlinks = True
                    break
            if not incoming_roadlinks: continue
            
            # set it
            roadnode.setTwoWayStopControl()
            two_way_stops_count += 1
            done.add(roadnode)
            
        dta.DtaLogger.info("addTwoWayStopControlToConnectorsAtRoadlinks: created %4d two way stops for connectors" % two_way_stops_count)

    def insertVirtualNodeBetweenCentroidsAndRoadNodes(self, startVirtualNodeId=None, startVirtualLinkId=None,
        distanceFromCentroid=0):
        """
        In some situations (for example, for a Dynameq netork), there need to be intermediate nodes between
        :py:class:`Centroid` nodes and :py:class:`RoadNode` objects.
        
        .. image:: /images/addVirtualNode_before_after.png
           :height: 300px

        If defined, the virtual nodes that will be added will begin from *startVirtualNodeId* and the
        virtual links from *startVirtualLinkId*.  The new virtual node will be placed along the connector
        link a distance away from the centroid specified by *distanceFromCentroid* (in :py:attr:`Node.COORDINATE_UNITS`),
        so it will be in the same location if that argument is specified as zero.
        """
        
        allLinkNodeIDPairs = self._linksByNodeIdPair.keys()
        modifiedConnectorCount = 0

        if startVirtualNodeId:
            if startVirtualNodeId < self._maxNodeId:
                raise DtaError("The startVirtualNodeId %d cannot be less than equal to the current max node id %d" %
                               (startVirtualNodeId, self._maxNodeId))                                
            self._maxNodeId = startVirtualNodeId 
        if startVirtualLinkId:
            if startVirtualLinkId < self._maxLinkId:
                raise DtaError("The startVirtualLinkId %d cannot be less than equal to hte current max link id %d" %
                               (startVirtualLinkId, self._maxLinkId))
            self._maxLinkId = startVirtualLinkId 
        
        
        for idPair in allLinkNodeIDPairs:
            # if we already took care of it when we did the reverse, it's not here anymore
            if idPair not in self._linksByNodeIdPair: continue
            
            connector = self._linksByNodeIdPair[idPair]
            
            # only look at connectors
            if not isinstance(connector, Connector): continue
            
            # if they connect a centroid directly to a road node
            startNode = connector.getStartNode()
            endNode   = connector.getEndNode()
            
            # Centroid => RoadNode
            if isinstance(startNode, Centroid) and connector.endIsRoadNode():
                #DtaLogger.debug("Inserting virtualNode in Centroid(%6d) => RoadNode(%6d)" % (startNode.getId(), endNode.getId()))

                try:
                    (newX,newY) = connector.coordinatesAlongLink(fromStart=True, distance=distanceFromCentroid, goPastEnd=True)
                except DtaError, e:
                    (newX,newY) = (startNode.getX(), startNode.getY())
                    
                newNode = VirtualNode(id=self._maxNodeId + 1, x=newX, y=newY)
                self.addNode(newNode)

                DtaLogger.debug("Network.insertVirtualNodeBetweenCentroidsAndRoadNodes() added virtual node %d between Centroid %d and RoadNode %d (conn len=%f)" %
                                (newNode.getId(), startNode.getId(), endNode.getId(), connector.euclideanLength()))

                
                # switch the node out
                self._switchConnectorNode(connector, switchStart=True, newNode=newNode)
                
                newConnector = None

                # add the virtualLink
                self.addLink(VirtualLink(id=self._maxLinkId + 1, startNode=startNode, endNode=newNode, label=None))
                    
                # tally
                modifiedConnectorCount += 1
                
                # do it for the reverse
                if (endNode.getId(),startNode.getId()) in self._linksByNodeIdPair:
                    reverseConnector = self._linksByNodeIdPair[(endNode.getId(),startNode.getId())]
                    # switch the node out
                    self._switchConnectorNode(reverseConnector, switchStart=False, newNode=newNode)
                    # add the virtualLink
                    self.addLink(VirtualLink(id=self._maxLinkId + 1, startNode=newNode, endNode=startNode, label=None))
                    # tally
                    modifiedConnectorCount += 1

            
            # RoadNode => Centroid               
            elif connector.startIsRoadNode() and isinstance(endNode, Centroid):
                #DtaLogger.debug("Inserting virtualNode in RoadNode(%6d) => Centroid(%6d)" % (startNode.getId(), endNode.getId()))

                try:
                    (newX,newY) = connector.coordinatesAlongLink(fromStart=False, distance=distanceFromCentroid, goPastEnd=True)
                except DtaError, e:
                    (newX,newY) = (startNode.getX(), startNode.getY())                            
                
                newNode = VirtualNode(id=self._maxNodeId+1, x=newX, y=newY)
                self.addNode(newNode)

                DtaLogger.debug("Network.insertVirtualNodeBetweenCentroidsAndRoadNodes() added virtual node %d between RoadNode %d and Centroid %d (conn len=%f)" %
                                (newNode.getId(), startNode.getId(), endNode.getId(), connector.euclideanLength()))
                
                # switch the node out
                self._switchConnectorNode(connector, switchStart=False, newNode=newNode)
                # add the virtualLink
                self.addLink(VirtualLink(id=self._maxLinkId + 1, startNode=newNode, endNode=endNode, label=None))
                # tally
                modifiedConnectorCount += 1
                            
                # do it for the reverse
                if (endNode.getId(),startNode.getId()) in self._linksByNodeIdPair:
                    reverseConnector = self._linksByNodeIdPair[(endNode.getId(),startNode.getId())]
                    # switch the node out
                    self._switchConnectorNode(reverseConnector, switchStart=True, newNode=newNode)
                    # add the virtualLink
                    self.addLink(VirtualLink(id=self._maxLinkId + 1, startNode=endNode, endNode=newNode, label=None))
                    # tally
                    modifiedConnectorCount += 1

        
        DtaLogger.info("Network.insertVirtualNodeBetweenCentroidsAndRoadNodes() modified %d connectors" % modifiedConnectorCount)


    def iterNodes(self):
        """
        Return an iterator to the node collection
        """
        return self._nodes.itervalues()

    def iterCentroids(self):
        """
        Return an iterator to the road node collection
        """
        for node in self.iterNodes():
            if node.isCentroid():
                yield node

    def iterRoadNodes(self):
        """
        Return an iterator to the :py:class:`RoadNode` instances in the network.
        """
        for node in self.iterNodes():
            if node.isRoadNode():
                yield node

    def iterVirtualNodes(self):
        """
        Return an iterator to the :py:class:`VirtualNode` instances in the network.
        """
        for node in self.iterNodes():
            if isinstance(node, VirtualNode):
                yield node

    def iterCentroids(self):
        """
        Return an iterator to the :py:class:`Centroid` instances in the network.
        """
        for node in self.iterNodes():
            if isinstance(node, Centroid):
                yield node

    def iterLinks(self):
        """
        Return an iterator to the link collection
        """
        return self._linksById.itervalues()

    def iterRoadLinks(self):
        """
        Return an iterator for to the :py:class:`RoadLink` instances in the network that are
        not instances of :py:class:`Connector`.
        """
        for link in self.iterLinks():
            if link.isRoadLink():
                yield link

    def iterConnectors(self):
        """
        Return an iterator to the :py:class:`Connector` instances in the network.
        """
        for link in self.iterLinks():
            if link.isConnector():
                yield link

    def iterVirtualLinks(self):
        """
        Return an iterator to the :py:class:`VirtualLink` instances in the network.
        """
        for link in self.iterLinks():
            if isinstance(link, VirtualLink):
                yield link
    
    def iterMovements(self):
        """
        Returns an iterator to all the :py:class:`Movement` instances in the network by
        iterating through links (sorted by ID) and their outgoing movements.
        """
        for linkId in sorted(self._linksById.keys()):
            # only roadlinks and connectors have movements
            if (not isinstance(self._linksById[linkId], RoadLink) and
                not isinstance(self._linksById[linkId], Connector)):
                continue
            
            for movement in self._linksById[linkId].iterOutgoingMovements():
                yield movement

    def hasCustomPriorities(self):
        """
        Does this network have custom priorities?  i.e. Were custom priorities set via :py:meth:`Movement.addHigherPriorityMovement` ?
        """
        for movement in self.iterMovements():
            for (higherprio_movement, critical_gap, critical_wait) in movement.iterHigherPriorityMovements():
                # found one
                return True
        return False

    def hasNodeForId(self, nodeId):
        """
        Return True if there is a node with the given id
        """
        try:
            self.getNodeForId(nodeId)
            return True
        except DtaError:
            return False
            
    def hasCentroidForId(self, nodeId):
        """
        Return True if there is a centroid with the given id
        """
        try:
            node = self.getNodeForId(nodeId)
            if node.isCentroid():
                return True
            return False
        except DtaError:
            return False
    
    def hasLinkForId(self, linkId):
        """
        Return True if a link with the given id exists
        """
        try:
            self.getLinkForId(linkId)
            return True
        except DtaError:
            return False

    def hasLinkForNodeIdPair(self, startNodeId, endNodeId):
        """
        Return True if the network has a link with the given node ids 
        """
        try:
            self.getLinkForNodeIdPair(startNodeId, endNodeId)
            return True
        except DtaError:
            return False

    def findNodeNearestCoords(self, x, y, quick_dist=None):
        """
        Iterates though :py:class:`RoadNode` instances and returns 
        the node closest to (*x*, *y*), as well as the distance.
        
        Uses *quick_dist* (if passed) to skip skip distance calcs and ignore anything
        greater than *quick_dist* difference in either coordinate.
        
        So the return is a tuple: (distance, RoadNode)
        
        *x*,*y* and *quick_dist* are  in :py:attr:`Node.COORDINATE_UNITS`
        """
        min_dist     = sys.float_info.max
        closest_node = None
        
        for roadnode in self.iterRoadNodes():
            
            if quick_dist and abs(roadnode.getX()-x) > quick_dist: continue
            if quick_dist and abs(roadnode.getY()-y) > quick_dist: continue
            
            dist = math.sqrt( (roadnode.getX()-x)**2 + (roadnode.getY()-y)**2 )
            if dist < min_dist:
                min_dist = dist
                closest_node = roadnode
        
        return (min_dist, closest_node)

    def findNodeForRoadLabels(self, road_label_list, CUTOFF):
        """ 
        Finds matching node for a set of road labels and returns a :py:class:`RoadNode` instance.
        
          * *road_label_list* a list of road names e.g. [mission st, 6th st]

        This method will provide an approximate matching if CUTOFF  is less than one. From
        our experience a CUTOFF of 0.7 provides good results
        
        """
        #print "Trying to find: %s" % (", ".join(road_label_list) )
        #CutoffBase = CUTOFF
        CutoffBase = 0.8
        road_label_list_u = [label.upper() for label in road_label_list]
        for roadnode in self.iterRoadNodes():
            matches = 0
            streetnames = roadnode.getStreetNames(incoming=True, outgoing=True)
            #if len(road_label_list) != len(streetnames):
            #    continue
            baseStreetNames = [self.getCleanStreetName(bs) for bs in streetnames]

            matched = []
            for idx2 in range(len(baseStreetNames)):
                for idx in range(len(road_label_list_u)):
                    if len(baseStreetNames[idx2]) != len(road_label_list_u[idx]):
                        continue
                    
                    street = str(road_label_list_u[idx])
                    street = street[:1]
                    try:
                        street = int(street)
                    except:
                        CUTOFF = CutoffBase
                    if isinstance(street,int) or road_label_list_u[idx]=="GREAT" or road_label_list_u=="GRANT":
                        CUTOFF=0.9
                    if not difflib.get_close_matches(road_label_list_u[idx], [baseStreetNames[idx2]], 1, CUTOFF):
                        continue
                    else:
                        if not difflib.get_close_matches(baseStreetNames[idx2], [road_label_list_u[idx]], 1, CUTOFF):
                            continue
                        elif road_label_list_u[idx] in matched:
                            continue
                        else:
                            matched.append(road_label_list_u[idx])
                            matches +=1
                            if matches >= len(road_label_list_u):
                                dta.DtaLogger.info("Matched %d names in intersection %s to street names %s" % (matches,baseStreetNames,road_label_list_u))
                                return roadnode

        dta.DtaLogger.error("Couldn't find intersection with %s in the Network" % road_label_list_u)            
        raise DtaError("findNodeForRoadLabels: Couldn't find intersection with %s in the Network" % 
                        (", ".join(road_label_list)  )  )
            
##            for idx in range(len(streetnames)):
##                for label_street in road_label_list_u:
##                    if label_street in str(streetnames[idx]):
##                        streetmatch += 1
##
##            if streetmatch >= len(road_label_list_u):
##                return roadnode

    def getCleanStreetName(self,streetName):

        corrections = {"TWELFTH":"12TH", 
                       "ELEVENTH":"11TH",
                       "TENTH":"10TH",
                       "NINTH":"9TH",
                       "EIGHTH":"8TH",
                       "SEVENTH":"7TH",
                       "SIXTH":"6TH",
                       "FIFTH":"5TH",
                       "FOURTH":"4TH",
                       "THIRD":"3RD",
                       "SECOND":"2ND",
                       "FIRST":"1ST",
                       "O'FARRELL":"O FARRELL",
                       "3RDREET":"3RD",
                       "EMBARCADERO/KING":"THE EMBARCADERO",
                       "VAN NESSNUE":"VAN NESS",
                       "3RD #3":"3RD",
                       "BAYSHORE #3":"BAYSHORE",
                       "09TH":"9TH",
                       "08TH":"8TH",
                       "07TH":"7TH",
                       "06TH":"6TH",
                       "05TH":"5TH",
                       "04TH":"4TH",
                       "03RD":"3RD",
                       "02ND":"2ND",
                       "01ST":"1ST"}


        itemsToRemove = [" STREETS",
                         " STREET",
                         " STS.",
                         " STS",
                         " ST.",
                         " ST",
                         " ROAD",
                         " RD.",
                         " RD",
                         " AVENUE",
                         " AVE.",
                         " AVES",
                         " AVE",
                         " BLVD.",
                         " BLVD",
                         " BOULEVARD",
                         "MASTER:",
                         " DRIVE",
                         " DR.",
                         " WAY",
                         " WY",
                         " CT",
                         " TERR",
                         " HWY",
                         " PL",
                         " AL",
                         " LN",
                         " NORTHBOUND",
                         " SOUTHBOUND",
                         " Ave",
                         " St"]

        newStreetName = streetName.strip()
        for wrongName, rightName in corrections.items():
            if wrongName in streetName:
                newStreetName = streetName.replace(wrongName, rightName)
            if newStreetName == 'EMBARCADERO':
                newStreetName = "THE EMBARCADERO"
            if newStreetName.endswith(" DR"):
                newStreetName = newStreetName[:-3]
            if newStreetName.endswith(" AV"):
                newStreetName = newStreetName[:-3]
            if newStreetName.endswith(" AVE"):
                newStreetName = newStreetName[:-4]
            if newStreetName.endswith(" ST"):
                newStreetName = newStreetName[:-3]
        streetName = newStreetName.strip()
        for item in itemsToRemove:
            if item in streetName:
                newStreetName = streetName.replace(item,"")

        return newStreetName.strip()

    

    def cleanStreetNames(self,streetNames):
        """Accept street names as a list and return a list 
        with the cleaned street names"""
    
        newStreetNames = map(self.cleanStreetName, streetNames)
        if len(newStreetNames) > 1 and newStreetNames[0] == "":
            newStreetNames.pop(0)
        return newStreetNames

    def findNRoadLinksNearestCoords(self, x, y, n=1, quick_dist = None):
        """
        Iterates though :py:class:`RoadLink` instances and returns the *n* closest
        road links to the given (*x*, *y*) coordinates.
        
        If *n* = 1, returns a 3-tuple (*roadlink*, *distance*, *t*).  
        The *roadlink* is the closest :py:class:`RoadLink` instance to (*x*, *y*),
        the *distance* is the distance between (*x*, *y*) and the *roadlink*, and 
        *t* is in [0,1] and indicates how far along from the start point and end point
        of the *roadlink* lies the closest point to (*x*, *y*).
        
        If *n* > 1: returns a list of 3-tuples as described above, sorted by the *distance*
        values.
        
        Uses *quick_dist* (if passed) to skip skip distance calcs and ignore anything
        greater than *quick_dist* difference in either coordinate.
        Returns (None, None, None) if none found and *n* = 1, or an empty list for *n* > 1
                
        *x*,*y* and *quick_dist* are  in :py:attr:`Node.COORDINATE_UNITS`
        """
        min_dist            = sys.float_info.max
        return_tuples       = []
        
        for roadlink in self.iterRoadLinks():
            # quickly rule out if a quick_dist is specified
            if quick_dist:
                # real dist threshhold - it could be a long link and the (x,y) is in the center
                dthres = max(quick_dist, 1.25*roadlink.getLengthInCoordinateUnits())
                     
                if x + dthres < min(roadlink.getStartNode().getX(), roadlink.getEndNode().getX()): continue
                if x - dthres > max(roadlink.getStartNode().getX(), roadlink.getEndNode().getX()): continue
                if y + dthres < min(roadlink.getStartNode().getY(), roadlink.getEndNode().getY()): continue
                if y - dthres > max(roadlink.getStartNode().getY(), roadlink.getEndNode().getY()): continue

            (dist, t) = roadlink.getDistanceFromPoint(x,y)
            if dist < min_dist:
                return_tuples.append( (roadlink, dist, t))
                
                # sort
                return_tuples = sorted(return_tuples, key=operator.itemgetter(1))
                
                # kick out extras
                if len(return_tuples) > n:
                    return_tuples.pop()
                    
                min_dist            = return_tuples[-1][1]
        
        if n==1:
            if len(return_tuples) == 0: 
                return (None, None, None)
            return return_tuples[0]

        return return_tuples
                            
    def findLinksForRoadLabels(self, on_street_label, on_direction,
                                       from_street_label, to_street_label,
                                       remove_label_spaces=False):
        """
        Attempts to find the link(s) with the given *on_street_label* and *on_direction*
        from the street matching *from_street_label* to the street matching *to_street_label*.
        
        *on_street_label*, *from_street_label* and *to_street_label* are checked against 
        :py:class:`RoadLink` labels and should be upper-case.  If *remove_label_spaces* is True, then
        the labels will have their spaces stripped before comparison.
        
        *on_direction* is one of :py:attr:`RoadLink.DIR_EB`, :py:attr:`RoadLink.DIR_NB`,
        :py:attr:`RoadLink.DIR_WB` or :py:attr:`RoadLink.DIR_SB`.
        
        Raises a :py:class:`DtaError` on failure, returns a list of :py:class:`RoadLink` instances on success.
        """
        # first find candidates for the two intersections in question
        roadnode_from = []
        roadnode_to   = []
            
        for roadnode_candidate in self.iterRoadNodes():
            # check the streets match
            streetnames = roadnode_candidate.getStreetNames(incoming=True, outgoing=True)
            if remove_label_spaces: streetnames = [s.replace(" ","") for s in streetnames]
            
            if on_street_label in streetnames and from_street_label in streetnames:
                roadnode_from.append(roadnode_candidate)
            
            if on_street_label in streetnames and to_street_label in streetnames:
                roadnode_to.append(roadnode_candidate)


        # Did we fail to find an intersection?
        if len(roadnode_from)==0:
            raise DtaError("findLinksForRoadLabels: Couldn't find intersection1 with %s and %s in the Network" % 
                           (on_street_label, from_street_label))
        
        if len(roadnode_to)==0:
            raise DtaError("findLinksForRoadLabels: Couldn't find intersection2 with %s and %s in the Network" % 
                           (on_street_label, to_street_label))
        
        # Debug output
        if False:            
            debug_from = ""
            for r in roadnode_from:
                if len(debug_from) > 0: debug_from += ","
                debug_from += str(r.getId())
            debug_to = ""
            for r in roadnode_to:
                if len(debug_to) > 0: debug_to += ","
                debug_to += str(r.getId())
            DtaLogger.debug("from: %s  to: %s" % (debug_from, debug_to))
        
        debug_str = ""
        
        # try each candidate from node
        for start_node in roadnode_from:
            
            # Walk from the from node
            curnode = start_node
            return_links = []
            
            while True:
                
                # look for the next link
                outgoing_link = None
                for olink in curnode.iterOutgoingLinks():                
                    olabel = olink.getLabel().upper()
                    if remove_label_spaces: olabel = olabel.replace(" ","")            
                    
                    # DtaLogger.debug("olink %s %s" % (olabel, olink.getDirection() if olink.isRoadLink else "nonroad"))
                    
                    # for now, require all links have the given direction
                    if olink.isRoadLink() and olabel==on_street_label and olink.getDirection()==on_direction:
                        outgoing_link = olink
                        break
                    
                # nothing found - we got stuck
                if not outgoing_link:
                    debug_str += "findLinksForRoadLabels: Couldn't find links from %s to %s on %s %s from %d; "% \
                                 (from_street_label, to_street_label, on_street_label, on_direction, curnode.getId())
                    break
                    
                # found it; -- make sure it's not already in our list (cycle!)
                if outgoing_link in return_links:
                    debug_str += "findLinksForRoadLabels: Found cycle when finding links from %s to %s on %s %s; " % \
                                 (from_street_label, to_street_label, on_street_label, on_direction)
                    break
    
                # add to our list
                return_links.append(outgoing_link)
                
                # we're finished if we got to the end
                if outgoing_link.getEndNode() in roadnode_to:
                    return return_links
                
                # continue on
                curnode = outgoing_link.getEndNode()
            
            # ok if we've gotten here, then we reached a break and we were unsuccessful
            # so we'll continue with the next road_node_from
            # DtaLogger.debug("Failure")
            
        # if we've gotten here then all attempts have failed
        raise DtaError(debug_str)
                
    def findMovementForRoadLabels(self, incoming_street_label, incoming_direction, 
                                            outgoing_street_label, outgoing_direction,
                                            intersection_street_label=None,
                                            roadnode_id=None,
                                            remove_label_spaces=False,
                                            use_dir_for_movement=True,
                                            dir_need_not_be_primary=False):
        """
        Attempts to find the movement from the given *incoming_street_label* and *incoming_direction*
        to the given *outgoing_street_label* and *outgoing_direction*.  If this is a through movement or a U-Turn
        (e.g. *incoming_street_label* == *outgoing_street_label*), then *intersection_street_label* is also required
        to identify the intersection.
        
        *incoming_street_label*, *outgoing_street_label* and *intersection_street_label* are checked against 
        :py:class:`RoadLink` labels and should be upper-case.  If *remove_label_spaces* is True, then
        the labels will have their spaces stripped before comparison.
        
        *incoming_direction* and *outgoing_direction* are one of :py:attr:`RoadLink.DIR_EB`, :py:attr:`RoadLink.DIR_NB`,
        :py:attr:`RoadLink.DIR_WB` or :py:attr:`RoadLink.DIR_SB`.
        
        Pass optional *roadnode_id* to speed things up but if the movement is not found for that :py:class:`RoadNode`,
        this method will fall back and try to find the movement based on the labels.
        
        Pass *use_dir_for_movement* as True if the *incoming_street_label* and *outgoing_street_label* are useful
        for identifying the intersection but not necessary for the movement (e.g. only the direction needs to match)
        
        Pass *dir_need_not_be_primary* as True if the direction matching should be loose; e.g. 
        if :py:attr:`RoadLink.DIR_EB` means the link must be going eastbound *somewhat* even if it's really heading
        south east and so :py:meth:`RoadLink.getDirection` returns :py:attr:RoadLink.DIR_SB`.
        
        Raises a :py:class:`DtaError` on failure, returns a :py:class:`Movement` instance on success.
        """
        
        if (incoming_street_label==outgoing_street_label) and (intersection_street_label==None):
            raise DtaError("findMovementForRoadLabels: intersection_street_label is required when "
                           "incoming_street_label==outgoing_street_label (%s)" % incoming_street_label)
            
        roadnode = None
        
        # see if the the given id will do it
        if roadnode_id:
            
            if roadnode_id in self._nodes:
                roadnode = self.getNodeForId(roadnode_id)
            
            if not isinstance(roadnode, RoadNode):
                roadnode = None
                DtaLogger.debug("findMovementForRoadLabels: given RoadNode id %d isn't a valid road node" % roadnode_id)
            else:
                # check the streets match
                streetnames = roadnode.getStreetNames(incoming=True, outgoing=True)
                if remove_label_spaces: streetnames = [s.replace(" ","") for s in streetnames]
                
                if incoming_street_label not in streetnames:
                    roadnode = None
                    DtaLogger.debug("findMovementForRoadLabels: given RoadNode %d doesn't have incoming street %s (streets are %s)" %
                                    (roadnode_id, incoming_street_label, str(streetnames)))
                if outgoing_street_label not in streetnames:
                    roadnode = None
                    DtaLogger.debug("findMovementForRoadLabels: given RoadNode %d doesn't have outgoing street %s (streets are %s)" %
                                    (roadnode_id, outgoing_street_label, str(streetnames)))
                    
        # Still haven't found the right roadnode; look for it
        if roadnode==None:
            
            for roadnode_candidate in self.iterRoadNodes():
                # check the streets match
                streetnames = roadnode_candidate.getStreetNames(incoming=True, outgoing=True)
                if remove_label_spaces: streetnames = [s.replace(" ","") for s in streetnames]
                
                if ((incoming_street_label in streetnames) and (outgoing_street_label in streetnames) and \
                    ((intersection_street_label == None) or (intersection_street_label in streetnames))):
                    roadnode = roadnode_candidate
                    break
            
        # Still haven't found it - give up
        if roadnode==None:
            raise DtaError("findMovementForRoadLabels: Couldn't find intersection with %s and %s in the Network" % 
                           (incoming_street_label, outgoing_street_label))
        
        #DtaLogger.debug("Found intersection with %s and %s in the network: %d %s" % 
        #                (incoming_street_label, outgoing_street_label, roadnode.getId(), str(roadnode.getStreetNames())))
        
        # Found the intersection; now find the exact incoming link
        candidate_links = {} # dir -> { name -> link }
        for ilink in roadnode.iterIncomingLinks():
            if not ilink.isRoadLink(): continue
            
            dir = ilink.getDirection(atEnd=True)
            if dir not in candidate_links: candidate_links[dir] = {}
            
            label = ilink.getLabel().upper()
            if remove_label_spaces: label = label.replace(" ","")
            candidate_links[dir][label] = ilink
        
        incoming_link = None
        # the direction is enough
        if use_dir_for_movement and incoming_direction in candidate_links and len(candidate_links[incoming_direction])==1:
            incoming_link = candidate_links[incoming_direction].values()[0]
        
        # direction is ambiguous but both match
        elif incoming_direction in candidate_links and incoming_street_label in candidate_links[incoming_direction]:
            incoming_link = candidate_links[incoming_direction][incoming_street_label]
        
        # dir need not be parimary -- use hasDirection
        elif dir_need_not_be_primary:
            for dir in candidate_links:
                for label in candidate_links[dir]:
                    if use_dir_for_movement and candidate_links[dir][label].hasDirection(incoming_direction):
                        incoming_link = candidate_links[dir][label]
                        break
                    
                    if incoming_street_label == label and candidate_links[dir][label].hasDirection(incoming_direction):
                        incoming_link = candidate_links[dir][label]
                        break
        
        # failed
        if not incoming_link:
            candidate_str = ""
            for dir in candidate_links: candidate_str += dir + ":" + ",".join(candidate_links[dir].keys()) + "  "
            raise DtaError("findMovementForRoadLabels: Couldn't find incoming link %s %s at %s: %s" %
                            (incoming_street_label, incoming_direction, intersection_street_label, candidate_str))
       
        # Found the intersection; now find the exact outgoing link      
        candidate_links = {} # dir -> { name -> link }
        for olink in roadnode.iterOutgoingLinks():
            if not olink.isRoadLink(): continue
            
            dir = olink.getDirection(atEnd=False)
            if dir not in candidate_links: candidate_links[dir] = {}
            
            label = olink.getLabel().upper()
            if remove_label_spaces: label = label.replace(" ","")
            candidate_links[dir][label] = olink
        
        outgoing_link = None
        # the direction is enough
        if use_dir_for_movement and outgoing_direction in candidate_links and len(candidate_links[outgoing_direction])==1:
            outgoing_link = candidate_links[outgoing_direction].values()[0]
        
        # direction is ambiguous but both match
        elif outgoing_direction in candidate_links and outgoing_street_label in candidate_links[outgoing_direction]:
            outgoing_link = candidate_links[outgoing_direction][outgoing_street_label]
            
        # dir need not be parimary -- use hasDirection
        elif dir_need_not_be_primary:
            for dir in candidate_links:
                for label in candidate_links[dir]:
                    if use_dir_for_movement and candidate_links[dir][label].hasDirection(outgoing_direction):
                        outgoing_link = candidate_links[dir][label]
                        break
                    
                    if outgoing_street_label == label and candidate_links[dir][label].hasDirection(outgoing_direction):
                        outgoing_link = candidate_links[dir][label]
                        break        
        # failed
        if not outgoing_link:
            candidate_str = ""
            for dir in candidate_links: candidate_str += dir + ":" + ",".join(candidate_links[dir].keys()) + "  "
            raise DtaError("findMovementForRoadLabels: Couldn't find outgoing link %s %s at %s: %s" %
                            (outgoing_street_label, outgoing_direction, intersection_street_label, candidate_str))            


        return incoming_link.getOutgoingMovement(outgoing_link.getEndNode().getId())
                                                                   
    def removeLink(self, linkToRemove):
        """
        Remove the input link from the network
        """
        #remove all incoming and ougoing movements from the link 
        if not linkToRemove.isVirtualLink():
            outMovsToRemove = [mov for mov in linkToRemove.iterOutgoingMovements()]
            inMovsToRemove = [mov for mov in linkToRemove.iterIncomingMovements()]

            for mov in outMovsToRemove:
                linkToRemove._removeOutgoingMovement(mov)

            for mov in inMovsToRemove:
                mov.getIncomingLink()._removeOutgoingMovement(mov)

        linkToRemove.getStartNode()._removeOutgoingLink(linkToRemove)
        linkToRemove.getEndNode()._removeIncomingLink(linkToRemove)

        del self._linksById[linkToRemove.getId()]
        del self._linksByNodeIdPair[linkToRemove.getStartNode().getId(),
                                linkToRemove.getEndNode().getId()]
        #TODO: do you want to update the maxIds?

    def removeNode(self, nodeToRemove):
        """
        Remove the input node from the network
        """
        if not self.hasNodeForId(nodeToRemove.getId()):
            raise DtaError("Network does not have node %d" % nodeToRemove.getId())
        
        linksToRemove = []
        for link in nodeToRemove.iterAdjacentLinks():
            linksToRemove.append(link)

        for link in linksToRemove:
            self.removeLink(link) 
        
        del self._nodes[nodeToRemove.getId()] 
        
        #TODO: do you want to update the maxIds? 

    def _split(self, linkToSplit, midNode, length1, length2, shapelen1): 
        """
        Helper function for splitting links. 
         
        * *linkToSplit* is the link to be split
        * *midNode* is the new node
        * *length1* and *length2* are the lengths of the new facilities, respectively, in :py:attr:`RoadLink.LENGTH_UNITS`
        * *shapelen1* is indicates how many shape points will go to link1 (the rest will go to link 2)

        """
        
        newLink1 = RoadLink(self._maxLinkId + 1,
                            linkToSplit.getStartNode(), 
                            midNode, 
                            None,
                            linkToSplit._facilityType,
                            length1,
                            linkToSplit._freeflowSpeed,
                            linkToSplit._effectiveLengthFactor,
                            linkToSplit._responseTimeFactor,
                            linkToSplit._numLanes,
                            linkToSplit._roundAbout,
                            linkToSplit._level, 
                            linkToSplit.getLabel(),
                            self._maxLinkId + 1)
        newLink1._lanePermissions = copy.copy(linkToSplit._lanePermissions)
        newLink1.setTollLink(linkToSplit.getTollLink())
        newLink1._shapePoints = linkToSplit._shapePoints[:shapelen1]
        self.addLink(newLink1)

        newLink2 = RoadLink(self._maxLinkId + 1,
                            midNode, 
                            linkToSplit.getEndNode(), 
                            None,
                            linkToSplit._facilityType,
                            length2,
                            linkToSplit._freeflowSpeed,
                            linkToSplit._effectiveLengthFactor,
                            linkToSplit._responseTimeFactor,
                            linkToSplit._numLanes,
                            linkToSplit._roundAbout,
                            linkToSplit._level,
                            linkToSplit.getLabel(),
                            self._maxLinkId + 1)
        newLink2._lanePermissions = copy.copy(linkToSplit._lanePermissions)
        newLink2.setTollLink(0)
        shapelen2 = len(linkToSplit._shapePoints) - shapelen1
        if shapelen2 > 0:
            newLink2._shapePoints = linkToSplit._shapePoints[-shapelen2:]
        self.addLink(newLink2) 

        for inMov in linkToSplit.iterIncomingMovements():

            newMovement = Movement(linkToSplit.getStartNode(),
                                   inMov.getIncomingLink(),
                                   newLink1,
                                   inMov._freeflowSpeed,
                                   inMov._permission,
                                   inMov._numLanes,
                                   inMov._incomingLane,
                                   inMov._outgoingLane,
                                   inMov._followupTime)


            inMov.getIncomingLink().addOutgoingMovement(newMovement)

        for outMov in linkToSplit.iterOutgoingMovements():

            newMovement = Movement(linkToSplit.getEndNode(),
                                   newLink2,
                                   outMov.getOutgoingLink(),
                                   outMov._freeflowSpeed,
                                   outMov._permission,
                                   outMov._numLanes,
                                   outMov._incomingLane,
                                   outMov._outgoingLane,
                                   outMov._followupTime)

            newLink2.addOutgoingMovement(newMovement)

        # if one of incoming or outgoing link doesn't allow all
        vcg = self.getScenario().getVehicleClassGroup(VehicleClassGroup.CLASSDEFINITION_ALL)
        if not newLink1.allowsAll():
            DtaLogger.warn("splitLink: incoming link %d-%d %s %s does not allow all" % 
                           (newLink1.getStartNode().getId(), newLink1.getEndNode().getId(),
                            newLink1.getLabel(), newLink1.getDirection()))
            vcg = newLink1._lanePermissions[0]
            
        if not newLink2.allowsAll():
            DtaLogger.warn("splitLink: outgoing link %d-%d %s %s does not allow all" % 
                           (newLink2.getStartNode().getId(), newLink2.getEndNode().getId(),
                            newLink2.getLabel(), newLink2.getDirection()))
            # this should really be more like an intersection between the incoming vcg and the outgoing
            vcg = newLink2._lanePermissions[0]

        newMovement = Movement(midNode,
                               newLink1,
                               newLink2,
                               newLink1._freeflowSpeed,
                               vcg,
                               newLink1._numLanes,
                               incomingLane=0,
                               outgoingLane=newLink1._numLanes)
        newLink1.addOutgoingMovement(newMovement)

    def splitLink(self, linkToSplit, splitReverseLink=False, fraction=0.5):
        """
        Split the input link at *fraction* of the way along the link. The two new links have the 
        attributes of the input link. If there is a link in the 
        opposing direction then split that too.
        
        Takes the shape into account when splitting.
        
        .. todo:: Document the how the movements are handled, especially regarding VehicleClassGroups.
                  Currently it looks like an ALL and a PROHIBITED are required?
        """ 
        if isinstance(linkToSplit, VirtualLink):
            raise DtaError("Virtual link %s cannot be split" % linkToSplit.getId())
        if isinstance(linkToSplit, Connector):
            raise DtaError("Connector %s cannot be split" % linkToSplit.getId())
        if fraction < 0.01 or fraction > 0.99:
            raise DtaError("Network.splitLink() fraction must be in (0.01,0.99): %f" % fraction)

        total_length = linkToSplit.getLength()
        length1      = total_length*fraction
        length2      = total_length*(1.0-fraction)
        
        (midX, midY, shpidx) = linkToSplit.coordinatesAndShapePointIdxAlongLink(fromStart=True, 
                                                                                distance=fraction*linkToSplit.euclideanLength(includeShape=True),
                                                                                goPastEnd=False)

        midNode = RoadNode(self._maxNodeId + 1, midX, midY, 
                           RoadNode.GEOMETRY_TYPE_JUNCTION,
                           RoadNode.CONTROL_TYPE_UNSIGNALIZED,
                           RoadNode.PRIORITY_TEMPLATE_NONE)

        self.addNode(midNode)

        self._split(linkToSplit, midNode, length1, length2, shpidx) 

        # split the reverse link if it exists
        if splitReverseLink and self.hasLinkForNodeIdPair(linkToSplit.getEndNode().getId(), 
                                                          linkToSplit.getStartNode().getId()):
            
                linkToSplit2 = self.getLinkForNodeIdPair(linkToSplit.getEndNode().getId(),
                                                         linkToSplit.getStartNode().getId())
                
                # assume the reverse link has the same number of shape points
                self._split(linkToSplit2, midNode, length2, length1, linkToSplit2.getNumShapePoints()-shpidx)
                self.removeLink(linkToSplit2)

                # prohibit U-Turns at the split
                link1 = self.getLinkForNodeIdPair(linkToSplit.getStartNode().getId(), midNode.getId())
                link2 = self.getLinkForNodeIdPair(midNode.getId(), linkToSplit.getStartNode().getId())
                
                prohibitedMovement = Movement.simpleMovementFactory(link1, link2,
                     self.getScenario().getVehicleClassGroup(VehicleClassGroup.CLASSDEFINITION_PROHIBITED))
                link1.addOutgoingMovement(prohibitedMovement)

                link1 = self.getLinkForNodeIdPair(linkToSplit.getEndNode().getId(), midNode.getId())
                link2 = self.getLinkForNodeIdPair(midNode.getId(), linkToSplit.getEndNode().getId())
                
                prohibitedMovement = Movement.simpleMovementFactory(link1, link2,
                     self.getScenario().getVehicleClassGroup(VehicleClassGroup.CLASSDEFINITION_PROHIBITED))
                link1.addOutgoingMovement(prohibitedMovement)

        self.removeLink(linkToSplit)
                      
        return midNode 

    def getNumVirtualLinks(self):
        """
        Return the number of connectors in the Network
        """
        return sum([1 for link in self.iterLinks() if link.isVirtualLink()])

    def getNumConnectors(self):
        """
        Return the number of connectors in the Network
        """
        return sum([1 for link in self.iterLinks() if link.isConnector()])

    def getNumRoadLinks(self):
        """
        Return the number of RoadLinks in the Network(excluding connectors)
        """
        return sum([1 for link in self.iterLinks() if link.isRoadLink()])

    def getNumTimePlans(self):
        """
        Return the number of nodes with a time plan
        """
        num = 0
        for node in self.iterRoadNodes():
            if node.hasTimePlan():
                num += 1
        return num
               
    def getScenario(self):
        """
        Return the scenario object associated with this network
        """
        return self._scenario 

    def areIDsUnique(self, net2):
        """
        Returns True if the node and link Ids are unique 
        """
        areIDsUnique = True
        #RoadNodes 
        nodeIds1 = set([node.getId() for node in self.iterRoadNodes()])
        nodeIds2 = set([node.getId() for node in net2.iterRoadNodes()])
        commonNodeIds = ",".join(["%d" % node
                                for node in nodeIds1.intersection(nodeIds2)])
        if commonNodeIds != "":            
            DtaLogger.error("The two networks have the following road nodes with a common id: %s" % commonNodeIds)
            areIDsUnique = False            

        #Virtual nodes
        nodeIds1 = set([node.getId() for node in self.iterVirtualNodes()])
        nodeIds2 = set([node.getId() for node in net2.iterVirtualNodes()])
        commonNodeIds = ",".join(["%d" % node
                                for node in nodeIds1.intersection(nodeIds2)])
        if commonNodeIds != "":            
            DtaLogger.error("The two networks have the following virtual nodes with a common id: %s" % commonNodeIds)
            areIDsUnique = False 

        #centroids
        nodeIds1 = set([node.getId() for node in self.iterCentroids()])
        nodeIds2 = set([node.getId() for node in net2.iterCentroids()])
        commonNodeIds = ",".join(["%d" % node
                                for node in nodeIds1.intersection(nodeIds2)]) 
        if commonNodeIds != "":            
            DtaLogger.error("The two networks have the following virtual nodes with a common id: %s" % commonNodeIds)
            areIDsUnique = False 
        
        #RoadLinks
        linkIds1 = set([link.getId() for link in self.iterRoadLinks()])
        linkIds2 = set([link.getId() for link in net2.iterRoadLinks()])

        commonLinkIds = ",".join(["%d" % link for link in linkIds1.intersection(linkIds2)])
        if commonLinkIds != "":
            DtaLogger.error("The two networks have the following common roadlinks %s" % commonLinkIds)
            areIDsUnique = False                          

        #virtual links
        linkIds1 = set([link.getId() for link in self.iterRoadLinks()])
        linkIds2 = set([link.getId() for link in net2.iterRoadLinks()])

        commonLinkIds = ",".join(["%d" % link for link in linkIds1.intersection(linkIds2)])
        
        if commonLinkIds != "":
            DtaLogger.error("The two networks have the following common virtual links %s" % commonLinkIds)
            areIDsUnique = False                          

        #connectors 
        linkIds1 = set([link.getId() for link in self.iterConnectors()])
        linkIds2 = set([link.getId() for link in net2.iterConnectors()])

        commonLinkIds = ",".join(["%d" % link for link in linkIds1.intersection(linkIds2)])
        
        if commonLinkIds != "":
            DtaLogger.error("The two networks have the following common connectors %s" % commonLinkIds)
            areIDsUnique = False

        return areIDsUnique

    def mergeSecondaryNetworkBasedOnLinkIds(self, secondaryNetwork):
        """
        This method will add all the elements of the secondary
        network to the current one. The method will throw an
        exception if there is an element of the current and
        secondary network have a common id
        """ 

        if not self.areIDsUnique(secondaryNetwork):
            raise DtaError("The two networks cannot be merge because they "
                           "have conflicting node and/or link ids") 

        #copy the secondary network 
        for node in secondaryNetwork.iterNodes():            
            cNode = copy.copy(node) 
            cNode._incomingLinks = []
            cNode._outgoingLinks = []
            self.addNode(cNode)

        for link in secondaryNetwork.iterLinks():
            cLink = copy.copy(link)
            cLink._startNode = self.getNodeForId(link._startNode.getId())
            cLink._endNode = self.getNodeForId(link._endNode.getId())
            if link.isRoadLink() or link.isConnector():
                cLink._outgoingMovements = []
                cLink._incomingMovements = [] 
            self.addLink(cLink) 

        for link in secondaryNetwork.iterLinks():
            if link.isRoadLink() or link.isConnector():
                for mov in link.iterOutgoingMovements():
                    cLink = self.getLinkForId(link.getId())
                    cMov = copy.copy(mov)
                    cMov._node = self.getNodeForId(mov._node.getId())
                    try: 
                        cMov._incomingLink = self.getLinkForId(mov._incomingLink.getId())                    
                        cMov._outgoingLink = self.getLinkForId(mov._outgoingLink.getId())
                        cLink.addOutgoingMovement(cMov) 
                    except DtaError, e:
                        DtaLogger.error(str(e))



    
        
    def mergeSecondaryNetworkBasedOnLinkIds2(self, secondaryNetwork):
        """
        This method will create copies of all the elements of the 
        secondary network that do not exist in the current network 
        and add them to the current network. The method will merge the 
        networks using node and link ids. Elements of the secondary 
        network having an id that exists in this network will not be 
        coppied.
        """ 

        if not self._areIDsUnique(self, secondaryNetwork):
            raise DtaError("The two networks cannot be merge because they "
                           "have conflicting node and/or link ids") 
        

        primaryNodesToDelete = set()
        primaryLinksToDelete = set()

        for node in self.iterNodes():
            if node.isCentroid():
                if secondaryNetwork.hasNodeForId(node.getId()) and secondaryNetwork.getNodeForId(node.getId()).isRoadNode():
                    for vLink in node.iterAdjacentLinks():
                        primaryLinksToDelete.add(vLink)

                        try:
                            cLink = vLink.getAdjacentConnector()
                            linksToSkip.append(cLink) 
                        except DtaError, e:
                            DtaLogger.error(str(e))

                        primaryNodesToDelete.add(vLink.getOtherEnd(node))


        for link in primaryLinksToDelete:
            self.removeLink(link)
        for node in primaryNodesToDelete:
            self.remove(node)
            

        nodesToSkip = set()
        linksToSkip = set()
        
        #first find the common centroids and skip all the links associated with them
        for node in secondaryNetwork.iterNodes():

            if node.getId() == 286:
                pdb.set_trace() 

            if node.isCentroid():
                if self.hasNodeForId(node.getId()):
                    nodesToSkip.add(node.getId())
                    for vLink in node.iterAdjacentLinks():
                        linksToSkip.add(vLink.getId())                    
                        cLink = vLink.getAdjacentConnector()
                        linksToSkip.add(cLink) 
                    nodesToSkip.add(vLink.getOtherEnd(node).getId())                        
            else:
                if self.hasNodeForId(node.getId()):
                    nodesToSkip.add(node.getId())
                
        #links with common ids. 
        for link in secondaryNetwork.iterLinks():
            if self.hasLinkForId(link.getId()):
                linksToSkip.add(link.getId())
                if link.isVirtualLink(): print "skipping virtual link", link.getId()
            if link.getStartNode().getId() in nodesToSkip:
                linksToSkip.add(link.getId())
                if link.isVirtualLink(): print "skipping virtual link", link.getId()
            if link.getEndNode().getId() in nodesToSkip:
                linksToSkip.add(link.getId())
                if link.isVirtualLink(): print "skipping virual link", link.getId()
         
        #copy the secondary network 
        for node in secondaryNetwork.iterNodes():            
            if node.getId() in nodesToSkip:
                continue 
            cNode = copy.copy(node) 
            cNode._incomingLinks = []
            cNode._outgoingLinks = []
            self.addNode(cNode)

        for link in secondaryNetwork.iterLinks():
            if link.getId() in linksToSkip:
                continue 
            cLink = copy.copy(link)
            cLink._startNode = self.getNodeForId(link._startNode.getId())
            cLink._endNode = self.getNodeForId(link._endNode.getId())
            if isinstance(link, RoadLink):                
                cLink._outgoingMovements = []
                cLink._incomingMovements = [] 
            self.addLink(cLink) 

        for link in secondaryNetwork.iterLinks():
            if link.getId() in linksToSkip:
                continue
            if link.isRoadLink() or link.isConnector():
                for mov in link.iterOutgoingMovements():
                    cLink = self.getLinkForId(link.getId())
                    cMov = copy.copy(mov)
                    cMov._node = self.getNodeForId(mov._node.getId())

                    try: 
                        cMov._incomingLink = self.getLinkForId(mov._incomingLink.getId())                    
                        cMov._outgoingLink = self.getLinkForId(mov._outgoingLink.getId())
                        cLink.addOutgoingMovement(cMov) 
                    except DtaError, e:
                        DtaLogger.error(str(e))

    def getNumOverlappingConnectors(self):
        """
        Return the number of connectors that overlap with a RoadLink or 
        another connector
        """
        num = 0
        for node in self.iterNodes():
            if not node.isRoadNode():
                continue
            for con in node.iterAdjacentLinks():
                if not con.isConnector():
                    continue
                for link in node.iterAdjacentLinks():
                    if link == con:
                        continue
                    if con.isOverlapping(link):
                        num += 1
        return num

    def moveVirtualNodesToAvoidShortConnectors(self, connectorMinLength, maxDistToMove):
        """
        Connectors are sometimes too short. This method tries to move 
        the virtual node attached to the connector in the vicinity 
        of the current virtual node so that the connector length is 
        greater than *connectorMinLength*, which should be in the units given by :py:attr:`RoadLink.LENGTH_UNITS`.
        
        The :py:class:`VirtualNode` will be moved randomly within the bounding box defined by its
        current location +/- *maxDistToMove*, where *maxDistToMove* is in the units given by 
        :py:attr:`Node.COORDINATE_UNITS`.
        
        This will be repeated until the connector is long enough (up to 4 times).
        """
        for link in self.iterLinks():
            if not link.isConnector():
                continue

            virtualNode = link.getVirtualNode()
            numMoves = 0

            while link.getLength() < connectorMinLength \
                    and numMoves < 4:
                virtualNode._x += random.uniform(0, maxDistToMove)
                virtualNode._y += random.uniform(0, maxDistToMove)
                numMoves += 1

            DtaLogger.info("Moved virtual node %8d associated with connector %8d to avoid overlapping links" % (virtualNode.getId(), link.getId()))

    def handleOverlappingLinks(self, warn, moveVirtualNodeDist=None):
        """
        For each node, checks if any incoming links overlap, and if any outgoing links overlap.
        
        If *moveVirtualNodeDist* is passed, if the overlapping links includes a c:py:class:`Connector`,
        the :py:class:`VirtualNode` instance will be moved +- *moveVirtualNodeDist* in each direction
        to see if that resolves the overlap.  If not, the node retains its original location.
        
        *moveVirtualNodeDist* is in :py:attr:`Node.COORDINATE_UNITS`
        
        (order attempted: (0,+dist), (+dist,0), (0,-dist), (-dist,0), 
                          (+dist,-dist), (+dist,+dist), (-dist,+dist), (-dist,-dist))
        
        """
        
        # going through the nodes in sequential order
        nodeIds = sorted(self._nodes.keys())
        for nodeId in nodeIds:
            node = self._nodes[nodeId]
            
            # check incoming links
            for link1 in node.iterIncomingLinks():
                if link1.isVirtualLink(): continue
                
                for link2 in node.iterIncomingLinks():
                    
                    self._handleOverlappingLinkPair(node, link1, link2, warn, moveVirtualNodeDist, incoming=True)

            # check outgoing links
            for link1 in node.iterOutgoingLinks():
                if link1.isVirtualLink(): continue
                
                for link2 in node.iterOutgoingLinks():
                    
                    self._handleOverlappingLinkPair(node, link1, link2, warn, moveVirtualNodeDist, incoming=False)                
                    
    def _handleOverlappingLinkPair(self, node, link1, link2, warn, moveVirtualNodeDist, incoming=True):
        """
        Helper method to avoid repeating code; handles a single pair of overlapping links
        """
        # virtual links are not a concern
        if link2.isVirtualLink(): return
                    
        # they're the same
        if link1 == link2: return

        # not overlapping
        try:
            if not link1.isOverlapping(link2, usingShapepoints=True): return
        except DtaError, e:
            # DtaLogger.warn("Couldn't determine link overlap: "+str(e))
            return

        warn_str = None
        if warn:
            warn_str = "node %d: %s links %d and %d are overlapping (angle=%.3f)" % \
                        (node.getId(), "incoming" if incoming else "outgoing", \
                         link1.getId(), link2.getId(), link1.getAngle(link2, True))

        if moveVirtualNodeDist:
            toMove = None
            if link1.getStartNode().isVirtualNode():
                toMove = link1.getStartNode()
            elif link1.getEndNode().isVirtualNode():
                toMove = link1.getEndNode()
            elif link2.getStartNode().isVirtualNode():
                toMove = link2.getStartNode()
            elif link2.getEndNode().isVirtualNode():
                toMove = link2.getEndNode()
            
            if toMove:
                original_loc = (toMove.getX(), toMove.getY())
                
                try_locs = [(original_loc[0], original_loc[1]+moveVirtualNodeDist),
                            (original_loc[0]+moveVirtualNodeDist, original_loc[1]),
                            (original_loc[0], original_loc[1]-moveVirtualNodeDist),
                            (original_loc[0]-moveVirtualNodeDist, original_loc[1]),
                            (original_loc[0]+moveVirtualNodeDist, original_loc[1]-moveVirtualNodeDist),
                            (original_loc[0]+moveVirtualNodeDist, original_loc[1]+moveVirtualNodeDist),
                            (original_loc[0]-moveVirtualNodeDist, original_loc[1]+moveVirtualNodeDist),
                            (original_loc[0]-moveVirtualNodeDist, original_loc[1]-moveVirtualNodeDist)]
                
                fixed = False
                for try_loc in try_locs:
                    toMove._x = try_loc[0]
                    toMove._y = try_loc[1]
                    
                    if not link1.isOverlapping(link2, usingShapepoints=True):
                        # fixed! stop here
                        if warn_str: warn_str += "; fixed by adjusting virtual node to %.2f, %.2f" % (try_loc[0],try_loc[1])
                        fixed = True
                        break
                    
                # failed to fix
                if not fixed:
                    toMove._x = original_loc[0]
                    toMove._y = original_loc[1]
                    if warn_str: warn_str += "; failed to fix"
        
        if warn_str: DtaLogger.warn(warn_str)

        
    def handleShortLinks(self, minLength, warn, setLength):
        """
        Goes through the :py:class:`RoadLink` instances (including :py:class:`Connectors`)
        and for those with lengths less than *minLength*, do the following:
        
        * if *warn* then issue a warning
        * if *setLength* then adjust the length attribute to the minimum
        
        Note that *minLength* and *setLength* are both in the units specified by :py:attr:`RoadLink.LENGTH_UNITS`
        
        """
        for link in self.iterLinks():
            # only handle road links and connectors
            if not link.isRoadLink() and not link.isConnector(): continue
            # that are too short
            if link.getLength() >= minLength: continue
            
            warn_str = None
            if warn:
                warn_str = "Short link warning: %d (%d,%d) has length %.4f < %.4f" % \
                            (link.getId(), link.getStartNode().getId(), link.getEndNode().getId(), \
                             link.getLength(), minLength)
            
            if setLength:
                link.setLength(minLength)
                if warn_str: warn_str += "; Setting length to min"

            if warn_str: DtaLogger.warn(warn_str)
                
            
    def writeNodesToShp(self, name):
        """
        Export all the nodes to a shapefile with the given name
        """
        w = shapefile.Writer(shapefile.POINT)
        w.field("ID",           "N", 10)
        w.field("Type",         "C", 12)
        w.field("Control",      "N", 2)
        w.field("Priority",     "N", 2)

        for node in self.iterNodes():
            w.point(node.getX(), node.getY())
            control = 0
            priority = 0
            if node.isRoadNode():
                type = "RoadNode"
                control = node.control
                priority = node.priority
            elif node.isCentroid():
                type = "Centroid"
            elif node.isVirtualNode():
                type = "VirtualNode"
            
            w.record(node.getId(), type, control, priority)

        w.save(name)
        DtaLogger.info("Wrote nodes to shapefile %s" % name)

    def writeLinksToShp(self, name):
        """
        Export all the links to a shapefile with the given name
        """
        w = shapefile.Writer(shapefile.POLYLINE) 
        w.field("ID",       "N", 10)
        w.field("Start",    "N", 10)
        w.field("End",      "N", 10)
        w.field("Start_End","C", 20) # for joins

        w.field("Type",     "C", 10) 
        w.field("Label",    "C", 60)
        w.field("facType",  "N", 10)
        w.field("numLanes", "N", 10)
        w.field("Direction","C", 2 )
        w.field("Length",   "N", 12, 4)
        
        for link in self.iterLinks():
            if link.isVirtualLink():
                
                centerline = ((link._startNode.getX(), link._startNode.getY()),
                            (link._endNode.getX(), link._endNode.getY()))
                w.line(parts=[centerline])
                label       = ""
                facType     = -1
                numLanes    = -1
                direction   = ""
                length      = "-1"
            else:                    
                w.line(parts=[link.getCenterLine(wholeLineShapePoints = True)])
                
                label       = link.getLabel()
                facType     = link.getFacilityType()
                numLanes    = link.getNumLanes()
                if link.isConnector():
                    type    = "Connector"
                elif link.isRoadLink():
                    type    = "RoadLink"
                elif link.isVirtualLink():
                    type    = "VirtualLink"
                direction   = link.getDirection()
                length      = "%10.4f" % link.getLength()
                
            w.record(link.getId(), link.getStartNode().getId(), link.getEndNode().getId(), 
                     "%d %d" % (link.getStartNode().getId(), link.getEndNode().getId()),
                     type, label, facType, numLanes, direction, length)

        w.save(name)
        DtaLogger.info("Wrote links to shapefile %s" % name)        

    def writeMovementsToShp(self, name, planInfo=None):
        """
        Export all the movements to a shapefile with the given name
        """
        w = shapefile.Writer(shapefile.POLYLINE)
        w.field("Start",    "N", 10)
        w.field("Middle",   "N", 10)
        w.field("End",      "N", 10)
        w.field("StaMidEnd","C", 30)
        
        w.field("NumLanes", "N", 10)
        w.field("Capacity", "N", 10, 3)
        w.field("TurnType", "C", 10)

        if not planInfo and self._planInfo.values():
            planInfo = self._planInfo.values()[0]
            
        for link in self.iterLinks():
            if link.isVirtualLink():
                continue
            for mov in link.iterOutgoingMovements():
                w.line(parts=[mov.getCenterLine()])
                
                try:
                    protected_capacity = mov.getProtectedCapacity(planInfo)
                except:
                    protected_capacity = -1
                    
                w.record(mov.getStartNodeId(), mov.getAtNode().getId(), mov.getEndNodeId(),
                         "%d %d %d" % (mov.getStartNodeId(), mov.getAtNode().getId(), mov.getEndNodeId()),
                         mov.getNumLanes(), "%10.2f" % protected_capacity,
                         mov.getTurnType())
        w.save(name)
        DtaLogger.info("Wrote movements to shapefile %s" % name)                
                
    def mergeLinks(self, link1, link2):
        """
        Merge the two input sequential links. If any of the characteristics of the 
        two links are different (except their length) the method will throw an 
        error
        """
        if link1.getEndNode() != link2.getStartNode():
            raise DtaError("Links %d and %d are not sequential and therefore cannot be merged" % (link1.getId(), link2.getId()))
        if not link1.isRoadLink() or not link2.isRoadLink():
            raise DtaError("Links %d and %d should both be road links" % (link1.getId(), link2.getId()))
        
        if not link1.getEndNode().isMidblockNode():
            raise DtaError("Links %d and %d cannot be merged because node %d is not "
                           "a shape point" % (link1.getId(), link2.getId(), link1.getEndNode().getId()))

        if not link1.hasSameAttributes(link2):
            raise DtaError("Links %d and %d cannot be merged because they have different attributes"
                            % (link1.getId(), link2.getId()))
            
        if link1._facilityType != link2._facilityType:
            raise DtaError("Links %d and %d cannot be merged because the have different facility types"
                           % (link1.getId(), link2.getId()))
            
        if link1._freeflowSpeed != link2._freeflowSpeed:
            raise DtaError("Links %d and %d cannot be merged because the have different free flow speeds"
                           % (link1.getId(), link2.getId()))            
        
        if link1._effectiveLengthFactor != link2._effectiveLengthFactor:
            raise DtaError("Links %d and %d cannot be merged because the have different effective "
                           "lenth factors" % (link1.getId(), link2.getId()))
                           
        
        if link1._responseTimeFactor != link2._responseTimeFactor:
            raise DtaError("Links %d and %d cannot be merged because the have different response "
                           "time factors" % (link1.getId(), link2.getId()))            
        
        if link1._numLanes != link2._numLanes:
            raise DtaError("Links %d and %d cannot be merged because the have different number "
                           "of lanes" % (link1.getId(), link2.getId()))                        

        if link1._roundAbout != link2._roundAbout:
            raise DtaError("Links %d and %d cannot be merged because the have different round about "
                           "classification" % (link1.getId(), link2.getId()))                                    

        if link1._level != link2._level:
            raise DtaError("Links %d and %d cannot be merged because they belong to different levels "
                           % (link1.getId(), link2.getId())) 

        label = ""
        if link1._label:
            label = link1._label 
        elif link2._label:
            label = link2._label

        newLink = RoadLink(self._maxLinkId + 1,
                           link1.getStartNode(), 
                           link2.getEndNode(), 
                            None,
                            link1._facilityType,
                            link1.getLength() + link2.getLength(), 
                            link1._freeflowSpeed,
                            link1._effectiveLengthFactor,
                            link1._responseTimeFactor,
                            link1._numLanes,
                            link1._roundAbout,
                            link1._level, 
                            label,
                            self._maxLinkId + 1)
        
        self.addLink(newLink)

        
        for inMov in link1.iterIncomingMovements():
                
            newMovement = Movement(link1.getStartNode(),
                                   inMov.getIncomingLink(),
                                   newLink,
                                   inMov._freeflowSpeed,
                                   inMov._permission,
                                   inMov._numLanes,
                                   inMov._incomingLane,
                                   inMov._outgoingLane,
                                   inMov._followupTime)


            inMov.getIncomingLink().addOutgoingMovement(newMovement)

        for outMov in link2.iterOutgoingMovements():

            newMovement = Movement(link2.getEndNode(),
                                   newLink,
                                   outMov.getOutgoingLink(),
                                   outMov._freeflowSpeed,
                                   outMov._permission,
                                   outMov._numLanes,
                                   outMov._incomingLane,
                                   outMov._outgoingLane,
                                   outMov._followupTime)

            newLink.addOutgoingMovement(newMovement)

        
        self.removeLink(link1)
        self.removeLink(link2)
        if link1.getEndNode().getCardinality() == (0,0):
            self.removeNode(link1.getEndNode()) 
            
    def readLinkShape(self, linkShapefile, startNodeIdField, endNodeIdField, skipEvalStr=None):
        """
        Uses the given *linkShapefile* to add shape points to the network, in order to more accurately
        represent the geometry of the roads.  For curvey or winding roads, this will help reduce errors in understanding
        intersections because of the angles involved.
        
        *startNodeIdField* and *endNodeIdField* are the column headers (so they're strings)
        of the start node and end node IDs within the *linkShapefile*.
        
        Optional argument *skipEvalStr* will be eval()ed by python, and if the expression returns True,
        the row will be skipped.  For example, to skip a specific couple of entries, the caller could pass
        ``"OBJECTID in [5234,2798]"``.

        If a link with the same (node1,node2) pair is specified more than once in the shapefile, only the first one
        will be used.
        
        Does this in two passes; in the first pass, the (a,b) from the shapefile is looked up in the network, and used
        to add shape points.  In the second pass, the (b,a) from the shapefile is looked up in the network, and used
        to add shape points **if that link has not already been updated from the first pass**.
        
        .. todo:: Dynameq warns/throws away shape points when there is only one, which makes me think the start or end
                  node should be included too.  However, if we include either the first or the last shape point below,
                  everything goes crazy.  I'm not sure why?
        """ 

        sf      = shapefile.Reader(linkShapefile)
        shapes  = sf.shapes()
        records = sf.records()
        
        links_found         = 0
        shapepoints_added   = 0

        fields = [field[0] for field in sf.fields]
        
        # if the first field is the 'DeletionFlag' -- remove
        if fields[0] == 'DeletionFlag':
            fields.pop(0)
            
        # If a link with the same (node1,node2) pair is specified more than 
        # once in the shapefile, only the first one will be used.
        links_done = {}
        
        # two passes - regular and reverse
        for direction in ["regular","reverse"]:
            
            for shape, recordValues in izip(shapes, records):

                assert(len(fields)==len(recordValues))
                
                localsdict  = dict(zip(fields, recordValues))
                
                # check if we're instructed to skip this one
                if skipEvalStr and eval(skipEvalStr, globals(), localsdict): continue
                
                if direction == "regular":
                    startNodeId = int(localsdict[startNodeIdField])
                    endNodeId   = int(localsdict[endNodeIdField])
                else:
                    startNodeId = int(localsdict[endNodeIdField])
                    endNodeId   = int(localsdict[startNodeIdField])
                        
                # DtaLogger.debug("shape %d %d" % (startNodeId, endNodeId))
                
                if (startNodeId, endNodeId) in links_done: continue 
                    
                if self.hasLinkForNodeIdPair(startNodeId, endNodeId):
                    link = self.getLinkForNodeIdPair(startNodeId, endNodeId)
                    links_found += 1
                    
                    # just a straight line - no shape points necessary
                    if len(shape.points) == 2: continue
                    
                    # Dynameq throws away a single, see todo above
                    if len(shape.points) == 3: continue
                    
                    # don't include the first and last, they're already there
                    link._shapePoints = shape.points[1:-1]
                    if direction == "reverse": link._shapePoints.reverse()
                    shapepoints_added += len(shape.points)-2
                    
                    links_done[(startNodeId, endNodeId)] = True

        DtaLogger.info("Read %d shape points for %d links from %s" % (shapepoints_added, links_found, linkShapefile))            
                
    def removeShapePoints(self):
        """
        Remove shape points from the network
        
        .. todo:: These are not the same "shape points" as the :py:class:`RoadLink._shapePoints`.  Define what these
                  are (call them something else if they're not the same).  Also, why wouldn't we convert them to
                  the other kind? 
        """
        for node in [node for node in self.iterRoadNodes()]:
            if node.isMidblockNode():
                if node.getCardinality() == (2,2):

                    pair1 = None
                    pair2 = None
                    linki1 = node._incomingLinks[0]
                    linki2 = node._incomingLinks[1]
                    linko1 = node._outgoingLinks[0]
                    linko2 = node._outgoingLinks[1] 

                    if abs(linki1.getReferenceAngleInDegrees() - linko1.getReferenceAngleInDegrees()) < 10:
                           pair1 = (linki1, linko1)
                           if abs(linki2.getReferenceAngleInDegrees() - linko2.getReferenceAngleInDegrees()) < 10:
                               pair2 = (linki2, linko2)
                               
                    elif abs(linki1.getReferenceAngleInDegrees() - linko2.getReferenceAngleInDegrees()) < 10:
                           pair1 = (linki1, linko2)
                           if abs(linki2.getReferenceAngleInDegrees() - linko1.getReferenceAngleInDegrees()) < 10:
                               pair2 = (linki2, linko1)                    
                    else:
                        continue 
                    if pair1 and pair1[0].hasSameAttributes(pair1[1]):                        
                        self.mergeLinks(*pair1) 
                        DtaLogger.info("Merged links  %8d and %8d" % (pair1[0].getId(), pair1[1].getId()))
                    if pair2 and pair2[0].hasSameAttributes(pair2[1]):
                        self.mergeLinks(*pair2) 
                        DtaLogger.info("Merged links  %8d and %8d" % (pair2[0].getId(), pair2[1].getId()))
                                                        
                elif node.getCardinality() == (1,1):                    
                        
                    link1 = node._incomingLinks[0]
                    link2 = node._outgoingLinks[0]
                    if abs(link1.getReferenceAngleInDegrees() - link2.getReferenceAngleInDegrees()) < 10:
                        if link1.hasSameAttributes(link2):
                            self.mergeLinks(link1, link2) 
                            DtaLogger.info("Merged links  %8d and %8d" % (link1.getId(), link2.getId()))

    def removeUnconnectedNodes(self):
        """
        Removes any nodes that aren't linked to anything (have no adjacent links).
        
        This might be useful for networks with too many nodes for the DTA software license.
        """
        nodesToRemove = [node for node in self.iterNodes() if node.getNumAdjacentLinks() == 0]

        for node in nodesToRemove:
            DtaLogger.info("Removing unconnected node %d" % node.getId())                
            self.removeNode(node)
     

    def renameLink(self, oldLinkId, newLinkId):
        """
        Give the newLinkId to the link with oldLinkId
        """
        if self.hasLinkForId(newLinkId):
            raise DtaError("A link with id %d already exists in the network" % newLinkId)
        
        linkToRename = self.getLinkForId(oldLinkId)

        linkToRename._id = newLinkId 
        del self._linksById[oldLinkId]
        self._linksById[newLinkId] = linkToRename 

        if newLinkId > self._maxLinkId:
            self._maxLinkId = newLinkId 

    def renameNode(self, oldNodeId, newNodeId):
        """
        Give the node with oldNodeId the new id 
        """
        if self.hasNodeForId(newNodeId):
            raise DtaError("A node with id %d already exists in the network" % newNodeId) 
        
        nodeToRename = self.getNodeForId(oldNodeId)
        if nodeToRename.isCentroid():
            raise DtaError("Network.renameNode(): cannot rename centroid %d" % newNodeId) 

        nodeToRename._id = newNodeId 

        if self._maxNodeId < newNodeId:
            self._maxNodeId = newNodeId 

        del self._nodes[oldNodeId] 

        self._nodes[newNodeId] = nodeToRename 

        for oLink in nodeToRename.iterOutgoingLinks():
            del self._linksByNodeIdPair[oldNodeId, oLink.getEndNode().getId()]
            self._linksByNodeIdPair[(oLink.getStartNode().getId(), oLink.getEndNode().getId())] = oLink

        for iLink in nodeToRename.iterIncomingLinks():
            del self._linksByNodeIdPair[iLink.getStartNode().getId(), oldNodeId]
            self._linksByNodeIdPair[(iLink.getStartNode().getId(), iLink.getEndNode().getId())] = iLink


    def getMaxLinkId(self):
        """
        Return the max link Id in the network
        """
        return self._maxLinkId

    def getMaxNodeId(self):
        """
        REturn the max noe id in the network
        """
        return self._maxNodeId

    def mergeSecondaryNetwork(self, secondaryNetwork):
        """
        This method will create a polygon around the current 
        (primary network). Every node or link of the secondary network 
        that is not in the polygon will be copied. 
        
        .. todo:: Code review and more detailed documentation.
        """ 
        print "\n\n*********************\nStarting network merge" 
        #primaryPolygon = getConvexHull([(node.getX(), node.getY()) for node in self.iterNodes()])
        primaryPolygon = getConvexHull([link.getMidPoint() for link in self.iterLinks() if not link.isVirtualLink()])        

        exitConnectors = []
        entryConnectors = []
        #the follwoing code will identify external links. Some of those links will be connectors
        # in the primary network and some of them may be roadway links. You do not need to add 
        # roadway links
        for sLink in secondaryNetwork.iterLinks():
            if not sLink.isRoadLink():
                continue
            point1 = (sLink.getStartNode().getX(), sLink.getStartNode().getY())
            point2 = (sLink.getEndNode().getX(), sLink.getEndNode().getY())
            if isPointInPolygon(point1, primaryPolygon) and not isPointInPolygon(point2, primaryPolygon):
                exitConnectors.append(sLink)
            if not isPointInPolygon(point1, primaryPolygon) and isPointInPolygon(point2, primaryPolygon):
                entryConnectors.append(sLink)

        print "\nEntryConnectors", [(link.getStartNodeId(), link.getEndNodeId()) for link in entryConnectors]
        print "\nExit connectors", [(link.getStartNodeId(), link.getEndNodeId()) for link in exitConnectors]



        #delete all the centroids in the primary polygon
        sNodesToDelete = []
        numCentroidsToDelete = 0
        for sCentroid in secondaryNetwork.iterCentroids():
            point = (sCentroid.getX(), sCentroid.getY())
            
            if isPointInPolygon(point, primaryPolygon):
                sNodesToDelete.append(sCentroid)
                numCentroidsToDelete += 1
                for vNode in sCentroid.iterAdjacentNodes():
                    sNodesToDelete.append(vNode)

        for sNode in sNodesToDelete:
            secondaryNetwork.removeNode(sNode)
            
        DtaLogger.info("Deleted %d centroids from the secondary network" % numCentroidsToDelete)

        #delete all the nodes and their associated links in the primary region
        sNodesToDelete = set()
        for sRoadNode in secondaryNetwork.iterRoadNodes():
            point = (sRoadNode.getX(), sRoadNode.getY())
            if isPointInPolygon(point, primaryPolygon):
                sNodesToDelete.add(sRoadNode)

                #TODO: why do I need this/ 
                for link in sRoadNode.iterAdjacentLinks():
                    if link.isConnector():
                        sNodesToDelete.add(link.getOtherEnd(sRoadNode))
        
        for sNode in sNodesToDelete:
            secondaryNetwork.removeNode(sNode)

        DtaLogger.info("Deleted %d roadNodes from the secondary network" % len(sNodesToDelete))            
        
        #rename all the nodes in the secondary network that conflict with primary nodes
        for sNode in secondaryNetwork.iterNodes():
            if self.hasNodeForId(sNode.getId()):
                secondaryNetwork.renameNode(sNode.getId(), max(secondaryNetwork.getMaxNodeId() + 1, self.getMaxNodeId() + 1))
                
        #rename all the links in the secondary network that conflict with primary links
        for sLink in secondaryNetwork.iterLinks():
            if self.hasLinkForId(sLink.getId()):
                secondaryNetwork.renameLink(sLink.getId(), max(secondaryNetwork.getMaxLinkId() + 1, self.getMaxLinkId() + 1))

        #identify external centroids
        externalCentroids = {}
        for centroid in self.iterCentroids():
            point = (centroid.getX(), centroid.getY())
            if not isPointInPolygon(point, primaryPolygon):
                externalCentroids[centroid.getId()] = centroid

        #delete externalCentroids
        for centroid in externalCentroids.itervalues():
            for vNode in centroid.iterAdjacentNodes():
                self.removeNode(vNode)
            self.removeNode(centroid)
        
        self.mergeSecondaryNetworkBasedOnLinkIds(secondaryNetwork)
    

        #add external links 
        for sLink in exitConnectors:            
            if not sLink.isRoadLink():
                continue


            pNode1, dist = getClosestNode(self, sLink.getStartNode())
            if dist > 10:
                continue 
            pNode2, dist = getClosestNode(self, sLink.getEndNode())
            if dist > 10:
                continue 
            print "Adding exit connector", pNode1.getId(), pNode2.getId() 

            pLink = copy.copy(sLink)

            if self.hasLinkForId(pLink.getId()):
                pLink._id = self.getMaxLinkId() + 1

            pLink._startNode = pNode1
            pLink._endNode = pNode2
        
            pLink._outgoingMovements = []
            pLink._incomingMovements = [] 
            
            if not self.hasLinkForNodeIdPair(pLink.getStartNodeId(), pLink.getEndNodeId()):
                self.addLink(pLink) 
                
        for sLink in entryConnectors:

            if not sLink.isRoadLink():
                continue
            
            pNode1, dist = getClosestNode(self, sLink.getStartNode())
            if dist > 50:
                continue 
            pNode2, dist = getClosestNode(self, sLink.getEndNode())
            if dist > 50:
                continue 
            
            print "Adding entry connector", pNode1.getId(), pNode2.getId() 

            pLink = copy.copy(sLink)
            pLink._startNode = pNode1
            pLink._endNode = pNode2

            if self.hasLinkForId(pLink.getId()):
                pLink._id = self.getMaxLinkId() + 1

            pLink._outgoingMovements = []
            pLink._incomingMovements = [] 

            if not self.hasLinkForNodeIdPair(pLink.getStartNodeId(), pLink.getEndNodeId()):                   
                self.addLink(pLink)

    def getNodeType(self):
        """
        Return a unique integer representing the node type.
        
        .. todo:: What is this for?
        """
        return self._nodeType

    def getLinkType(self):
        """
        Return a unique integer representing the link type
        
        .. todo:: What is this for?
        """
        return self._linkType 
    

                
