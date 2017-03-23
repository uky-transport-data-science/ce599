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
from .Node import Node

class Centroid(Node):
    """
    A Node subclass that represents a centroid node in a network, which is the origin or destination
    of :py:class:`Demand`.
    
    Centroids are typically separated from :py:class:`RoadNode` instances via a :py:class:`VirtualNode`,
    with an intermediate :py:class:`VirtualLink` connecting the :py:class:`VirtualNode` to the centroid, 
    and a :py:class:`Connector` linking the :py:class:`VirtualNode`
    to the :py:class:`RoadNode`.

    See :py:meth:`Network.insertVirtualNodeBetweenCentroidsAndRoadNodes` for diagram.

    .. note:: lmz has read over this, so todos are marked.
    """        
    def __init__(self, id, x, y, label=None, level=None):
        """
        Constructor.
        
         * id is a unique identifier (unique within the containing network), an integer
         * x and y are coordinates (what units?)
         * label is a string, for readability.  If None passed, will default to "label [id]"
         * level is for vertical alignment.  More details TBD.  If None passed, will use default.  
        """        
        Node.__init__(self, id, x, y, geometryType=Node.GEOMETRY_TYPE_CENTROID, label=label, level=level)

    def isRoadNode(self):
        """
        Return True if this Node is a RoadNode.
        """
        return False

    def isCentroid(self):
        """
        Return True if this Node is a Centroid.
        """
        return True

    def isVirtualNode(self):
        """
        Return True if this Node is a VirtualNode.
        """
        return False
        
    def isConnectedToRoadNode(self, roadNode):
        """
        Return True if there is a :py:class:`VirtualLink` followed by a :py:class:`Connector` that 
        connects to the given :py:class:`RoadNode`.  (It doesn't actually check the types of the links or nodes,
        however.)
        """
        
        for vLink in self.iterAdjacentLinks():
            vNode = vLink.getOtherEnd(self)
            con = vLink.getAdjacentConnector()
            rNode = con.getOtherEnd(vNode)
            
            if rNode == roadNode:
                return True
        return False
        
    def getNumAttachedConnectors(self):
        """
        Return the number of connectors attached to this Centroid.
        
        .. todo:: again, this isn't accurate, because it's upstream nodes plus downstream nodes, confusing
                  when they are the same...
        """
        return self.getNumOutgoingConnectors() + self.getNumIncomingConnectors()

    def getNumOutgoingConnectors(self):
        """
        Return the number of outgoing connectors.
        
        .. todo:: This is not really accurate, why not call it what it is?  Number of downstream nodes?  And put it
                  in :py:class:`Node`?
        """
        return sum([1 for con in self.iterDownstreamNodes()]) 

    def getNumIncomingConnectors(self):
        """
        Return the number of incoming connectors.
        
        .. todo:: his is not really accurate, why not call it what it is?  Number of upstream nodes?  And put it
                  in :py:class:`Node`?
        """
        return sum([1 for con in self.iterUpstreamNodes()])

        #    this does not work. Why? 
        #    for con in vNode.iterOutgoingLinks():
        #        if con.isConnector():
        #            yield con     
        #for vNode in self.iterUpstreamNodes():
        #    for con in vNode.iterIncomingLinks():
        #        if con.isConnector():
        #            yield con
                    
    def iterAdjacentConnectors(self):
        """
        Returns an iterator to each adjacent link of each adjacent link (e.g. each link separated from this node
        by an intermediate link, presumably a virtual link) that are not :py:class:`VirtualLink` instances.
        
        .. todo:: The function definition is misleading because the results aren't verified as :py:class:`Connector` instances.
        """
        connectors = set()
        for vLink in self.iterAdjacentLinks():
            vNode = vLink.getOtherEnd(self)
            for con in vNode.iterAdjacentLinks():
                if con.isVirtualLink():
                    continue
                connectors.add(con)
        return iter(connectors) 

    def isConnectedTo(self, roadNodeId):
        """
        Return True a :py:class:`RoadNode` with the given *roadNodeId* is at the other end of one of the
        connectors returned by :py:meth:`Centroid.iterAdjacentConnectors`.
        """
        for con in self.iterAdjacentConnectors():
            if con.startIsRoadNode():
                if con.getStartNodeId() == roadNodeId:
                    return True
            elif con.endIsRoadNode():
                if con.getEndNodeId() == roadNodeId:
                    return True                
        return False
        
        
            
        
