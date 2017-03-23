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

import datetime
import dta
import itertools
import random
import re
import sys
from collections import defaultdict
from pyparsing import *


def createTPPlusTransitRouteParser():
    """Create two parsers on the the header and one for the body containing hte nodes
    I may be able to create one parser if I can deal with N= wich has the same format with the
    header expresions. My problem is that I cannot get the parser to see the N= not as a header 
    expression but as a block of data"""

    lineName = Word(alphanums +" "+"#" + ":" + "_" + "-" + "/" + "\\" + "(" + ")" +"." + "&" + '"') + Literal(',').suppress()
    expr = Word(alphanums + '[' + ']') + Literal('=').suppress() + Word(alphanums + '"' + '.') + Literal(',').suppress()
    header = Literal('LINE NAME=') + lineName + OneOrMore(expr) 


    nodeId = Word(nums + '-') + ZeroOrMore(Literal(',').suppress())
    access = Optional('ACCESS=' + Word(nums) + ZeroOrMore(Literal(',').suppress()))
    delay = Optional('DELAY=' + Word(nums+'.'+nums) + ZeroOrMore(Literal(',').suppress()))
    segment = Group('N=' + OneOrMore(nodeId) + access + delay)
    body = OneOrMore(segment)
    route = header + body

    return header.parseString, body.parseString

def getDictOfParsedElements(parsedSegment):

    result = defaultdict(list)
    keyword = ""
    for i in parsedSegment:
        if i in ["N=", "ACCESS=", "DELAY="]:
            keyword = i
        else:
            result[keyword].append(i)
                
    return result

def parseRoute(net, routeAsString, includeOnlyNetNodes=False):

    header = routeAsString[0:routeAsString.find('N=')]
    body = routeAsString[routeAsString.find('N='):]
    
    headerParser, bodyParser = createTPPlusTransitRouteParser()
    headerFields = headerParser(header).asList()
    bodyFields = bodyParser(body)

    if 'LINE NAME=' not in headerFields:
        raise TPPlusError("I cannot create a route from %s" % str(headerFields))
    name = headerFields[headerFields.index('LINE NAME=') + 1]
    
    route = TPPlusTransitRoute(net, name)

    #TODO I do not like the following
    #print '\n\n', headerFields, '\n\n'
    #nose.tools.set_trace()

    for extAttrName, intAttrName in TPPlusTransitRoute.attrs.iteritems():
        if extAttrName in headerFields:
            setattr(route, intAttrName, headerFields[headerFields.index(extAttrName) + 1])

    
        
    for segment in bodyFields:
        
        access = TPPlusTransitNode.ACCESS_BOTH
        delay = TPPlusTransitNode.DELAY_VAL

        parsedSegment = getDictOfParsedElements(segment)

        nodeIds = parsedSegment["N="]
        if "ACCESS=" in parsedSegment:
            accessLast = float(parsedSegment["ACCESS="][0])
        else:
            accessLast = access
        if "DELAY=" in parsedSegment:
            delayLast = float(parsedSegment["DELAY="][0])
        else:
            delayLast = delay 
        
        #if segment[-2] == 'ACCESS=':
        #    access == segment[-1]
        #    nodeIds = segment[1:-2]
        #elif segment[-2] == 'DELAY=':
        #    delay == segment[-1]
        #    nodeIds = segment[1:-3]
        #else:
        #    nodeIds = segment[1:]
            
        for i, nodeId in enumerate(nodeIds):
            isStop = True
            if nodeId.startswith('-'):
                isStop = False
                nodeId = nodeId[1:]
            if includeOnlyNetNodes:
                if not net.hasNode(nodeId):
                    continue
                
            if i == len(nodeIds) - 1:
                route.addTransitNode(int(nodeId), isStop, accessLast, delayLast)
            else:
                route.addTransitNode(int(nodeId), isStop, access, delay)
            
            #print 'nodeId = ',nodeId

    return route
        
class TPPlusTransitNode(object):
    """
    Representation of a transit node for a :py:class:`TPPlusTransitRoute`
    """

    ACCESS_BOARD    = 1
    ACCESS_ALIGHT   = 2
    ACCESS_BOTH     = 0
    DELAY_VAL       = 0.0

    def __init__(self, nodeId, isStop, access, delay):
        """
        Basic transit node in a :py:class:`TPPlusTransitRoute`.
        
        * *nodeId* is a node number
        * *isStop* is a boolean
        * *access* is an integer
        * *delay* is a float representing the delay at this node, in minutes
        """
        self.nodeId = nodeId
        self.isStop = isStop
        self.access = access
        self.delay  = delay

    def __repr__(self):
        
        if self.isStop:
            return "%s, ACCESS=%d, DELAY=%.2f, \n" % (self.nodeId, self.access, self.delay)
        else:
            return "-%s, ACCESS=%d, DELAY=%.2f, \n" % (self.nodeId, self.access, self.delay)

