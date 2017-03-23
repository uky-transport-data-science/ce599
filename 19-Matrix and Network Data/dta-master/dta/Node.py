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

from itertools import chain 
from .DtaError import DtaError
from .VehicleClassGroup import VehicleClassGroup

class Node(object):
    """
    Base class that represents a node in a network.
    
    .. note:: lmz has read over this, so todos are marked.
    """
    #: Static variable representing the units of the x,y (and so therefore Euclidean length)
    #: Should be ``meters`` or ``feet``
    COORDINATE_UNITS = None
    
    # Defaults
    DEFAULT_LABEL = ""
    DEFAULT_LEVEL = 0

    # Geometry types - how is this used?  Why is the centroid not in the type list?
    
    #: :py:class:`RoadNode` geometry type
    GEOMETRY_TYPE_INTERSECTION      = 1
    #: :py:class:`RoadNode` geometry type
    GEOMETRY_TYPE_JUNCTION          = 2
    #: :py:class:`VirtualNode` geometry type
    GEOMETRY_TYPE_VIRTUAL           = 99
    #: :py:class:`Centroid` geometry type
    GEOMETRY_TYPE_CENTROID          = 100
    GEOMETRY_TYPES                  = [GEOMETRY_TYPE_INTERSECTION,
                                       GEOMETRY_TYPE_JUNCTION,
                                       GEOMETRY_TYPE_VIRTUAL,
                                       GEOMETRY_TYPE_CENTROID]

    def __init__(self, id, x, y, geometryType, label=None, level=None):
        """
        Constructor.
        
         * *id* is a unique identifier (unique within the containing network), an integer
         * *x* and *y* are coordinates in the units specified by :py:attr:`Node.COORDINATE_UNITS`
         * *geometryType* is one of :py:attr:`Node.GEOMETRY_TYPE_INTERSECTION`, :py:attr:`Node.GEOMETRY_TYPE_JUNCTION`, or 
           :py:attr:`Node.GEOMETRY_TYPE_VIRTUAL`
         * *label* is a string, for readability.  If None passed, will use default. 
         * *level* is for vertical alignment.  More details TBD.  If None passed, will use default.  
        
        """
        self._id             = id   # unique identifier (integer)
        self._x              = x    # x-coordinate
        self._y              = y    # y-coordinate
        self._geometryType   = geometryType # one of Node.GEOMETRY_TYPE_INTERSECTION, Node.GEOMETRY_TYPE_JUNCTION, or Node.GEOMETRY_TYPE_VIRTUAL
        
        if label:
            self._label = label
        else:
            self._label = Node.DEFAULT_LABEL
            
        if level:
            self._level = level
        else:
            self._level = Node.DEFAULT_LEVEL
        
        # List of incoming Link objects, in clockwise order starting from <1,0>
        self._incomingLinks = []
        
        # List of outgoing link objects, in clockwise order starting from <1,0>
        self._outgoingLinks = []
    
    @property
    def geometryType(self):
        """
        Returns the geometry type for this node, one of :py:attr:`Node.GEOMETRY_TYPE_INTERSECTION`, :py:attr:`Node.GEOMETRY_TYPE_JUNCTION`,
        :py:attr:`Node.GEOMETRY_TYPE_VIRTUAL` or :py:attr:`Node.GEOMETRY_TYPE_CENTROID`.
        """
        return self._geometryType
    
    @geometryType.setter
    def geometryType(self, value):
        """
        Sets the geometry type for this node, which should be one of :py:attr:`Node.GEOMETRY_TYPE_INTERSECTION`, :py:attr:`Node.GEOMETRY_TYPE_JUNCTION`,
        :py:attr:`Node.GEOMETRY_TYPE_VIRTUAL` or :py:attr:`Node.GEOMETRY_TYPE_CENTROID`.
        """
        if value not in Node.GEOMETRY_TYPES:
            raise DtaError("Trying to set geometry type to invalid value %s for node %d" % (str(value), self._id))
        
        self._geometryType = value
    
    def __str__(self):
        """
        Human-readable string representation.
        """
        return "Node of type %s, id=%s, x,y=(%f,%f)" % (self.__class__, self._id, self._x, self._y)
    
    def _addIncomingLink(self, link):
        """
        Verify that the given link ends in this node, and adds it to the list of
        incoming links.
        """
        #if not isinstance(link, Link):
        #    raise DtaError("Node.addIncomingLink called with an invalid link: %s" % str(link))
        
        if link.getEndNode() != self:
            raise DtaError("Node.addIncomingLink called for link that doesn't end here: %s" % str(link))

        angle = link.getReferenceAngle()
        
        position = 0
        for i in range(len(self._incomingLinks)):
            if self._incomingLinks[i].getReferenceAngle() > angle: break
            position += 1
            
        self._incomingLinks.insert(position, link)
    
    def _removeIncomingLink(self, link):
        """
        Simple removal.
        """
        if link not in self._incomingLinks:
            raise DtaError("Node.removeIncomingLink called for link not in incoming links list: %s" % str(link))
        self._incomingLinks.remove(link)
    
    def _addOutgoingLink(self, link):
        """
        Verify that the given link starts with this node, and adds it to the list of
        outgoing links.
        """
        #if not isinstance(link, Link):
        #    raise DtaError("Node.addOutgoingLink called with an invalid link: %s" % str(link))
        
        if link.getStartNode() != self:
            raise DtaError("Node.addOutgoingLink called for link that doesn't start here: %s" % str(link))

        angle = link.getReferenceAngle()
        
        position = 0
        for i in range(len(self._outgoingLinks)):
            if self._outgoingLinks[i].getReferenceAngle() > angle: break
            position += 1
            
        self._outgoingLinks.insert(position, link)
        
    def _removeOutgoingLink(self, link):
        """
        Simple removal.
        """
        if link not in self._outgoingLinks:
            raise DtaError("Node.removeOutgoingLink called for link not in outgoing links list: %s" % str(link))
        self._outgoingLinks.remove(link)

    def iterIncomingLinks(self):
        """
        Returns iterator for the incoming links.
        """
        return iter(self._incomingLinks)

    def iterUpstreamNodes(self):
        """
        Returns an iterator to the start nodes of all incoming links.
        """
        for link in self.iterIncomingLinks():
            yield link.getStartNode()
            
    def iterOutgoingLinks(self):
        """
        Returns iterator for the outgoing links.
        """
        return iter(self._outgoingLinks)

    def iterLinks(self):
        """
        Returns an iterator to all adjacent links.
        """
        return chain(self.iterIncomingLinks(), self.iterOutgoingLinks())

    def iterDownstreamNodes(self):
        """
        Returns an iterator to the end nodes of all outgoing links.
        """
        for link in self.iterOutgoingLinks():
            yield link.getEndNode() 

    def getId(self): 
        """
        Returns the integer id for this node.
        """
        return self._id
    
    def getX(self):
        """
        Returns the x-coordinate for this node.
        """
        return self._x
    
    def getY(self):
        """
        Returns the y-coordinate for this node.
        """
        return self._y

    def getLabel(self):
        """
        Return the node label
        """
        return self._label
    
    def hasIncomingLinkForId(self, linkId):
        """
        Returns True if there is an incoming link with the given *linkId*.
        """
        for link in self.iterIncomingLinks():
            if link.getId() == linkId:
                return True
        return False

    def hasIncomingLinkForNodeId(self, nodeId):
        """
        Returns True if there is an incoming link starting from *nodeId*.
        """
        for link in self.iterIncomingLinks():
            if link.getStartNode().getId() == nodeId:
                return True
        return False

    def hasOutgoingLinkForId(self, linkId):
        """
        Returns True if there is an outgoing link with the given *linkId*.
        """
        for link in self.iterIncomingLinks():
            if link.getId() == linkId:
                return True
        return False

    def hasOutgoingLinkForNodeId(self, nodeId):
        """
        Returns True if there is an outgoing link towards a node with the given *nodeId*.
        """
        for link in self.iterOutgoingLinks():
            if link.getEndNode(). getId() == nodeId:
                return True
        return False
        
    def hasMovement(self, startNodeId, endNodeId):
        """
        Return True if a :py:class:`Movement` exists from the node with *startNodeId* through this node
        to the node with *endNodeId*, and if that movement is **not prohibited**.
        """
        for ilink in self.iterIncomingLinks():
            if ilink.getStartNodeId() != startNodeId: continue

            for mov in ilink.iterOutgoingMovements():
                if mov.getEndNodeId() != endNodeId: continue
                
                # movement exists with the given start/end nodes
                if mov._permission.classDefinitionString != VehicleClassGroup.CLASSDEFINITION_PROHIBITED:
                    return True

        return False
                   
    def getNumAdjacentLinks(self):
        """
        Returns the number of links adjacent to this node (either incoming or outgoing).
        """
        return len(self._incomingLinks) + len(self._outgoingLinks) 

    def getNumAdjacentRoadLinks(self):
        """
        Returns the number of :py:class:`RoadLink` instances adjacent to this node (either incoming or outgoing).
        """
        return sum([1 for link in self.iterAdjacentRoadLinks()])

    def iterAdjacentNodes(self):
        """
        Return an iterator to the adjacent :py:class:`Node` instances.
        """ 
        nodes = set()
        for link in self.iterIncomingLinks():
            nodes.add(link.getStartNode())

        for link in self.iterOutgoingLinks():
            nodes.add(link.getEndNode()) 
        return iter(nodes) 

    def getNumAdjacentNodes(self):
        """
        Return the number of nodes that are connected to this node.
        """ 
        return sum([1 for node in self.iterAdjacentNodes()])
        
    def iterAdjacentLinks(self):
        """
        Return an iterator to all :py:class:`Link` instances adjacent (incoming or outgoing)
        to this node
        """
        return chain(iter(self._incomingLinks), iter(self._outgoingLinks))

    def iterAdjacentRoadLinks(self):
        """
        Return an iterator to all :py:class:`RoadLink` instances adjacent to this node (excluding Connectors)
        """
        for link in self.iterAdjacentLinks():
            if link.isRoadLink():
                yield link 

    def iterAdjacentRoadNodes(self):
        """
        Return an iterator to all :py:class:`RoadNode` instances adjacent to this Node
        """
        for node in self.iterAdjacentNodes():
            if node.isRoadNode():
                yield node

    def getNumAdjacentRoadNodes(self):
        """
        Return the number of :py:class:`RoadNode` instances that share a link with this node.
        """ 
        return sum([1 for node in self.iterAdjacentRoadNodes()])

    def getIncomingLinkForId(self, linkId):
        """
        Returns an incoming link if one has an ID matching *linkId*.
        It no incoming links qualify, raises a :py:class:`DtaError`.
        """
        for link in self.iterIncomingLinks():
            if link.getId() == linkId:
                return link 
        raise DtaError("Node %d does not have incoming link with id %d" % (self._id, linkId)) 

    def getIncomingLinkForNodeId(self, nodeId):
        """
        Returns an incoming link if one starts from *nodeId*.
        It no incoming links qualify, raises a :py:class:`DtaError`.
        """
        for link in self.iterIncomingLinks():
            if link.getStartNode().getId() == nodeId:
                return link
        raise DtaError("Node %d does not have an incoming link starting from %d" % (self._id, nodeId)) 

    def getNumIncomingLinks(self):
        """
        Returns the number of incoming links.
        """
        return len(self._incomingLinks)

    def getNumOutgoingLinks(self):
        """
        Returns the number of outgoing links.
        """
        return len(self._outgoingLinks)


    def hasConnector(self):
        """
        Return True if there is a connector attached to the node.
        """
        for link in self.iterIncomingLinks():
            if link.isConnector():
                return True

        for link in self.iterOutgoingLinks():
            if link.isConnector():
                return True

        return False 

    def getCardinality(self):
        """
        Return a pair of numbers representing the number of 
        incoming and outgoing links respectively.
        """
        return (len(self._incomingLinks), len(self._outgoingLinks))
        
    def isIntersection(self):
        """
        Return True if this node is an intersection
        
        .. todo:: And an intersection is what?  Technical definition please.
        """
        return not self.isJunction() 

    def isJunction(self, countRoadNodesOnly=False):
        """
        Return True if this node is a junction. 
        
        .. todo:: And a junction is what?  Technical definition please.
        """
        if self.getNumOutgoingLinks() == 1 or self.getNumIncomingLinks() == 1:
            return True
        if self.isMidblockNode(countRoadNodesOnly=countRoadNodesOnly):
            return True 

        return False 

    def isMidblockNode(self, countRoadNodesOnly=False):
        """
        Return True if the node is a shape point (e.g. Node 51245 in the 
        following graph).  Specifically, a node is a shape point iff:
        
        * it has exactly two adjacent nodes *and*
        * it has either two (in the case one a one-way street) or four (in the case of a two way street) adjacent links 
        
        If *countRoadNodesOnly* is True the method will count only adjacent :py:class:`RoadNode` instances and
        adjacent :py:class:`RoadLink` instances (so it will disregard any connectors). 
        
        .. image:: /images/shapePoint.png
           :height: 300px

        """
        
        if not countRoadNodesOnly:
            if self.getNumAdjacentLinks() == 4 and self.getNumAdjacentNodes() == 2:
                return True
            if self.getNumAdjacentLinks() == 2 and self.getNumAdjacentNodes() == 2:
                return True
        else: 
            if self.getNumAdjacentRoadLinks() == 4 and self.getNumAdjacentRoadNodes() == 2:
                return True
            if self.getNumAdjacentRoadLinks() == 2 and self.getNumAdjacentRoadNodes() == 2:
                return True
 
        return False
    
    def getName(self):
        """
        Return the name of the intersection as a string consisting of the upper-cased labels 
        of the incoming links in sorted order, separated by ``AND``.  (e.g. ``VAN NESS AVE AND MARKET ST``)
        """
        return " AND ".join(self.getStreetNames())

    def getStreetNames(self, incoming=True, outgoing=False):
        """
        Return the street names (labels) of the relevant links as a sorted upper-case list.
        """
        names = set()
        if incoming:
            for ilink in self.iterIncomingLinks():
                if ilink.getLabel(): names.add(ilink.getLabel().upper())
                
        if outgoing:
            for olink in self.iterOutgoingLinks():
                if olink.getLabel(): names.add(olink.getLabel().upper())
                    
        return sorted(names)

    def iterMovements(self):
        """
        Return an iterator to all the :py:class:`Movement` instances going through the node.
        """
        return (mov for iLink in self.iterIncomingLinks() for mov in
                iLink.iterOutgoingMovements())
        
    def getMovement(self, startNodeId, endNodeId):
        """
        Return the :py:class:`Movement` from the start node identified by the *startNodeId* to 
        the end node identified by the *endNodeId* that goes through this node.
        """
        iLink = self.getIncomingLinkForNodeId(startNodeId)
        return iLink.getOutgoingMovement(endNodeId)
    
    def getMovementForLinkIds(self, incomingLinkId, outgoingLinkId):
        """
        Return the :py:class:`Movement` with incoming and outgoing links specified by
        *incomingLinkId* and *outgoingLinkId*.
        """
        iLink = self.getIncomingLinkForId(incomingLinkId)
        return iLink.getOutgoingMovementForLinkId(outgoingLinkId)
        
    def getNumMovements(self):
        """
        Return the number of :py:class:`Movement` instances associated with this node.
        """
        return sum(link.getNumOutgoingMovements() for link in self.iterIncomingLinks())
        

