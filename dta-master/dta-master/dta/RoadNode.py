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
from .Logger import DtaLogger
from .Node import Node

from .Utils import lineSegmentsCross, getMidPoint


class RoadNode(Node):
    """
    A Node subclass that represents a road node in a network.
    
    .. note:: lmz has read over this, so todos are marked.
    """
    #: the intersection is not signalized
    CONTROL_TYPE_UNSIGNALIZED       = 0
    #: the intersection is signalized
    CONTROL_TYPE_SIGNALIZED         = 1
    #: all control types
    CONTROL_TYPES                   = [CONTROL_TYPE_UNSIGNALIZED,
                                       CONTROL_TYPE_SIGNALIZED]
    

    #: No template: either a signalized or unsignalized junction, where there is no yielding of any
    #: kind, and the permitted capacity is equal to the protected capacity. 
    PRIORITY_TEMPLATE_NONE          = 0
    
    #: All Way Stop Control - an intersection with a stop sign on every approach
    PRIORITY_TEMPLATE_AWSC          = 1
    
    #: Two Way Stop Control - an intersection at which a minor street crosses a major street and
    #: only the minor street is stop-controlled
    PRIORITY_TEMPLATE_TWSC          = 2
    
    #: A junction on a roundabout at which vehicles enter the roundabout. Vehicles entering the
    #: roundabout must yield to those already on the roundabout (by convention in most countries).
    PRIORITY_TEMPLATE_ROUNDABOUT    = 3
    
    #: An uncontrolled (unsignalized) junction at which a minor street must yield to the major street,
    #: which may or may not be explicitly marked with a Yield sign. 
    PRIORITY_TEMPLATE_MERGE         = 4
    
    #: Any signalized intersection (three-leg, four-leg, etc.). For right-side driving, left-turn
    #: movements yield to opposing through traffic and right turns, and right turns yield to the
    #: conflicting through traffic (if applicable). For left-side driving, the rules are the same but reversed.
    PRIORITY_TEMPLATE_SIGNALIZED    = 11
    
    #: For each control type, a list of available Capacity/Priority templates is provided.
    #: Choosing a template from the list will automatically provide follow-up time values with
    #: corresponding permitted capacity values in the movements table below, and define all movement
    #: priority relationships at the node with corresponding gap acceptance values.     
    PRIORITY_TEMPLATES              = [PRIORITY_TEMPLATE_NONE,
                                       PRIORITY_TEMPLATE_AWSC,
                                       PRIORITY_TEMPLATE_TWSC,
                                       PRIORITY_TEMPLATE_ROUNDABOUT,
                                       PRIORITY_TEMPLATE_MERGE,
                                       PRIORITY_TEMPLATE_SIGNALIZED]
        
    def __init__(self, id, x, y, geometryType, control, priority, label=None, level=None):
        """
        Constructor.
        
         * *id* is a unique identifier (unique within the containing network), an integer
         * *x* and *y* are coordinates in the units specified by :py:attr:`Node.COORDINATE_UNITS`
         * *geometryType* is one of :py:attr:`Node.GEOMETRY_TYPE_INTERSECTION` or 
           :py:attr:`Node.GEOMETRY_TYPE_JUNCTION`
         * *control* is one of :py:attr:`RoadNode.CONTROL_TYPE_UNSIGNALIZED` or 
           :py:attr:`RoadNode.CONTROL_TYPE_SIGNALIZED`
         * *priority* is one of
         
           * :py:attr:`RoadNode.PRIORITY_TEMPLATE_NONE`
           * :py:attr:`RoadNode.PRIORITY_TEMPLATE_AWSC`
           * :py:attr:`RoadNode.PRIORITY_TEMPLATE_TWSC`
           * :py:attr:`RoadNode.PRIORITY_TEMPLATE_ROUNDABOUT`
           * :py:attr:`RoadNode.PRIORITY_TEMPLATE_MERGE`
           * :py:attr:`RoadNode.PRIORITY_TEMPLATE_SIGNALIZED`
                                       
         * *label* is a string, for readability.  If None passed, will default to "label [id]"
         * *level* is for vertical alignment.  More details TBD.  If None passed, will use default.  
        """
        if geometryType not in [Node.GEOMETRY_TYPE_INTERSECTION, Node.GEOMETRY_TYPE_JUNCTION]:
            raise DtaError("RoadNode initialized with invalid type: %d" % type)
        
        if control not in RoadNode.CONTROL_TYPES:
            raise DtaError("RoadNode initailized with invalid control: %d" % control)
        
        Node.__init__(self, id, x, y, geometryType, label, level)

        self._control    = control
        self._priority   = priority
        
        # indexed by the :py:class:`PlanCollectionInfo`
        self._timePlans = {}

    def isRoadNode(self):
        """
        Return True if this Node is a RoadNode.
        """
        return True

    def isCentroid(self):
        """
        Return True if this Node is a Centroid
        """
        return False

    def isVirtualNode(self):
        """
        Return True if this Node is a VirtualNode
        """
        return False
    
    def getCandidateLinksForSplitting(self, connector, disallowConnectorEvalStr):
        """
        Given a :py:class:`Connector` instance whose start node or end node is the calling instance,
        returns a list of :py:class:`RoadLink` instances where:
        
        * The link is at least 0.009 miles long (why?)
        * If *disallowConnectorEvalStr*, then it evaluates as False for a :py:class:`RoadLink` 
          (using :py:meth:`RoadLink.disallowSplitForConnector`
        * If one were to create a new link between the *connector*'s :py:class:`VirtualNode` and
          the midpoint of the link, none of the other :py:class:`RoadLink` instances adjacent to the calling node
          would cross it.
          
        The returned list is sorted by euclidean length, longest to shortest.
        
        .. todo:: I think a picture would be useful here
        .. todo:: explain the 0.009 minimum length -- is it just to make sure resulting links aren't too small?
                  If we keep it, make it an arg, it really is in :py:attr:`RoadLink.LENGTH_UNITS`
              
        """
        MIN_LENGTH_IN_MILES = 0.009

        if self not in [connector.getStartNode(), connector.getEndNode()]:
            raise DtaError("Node %d is not adjacent to connector %d" %
                           (self.getId(), connector.getId())) 
    
        if connector.startIsRoadNode():
            vNode = (connector.getEndNode().getX(), connector.getEndNode().getY())
        else:
            vNode = (connector.getStartNode().getX(), connector.getStartNode().getY())
            
        result = []
        
        for candidateLink in self.iterAdjacentRoadLinks():
            
            if candidateLink.getLength() < MIN_LENGTH_IN_MILES:
                continue
            
            # if this one isn't allowed, don't consider it
            if disallowConnectorEvalStr and candidateLink.disallowSplitForConnector(disallowConnectorEvalStr): continue

            candidateLinkStart, candidateLinkEnd = candidateLink.getCenterLine()
            middlePointAtCandidateLink = getMidPoint(candidateLinkStart, candidateLinkEnd)
            otherCross = False
            for everyOtherRoadLink in self.iterAdjacentRoadLinks():
                
                if candidateLink == everyOtherRoadLink: continue 
                
                # don't worry about this one if it's not a candidate for splitting itself.
                if disallowConnectorEvalStr and everyOtherRoadLink.disallowSplitForConnector(disallowConnectorEvalStr): continue
                
                otherLinkStart, otherLinkEnd = everyOtherRoadLink.getCenterLine() 
                if lineSegmentsCross(vNode, middlePointAtCandidateLink, otherLinkStart, otherLinkEnd):
                    otherCross = True
                    break
            
            if not otherCross:
                result.append(candidateLink)         
        #finally sort the candidate links based on their length 
        return  sorted(result, key = lambda l:l.getLength(), reverse=True) 
                                
    def getOrientation(self, point):
        """
        Return the clockwise angle from the North measured in degrees of the line 
        segment that has the current node as its start and the given *point* as its end. 
        """
        x1 = self.getX()
        y1 = self.getY()
        x2 = point[0]
        y2 = point[1]

        if x2 > x1 and y2 <= y1:   # 2nd quarter
            orientation = math.atan(abs(y2-y1)/abs(x2-x1)) + math.pi/2
        elif x2 <= x1 and y2 < y1:   # 3th quarter
            orientation = math.atan(abs(x2-x1)/abs(y2-y1)) + math.pi
        elif x2 < x1 and y2 >= y1:  # 4nd quarter 
            orientation = math.atan(abs(y2-y1)/abs(x2-x1)) + 3 * math.pi/2
        elif x2 >= x1 and y2 > y1:  # 1st quarter
            orientation = math.atan(abs(x2-x1)/abs(y2-y1))
        else:
            orientation = 0.0

        return orientation * 180.0 / math.pi

    def _getMinAngle(self, node1, edge1, node2, edge2):
        """
        Returns a positive number in degrees within [0, 180]
        that corresponds to the angle between the two edges.
        """
        orientation1 = node1.getOrientation(edge1.getMidPoint())
        orientation2 = node2.getOrientation(edge2.getMidPoint())
        if orientation2 > orientation1:
            angle1 = orientation2 - orientation1
            angle2 = 360 - orientation2 + orientation1
            assert min(angle1, angle2) > 0
            return min(angle1, angle2)
        elif orientation1 > orientation2:
            angle1 = orientation1 - orientation2 
            angle2 = 360 - orientation1 + orientation2
            assert min(angle1, angle2) > 0
            return min(angle1, angle2)
        else:
            return 0

    def isOverlapping(self, link, minAngle):
        """
        Returns True if the minimum angle between the input link and any similarly 
        oriented link of the intersection is less than the input *minAngle*, which is specified in degrees.
        
        By "similarly oriented", the method looks at all other incoming links if *link* is incoming, 
        and all other outgoing links if *link* is outgoing to this node.  If *link* is neither incoming nor
        outgoing to this node, raises a :py:class:`DtaError`.
        """
        #outgoing link
        if link.getEndNode() == self: 
            for ilink in self.iterIncomingLinks():  
                if ilink == link:
                    continue
                if link.getAngle(ilink) < minAngle:
                    # print self.getId(),link.getId(), ilink.getId()                     
                    return True
            else:
                return False
        #incoming link
        elif link.getStartNode() == self:
            for olink in self.iterOutgoingLinks():
                if olink == link:
                    continue
                if link.getAngle(olink) < minAngle:
                    # print self.getId(),link.getId(), olink.getId() 
                    return True
            else:
                return False
        else:
            raise DtaError("Link %d is not adjacent to node %d" % (link.getId(), node.getId()))

    def addTimePlan(self, timePlan, raiseValidateError=False):
        """
        Add the given *timePlan*, an instance of :py:class:`TimePlan`, to the current collection.
        
        This method will call :py:meth:`TimePlan.validate`
        If *raiseValidateError*, any errors will be raised; otherwise they will just be warned.
        """
        try:
            timePlan.validate()
        except DtaError, e:
            DtaLogger.warn("RoadNode %d addTimePlan() validation failure: %s" % (self.getId(), str(e)))
            if raiseValidateError:
                raise e
                        
        self._timePlans[timePlan.getPlanInfo()] = timePlan
        self._control = RoadNode.CONTROL_TYPE_SIGNALIZED
        self._priority = RoadNode.PRIORITY_TEMPLATE_SIGNALIZED
        
    def hasTimePlan(self, planInfo=None):
        """
        Return True if the node has at least one :py:class:`TimePlan`.
        """
        if not planInfo:
            return True if self._timePlans else False
        return True if planInfo in self._timePlans else False

    def getTimePlan(self, planInfo):
        """
        Return the :py:class:`TimePlan` for the specific time period defined by *planInfo*, an instance of
        :py:class:`PlanCollectionInfo`.
        """
        try:
            return self._timePlans[planInfo]
        except KeyError:
            raise DtaError("Node %d does not have a timeplan between %d and %d" %
                           (self.getId(), planInfo.getTimePeriod()[0],
                            planInfo.getTimePeriod()[1]))

    def iterTimePlans(self):
        """
        Return an iterator over the :py:class:`TimePlan` instances corresponding to this node.
        """
        return iter(self._timePlans.itervalues())

    def setAllWayStopControl(self):
        """
        Sets the road node's stop control to all way stop.
        
        Raises an error if it was already marked as signalized.
        """
        if self._control == RoadNode.CONTROL_TYPE_SIGNALIZED:
            raise DtaError("setAllWayStopControl: Node %d set to signalized" % self.getId())
        
        self._priority = RoadNode.PRIORITY_TEMPLATE_AWSC
        
        
    def setTwoWayStopControl(self):
        """
        Sets the road node's stop control to two way stop.
        
        Raises an error if it was already marked as signalized.
        """
        if self._control == RoadNode.CONTROL_TYPE_SIGNALIZED:
            raise DtaError("setAllWayStopControl: Node %d set to signalized" % self.getId())
        
        self._priority = RoadNode.PRIORITY_TEMPLATE_TWSC
    
    def setPriorityTemplateNone(self):
        """
        Sets the road node's priority template to :py:attr:`RoadNode.PRIORITY_TEMPLATE_NONE`.
        """
        self._priority = RoadNode.PRIORITY_TEMPLATE_NONE
    
    @property
    def control(self):
        """
        Returns the control at this road node, one of :py:attr:`RoadNode.CONTROL_TYPE_UNSIGNALIZED` or :py:attr:`CONTROL_TYPE_SIGNALIZED`
        """
        return self._control
    
    @property
    def priority(self):
        """
        Returns the priority at this road node, one of :py:attr:`RoadNode.PRIORITY_TEMPLATE_NONE`, :py:attr:`RoadNode.PRIORITY_TEMPLATE_AWSC`,
        :py:attr:`RoadNode.PRIORITY_TEMPLATE_TWSC`, :py:attr:`RoadNode.PRIORITY_TEMPLATE_ROUNDABOUT`, :py:attr:`RoadNode.PRIORITY_TEMPLATE_MERGE`,
        or :py:attr:`RoadNode.PRIORITY_TEMPLATE_SIGNALIZED`.
        """
        return self._priority
    
