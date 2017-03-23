"""

Utility functions for use throughout DTA Anyway.

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
import copy
import re
import sys
import datetime

import dta
import shapefile

from itertools import izip
from collections import defaultdict
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

def parseTextRecord(iterable, is_separator=re.compile(r"^a"), 
                is_comment = re.compile(r"^#"), 
                joiner=lambda tokens: " ".join(tokens)): 


    """
    Read a text file record by record where a record is defined
    in multiple sequential lines and return a string concatenating 
    all the lines of a record into one line. 
    
    * *is_separator* is a regex instance that identifies the lines which separate records. 
    * *is_comment* is a regex instance that identifies comment lines that ought to 
      be bypassed. 
    * *joiner*  is a function used on the list of strings
    
    Yields the result of *joiner* on the list of strings.
    """

    record = []
    for line in iterable:
        line = line.strip()
        if is_comment.match(line):
            continue
        if is_separator.match(line):
            if record:
                if isinstance(joiner(record), str):
                    if is_separator.match(joiner(record)):
                        yield joiner(record)
                    record = []
                else:
                    yield record
                    record = [] # remove if record headers do
                            # not serve as record separators
            record.append(line)
        else:
            record.append(line)
    if record:
        yield joiner(record)


def militaryTimeToDateTime(militaryTime):
    """
    Return a datetime.time object that corresponds
    to the military time
    """
    mTime = str(militaryTime)
    if len(mTime) == 4:
        hours = int(mTime[:2])
        minutes = int(mTime[2:])
        return datetime.time(hours, minutes)
    
    elif len(mTime) == 3:
        hours = int(mTime[0])
        minutes = int(mTime[1:])
        return datetime.time(hours, minutes)
    else:
        raise dta.DtaError('Unknown military time format %d' % militaryTime)

def writePoints(iterPoints, fileName):
    """
    Write the input points to a shapefile. Each point should be a tuple of (x, y) floats
    """
    w = shapefile.Writer(shapefile.POINT)
    w.field("ID", "N", 10) 
    i = 0
    for x,y in iterPoints:
        i += 1
        w.point(x,y)
        w.record(i)
    w.save(fileName)

def writePolygon(listOfPoints, fileName): 
    """
    Write the input points as a polygon. Each point should be a tuple of (x,y) coordinates
    """
    w = shapefile.Writer(shapefile.POLYGON)
    w.field("ID", "N", 10) 
    w.poly(parts=[listOfPoints])
    w.record(1) 
    w.save(fileName)

def isRightTurn(pi, pj, pk):
    
    if direction(pi, pj, pk) > 0:
        return True
    return False

def direction(point0, point1, point2):
    """
    Returns the :py:func:`dta.crossProduct` result of the two vectors
    <*point2*-*point0*, *point1*-*point0*>
    e.g. the vectors emanating from point0 to point2 and point1.
    
    All arguments should be 2-tuple points of floats.
    """
    return crossProduct((point2[0] - point0[0], point2[1] - point0[1]),
                        (point1[0] - point0[0], point1[1] - point0[1])) 

def crossProduct(v1, v2):
    """
    Assuming the two vectors *v1* and *v2* are on the z=0 plane, returns
    the z-component of the cross product between *v1* and *v2*.
    
    The magnitude of this value is the area of the parallelogram with *v1* and *v2* as sides,
    and is therefore 0 when the vectors are collinear.
    """ 
    return v1[0]*v2[1] - v2[0]*v1[1]

def lineSegmentsCross(p1, p2, p3, p4, checkBoundaryConditions=False):
    """
    Helper function that determines if two line segments, 
    defined as a sequence of pairs of points, (*p1*, *p2*) and (*p3*, *p4*) intersect. 
    If so it returns True, otherwise False. If the two 
    line segments touch each other the method will 
    return False.
    
    If *checkBoundaryConditions* is True, then if one point collinear with the other segment, we return
    True if and only if the point is **on** the other segment.
    
    If *checkBoundaryConditions* is False, we don't care about this case, and return False.  
    """
    
    d1 = direction(p3, p4, p1)
    d2 = direction(p3, p4, p2)
    d3 = direction(p1, p2, p3)
    d4 = direction(p1, p2, p4) 

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
            ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    if not checkBoundaryConditions:
        return False
    if d1 == 0 and onSegment(p3, p4, p1):
        return True
    elif d2 == 0 and onSegment(p3, p4, p2):
        return True
    elif d3 == 0 and onSegment(p1, p2, p3):
        return True
    elif d4 == 0 and onSegment(p1, p2, p4):
        return True
    return False

def polylinesCross(polyline1, polyline2):
    """
    Return True if the two polylines cross.
    Each polyline is should be a list of two point tuples
    """
    for p1, p2 in izip(polyline1, polyline1[1:]):
        for p3, p4 in izip(polyline2, polyline2[1:]):
            if lineSegmentsCross(p1, p2, p3, p4):
                return True
    if lineSegmentsCross(polyline1[-2], polyline1[-1],
                         polyline2[-2], polyline2[-1],
                         checkBoundaryConditions=True):
        return True
    return False
            
def onSegment(pi, pj, pk):
    """
    Assuming that point *pk* is known to be collinear with a segment (*pi*, *pj*),
    this function determines if *pk* lies **on** segment (*pi*, *pj*).
    It does so by examining if point *pk* is inside the boundary box of segment (*pi*,*pj*)
    
    *pi*, *pj*, *pk* are 2-tuples of floats (x,y).
    """
    if min(pi[0], pj[0]) <= pk[0] <= max(pi[0], pj[0]) and \
            min(pi[1], pj[1]) <= pk[1] <= max(pi[1], pj[1]):
        return True
    return False
    
def getMidPoint(p1, p2):
    """
    Return the the point in the middle of p1 and p2 as a (x,y) tuple.
    """
    return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

def getReverseNetwork(net):
    """
    Returns a network copy that has all the links reversed
    """
    rNet = dta.Network(net.getScenario())

    for node in net.iterNodes():
        cNode = copy.copy(node) 
        cNode._incomingLinks = []
        cNode._outgoingLinks = []
        rNet.addNode(cNode)

    for link in net.iterLinks():
        rLink = dta.Link(link._id,
                     rNet.getNodeForId(link.getEndNode().getId()),
                     rNet.getNodeForId(link.getStartNode().getId()), 
                     "")                                       
        rNet.addLink(rLink)
        
    return rNet

def plotSignalAttributes(net, militaryStartTime, militaryEndTime, outputFile):
    """
    plot signal attributes
    """
    w = shapefile.Writer(shapefile.POINT)
    
    w.field("ID", "N", 10)
    w.field("Cycle", "N", 10)
    w.field("NumPhas", "N", 10)
    w.field("allRed", "N", 10)
    w.field("yellow", "N", 10)
    w.field("green", "N", 10)
    w.field("minGreen", "N", 10)
    w.field("maxGreen", "N", 10)

    pi = net.getPlanCollectionInfo(militaryStartTime, militaryEndTime)

    for node in net.iterRoadNodes():
        if node.hasTimePlan(pi):
            tp = node.getTimePlan(pi)
            cycle = tp.getCycleLength()
            numPhas = tp.getNumPhases()

            allRed = sum([phase.getRed() for phase in tp.iterPhases()])
            yellow = sum([phase.getYellow() for phase in tp.iterPhases()])
            green = cycle - yellow - allRed
            
            minGreen = min([phase.getGreen() for phase in tp.iterPhases()])
            maxGreen = max([phase.getGreen() for phase in tp.iterPhases()])

            w.point(node.getX(), node.getY())
            w.record(node.getId(), cycle, numPhas, allRed, yellow, green, minGreen, maxGreen)

    w.save(outputFile)
            
            
class MappingError(Exception):
    pass

class NetworkMapping(object):
    """
    Contains the node and link mappings of two network objects
    """
    def __init__(self, netOne, netTwo):
        """
        netOne and netTwo are the two network objects to be mapped
        """
        self._netOne = netOne
        self._netTwo = netTwo

        self._mapNodesOneToTwo = dict()
        self._mapNodesTwoToOne = dict() 
        self._mapLinksOneToTwo = defaultdict(dict)
        self._mapLinksTwoToOne = defaultdict(dict)

    def mapNodesById(self):
        """
        Map the nodes of the two objects based on node ids
        """
        for nodeOne in self._netOne.iterNodes():
            if self._netTwo.hasNodeForId(nodeOne.getId()):
                nodeTwo = self._netTwo.getNodeForId(nodeOne.getId())
                self.setMappedNode(nodeOne, nodeTwo)

    def mapLinksByOrientation(self, maxAngle):
        """
        Map the links based on the input maxAngle for all the
        pair of nodes that have already been mapped
        """
        def getMinAngle(node1, edge1, node2, edge2):
            """
            Returns a positive number in degrees always in [0, 180]
            that corresponds to the
            acute angle between the two edges
            """
            orientation1 = node1.getOrientation(edge1.getMidPoint())
            orientation2 = node2.getOrientation(edge2.getMidPoint())
            if orientation2 > orientation1:
                angle1 = orientation2 - orientation1
                angle2 = 360 - orientation2 + orientation1
                return min(angle1, angle2)
            elif orientation1 > orientation2:
                angle1 = orientation1 - orientation2 
                angle2 = 360 - orientation1 + orientation2
                return min(angle1, angle2)
            else:
                return 0
            
        for nodeOne, nodeTwo in self._mapNodesOneToTwo.iteritems():            
            #incoming edges
            edges2 = list(nodeTwo.iterIncomingEdges())
            for edge1 in nodeOne.iterIncomingEdges():
                #pick the closest
                if len(edges2) == 0:
                    break 
                edges2 = sorted(edges2, key = lambda edge2: getMinAngle(nodeOne, edge1, nodeTwo, edge2))
                closestEdge = edges2[0]

                if getMinAngle(nodeOne, edge1, nodeTwo, closestEdge) < maxAngle:
                    self.setMappedLink(nodeOne, edge1, nodeTwo, closestEdge)
                    edges2.pop(0)
                
            #outgoing edges
            edges2 = list(nodeTwo.iterOutgoingEdges())
            for edge1 in nodeOne.iterOutgoingEdges():
                if len(edges2) == 0:
                    break
                edges2 = sorted(edges2, key = lambda edge2: getMinAngle(nodeOne, edge1, nodeTwo, edge2))
                closestEdge = edges2[0]
                if getMinAngle(nodeOne, edge1, nodeTwo, closestEdge) < maxAngle:
                    self.setMappedLink(nodeOne, edge1, nodeTwo, closestEdge)
                    edges2.pop(0)
            
    def setMappedNode(self, nodeOne, nodeTwo):
        """
        Map the two input nodes to each other. A one to one mapping is
        being created for the two nodes.
        """
        if nodeOne in self._mapNodesOneToTwo:
            raise DtaError("Node one %s has already been mapped to a node"
                               % nodeOne.id)
        if nodeTwo in self._mapNodesTwoToOne:
            raise DtaError("Node two %s has already been mapped to a node"
                               % nodeTwo.id)
        
        self._mapNodesOneToTwo[nodeOne] = nodeTwo
        self._mapNodesTwoToOne[nodeTwo] = nodeOne
        #TODO: consider
        #self._mapLinksOneToTwo[nodeOne] = {}
            
    def getMappedNode(self, node):
        """
        Return the mapped node. If the input node is from networkOne the
        corresponding node from network two is being returned and vice
        versa 
        """        
        if isinstance(node, self._netOne.getNodeType()):
            if node not in self._mapNodesOneToTwo:
                raise DtaError("Node %s does not have a mapped node" % node.id)
            return self._mapNodesOneToTwo[node]            
        elif isinstance(node, self._netTwo.getNodeType()):
            if node not in self._mapNodesTwoToOne:
                raise DtaError("Node %s does not have a mapped node" % node.id)
            return self._mapNodesTwoToOne[node]
        else:
            raise DtaError("Node %s should belong to one of the mapped networks"
                               % node.id)
           
    def setMappedLink(self, nodeOne, linkOne, nodeTwo, linkTwo):
        """
        Map linkOne attached to nodeOne to linkTwo attached to nodeTwo
        """
        assert isinstance(nodeOne, self._netOne.getNodeType())
        assert isinstance(linkOne, self._netOne.getLinkType())

        assert isinstance(nodeTwo, self._netTwo.getNodeType())
        assert isinstance(linkTwo, self._netTwo.getLinkType())

        if nodeOne is not linkOne.startVertex and nodeOne is not linkOne.endVertex:
            raise DtaError("Node %s is not connected to link %s" %
                               (nodeOne.id, linkTwo.iid_))

        if nodeTwo is not linkTwo.startVertex and nodeTwo is not linkTwo.endVertex:
            raise DtaError("Node %s is not connected to link %s" %
                               (nodeTwo.id, linkTwo.iid_))
        
        if nodeOne not in self._mapNodesOneToTwo:
            raise DtaError("Node %s has not been mapped"
                               % nodeOne.id)
        
        if self._mapNodesOneToTwo[nodeOne] != nodeTwo:
            raise DtaError("Node %s is not mapped to node %s"
                               % nodeTwo.id) 
                                      
        if nodeOne in self._mapLinksOneToTwo and linkOne in self._mapLinksOneToTwo[nodeOne]:
            raise DtaError("Node %s and link %s have already been mapped" %
                               (nodeOne.id, linkOne.iid))

        if nodeTwo in self._mapLinksTwoToOne and linkTwo in self._mapLinksTwoToOne[nodeTwo]:
            raise DtaError("Node two %s and link two %s have already been mapped" %
                               (nodeTwo.id, linkTwo.iid))

        self._mapLinksOneToTwo[nodeOne][linkOne] = linkTwo
        #TODO: more error checks 
        self._mapLinksTwoToOne[nodeTwo][linkTwo] = linkOne

    def getMappedLink(self, node, link):

        if isinstance(node, self._netOne.getNodeType()) and \
           isinstance(link, self._netOne.getLinkType()):

            if node is not link.startVertex and node is not link.endVertex:
                raise DtaError("Node %s is not connected to link %s" %
                                   (node.id, linkTwo.iid_))        

            if node not in self._mapLinksOneToTwo or link not in self._mapLinksOneToTwo[node]:
                raise DtaError("Node %s and link %s have not been mapped" %
                                   (node.id, link.iid))

            return self._mapLinksOneToTwo[node][link]
        elif isinstance(node, self._netTwo.getNodeType()) and \
           isinstance(link, self._netTwo.getLinkType()):

            if node is not link.startVertex and node is not link.endVertex:
                raise DtaError("Node %s is not connected to link %s" %
                                   (node.id, linkTwo.iid_))        

            if node not in self._mapLinksTwoToOne or link not in self._mapLinksTwoToOne[node]:
                raise DtaError("Node %s and link %s have not been mapped" %
                                   (node.id, link.iid))

            return self._mapLinksTwoToOne[node][link]
        else:
            raise DtaError("Node %s and Link %s must belong to the same network"
                               % (node.id, link.iid_))


class Time(datetime.time):
    """
    Class that represents a time (without a specific date).
    Adds a few simple methods to the standard python datetime.time class.
    """

    @classmethod
    def readFromStringWithoutColon(cls, timeAsString):
        """
        Read a string representing time in the format %H:%M e.g. 1630
        and return a time object
        """
        startTimeDT = datetime.datetime.strptime(timeAsString, "%H%M")  
        return Time(startTimeDT.hour, startTimeDT.minute)

    @classmethod
    def readFromString(cls, timeAsString):
        """
        Read a string representing time in the format %H:%M or %H:%M:%S e.g. 16:30
        and return a time object
        """        
        if timeAsString.count(":") == 1:
            startTimeDT = datetime.datetime.strptime(timeAsString, "%H:%M")
            return Time(startTimeDT.hour, startTimeDT.minute)
        
        startTimeDT = datetime.datetime.strptime(timeAsString, "%H:%M:%S")
        return Time(startTimeDT.hour, startTimeDT.minute, startTimeDT.second)
        

    @classmethod
    def fromMinutes(cls, minutes):
        """
        Return a Time object that has the same number of minutes and the input arguments
        """
        hours = minutes / 60
        minutes = minutes % 60
        return Time(hours, minutes) 
    
    @classmethod
    def fromSeconds(cls, seconds):
        """
        Return a Time object that assuming *seconds* represents seconds after midnight.
        """
        seconds = seconds % (60*60*24)
        
        hours = int( seconds / (60*60))
        seconds -= hours*(60*60)
        
        minutes = int(seconds/60)
        seconds -= minutes*60
        
        return Time(hours, minutes, seconds)
    
    def __init__(self, hour, minute, second=0):

        datetime.time.__init__(hour, minute, second)

    def __lt__(self, other):
        """
        Implementation of the less than < operator
        """
        if self.hour < other.hour:
            return True
        elif self.hour == other.hour:
            if self.minute < other.minute:
                return True
        return False

    def __eq__(self, other):
        """
        Implementation of the == operator
        """
        if self.hour == other.hour and self.minute == other.minute:
            return True
        else:
            return False

    def __gt__(self, other):
        """
        Implementation of the > operator
        """
        return not self.__lt__(other)

    def __add__(self, other):
        """
        Implements the addition operator
        """
        hour = self.hour + other.hour
        minute = self.minute + other.minute
        if minute >= 60:
            minute -= 60
            hour += 1
        if hour >= 24:
            hour -= 24
        return Time(hour, minute)

    def __sub__(self, other):
        """
        Implements the minus operator
        """
    
        minute = self.minute - other.minute
        hour = self.hour - other.hour
        if minute < 0:
            minute += 60
            hour -= 1
        if hour < 0:
            hour += 24 
        return Time(hour, minute)        

    def __hash__(self):
        """
        Returns military time as an integer
        """
        return self.hour * 100 + self.minute

    def __mod__(self, other):
        """
        Implementation of the modulus operator
        """
        return self.getMinutes() % other.getMinutes() 

    def getMinutes(self):
        """
        Return the number of minutes from 0:00AM that
        correspond to the hours and minutes of this
        object.
        """
        return self.hour * 60 + self.minute 

def bucketRounding(matrix, decimalPosition):
    """
    This method applies bucket rounding to the input numpy matrix in place.
    The decimal position is identified by the the input integer decimalPosition
    The matrix rounding algorithm will preserve row sums but will not preserve
    column sums
    """
    numRows = matrix.shape[0]
    numCols = matrix.shape[1]

    levelOfAccuracy = 1.0 / 10 ** decimalPosition
    numRows = matrix.shape[0]
    numCols = matrix.shape[1]
    bucket = 0
    for i in range(numRows):
        for j in range(numCols):
            value = matrix[i,j]
            roundedValue = round(matrix[i,j], decimalPosition)
            bucket += value - roundedValue
            if bucket > levelOfAccuracy:
                finalValue = roundedValue + levelOfAccuracy
                bucket -= levelOfAccuracy
            elif bucket < -levelOfAccuracy and roundedValue >= levelOfAccuracy:
                finalValue = roundedValue - levelOfAccuracy
                bucket += levelOfAccuracy
            else:
                finalValue = roundedValue
            matrix[i,j] = finalValue

def getNumZeroEntries(matrix):
    """
    Return the number of cells(=OD Pairs) in the input matrix with zero values
    """
    return (matrix == 0).sum()

def plotTripHistogram(matrix, outputFile):
    """
    Plot a histogram of the cell values and write the result in the outputFile
    *matrix* is a numpy array .
    
    .. Note:: Requires `pylab <http://www.scipy.org/PyLab>`_ module.
    """
    import pylab as plt
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)

    ax.hist(matrix.flat, bins=100, facecolor='green', alpha=0.75, log=True)
    ax.set_xlabel('OD trips')
    ax.set_ylabel('Frequency')
    ax.set_title("%s. Trip Frequency. Sum = %.0f"  %
                 (outputFile, matrix.sum()))
    plt.savefig("%s" % outputFile)
    plt.cla()


