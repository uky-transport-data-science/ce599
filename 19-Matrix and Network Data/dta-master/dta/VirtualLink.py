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

from .Centroid import Centroid
from .Connector import Connector
from .DtaError import DtaError
from .Link import Link
from .VirtualNode import VirtualNode

class VirtualLink(Link):
    """
    A VirtualLink is a Link that connects a :py:class:`Centroid` with
    a :py:class:`Connector`.
    
    """
    
    # Dummy values to use if you must
    REVERSE         = -1
    FACILITY_TYPE   = 100
    LENGTH          = 0
    FFSPEED         = 30
    RESPONSE_FACTOR = 0
    LENGTH_FACTOR   = 0
    LANES           = 1
    RABOUT          = 0
    LEVEL           = 0
        
    def __init__(self, id, startNode, endNode, label):
        """
        Constructor. Verifies one node is a :py:class:`Centroid` and the
        other node is a :py:class:`VirtualNode`.
        
         * *id* is a unique identifier (unique within the containing network), an integer
         * *startNode*, *endNode* are :py:class:`Node` instances
         * *label* is a string, or None 
        """
        
        if not isinstance(startNode, Centroid) and not isinstance(endNode, Centroid):
            raise DtaError("Attempting to initialize a VirtualLink without a Centroid: %s - %s" % 
                           (str(startNode), str(endNode)))

        if not isinstance(startNode, VirtualNode) and not isinstance(endNode, VirtualNode):
            raise DtaError("Attempting to initialize a VirtualLink without a VirtualNode: %s - %s" % 
                           (str(startNode), str(endNode)))
       
        Link.__init__(self, id, startNode, endNode, label)


    def getAdjacentConnector(self):
        """
        A VirtualLink connects a :py:class:`Centroid` with a :py:class:`Connector`; this
        returns the :py:class:`Connector` instance.
        """
        if isinstance(self._startNode, Centroid):
            for link in self._endNode.iterOutgoingLinks():
                if isinstance(link, Connector): return link

            raise DtaError("VirtualLink getAdjacentConnector(): Connector not found for %d-%d from endNode: %d" % 
                           (self._startNode.getId(), self._endNode.getId(),
                            self._endNode.getId()))
                        
        if isinstance(self._endNode, Centroid):
            for link in self._startNode.iterIncomingLinks():
                if isinstance(link, Connector): return link
            
            raise DtaError("VirtualLink getAdjacentConnector(): Connector not found for %d-%d from startNode: %d" % 
                           (self._startNode.getId(), self._endNode.getId(),
                            self._startNode.getId()))

    def isRoadLink(self):
        """
        Return True this Link is RoadLink
        """
        return False

    def isConnector(self):
        """
        Return True if this Link is a Connector
        """
        return False

    def isVirtualLink(self):
        """
        Return True if this LInk is a VirtualLink
        """
        return True

    def getCentroid(self):
        """
        Return the centroid associated with the VirtualLink 
        """
        
        if self.getStartNode().isCentroid():
            return self.getStartNode()
        elif self.getEndNode().isCentroid():
            return self.getEndNode()
        else:
            raise DtaError("Virtual link %d is not asociated with a Centroid" % self.getId())
