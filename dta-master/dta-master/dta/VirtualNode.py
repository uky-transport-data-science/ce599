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
from .Node import Node

class VirtualNode(Node):
    """
    A Node subclass that represents a virtual node in a network.

    Virtual nodes typically sit between a :py:class:`Centroid` (via a :py:class:`VirtualLink` )
    and a :py:class:`RoadNode` (via a :py:class:`Connector` ).  
    See :py:meth:`Network.insertVirtualNodeBetweenCentroidsAndRoadNodes` for diagram.
    
    .. note:: lmz has read over this, so todos are marked.
    """
    
    DEFAULT_CONTROL  = 0 # value to use if we must
    DEFAULT_PRIORITY = 0 # value to use if we must

    def __init__(self, id, x, y, label=None, level=None):
        """
        Constructor.
        
         * id is a unique identifier (unique within the containing network), an integer
         * *x* and *y* are coordinates in the units specified by :py:attr:`Node.COORDINATE_UNITS`
         * label is a string, for readability.  If None passed, will default to "label [id]"
         * level is for vertical alignment.  More details TBD.  If None passed, will use default.  
        """        
        Node.__init__(self, id, x, y, geometryType=Node.GEOMETRY_TYPE_VIRTUAL, label=label, level=level)

    def isRoadNode(self):
        """
        Return True if this Node is a RoadNode.
        """
        return False

    def isCentroid(self):
        """
        Return True if this Node is a Centroid
        """
        return False

    def isVirtualNode(self):
        """
        Return True if this Node is a VirtualNode
        """
        return True

    def getCentroid(self):
        """
        Return the :py:class:`Centroid` associated with this virtual node.
        
        .. todo:: what makes this a Centroid as opposed to just an adjacent node?
        """
        for ilink in self.iterIncomingLinks():
            return ilink.getStartNode() 
        for olink in self.iterOutgoingLinks():
            return olink.getEndNode() 
        raise DtaError("VirtualNode %d is not connected to a centroid" % self.getId())

    def getConnectedRoadNode(self):
        """
        Return a connected :py:class:`RoadNode`.
        
        .. todo:: Why is this useful, it returns one when there could be others?
        """
        for ilink in self.iterIncomingLinks():
            if ilink.isConnector():
                return ilink.getOtherEnd(self)
        for olink in self.iterOutgoingLinks():
            if olink.isConnector():
                return olink.getOtherEnd(self)            
        raise DtaError("VirtualNode %d is not connected to a road node" % self.getId())            
