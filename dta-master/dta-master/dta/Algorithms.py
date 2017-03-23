"""

Algorithms for use throughout DTA Anyway

"""

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

import sys
import pdb 
import math 
from collections import deque

import dta
from dta.Utils import isRightTurn, lineSegmentsCross
from itertools import izip, tee, cycle, ifilter, ifilterfalse

def all2(seq, pred=None):
    "Returns True if pred(x) is true for every element in the iterable"
    for elem in ifilterfalse(pred, seq):
        return False
    return True

def any2(seq, pred=None):
    """
    Returns True if pred(x) is true for at least one element in the iterable
    """
    for elem in ifilter(pred, seq):
        return True
    return False

def pairwise(iterable):
    """
    This function will return len(iterable) pairs from the input iterable
    example [1, 2, 3] will produce (1, 2), (2, 3), (3, 1)
    """
    a, b = tee(iterable)
    b = cycle(b) 
    b.next()
    return izip(a, b)
    
def dfs(net, root=None):
    """
    Non-Recursive depth first search algorithm with 
    pre and post orderings. At the end of the execution
    all nodes in the network have a pre and post numbers
    and predecessor nodes assigned to them.
    """
    
    time = 0
    for node in net.iterNodes():
        node.pre = 0
        node.post = 0
        node.pred = None
        node.visited = False 

    allNodes = [node for node in net.iterNodes()]
    if root:
        allNodes.remove(root)
        allNodes.insert(0, root)

    nodesToExamine = []

    for node in allNodes:
        
        if node.pre == 0:
            nodesToExamine.append(node)

        while nodesToExamine:        
            pivot = nodesToExamine[-1]
            if pivot.visited == False:            
                for downNode in pivot.iterDownstreamNodes():                
                    if downNode.visited == False:                    
                        nodesToExamine.append(downNode)
                        downNode.pred = pivot 
                pivot.visited = True
                time += 1
                pivot.pre = time 
            elif pivot.post > 0:
                nodesToExamine.pop() 
            else:
                time += 1
                pivot.post = time

def getMetaGraph(net):
    """
    Return a network that represents the meta graph of the input network. 
    At the end of the execution of this algorithm each node points to 
    its metanode
    """
    pass 


def hasPath(net, originNode, destNode):
    """
    Return true if the network has a path 
    from the origin node to the destination node
    """
    
    dfs(net, originNode) 

    node = destNode
    while node and node != originNode:
        node = node.pred 

    if node is None:
        return False
    return True

def predicate(elem1, elem2):
    """
    Compare the two input elements and return a positive 
    integer if elem2 is greater than elem1. If the first
    two coordinates of the input elments are the 
    comparisson is made using the second ones
    >>> elem1 = (1,4)
    >>> elem2 = (1,3) 
    >>> predicate(elem1, elem2)
    >>> -1    
    """ 
    if elem1[0] == elem2[0]:                
        if elem1[1] < elem2[1]:
            return -1 
        elif elem1[1] == elem2[1]:
            return 0
        else:
            return 1
    else:
        if elem1[0] < elem2[0]:
            return -1
        else:
            return 1

def nodesInLexicographicOrder(node1, node2):
    """
    Compare the two input elements and return a positive 
    integer if node2 is greater than node1. If the first
    two coordinates of the input elments are the 
    comparisson is made using the second ones
    >>> node1 = (1,4)
    >>> node2 = (1,3) 
    >>> predicate(node1, node2)
    >>> -1    
    """ 
    if node1.getX() == node2.getX():                
        if node1.getY() < node2.getY():
            return -1 
        elif node1.getY() == node2.getY():
            return 0
        else:
            return 1
    else:
        if node1.getX() < node2.getX():
            return -1
        else:
            return 1

