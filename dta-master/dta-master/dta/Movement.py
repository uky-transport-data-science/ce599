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
import copy
import math
from itertools import izip
from collections import defaultdict

from .DtaError import DtaError
from .Logger import DtaLogger
from .Node import Node
from .RoadNode import RoadNode
from .VehicleClassGroup import VehicleClassGroup
from .Utils import getMidPoint, lineSegmentsCross, polylinesCross
from .Algorithms import pairwise

class Movement(object):
    """
    A movement consists of an incoming link, and outgoing link, and attributes
    that define the movement from one to the other (is it a turn?  what's the capacity? etc.)
    """
    #: U-turn movement (returned by :py:meth:`Movement.getTurnType`)
    DIR_UTURN   = "UTURN"
    #: Right turn movement (returned by :py:meth:`Movement.getTurnType`)
    DIR_RT      = 'RT'
    #: Right turn 2 (diff from RT?) movement (returned by :py:meth:`Movement.getTurnType`)
    DIR_RT2     = 'RT2'
    #: Left turn 2 (diff from LT?) movement (returned by :py:meth:`Movement.getTurnType`)
    DIR_LT2     = 'LT2'
    #: left turn movement (returned by :py:meth:`Movement.getTurnType`)
    DIR_LT      = 'LT'
    #: Throughmovement (returned by :py:meth:`Movement.getTurnType`)
    DIR_TH      = 'TH'
    
    #: Where did this come from?
    PROTECTED_CAPACITY_PER_HOUR_PER_LANE = 1900
    
    #: Use this to signify that a default follow-up time is to be used for movement
    #:
    #: .. note::
    #:    In Dynameq, if a value of follow-up time other than this is specified for any movement at a node, 
    #:    the Customize option will be automatically set for the specified priority template at this node and
    #:    the user-defined values of follow-up time will be used in place of those specified by the template.
    #:    All movements at the node for which this value is specified for the follow-up time will receive the follow-up 
    #:    time specified by the priority template (if applicable).
    #:
    FOLLOWUP_TIME_DEFAULT = -1
    
    @classmethod
    def simpleMovementFactory(cls, incomingLink, outgoingLink, vehicleClassGroup):
        """
        Return a movement connecting the input links with the given permissions 
        defined by the vehicle class group.
        """
        return Movement(incomingLink.getEndNode(), 
                        incomingLink, 
                        outgoingLink, 
                        incomingLink._freeflowSpeed, 
                        vehicleClassGroup
                        )
                                
    def __init__(self, node, incomingLink, outgoingLink, freeflowSpeed, vehicleClassGroup,
                 numLanes=None, incomingLane=None, outgoingLane=None, followupTime=FOLLOWUP_TIME_DEFAULT):
        """
        Constructor.
        
         :param node: a :py:class:`RoadNode` instance where the movement is located
         :param incomingLink: a :py:class:`Link` instance representing the incoming link of the movement
         :param outgoingLink: a :py:class:`Link` instance representing the outgoing link of the movement
         :param freeflowSpeed: is the maximum speed of the movement; pass None to use that of the *incomingLink*
         :param vehicleClassGroup: the allowed group of vehicles that can use this Movement; it should be an
           instance of :py:class:`VehicleClassGroup`
         :param numLanes: the width of the movement.  For a movement that has a different number of lanes
           upstream and downstream, the minimum of these two values should be used.  The number of lanes
           can vary over time.  Pass `None` to let the software choose.
         :param incomingLane: Of the lanes associated with this movement on the *incomingLink*, the id number
           of the lane closest to the inside of the roadway (that is, the one with the highest id number).
           This attribute can vary over time.  Pass `None` to let the software choose.
         :param outgoingLane: Of the lanes associated with this movement on the *outgoingLink*, the id number
           of the lane closest to the inside of the roadway (that is, the one with the highest id number).
           This attribute can vary over time.  Pass `None` to let the software choose.
         :param followupTime: is the follow-up time for the movement.  This attribute can vary over time.
           Default value is :py:attr:`Movement.FOLLOWUP_TIME_DEFAULT`
         
        """
        # type checking
        if not isinstance(node, RoadNode):
            DtaLogger.debug("Movement instantiated with non-RoadNode: %s" % str(node))

        if not isinstance(vehicleClassGroup, VehicleClassGroup):
            raise DtaError("Movement instantiated with invalid vehicleClassGroup: %s" % str(vehicleClassGroup))
        
        # todo: sanity checking on numLanes, incomingLane, outgoingLane
            
        self._node          = node
        self._incomingLink  = incomingLink
        self._outgoingLink  = outgoingLink
        self._freeflowSpeed = freeflowSpeed
        self._permission    = vehicleClassGroup
        self._numLanes      = numLanes
        self._incomingLane  = incomingLane
        self._outgoingLane  = outgoingLane
        self._followupTime  = followupTime
        self._overrideTurnType = None
        
        self._centerline    = self.getCenterLine()
        
        self._higherPriorityMovements = [] # list of (Movement, CriticalGapTime(sec), CriticalWaitTime(sec)
        
        self._simOutVolume  = defaultdict(int)      # indexed by timeperiod
        self._simInVolume   = defaultdict(int)      # indexed by timeperiod
        self._simMeanTT     = defaultdict(float)    # indexed by timeperiod
        
        # TODO: what is this used for?!      
        self._penalty   = 0
        self._timeVaryingCosts = []
        self._timeStep  = None
        
        self.simTimeStepInMin = None
        self.simStartTimeInMin = None
        self.simEndTimeInMin = None

        self._obsCount = {}
        
    def __repr__(self):
        return "Movement node:%d inlink:%d outlink:%d" % (self._node.getId(), self._incomingLink.getId(), self._outgoingLink.getId())
        
    def getIncomingLink(self):
        """
        Returns the incomingLink, a :py:class:`Link` instance
        """
        return self._incomingLink
    
    def getOutgoingLink(self):
        """
        Returns the outgoung, a :py:class:`Link` instance
        """
        return self._outgoingLink
        
    def getAtNode(self):
        """
        Returns the node at which the movement is happening
        """        
        return self._node
    
    def getStartNode(self):
        """
        Returns the start node of incomingLink, a :py:class:`Link` instance
        """
        return self._incomingLink.getStartNode()
    
    def getEndNode(self):
        """
        Returns the end node of outgoingLink, a :py:class:`Link` instance
        """
        return self._outgoingLink.getEndNode()

    def getStartNodeId(self):
        """
        Returns the start node of incomingLink, a :py:class:`Link` instance
        """
        return self._incomingLink.getStartNodeId()
    
    def getEndNodeId(self):
        """
        Returns the end node of outgoingLink, a :py:class:`Link` instance
        """
        return self._outgoingLink.getEndNodeId()

    def getId(self):
        """
        Return a string containing the three node ids that define the movement
        """
        return "%d %d %d" % (self.getStartNodeId(), self.getAtNode().getId(), self.getEndNodeId())

    def isUTurn(self):
        """
        Return True if the movement is a U-Turn.
        
        This is True if either the incoming start node is the same as the outgoing end node, or if
        the incoming link and outgoing link have the same name and have an orientation difference
        of between 160 and 180 degrees according to :py:meth:`RoadLink.getOrientation`
        
        """
        if self._incomingLink.getStartNode() == self._outgoingLink.getEndNode():
            return True
        
        # if the link is a split link, it still might be a UTurn
        if self._incomingLink.getLabel() == self._outgoingLink.getLabel():
            
            angle_between = self._incomingLink.getOrientation(atEnd=True) - self._outgoingLink.getOrientation(atEnd=False)
            if angle_between > 360:
                angle_between -= 360
            if angle_between < 0:
                angle_between += 360
            
            if angle_between > 160 and angle_between <= 180:
                DtaLogger.debug("Assuming movement @ %d (link %d link %d) is a U-Turn based on angle %f and labels %s" %
                                (self.getAtNode().getId(),
                                 self._incomingLink.getId(), self._outgoingLink.getId(),
                                 angle_between, self._incomingLink.getLabel()))
                return True
        return False

    def isThruTurn(self):
        """
        Return True if the movement is a Through movement
        """
        return True if self.getTurnType() == Movement.DIR_TH else False 

    def isLeftTurn(self):
        """
        Return True if the movement is a left turn
        """
        if self.getTurnType() == Movement.DIR_LT or \
           self.getTurnType() == Movement.DIR_LT2:
            return True
        return False

    def isRightTurn(self):
        """
        Return True if the movement is a right turn
        """
        if self.getTurnType() == Movement.DIR_RT or \
           self.getTurnType() == Movement.DIR_RT2:
            return True
        return False

    def setOverrideTurnType(self, turntype):
        """
        Sets this movement to use the given turntype rather than figuring it out from the angle between the
        incoming and outgoing link.
        
        Throws an exception if the turntype is invalid.
        """
        if turntype not in [Movement.DIR_UTURN, Movement.DIR_RT, Movement.DIR_RT2, 
                            Movement.DIR_LT2, Movement.DIR_LT, Movement.DIR_TH]:
            raise DtaError("Invalid override turn_type: %s -- skipping" % str(turntype))
            
        self._overrideTurnType = turntype
        
    def getTurnType(self):
        """
        Returns the type of the movement, one of :py:attr:`Movement.DIR_UTURN`, :py:attr:`Movement.DIR_RT`, :py:attr:`Movement.DIR_RT2`,
        :py:attr:`Movement.DIR_LT2`, :py:attr:`Movement.DIR_LT`, :py:attr:`Movement.DIR_TH`.

        The movement type is determined by the angle of the outgoing link with respect to that of the incoming link 
        (based on the start nodes and end nodes only for now, but maybe it makes more sense to include shape points?).
        
        .. image:: /images/TurnTypes.png
           :height: 400px
           
        However, if a Movement type override is set using :py:meth:`Movement.setOverrideTurnType` then that will
        supercede the angle-based analysis.
        """
        if self._overrideTurnType != None:
            return self._overrideTurnType
                    
        angle = self._incomingLink.getAngle(self._outgoingLink)
        if self.isUTurn():
            turnType =  Movement.DIR_UTURN
        elif -45 <= angle < 45:
            turnType = Movement.DIR_TH
        elif 45 <= angle < 135:
            turnType = Movement.DIR_RT
        elif 135 <= angle:
            turnType = Movement.DIR_RT2
        elif -135 <= angle < -45:
            turnType = Movement.DIR_LT
        elif angle < -135:
            turnType = Movement.DIR_LT2

        return turnType

    def getDirection(self):
        """
        Return the direction of the movement as a string
        """
        return self._incomingLink.getDirection() + self.getTurnType()
                
    def getCenterLine(self):
        """
        Get a list of points representing the movement
        """
        inlink_cline  = self._incomingLink.getCenterLine(atStart=False, atEnd=True)
        outlink_cline = self._outgoingLink.getCenterLine(atStart=True, atEnd=False)

        if lineSegmentsCross(inlink_cline[0], inlink_cline[-1], outlink_cline[0], outlink_cline[-1]):
            p1 = getMidPoint(*inlink_cline)
            p2 = getMidPoint(*outlink_cline) 
            self._centerLine = [inlink_cline[0], p1, p2, outlink_cline[-1]]
        else:
            self._centerLine = [inlink_cline[0], inlink_cline[-1], outlink_cline[0], outlink_cline[-1]]
            
        return self._centerLine

    def isInConflict(self, other):
        """
        Return true if the current movement is conflicting with the other one
        """
        line1 = self.getCenterLine()
        line2 = other.getCenterLine()

        if self.getIncomingLink() == other.getIncomingLink():
            return False
        if self.getOutgoingLink() == other.getOutgoingLink():
            return False
        
        for p1, p2 in izip(line1, line1[1:]):
            for p3, p4 in izip(line2, line2[1:]):
                if lineSegmentsCross(p1, p2, p3, p4):
                    return True
                
        if lineSegmentsCross(line1[-2], line1[-1],
                            line2[-2], line2[-1],
                             checkBoundaryConditions=True):
            return True
        return False

    def getNumLanes(self):
        """
        Return the number of lanes the movement has
        """
        return self._numLanes

    def setNumLanes(self, numlanes):
        """
        Mutator for the number of lanes of the movement
        """
        self._numLanes = numlanes

    def getProtectedCapacity(self, planInfo):
        """
        Return the capacity of the movement in vehicles per hour
        This method calulates the capacity of of the movement by
        adding the green times of all the phases this movement
        participates in. 
        """
        if self._node.hasTimePlan(planInfo=planInfo):
            tp = self._node.getTimePlan(planInfo=planInfo)
            greenTime = 0
            for phase in tp.iterPhases():                                
                if phase.hasPhaseMovement(self.getStartNodeId(), self.getEndNodeId()):
                    mov = phase.getPhaseMovement(self.getStartNodeId(), self.getEndNodeId())
                    if mov.isProtected():
                        greenTime += phase.getGreen()
            if greenTime > 0:                
                return float(greenTime) / tp.getCycleLength() * self.getNumLanes() * Movement.PROTECTED_CAPACITY_PER_HOUR_PER_LANE
        raise DtaError("The movement %s does does not operate under a protected phase"
                       % self.getId())
         #return self.getNumLanes() * Movement.PROTECTED_CAPACITY_PER_HOUR_PER_LANE
                
    def addHigherPriorityMovement(self, higherprio_movement, critical_gap=4, critical_wait=30):
        """
        Sets the given *higherprio_movement* (another :py:class:`Movement` instance) as having higher
        priority than this one, with the given *critical_gap* and *critical_wait* times in seconds.
        
        The *critical_gap* determines the gap that waiting drivers performing the lower-priority movement
        will accept before making their movement.  From the Dynameq documentation::
        
          Decreasing this value results in more vehicles on the lower
          priority movement merging with or crossing the higher-priority traffic stream, when this stream is in
          under-saturated conditions.  In saturated traffic conditions, there are essentially no available gaps, 
          and the *critical_wait* parameter determines the amount of flow on the lower-priority movement.
          
          The *critical_wait* reflects the influence of driver impatience on gap-acceptance behavior.
          As waiting time increases, the driver may eventually accept a gap that is not normally considered
          acceptable, and may even oblige the higher priority vehicle to slow down in order to maintain a
          safe distance (or to avoid a collision).
          
          Decreasing the value of critical wait results in more vehicles on the lower-priority movement
          merging with or crossing the higher-priority traffic stream, when this stream is in saturated conditions.
        
        """
        # could do more checking
        if not isinstance(higherprio_movement, Movement):
            DtaLogger.debug("addHigherPriorityMovement called with non-movement: %s" % str(higherprio_movement))

        self._higherPriorityMovements.append( (higherprio_movement, critical_gap, critical_wait) )
        
    def iterHigherPriorityMovements(self):
        """
        Returns an iterator to the higher priority movements, which is really a 3-tuple of
        (higherprio_movement (a :py:class:`Movement` instance), critical gap (a float), critical wait (a float))
        For example::
        
          for (higherprio_movement, critical_gap, crical_wait) in movement.iterHigherPriorityMovements():
              print "Movement = %s, critical_gap = %f, critical_wait = %f" % (str(higherprio_movement, critical_gap, critical_wait)
            
        """
        return iter(self._higherPriorityMovements)
    
    def _checkInputTimeStep(self, startTimeInMin, endTimeInMin):
        """The input time step should always be equal to the sim time step"""
        if endTimeInMin - startTimeInMin != self.simTimeStepInMin:
            raise DtaError('Time period from %d to %d is not '
                                   'equal to the simulation time step %d'
                                   % (startTimeInMin, endTimeInMin, 
                                      self.simTimeStepInMin))
            

    def _checkOutputTimeStep(self, startTimeInMin, endTimeInMin):
        """Checks that the difference in the input times is in multiples 
        of the simulation time step"""
        if (endTimeInMin - startTimeInMin) % self.simTimeStepInMin != 0:
            raise DtaError('Time period from %d to %d is not '
                                   'is a multiple of the simulation time step ' 
                                    '%d' % (startTimeInMin, endTimeInMin,
                                                    self.simTimeStepInMin))


    def _validateInputTimes(self, startTimeInMin, endTimeInMin):
        """Checks that the start time is less than the end time and that both 
        times are in the simulation time window"""
        
        if startTimeInMin >= endTimeInMin:
            raise DtaError("Invalid time bin (%d %s). The end time cannot be equal or less "
                                "than the end time" % (startTimeInMin, endTimeInMin))

        if startTimeInMin < self.simStartTimeInMin or endTimeInMin > \
                self .simEndTimeInMin:
            raise DtaError('Time period from %d to %d is out of '
                                   'simulation time' % (startTimeInMin, endTimeInMin))
        
    def getSimOutVolume(self, startTimeInMin, endTimeInMin):
        """
        Return the outgoing flow from the start to end
        """

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        result = 0
        for stTime, enTime in pairwise(range(startTimeInMin, endTimeInMin + 1, 
                                             self.simTimeStepInMin)):
            result += self._simOutVolume[stTime, enTime]
        return result

    def getSimOutFlow(self, startTimeInMin, endTimeInMin):
        """
        Get the outgoing flow for the specified time period 
        in vph
        """
        volume = self.getSimOutVolume(startTimeInMin, endTimeInMin)
        return  60.0 / (endTimeInMin - startTimeInMin) * volume

    def getSimInVolume(self, startTimeInMin, endTimeInMin):
        """
        Return the incoming flow from the start to end
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        result = 0
        for stTime, enTime in pairwise(range(startTimeInMin, endTimeInMin + 1, 
                                             self.simTimeStepInMin)):
            result += self._simInVolume[stTime, enTime]
        return result

    def getSimInFlow(self, startTimeInMin, endTimeInMin):
        """Get the simulated flow for the specified time period 
        in vph"""
        volume = self.getSimInVolume(startTimeInMin, endTimeInMin)
        return  60.0 / (endTimeInMin - startTimeInMin) * volume

    def getSimTTInMin(self, startTimeInMin, endTimeInMin):
        """Return the mean movement travel time in minutes of 
        for all the vehicles that entered the link between the 
        input times
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        totalFlow = 0
        totalTime = 0
        
        if (startTimeInMin, endTimeInMin) in self._simMeanTT:
            return self._simMeanTT[startTimeInMin, endTimeInMin]

        for (stTime, enTime), flow in self._simOutVolume.iteritems():
            if stTime >= startTimeInMin and enTime <= endTimeInMin:
                binTT = self._simMeanTT[(stTime, enTime)]

                if binTT > 0 and flow > 0:
                    totalFlow += flow
                    totalTime += self._simMeanTT[(stTime, enTime)] * flow
                elif binTT == 0 and flow == 0:
                    continue
                else:
                    raise DtaError("Movement %s has flow:%f and TT:%f "
                                           "for time period from %d to %d"  % 
                                           (self.getId(), flow, binTT, 
                                            startTimeInMin, endTimeInMin))

        if totalFlow > 0:
            return totalTime / float(totalFlow) + self._penalty
        else:
            return (self._incomingLink.getLength() / 
                float(self._incomingLink.getFreeFlowSpeedInMPH()) * 60 + self._penalty)

    def getSimSpeedInMPH(self, startTimeInMin, endTimeInMin):
        """
        Return the travel time of the first edge of the movement in 
        miles per hour
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        ttInMin = self.getSimTTInMin(startTimeInMin, endTimeInMin)
        lengthInMiles = self.upLink.getLengthInMiles()
        return lengthInMiles / (ttInMin / 60.)

    def getFreeFlowSpeedInMPH(self):
        """
        Return the free flow travel speed in mph
        """
        return self.incomingLink.getFreeFlowSpeedInMPH()

    def getFreeFlowTTInMin(self):
        """
        Return the free flow travel time in minutes
        """
        return self._incomingLink.getFreeFlowTTInMin()

    def getTimeVaryingCostAt(self, timeInMin):
        """
        Return the cost (in min) for the time period begining at the 
        input time
        """
        period = int((timeInMin - self.simStartTimeInMin) // self._timeStep)
        return self._timeVaryingCosts[period]

    def getTimeVaryingCostTimeStep(self):
        """
        Return the time step that is used for the time varying costs
        """
        return self._timeStep
    
    def setSimOutVolume(self, startTimeInMin, endTimeInMin, flow):
        """
        Specify the simulated outgoing flow (vehicles per HOUR) for the supplied time period
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        self._simOutVolume[startTimeInMin, endTimeInMin] = flow

    def setSimInVolume(self, startTimeInMin, endTimeInMin, flow):
        """
        Specify the simulated incoming flow (vehicles per HOUR) for the supplied time period
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        self._simInVolume[startTimeInMin, endTimeInMin] = flow

    def setSimTTInMin(self, startTimeInMin, endTimeInMin, averageTTInMin):
        """
        Specify the simulated average travel time for the 
        input time period
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        if averageTTInMin < 0:
            raise DtaError("The travel time on movement %s cannot be negative" %
                                   str(self.getId()))
        if averageTTInMin == 0:
            if self.getSimOutFlow(startTimeInMin, endTimeInMin) > 0:
                raise DtaError("The travel time on movement %s with flow %d from %d to %d "
                                       "cannot be 0" % (self.iid, 
                                                        self.getSimOutFlow(startTimeInMin, endTimeInMin),
                                                        startTimeInMin, endTimeInMin))
            else:
                return

        if self.getSimOutFlow(startTimeInMin, endTimeInMin) == 0:
            raise DtaError('Cannot set the travel time on a movement with zero flow')

        self._simMeanTT[startTimeInMin, endTimeInMin] = averageTTInMin

    def setTimeVaryingCosts(self, timeVaryingCosts, timeStep):
        """
        Inputs:timeVaryingCosts is an array containing the cost 
        of the edge in each time period. timeStep is the interval 
        length in minutes
        """
        #make sure the costs are positive. 
        self._timeStep = timeStep
        for cost in timeVaryingCosts:
            assert cost > 0
        self._timeVaryingCosts = timeVaryingCosts

    def setPenaltyInMin(self, penalty):
        """
        Add the input penalty to the simulated movement travel time
        """
        self._penalty = penalty

    def getVehicleClassGroup(self):
        """
        Return the vehicle class group
        """
        return self._permission

    def setVehicleClassGroup(self, vehicleClassGroup):
        """
        Set the vehicle class group for this movement
        """
        self._permission = vehicleClassGroup

    def isProhibitedToAllVehicleClassGroups(self):
        """
        Return True if the movement is prohibited for all vehicles
        """
        return self._permission.allowsNone()

    def prohibitAllVehicleClassGroups(self):
        """
        Set the movement to prohibited to all vehicles
        """
        self._permission = VehicleClassGroup.getProhibited()

    def prohibitAllVehiclesButTransit(self):
        """
        Set the movement to prohibited to all vehicles but transit 
        """
        self._permission = VehicleClassGroup.prohibitAllMovementsButTransit()

    def setObsCount(self, startTimeInMin, endTimeInMin, count):
        """
        Set the number of vehicles executing the movement 
        in the input time period 
        """

        self._validateInputTimes(startTimeInMin,endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        if startTimeInMin >= endTimeInMin:
            raise DtaError("Invalid time bin (%d %s). The end time cannot be equal or less "
                                "than the end time" % (startTimeInMin, endTimeInMin))
        if count < 0:
            raise DtaError('Count for time period from %d to %d cannot be '
                                   'negative' % (startTimeInMin, endTimeInMin))
        self._obsCount[startTimeInMin, endTimeInMin] = count

    def getObsCount(self, startTimeInMin, endTimeInMin):
        """Return the number of vehicles executing the
        movement in the input time window. 
        """

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        try:
            return self._obsCount[startTimeInMin, endTimeInMin]            
        except KeyError:
            return None

    def hasCountInfo(self):
        """Return True if the movement contains count information else false"""
        return True if len(self._obsCount) else False

    def hasObsCount(self, startTimeInMin, endTimeInMin):
        """Return True if there is a count for the input time period  
        """
        return True if self.getObsCount(startTimeInMin, endTimeInMin) else False 
    
    def getFollowup(self):
        """
        Returns the follow-up time
        """        
        return self._followupTime
    
    def setFollowup(self, newFollowupTime):
        """
        Sets the follow-up time to the given value
        """ 
        self._followupTime = newFollowupTime
                
        
