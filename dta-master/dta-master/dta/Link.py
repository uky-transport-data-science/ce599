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
import math
from .DtaError import DtaError
from .Node import Node

class Link(object):
    """
    Base class that represents a link in a network.
    """
    #: Default label is an empty string
    DEFAULT_LABEL = ""
    
    def __init__(self, id, startNode, endNode, label):
        """
        Constructor.
        
         * *id* is a unique identifier (unique within the containing network), an integer, or None
         * *startNode*, *endNode* are Nodes
         * *label* is a string. If None passed, will use default.
         
        """ 
        self._id    = id     # integer id
        if label:   
            self._label = label
        else:
            self._label = Link.DEFAULT_LABEL
        
        if not isinstance(startNode, Node):
            raise DtaError("Initializing Link with non-Node startNode: %s" % str(startNode))
        
        if not isinstance(endNode, Node):
            raise DtaError("Initializing Link with non-Node endNode: %s" % str(endNode))

        # a Node instance
        self._startNode = startNode
        # a Node instance
        self._endNode   = endNode
                
    def getStartNode(self):
        """
        Accessor for startNode
        """
        return self._startNode
    
    def getEndNode(self):
        """
        Accessor for endNode
        """
        return self._endNode
    
    def euclideanLength(self, includeShape=False):
        """
        Calculates the length based on simple Euclidean distance.
        
        This will be in the units specified by :py:attr:`Node.COORDINATE_UNITS`.
        
        *includeShape* is ignored in the generic case; the :py:class:`RoadLink` will use that arg.
        """
        return math.sqrt( ((self._startNode.getX()-self._endNode.getX())*(self._startNode.getX()-self._endNode.getX())) +
                          ((self._startNode.getY()-self._endNode.getY())*(self._startNode.getY()-self._endNode.getY())) )
        
    def getReferenceAngle(self):
        """
        Visualizing the link as a straight vector from (0,0), returns the angle between <1,0> and this link.
        
        So returns a number in [0,2pi), increasing clockwise.
        
        These are based on the euclidean length of the link, so assumes a straight line.  If the link has no length,
        returns 0.
        
        """
        if self.euclideanLength() == 0: return 0
        
        angle = math.acos( (self._endNode.getX() - self._startNode.getX()) / self.euclideanLength() )
        # angle is in [0, pi]
        if angle > 0 and self._endNode.getY() > self._startNode.getY():
            angle = 2.0*math.pi - angle
        return angle
    
    def getReferenceAngleInDegrees(self):
        """
        Return the Reference angle in degrees
        """
        return self.getReferenceAngle() / math.pi * 180.0
        
    def getOtherEnd(self, node):
        """
        Return the other end node than the one provided.
        """
        if self._startNode == node:
            return self._endNode
        elif self._endNode == node:
            return self._startNode 
        else:
            raise DtaError("Link %d does not have end node %d" % (Link.getId(),
                                                                      node.getId()))

    def getId(self):
        """
        Return the link id
        """
        return self._id

    def getIid(self):
        """
        Return a pair representing the start and end node ids
        """
        return (self.getStartNode().getId(), self.getEndNode().getId())

    def setLabel(self, label):
        """
        Set the link label
        """
        self._label = label
        
    def getLabel(self):
        """
        Return the link label
        """
        return self._label
        
    def hasSameAttributes(self, other):
        """
        Return True if the two links have the same attributes return True
        """

        def getattrs(link):
            attrs = (link._facilityType,
                     link._freeflowSpeed,
                     link._effectiveLengthFactor,
                     link._responseTimeFactor,
                     link._numLanes,
                     link._roundAbout,
                     link._level)
            return attrs 

        attr1 = getattrs(self)
        attr2 = getattrs(other) 

        if attr1 == attr2:
            return True 
        return False 
        
    def getStartNodeId(self):
        """
        Return the id of the start node
        """
        return self.getStartNode().getId()

    def getEndNodeId(self):
        """
        Return the id of the end node
        """
        return self.getEndNode().getId()
    