class TPPlusTransitRoute(object):
    """
    Representation of a transit line read from Cube line file (TRNBUILD or PT)
    """

    extAttributes = ['RUNTIME', 'ONEWAY', 'MODE', 'OWNER', 'XYSPEED', 'TIMEFAC', 'FREQ[1]', 
                     'FREQ[2]', 'FREQ[3]', 'FREQ[4]', 'FREQ[5]']
    intAttributes = ['runtime', 'oneway', 'mode', 'owner', 'xySpeed', 'timefac', 'freq1',
                     'freq2', 'freq3', 'freq4', 'freq5']

    attrs = dict(itertools.izip(extAttributes, intAttributes))

    @classmethod
    def read(cls, net, fileName, includeOnlyNetNodes=False):

        inputStream = open(fileName, 'r')
        for record in dta.Utils.parseTextRecord(inputStream, is_separator=re.compile(r'^LINE NAME')):

            transitRoute = parseRoute(net, record, includeOnlyNetNodes=includeOnlyNetNodes)

            yield transitRoute
        
    
    def __init__(self, net, name):
        
        self._net       = net
        if name.startswith('"') and name.endswith('"'):
            name = name[1:-1]
        self.name       = name
        self.color      = None
        self.mode       = None
        self.oneway     = None
        self.owner      = None
        self.timefac    = None
        self.xySpeed    = None
        self.freq1      = None
        self.freq2      = None
        self.freq3      = None
        self.freq4      = None
        self.freq5      = None
        self.runtime    = None
        self._transitNodes = []

        self.attributes = {'RUNTIME':self.__dict__['runtime'], 
                           'ONEWAY':self.__dict__['oneway'],
                           'MODE':self.__dict__['mode'],
                           'OWNER':self.__dict__['owner'],
                           'XYSPEED':self.__dict__['xySpeed'],
                           'TIMEFAC':self.__dict__['timefac'],
                           'FREQ[1]':self.__dict__['freq1'],
                           'FREQ[2]':self.__dict__['freq2'],
                           'FREQ[3]':self.__dict__['freq3'],
                           'FREQ[4]':self.__dict__['freq4'],
                           'FREQ[5]':self.__dict__['freq5']}

    def __repr__(self):
        
        header = 'LINE NAME=%s' % self.name
        
        for extAttrName, intAttrName in TPPlusTransitRoute.attrs.iteritems():
            attrValue = getattr(self, intAttrName)
            if attrValue:
                header += ', %s=%s' % (extAttrName, str(attrValue))
                
        body = ', N='
        for transitNode in self.iterTransitNodes():
            if transitNode.isStop:
                body += '%s, ACCESS=%d, DELAY=%.2f, \n' % (transitNode.nodeId, transitNode.access, transitNode.delay) 
            else:
                body += '-%s, ACCESS=%d, DELAY=%.2f, \n' % (transitNode.nodeId, transitNode.access, transitNode.delay) 

        return header + body[:-2] + '\n'

    def getRouteName(self):

        name = 'LINE NAME=%s' % self.name

        return name
    
    def getHeadway(self, indexnum):
        """
        Returns the float representing the headway, in minutes.
        *indexnum* is 1 through 5, an index into the list of time periods
        """
        if indexnum == 1:
            return float(self.freq1)
        elif indexnum == 2:
            return float(self.freq2)
        elif indexnum == 3:
            return float(self.freq3)
        elif indexnum == 4:
            return float(self.freq4)
        elif indexnum == 5:
            return float(self.freq5)
        raise DtaError("TPPlusTransitRoute.getHeadway() received invalid index num " + str(indexnum))
        
    def addTransitNode(self, nodeId, isStop, access, delay):
        """
        Add a node with the given parameters to the route.  See :py:meth:`TPPlusTransitNode.__init__` for parameter info.
        """        
        transitNode = TPPlusTransitNode(nodeId, isStop, access, delay)
        self._transitNodes.append(transitNode)

    def getTransitNode(self, nodeId):
        """
        Return the transit node with the given id; this is an instance of :py:class:`TPPlusTransitNode`
        """
        for transitNode in self.iterTransitNodes():
            if transitNode.nodeId == nodeId:
                return transitNode
        raise TPPlusError("Node %s is not in the route %s" % (nodeId, self.name))

    def getTransitDelay(self, nodeId):
        """
        Return the delay for the transit node with the given id, in minutes.
        """
        for transitNode in self.iterTransitNodes():
            if transitNode.nodeId == nodeId :
                return transitNode.delay

    def hasTransitNode(self, nodeId):
        """
        Return True if the route has a node with the given id otherwise false
        """
        return nodeId in [tn.nodeId for tn in self.iterTransitNodes()]
        
    def iterTransitNodes(self):
        """
        Return an iterator to the transit nodes, which are instances of :py:class:`TPPlusTransitNode`
        """
        return iter(self._transitNodes)

    def iterTransitStops(self):
        """
        Iterator for the :py:class:`TPPlusTransitNode` instances that are stops.
        """
        for trNode in self.iterTransitNodes():
            if trNode.isStop:
                yield trNode

    def isFirstNode(self, nodeId):
        """
        Return True if the input node id is the first node in the route

        """
        if self.getNumTransitNodes() == 0:
            raise DtaError("TPPlusTransitRoute.isFirstNode(): Route %s does not have any transit nodes" % self.name)
        if self._transitNodes[0].nodeId == nodeId:
            return True
        else:
            return False

    def isLastNode(self, nodeId):
        """
        Return True if the input node id is the last node in the route
        """

        if self.getNumTransitNodes() == 0:
            raise DtaError("TPPlusTransitRoute.isLastNode(): Route %s does not have any transit nodes" % self.name)
        if self._transitNodes[-1].nodeId == nodeId:
            return True
        else:
            return False

    def getNumTransitNodes(self):
        """
        Return the number of transit nodes in the route
        """
        return len(self._transitNodes)

    def getNumStops(self):
        """
        Return the number of stops the route makes
        """
        return sum([tr.isStop for tr in self.iterTransitNodes()])


    def toTransitLine(self, dtaNetwork, dtaRouteId, MODE_TO_LITYPE, MODE_TO_VTYPE, headwayIndex,
                        startTime, demandDurationInMin, doShortestPath=True, maxShortestPathLen=4):
        """
        Convert this instance to an equivalent DTA transit line(s).  Returns list of instances of 
        :py:class:`TransitLine`.
        
        Links on the route are checked against the given *dtaNetwork* (an instance of :py:class:`Network`).
        If *doShortestPath* is True, then a shortest path is searched for on the *dtaNetwork* and that
        is included (so this is assuming that the calling instance is missing some nodes; this can happen, for example, 
        if the DTA network has split links for centroid connectors, etc.).
        If *doShortestPath* is True then any shortest path segments longer than *maxShortestPathLen*
        are dropped (e.g. if they're Light rail segments underground) and a second 

        Other arguments:
        
        * *dtaRouteId* is the id number for the new :py:class:`TransitLine` instance.
        * *MODE_TO_LITYPE* maps the :py:attr:`TPPlusTransitRoute.mode` attribute (strings) to a line type
          (either :py:attr:`TransitLine.LINE_TYPE_BUS` or :py:attr:`TransitLine.LINE_TYPE_TRAM`)
        * *MODE_TO_VTYPE* maps the :py:attr:`TPPlusTransitRoute.mode` attribute (strings) to a 
          :py:class:`VehicleType` name
        * *headwayIndex* is the index into the frequencies to use for the headway (for use with
          :py:meth:`TPPlusTransitRoute.getHeadway`)
        * *startTime* is the start time for the bus line (and instance of :py:class:`Time`),
          and *demandDurationInMin* is used for calculating the number of transit vehicle
          departures that will be dispatched.
        
        Note that the start time for the :py:class:`TransitLine` instance will be randomized within 
        [*startTime*, *startTime* + the headway).        
        """

        transitLines = []
        
        dNodeSequence = []
        for tNode in self.iterTransitNodes():
            if not dtaNetwork.hasNodeForId(tNode.nodeId):
                dta.DtaLogger.debug('Node id %d does not exist in the Dynameq network' % tNode.nodeId)
                continue
            dNode = dtaNetwork.getNodeForId(tNode.nodeId)
            dNodeSequence.append(dNode)

        if len(dNodeSequence) == 0:
             dta.DtaLogger.error('Tpplus route %-15s cannot be converted to Dynameq because '
                                 'none of its nodes is in the Dynameq network' % self.name)
                                              
        if len(dNodeSequence) == 1:
             dta.DtaLogger.error('Tpplus route %-15s cannot be converted to Dyanmeq because only '
                                 'one of its nodes is in the Dynameq network' % self.name)

        # randomize the start time within [startTime, startTime+headway)
        headway_secs = int(60*self.getHeadway(headwayIndex))
        rand_offset_secs = random.randint(0, headway_secs-1)
        # need a datetime version of this to add the delta
        start_datetime = datetime.datetime(1,1,1,startTime.hour,startTime.minute,startTime.second)
        random_start = start_datetime + datetime.timedelta(seconds=rand_offset_secs)
        
        dRoute = dta.TransitLine(net=dtaNetwork, 
                                 id=dtaRouteId,
                                 label=self.name, 
                                 litype=MODE_TO_LITYPE[self.mode],
                                 vtype=MODE_TO_VTYPE[self.mode],
                                 stime=dta.Time(random_start.hour, random_start.minute, random_start.second),
                                 level=0,
                                 active=dta.TransitLine.LINE_ACTIVE,
                                 hway=self.getHeadway(headwayIndex),
                                 dep=int(float(demandDurationInMin)/self.getHeadway(headwayIndex)))
        transitLines.append(dRoute)
        
        for dNodeA, dNodeB in itertools.izip(dNodeSequence, dNodeSequence[1:]):
               
            if dtaNetwork.hasLinkForNodeIdPair(dNodeA.getId(), dNodeB.getId()):
                dLink = dtaNetwork.getLinkForNodeIdPair(dNodeA.getId(), dNodeB.getId())
                dSegment = dRoute.addSegment(dLink, 0, label='%d_%d' % (dNodeA.getId(), dNodeB.getId()))

                tNodeB = self.getTransitNode(dNodeB.getId())
                dSegment.dwell = 60*self.getTransitDelay(dNodeB.getId())
            else:
                # if we're not doing shortest path, nothing to do -- just move on
                if not doShortestPath: continue
                
                # dta.DtaLogger.debug('Running the SP from node %d to %d' % (dNodeA.getId(), dNodeB.getId()))
                try:
                    dta.ShortestPaths.labelSettingWithLabelsOnNodes(dtaNetwork, dNodeA, dNodeB)
                    assert(dNodeB.label < sys.maxint)
                except:
                    dta.DtaLogger.error("Error: %s" % str(sys.exc_info()))
                    dta.DtaLogger.error("Tpplus route %-15s No shortest path found from %d to %d" %
                                        (self.name, dNodeA.getId(), dNodeB.getId()))
                    continue

                pathNodes = dta.ShortestPaths.getShortestPathBetweenNodes(dNodeA, dNodeB)
                
                # Warn on this because it's a little odd
                if len(pathNodes)-1 > maxShortestPathLen:
                    pathnodes_str = ""
                    for pathNode in pathNodes: pathnodes_str += "%d " % pathNode.getId()
                    dta.DtaLogger.warn('Tpplus route %-15s shortest path from %d to %d is long: %s; dropping' %
                                        (self.name, dNodeA.getId(), dNodeB.getId(), pathnodes_str))
                    # make a new TransitLine for the next portion
                    dRoute = dta.TransitLine(net=dtaNetwork, 
                                             id=dtaRouteId+1,
                                             label="%s_%d" % (self.name, len(transitLines)),
                                             litype=MODE_TO_LITYPE[self.mode],
                                             vtype=MODE_TO_VTYPE[self.mode],
                                             stime=dta.Time(random_start.hour, random_start.minute, random_start.second),
                                             level=0,
                                             active=dta.TransitLine.LINE_ACTIVE,
                                             hway=self.getHeadway(headwayIndex),
                                             dep=int(float(demandDurationInMin)/self.getHeadway(headwayIndex)))
                    transitLines.append(dRoute)
                    continue
                        
                nodeNumList = [ dNodeA.getId() ]
                for pathNodeA, pathNodeB in itertools.izip(pathNodes, pathNodes[1:]):
                    nodeNumList.append(pathNodeB.getId())
                    dLink = dtaNetwork.getLinkForNodeIdPair(pathNodeA.getId(), pathNodeB.getId())
                    dSegment = dRoute.addSegment(dLink, 0, label='%d_%d' % (dNodeA.getId(), dNodeB.getId()))

            # add delay
            tNodeB = self.getTransitNode(dNodeB.getId())
            dSegment.dwell = 60*self.getTransitDelay(dNodeB.getId())
        
        
        dRoute.isPathValid()
        return transitLines

    

        