def getTightHull(setOfPoints, step):
    """
    Return the points and and their corresponding 
    indices with the highest y values in each of 
    the intervals identified by the input step
    """
    points = sorted(setOfPoints, cmp=predicate)    

    hull = []
    hullIndices = []
    hull.append(points[0])
    i = 1

    maxY = -sys.maxint 
    pivotIndex = 0
    threshold = points[0][0] + step

    while i < len(points):
        #print i, points[i], threshold 
        while points[i][0] <= threshold:

            if i >= len(points) - 1:
                i += 1
                break 
            if points[i][1] > maxY:
                maxY = points[i][1]
                pivotIndex = i
            i += 1

        if pivotIndex == 0:
            threshold += step 
        else:
            threshold += step
            hull.append(points[pivotIndex])
            hullIndices.append(pivotIndex)
            maxY = - sys.maxint 
            pivotIndex = 0
                        

    return hull, hullIndices         

def getConvexHull3(points, step):
    """
    Modifield implementation of Graham's algorithm.
    The resulting polygon is no longer convex but will
    still contain all the given points. 
    """
    hull, hullIndices = getTightHull(points, step)

    bigHull = []
    for i, j in izip(hullIndices, hullIndices[1:]):
        
        #print i, j
       # print points[i:j+1]
        partialHull = getConvexHull(points[i:j+1])
        partialHull.pop()
        bigHull.extend(partialHull)
    

    return bigHull

def getConvexHull(points, upper=True):
    """
    Return the convex hull of the given points 
    """ 
    hull = []
    if upper:
        hull.append(points[0])
        hull.append(points[1])
        sequenceOfPoints = range(3, len(points))
        
    else:
        hull.append(points[-1])
        hull.append(points[-2])
        sequenceOfPoints = range(len(points) - 3, -1, -1)

    for i in sequenceOfPoints:
        hull.append(points[i])
        while len(hull) > 2 and not isRightTurn(hull[-3], hull[-2], hull[-1]):
            hull.pop(len(hull) - 2)

    return hull

def getContainingPolygon(net):
    """

    """
    points = [(n.getX(), n.getY()) for n in net.iterRoadNodes()]
    nodes = dict(izip(points, net.iterRoadNodes()))
    
    convexHull = getConvexHull(points)
 
    firstNode = nodes[convexHull[0]]
    node2 = nodes[convexHull[1]]
    linkOrientation = firstNode.getOrientation((node2.getX(), node2.getY()))

    polygon = [firstNode]

    adjNodes = sorted(firstNode.iterAdjacentNodes(), key=lambda n: firstNode.getOrientation((n.getX(), n.getY())))    
    for node in adjNodes:
        orientation = firstNode.getOrientation((node.getX(), node.getY()))
        if orientation >= linkOrientation:
            polygon.append(node)
            break 

    while True:

        node1 = polygon[-2]
        node2 = polygon[-1]

        adjNodes = sorted(lastNode.iterAdjacentNodes(), key=lambda n: lastNode.getOrientation(n))
        index = adjNodes.index(lastNode)

        if index == len(adjNodes) - 1:
            index = [0]
        else:
            index += 1

        if nodeToAdd == polygon[0]:
            break 
        
        
    
def getSmallestPolygonContainingNetwork(network):
    """
    treat all the links as bidirectional
    """

    nodes = list(net.iterRoadNodes())
    sorted(nodes, nodesInLexicographicOrder)
    
    #make a direct copy of the network
    #add the opposing links if they do not exist
    #add all the movements

    #find the left most node
    #if the leftmost node does not have any incoming or outgoing links then
    #move to the next one
    #by making the links bydirectional you are also making the network connected
    #if you remove the connectors you are also removing the external links 

def getConvexHull2(setOfPoints):
    """
    Refactored Graham's scan algorithm
    """
    points = sorted(setOfPoints, cmp=predicate)
    upperHull = getConvexHull(points, upper=True)
    lowerHull = getConvexHull(points, upper=False)
    upperHull.extend(lowerHull[1:-1])
    return upperHull
        
def getConvexHullGrahamScan(setOfPoints):
    """
    Implementation of Graham's scan algorithm
    """
    points = sorted(setOfPoints, cmp=predicate)

    upper = []
    upper.append(points[0])
    upper.append(points[1])
    
    for i in range(3, len(points)):        
        upper.append(points[i])
        while len(upper) > 2 and not isRightTurn(upper[-3], upper[-2], upper[-1]):
            upper.pop(len(upper) - 2)

    lower = []
    lower.append(points[-1])
    lower.append(points[-2])

    for i in range(len(points) - 3, -1, -1):

        lower.append(points[i])
        while len(lower) > 2 and not isRightTurn(lower[-3], lower[-2], lower[-1]):
            lower.pop(len(lower) - 2)

    lower.pop(0)
    lower.pop(len(lower) -1) 

    upper.extend(lower)
    return upper 

def isPointInPolygon(point, polygon):
    """
    Returns true if the point is inside the polygon 
    Point should be a (x,y) tuple or list
    Polygon is a list of points in clockwise order
    """

    x, y = point
    p1 = [0, y]
    p2 = [x, y]
    
    numIntersections = 0
    for polyPoint1, polyPoint2 in pairwise(polygon):        
        if lineSegmentsCross(p1, p2, polyPoint1, polyPoint2, checkBoundaryConditions=True):
            numIntersections += 1

    if numIntersections == 0:
        return False
    elif numIntersections % 2 == 0:
        return False
    return True 
            
def getClosestNode(net, inputNode):
    """
    Return the closest node in the input network
    """
    minDist = sys.maxint 
    closestNode = None
    for node in net.iterNodes():
        dist = (node.getX() - inputNode.getX()) ** 2 + (node.getY() - inputNode.getY()) ** 2
        if dist < minDist:
            minDist = dist 
            closestNode = node 

    return closestNode, math.sqrt(minDist)

def getClosestCentroid(net, inputCent):
    """
    Return the closest centroid in the input network
    """
    minDist = sys.maxint 
    closestCent = None
    for centroid in net.iterCentroids():
        dist = (centroid.getX() - inputCent.getX()) ** 2 + (centroid.getY() - inputCent.getY()) ** 2
        if dist < minDist and centroid!=inputCent:
            minDist = dist 
            closestCent = centroid

    return closestCent, math.sqrt(minDist) 

def getSPPathBetweenLinks(net, pathName, sourceLinkId, destLinkId):
    """
    Return a Path object containing he shortest path between the source link 
    and then dest link
    """
    sourceLink = net.getLinkForId(sourceLinkId)
    destinationLink = net.getLinkForId(destLinkId)
    ShortestPaths.initializeMovementCostsWithLengthInFeet(net)
    ShortestPaths.labelCorrectingWithLabelsOnLinks(net, sourceLink)
    path = ShortestPaths.getShortestPathBetweenLinks(sourceLink, destinationLink)
    return dta.Path(net, pathName, path)

class ShortestPaths(object):
    """
    Shortest path algorithms and various utilities
    """
    @staticmethod
    def initialiseMovementCostsWithFFTT(network):
        """Initialize all the movement costs with the edge free flow travel time in min"""
        for edge in network.iterLinks():
            for movement in edge.iterOutgoingMovements():
                movement.cost = edge.getFreeFlowTTInMin()

    @staticmethod
    def initializeMovementCostsWithLength(network):
        for edge in network.iterLinks():
            if edge.isVirtualLink():
                continue
            for movement in edge.iterOutgoingMovements():
                movement.cost = edge.getLength()

    @staticmethod
    def initiaxblizeEdgeCostsWithFFTT(network):
        """Initialize all the edge costs with the edge free flow travel times in minutes"""
        for edge in network.iterLinks():
            if edge.isLink():
                edge.cost = edge.getFreeFlowTTInMin()
            else:
                edge.cost = sys.maxint 
            
    @staticmethod
    def initializeEdgeCostsWithLength(network):
        """Initalize all the edge costs with the edge lengths in feet"""
        for edge in network.iterLinks():
            if edge.isVirtualLink():
                continue
            edge.cost = edge.getLength()

    @classmethod
    def labelCorrectingWithLabelsOnLinks(cls, graph, sourceLink):
        """
        Implementation of Pape's shortest path
        using a deque. Links are inserted to the 
        left of the deque if they have been already 
        visited. Otherwise they are inserted to the
        right of the deque.

        Movements need to have a cost attribute

        """
        for edge in graph.iterLinks():
            edge.label = sys.maxint 
            edge.alreadyVisited = False
            edge.predEdge = None
            
        sourceLink.label = 0

        edgesToExamine = deque()
        edgesToExamine.appendleft(sourceLink)

        while edgesToExamine:
            pivotEdge = edgesToExamine.popleft()
            pivotEdge.alreadyVisited = True
            for eMovement in pivotEdge.iterOutgoingMovements():
                newLabel = pivotEdge.label + eMovement.cost
                downstreamEdge = eMovement.getOutgoingLink()
                if newLabel < downstreamEdge.label:
                    downstreamEdge.label = newLabel
                    downstreamEdge.predEdge = pivotEdge
                    if downstreamEdge.alreadyVisited:
                        edgesToExamine.appendleft(downstreamEdge)
                    else:
                        edgesToExamine.append(downstreamEdge)        

                        
    @classmethod
    def labelCorrectingWithLabelsOnNodes(cls, graph, sourceVertex):
        """
        Implementation of Pape's shortest path
        using a deque. Vertices are inserted to the 
        left of the deque if they have been already 
        visited. Otherwise they are inserted to the
        right of the deque

        *graph* is an instance of a :py:class:`Network`.
        The edge cost used is given by :py:meth:`Link.euclideanLength`.
        :py:class:`VirtualLink` instances and :py:class:`VirtualNode` instances
        are not included in the shortest path.
        
        :py:class:`Node` instances have the following set:
        
        * *label* is set to the cost
        * *alreadyVisited* is a boolean
        * *predVertex* references the previous vertex Node
        
        """

        for vertex in graph.iterNodes():
            vertex.label = sys.maxint
            vertex.alreadyVisited = False 
            vertex.predVertex = None

        sourceVertex.label = 0
        verticesToExamine = deque()
        verticesToExamine.appendleft(sourceVertex)
        
        while verticesToExamine:
            pivotVertex = verticesToExamine.popleft()
            pivotVertex.alreadyVisited = True

            for edge in pivotVertex.iterOutgoingLinks():

                # VirtualLink instances are not included in the shortest path.
                if edge.isVirtualLink(): continue
                
                downstreamVertex = edge.getEndNode()
                
                # VirtualNode instances are not included in the shortest path.
                if downstreamVertex.isVirtualNode(): continue
                
                # The edge cost used is given by :py:meth:`Link.euclideanLength`.
                newLabel = pivotVertex.label + edge.euclideanLength()
                
                if newLabel < downstreamVertex.label:
                    downstreamVertex.label = newLabel
                    downstreamVertex.predVertex = pivotVertex
                    if downstreamVertex.alreadyVisited:
                        verticesToExamine.appendleft(downstreamVertex)
                    else:
                        verticesToExamine.append(downstreamVertex)



    @classmethod
    def labelSettingWithLabelsOnNodes(cls, graph, sourceVertex, endVertex, includeVirtual=False, sourceLabel=0.0, maxLabel=sys.float_info.max, 
                                          filterRoadLinkEvalStr=None):
        """
        .. TODO:: document new args
        
        Implementation of Pape's shortest path
        using a deque. Vertices are inserted to the 
        left of the deque if they have been already 
        visited. Otherwise they are inserted to the
        right of the deque

        *graph* is an instance of a :py:class:`Network`.
        The edge cost used is given by :py:meth:`Link.euclideanLength`.
        :py:class:`VirtualLink` instances and :py:class:`VirtualNode` instances
        are not included in the shortest path.
        
        :py:class:`Node` instances have the following set:
        
        * *label* is set to the cost
        * *alreadySet* is a boolean
        * *predVertex* references the previous vertex Node
        
        """

        for vertex in graph.iterNodes():
            vertex.label        = sys.float_info.max
            vertex.alreadySet   = False
            vertex.predVertex   = None
            mincostVertex       = sourceVertex

        sourceVertex.label      = sourceLabel
        
        verticesToExamine       = deque()
        nextPivotVertex         = sourceVertex
        
        # these are permanently labeled
        labeledVertices           = set()
        
        while True:
            
            pivotVertex = nextPivotVertex
            pivotVertex.alreadySet = True
            labeledVertices.add(pivotVertex)
                        
            # end condition if endVertex is passed
            if endVertex and (pivotVertex == endVertex): break
            # end condition if maxLabel is real
            if pivotVertex.label > maxLabel: break
            
            for edge in pivotVertex.iterOutgoingLinks():
                
                # don't include VirtualLink instances unless specified
                if not includeVirtual and edge.isVirtualLink(): continue
                
                # don't include the RoadLink instance if specified
                localsdict = {}
                localsdict['roadlink'] = edge
                if edge.isRoadLink() and filterRoadLinkEvalStr and eval(filterRoadLinkEvalStr, globals(), localsdict): 
                    dta.DtaLogger.debug("Skipping edge %10s with ft=%d" % (edge.getId(), edge.getFacilityType()))
                    continue
                
                downstreamVertex = edge.getEndNode()

                # don't include VirtualNode instances unless specified
                if not includeVirtual and downstreamVertex.isVirtualNode(): continue
                
                # The edge cost used is given by :py:meth:`Link.euclideanLength`.
                newLabel = pivotVertex.label + edge.euclideanLength(includeShape=True)
                
                if newLabel < downstreamVertex.label:
                    downstreamVertex.label = newLabel
                    downstreamVertex.predVertex = pivotVertex
                    if not downstreamVertex.alreadySet:
                        verticesToExamine.appendleft(downstreamVertex)

            mincost = 0
            if len(verticesToExamine)==0:
                return labeledVertices
            for updateVertex in verticesToExamine:
                if mincost==0:
                    mincost = updateVertex.label
                    mincostVertex = updateVertex
                else:
                    if updateVertex.label<mincost:
                        mincost = updateVertex.label
                        mincostVertex = updateVertex
            verticesToExamine.remove(mincostVertex)
            nextPivotVertex = mincostVertex
                
        return labeledVertices

    @classmethod
    def getShortestPathBetweenLinks(cls, graph, sourceLink, destinationLink, runSP=False):
        """
        Return the path from the sourceLink to the 
        destinationLink as a list of edges. The return list always contains the 
        destination and the source edge
        """
        if sourceLink==destinationLink:
            return []
        
        if runSP:
            ShortestPaths.labelCorrectingWithLabelsOnLinks(graph, sourceLink)
        
        edge = destinationLink
        path = []
        while edge != sourceLink:
            path.insert(0, edge)
            edge = edge.predEdge
        path.insert(0, edge)
        return path

    @classmethod
    def getShortestPathBetweenNodes(cls, sourceNode, destinationNode):
        """
        Return the path from the sourceNode to the 
        destinationNode as a list of nodes. The return list always contains the 
        destination and the source node
        """
        if sourceNode==destinationNode:
            return []
        vertex = destinationNode
        path = []
        while vertex != sourceNode:
            path.insert(0, vertex)
            vertex = vertex.predVertex
        path.insert(0, vertex)
        return path

     
