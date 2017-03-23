_copyright__   = "Copyright 2011 SFCTA"
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
import pdb 
import math
import sys
from collections import defaultdict 

from .DtaError import DtaError
from .Link import Link
from .Logger import DtaLogger
from .Movement import Movement
from .Node import Node
from .VehicleClassGroup import VehicleClassGroup
from .Utils import polylinesCross, lineSegmentsCross
from .Algorithms import pairwise

class RoadLink(Link):
    """
    A RoadLink in a network.  Both nodes must be RoadNodes.
    
    """
    #: Static variable representing the units of the length variable
    #: Should be ``kilometers`` or ``miles``
    LENGTH_UNITS = None
    
    #: default level value
    DEFAULT_LEVEL = 0
    #: default lane width in :py:attr:`Node.COORDINATE_UNITS`
    DEFAULT_LANE_WIDTH = 12

    #: Eastbound return value for :py:meth:`RoadLink.getDirection`
    DIR_EB = "EB"
    #: Westbound return value for :py:meth:`RoadLink.getDirection`
    DIR_WB = "WB"
    #: Northbound return value for :py:meth:`RoadLink.getDirection`    
    DIR_NB = "NB"
    #: Southbound return value for :py:meth:`RoadLink.getDirection`
    DIR_SB = "SB"

    
    def __init__(self, id, startNode, endNode, reverseAttachedLinkId, facilityType, length,
                 freeflowSpeed, effectiveLengthFactor, responseTimeFactor, numLanes, 
                 roundAbout, level, label, group):
        """
        Constructor.
        
         * *id* is a unique identifier (unique within the containing network), an integer
         * *startNode*, *endNode* are Nodes
         * *reverseAttachedId* is the id of the reverse link, if attached; pass None if not
           attached
         * *facilityType* is a non-negative integer indicating the category of facility such
           as a freeway, arterial, collector, etc.  A lower number indicates a facility of
           higher priority, that is, higher capacity and speed.
         * *length* is the link length, in :py:attr:`RoadLink.LENGTH_UNITS`. Pass None to automatically calculate it.
         * *freeflowSpeed* is in km/h or mi/h
         * *effectiveLengthFactor* is applied to the effective length of a vehicle while it is
           on the link.  May vary over time with LinkEvents
         * *responseTimeFactor* is the applied to the response time of the vehicle while it is
           on the link.  May vary over time with LinkEvents
         * *numLanes* is an integer
         * *roundAbout* is true/false or 1/0
         * *level* is an indicator to attribute vertical alignment/elevation. If None passed, will use default.
         * *label* is a link label. If None passed, will use default. 
         * *group* is an integer that identifies one or more links; groups are used for calculation of approach
           delay to an intersection.  So all vehicles approaching on the links in one group experience the
           same approach delay.  (todo: example of how this should be used?)  If -1 is passed, no group will be
           used.
         
        """
        Link.__init__(self, id, startNode, endNode, label)
        self._reverseAttachedLinkId     = reverseAttachedLinkId
        self._facilityType              = facilityType
        self._freeflowSpeed             = freeflowSpeed
        self._effectiveLengthFactor     = effectiveLengthFactor
        self._responseTimeFactor        = responseTimeFactor
        self._group                     = group

        if numLanes <= 0: 
            raise DtaError("RoadLink %d cannot have number of lanes = %d" % (self.getId(), numLanes))

        self._numLanes                  = numLanes
        self._roundAbout                = roundAbout
        if level:
            self._level                 = level
        else:
            self._level                 = RoadLink.DEFAULT_LEVEL

        #TODO: warn when the input link length is weird
        if length is None or length is -1:
            self._length = self.euclideanLengthInLengthUnits()
        else:
            self._length = length
            

        self._lanePermissions           = {}  # lane id -> VehicleClassGroup reference
        self._outgoingMovements         = []  # list of outgoing Movements
        self._incomingMovements         = []  # list of incoming Movements
        self._startShift                = None
        self._endShift                  = None
        self._shapePoints               = []  # sequenceNum -> (x,y)

        self._simOutVolume = defaultdict(int)
        self._simMeanTT = defaultdict(float)
        self._obsCount = {}
        self._tollLink = 0
    
    def __repr__(self):
        return "<Link id:%d  label:%s  dir:%s>" % (self.getId(), self.getLabel(), self.getDirection())
        
    def createReverseLink(self, newid):
        """
        Instantiate and return a new link that is the reverse of this one.
        """
        return RoadLink(id=newid, startNode=self._endNode, endNode=self._startNode, reverseAttachedLinkId=self._id, 
                        facilityType=self._facilityType, length=self._length,
                        freeflowSpeed=self._freeflowSpeed, effectiveLengthFactor=self._effectiveLengthFactor,
                        responseTimeFactor=self._responseTimeFactor, numLanes=self._numLanes,
                        roundAbout=self._roundAbout, level=self._level, label=self._label, group=self._group)

    def _validateInputTimes(self, startTimeInMin, endTimeInMin):
        """Checks that the input times belong to the simulation window"""
        if startTimeInMin >= endTimeInMin:
            raise DtaError("Invalid time bin (%d %s). The end time cannot be equal or less "
                                "than the end time" % (startTimeInMin, endTimeInMin))

        if startTimeInMin < self.simStartTimeInMin or endTimeInMin > \
                self.simEndTimeInMin:
            raise DtaError('Time period from %d to %d is out of '
                                   'simulation time' % (startTimeInMin, endTimeInMin))

    def _checkInputTimeStep(self, startTimeInMin, endTimeInMin):
        """Checks if the difference of the input times is equal to the simulation time step"""
        #TODO which check should I keep
        if endTimeInMin - startTimeInMin != self.simTimeStepInMin:
            raise DtaError('Time period from %d to %d is not '
                                   'is not in multiple simulation '
                                   'time steps %d' % (startTimeInMin, endTimeInMin,
                                                    self.simTimeStepInMin))
            

    def _checkOutputTimeStep(self, startTimeInMin, endTimeInMin):
        """Check that the difference of the input times is in multiples of the simulation time step"""
        if (endTimeInMin - startTimeInMin) % self.simTimeStepInMin != 0:
            raise DtaError('Time period from %d to %d is not '
                                   'is not in multiple simulation '
                                   'time steps %d' % (startTimeInMin, endTimeInMin,
                                                    self.simTimeStepInMin))

    def _hasMovementVolumes(self, startTimeInMin, endTimeInMin):
        """Return True if at least one movement has a volume 
        greater than 0"""
        for mov in self.iterOutgoingMovements():
            if mov.getSimVolume(startTimeInMin, endTimeInMin) > 0:
                return True
        return False

    def getSimOutFlow(self, startTimeInMin, endTimeInMin):
        """Get the simulated flow in vph"""
        volume = self.getSimVolume(startTimeInMin, endTimeInMin)        
        return int(float(volume) / (endTimeInMin - startTimeInMin) * 60)

    def getSimOutVolume(self, startTimeInMin, endTimeInMin):
        """Return the volume on the link from startTimeInMin to endTimeInMin"""

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        if self.getNumOutgoingMovements() > 0:
            return sum([mov.getSimOutVolume(startTimeInMin, endTimeInMin) 
                        for mov in self.iterOutgoingMovements()])
        else:
            result = 0
            for stTime, enTime in pairwise(range(startTimeInMin, endTimeInMin + 1, 
                                                 self.simTimeStepInMin)):
                result += self._simOutVolume[stTime, enTime]
            return result

    def getSimInFlow(self, startTimeInMin, endTimeInMin):
        """
        Get the simulated incoming flow in vph
        """
        volume = self.getSimInVolume(startTimeInMin, endTimeInMin)        
        return int(float(volume) / (endTimeInMin - startTimeInMin) * 60)

    def getSimInVolume(self, startTimeInMin, endTimeInMin):
        """
        Return the incoming volume on the link from startTimeInMin to endTimeInMin
        """

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        if self.getNumOutgoingMovements() > 0:
            return sum([mov.getSimInVolume(startTimeInMin, endTimeInMin) 
                        for mov in self.iterOutgoingMovements()])
        else:
            result = 0
            for stTime, enTime in pairwise(range(startTimeInMin, endTimeInMin + 1, 
                                                 self.simTimeStepInMin)):
                result += self._simInVolume[stTime, enTime]
            return result

    def getSimTTInMin(self, startTimeInMin, endTimeInMin):
        """Get the average travel time of the vehicles traversing the link"""

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        start = startTimeInMin
        end = endTimeInMin

        totalFlow = self.getSimOutVolume(startTimeInMin, endTimeInMin)
        if totalFlow == 0:
            return self.getFreeFlowTTInMin()

        if not self._simMeanTT and not self._simOutVolume:
            totalTime = sum([ mov.getSimTTInMin(start, end) * mov.getSimOutVolume(start, end)
                          for mov in self.iterOutgoingMovements()])
            return totalTime / float(totalFlow)
        elif self._simMeanTT and self._simOutVolume:
            totalTime = 0
            totalFlow = 0
            for (stTime, enTime), flow in self._simOutVolume.iteritems():
                if stTime >= startTimeInMin and enTime <= endTimeInMin:

                    binTT = self._simMeanTT[(stTime, enTime)]

                    if flow == 0 and binTT == 0:
                        continue
                    elif flow > 0 and binTT > 0:
                        totalFlow += flow
                        totalTime += binTT * flow
                    else:                        
                        raise SimMovementError("Movement %s has flow: %f and TT: %f "
                                               "for time period from %d to %d"  % 
                                               (self.iid, flow, binTT, 
                                                startTimeInMin, endTimeInMin))

            return totalTime / float(totalFlow)
            
            if endTimeInMin - startTimeInMin != self.simTimeStepInMin:
                raise DtaError("Not implemeted yet")

            return self._simMeanTT[start, end]
        else:
            return self.lengthInMiles / float(self._freeflowSpeed) * 60

    def getSimSpeedInMPH(self, startTimeInMin, endTimeInMin):

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)
        
        #TODO if the coordinate system is not in feet 
        # you are going to have a problem
        tt = self.getSimTTInMin(startTimeInMin, endTimeInMin)
        speedInMPH = self.getLength() / (tt / 60.)
        return speedInMPH

    def getObsMeanTT(self, startTimeInMin, endTimeInMin):
        """Get the observed mean travel time of the link in minutes"""
        raise Exception("Not implemented yet")
        return self._obsMeanTT[startTimeInMin, endTimeInMin]
            
    def getObsSpeedInMPH(self, startTimeInMin, endTimeInMin):
        """Get the observed speed of specified time period"""
        raise Exception("Not implemented yet")
        return self._obsSpeed[startTimeInMin, endTimeInMin]
    
    def setSimOutVolume(self, startTimeInMin, endTimeInMin, volume):
        """
        Set the simulated volume on the edge provided that the edge 
        does not have any emanating movements
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        if self._hasMovementVolumes(startTimeInMin, endTimeInMin):
            raise DtaError('Cannoot set the simulated volume on the edge %s'
                               'because there is at least one emanating '
                               'movement with volume greater than zero ' %
                               str(self.iid))

        if self.getNumOutgoingMovements() > 1:
            raise DtaError('Cannot set the simulated volume of the edge %s'
                               'with one or more emanating movements. Please'
                               ' set the volume of the movements' % str(self.iid))
        elif self.getNumOutgoingMovements() == 1:
            for emanatingMovement in self.iterOutgoingMovements():
                emanatingMovement.setSimVolume(startTimeInMin, endTimeInMin, volume)
        else:
            self._simOutVolume[startTimeInMin, endTimeInMin] = volume
        
    def setSimTTInMin(self, startTimeInMin, endTimeInMin, averageTTInMin):
        """
        Set the simulated travel time on the link for the particular input period
        """
        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkInputTimeStep(startTimeInMin, endTimeInMin)

        #TODO the input period should be in multiples of the simTimeStep        
        if startTimeInMin < self.simStartTimeInMin or endTimeInMin > \
                self.simEndTimeInMin:
            raise DtaError('Time period from %d to %d is out of '
                                   'simulation time' % (startTimeInMin, endTimeInMin))

        if endTimeInMin - startTimeInMin != self.simTimeStepInMin:
            raise DtaError('Not implemetd yet. Time period is different than the time step.')


        if self.getNumOutgoingMovements() > 1:
            raise DtaError('Cannot set the simulated travel time of the edge %s'
                               'with one or more emanating movements. Please'
                               ' set the time of the movements instead' % str(self.iid))
        elif self.getNumOutgoingMovements() == 1:
            if averageTTInMin == 0:
                return
            for emanatingMovement in self.iterOutgoingMovements():
                emanatingMovement.setSimTTInMin(startTimeInMin, endTimeInMin, averageTTInMin)
        else:
            if averageTTInMin == 0:
                return
            if self.getSimVolume(startTimeInMin, endTimeInMin) == 0:
                raise DtaError('Cannot set the travel time on edge %s because it has zero flow' % self.iid_)

            self._simMeanTT[startTimeInMin, endTimeInMin] = averageTTInMin
                        
    def addLanePermission(self, laneId, vehicleClassGroup):
        """
        Adds the lane permissions for the lane numbered by *laneId* (outside lane is lane 0, increases towards inside edge.)
        """
        if not isinstance(vehicleClassGroup, VehicleClassGroup):
            raise DtaError("RoadLink addLanePermission() called with invalid vehicleClassGroup %s" % str(vehicleClassGroup))
        
        if laneId < 0 or laneId >= self._numLanes:
            raise DtaError("RoadLink addLanePermission() called with invalid laneId %d; numLanes = %d" % 
                           (laneId, self._numLanes))
        
        self._lanePermissions[laneId] = vehicleClassGroup
    
    def getLanePermission(self, laneId):
        """
        Accessor for the :py:class:`VehicleClassGroup` that uses the given lane.
        
        Returns None if nothing is set.
        """
        if len(self._lanePermissions) <= laneId:
            return None
        
        return self._lanePermissions[laneId]
    
    def allowsAll(self):
        """
        Is there a lane on this link that allows all?
        """
        # no lane permissions -- all allowed implicitly
        if len(self._lanePermissions) == 0:
            return True
        
        for lane_id,perm in self._lanePermissions.iteritems():
            if perm.allowsAll(): return True
            
        return False
        
    def addShifts(self, startShift, endShift, addShapepoints=False):
        """
        Adds a shift to the start and/or end of the roadlink, to change the alignment of either end by one (or more) lane(s).
        
        :param startShift: the shift value of the first segment of the link, that is, the number of lanes from
           the center line of the roadway that the first segment is shifted.
        :param endShift: End-shift: the shift value of the last segment of the link, that is, the number of 
           lanes from the center line of the roadway that the last segment is shifted.
           
        Dynameq software requires the link to have at least 2 shape points in order to use these shifts.
        Thus, this method will also add the required shape points, if they're lacking (just a linear interpolation
        1/3 and 2/3 along the line via :py:meth:`RoadLink.coordinatesAlongLink` if *addShapepoints* is True.
        """
        self._startShift    = startShift
        self._endShift      = endShift
        
        # Dynameq requires the RoadLink to have at least 2 shapepoints in order to use the shifts
        # Add them, if necessary
        if addShapepoints and len(self._shapePoints) < 2:
            self._shapePoints.append(self.coordinatesAlongLink(fromStart=True, distance=self.euclideanLength()*0.33, goPastEnd=False))
            self._shapePoints.append(self.coordinatesAlongLink(fromStart=True, distance=self.euclideanLength()*0.66, goPastEnd=False))

    def getNumOutgoingMovements(self):
        """
        Returns the number of outgoing movements
        """
        return len(self._outgoingMovements)
    
    def getShifts(self):
        """
        Returns the *startShift* and *endShift* ordered pair, or (None,None) if it wasn't set.
        See addShifts() for details.
        """
        return (self._startShift, self._endShift)
    
    def addShapePoint(self, x, y):
        """
        Append a shape point to the link.
        Shape points are not actual nodes, but additional coordinates that inform the geometry of a link,
        such as showing curvature.
        """
        self._shapePoints.append((x,y))

    def getNumShapePoints(self):
        """
        Return the number of shape points this link has
        """
        return len(self._shapePoints)
    
    def getShapePoints(self):
        """
        Accessor for the shape points.
        """
        return self._shapePoints

    def coordinatesAlongLink(self, fromStart, distance, goPastEnd=False):
        """
        Like :py:meth:`RoadLink.coordinatesAndShapePointIdxAlongLink` but only returns the
        coordinates 2-tuple (*x*,*y*).  For backwards compatibility.
        """
        (x,y,idx) = self.coordinatesAndShapePointIdxAlongLink(fromStart, distance, goPastEnd)
        return (x,y)

    def coordinatesAndShapePointIdxAlongLink(self, fromStart, distance, goPastEnd=False):
        """
        Returns the 3-tuple (*x*,*y*,*idx*) where (*x*,*y*) is the point along this link given by
        *distance*, which is in :py:attr:`Node.COORDINATE_UNITS`.  *idx* is the index into the
        point array (including the start point, intermediate shape points, and end point) where
        the (*x*,*y*) was ultimately found (useful for splitting links and allocating the shape points).  
        
        If *fromStart*, starts at start, otherwise at end.
        
        Takes shape points into account.
        
        If *distance* is longer than the euclidean distance of the link, and not *goPastEnd* raises
        a :py:class:`DtaError`.
        """
        points = [[self._startNode.getX(),self._startNode.getY()]]
        points.extend(self._shapePoints)
        points.append([self._endNode.getX(), self._endNode.getY()])
        
        if not fromStart:
            points.reverse()
        
        if distance == 0:
            return (points[0][0], points[0][1], 0)
        
        distance_left = distance
        idx           = 0
        total_distance= 0
        while distance_left > 0 and (idx+1) < len(points):
            
            shape_dist = math.sqrt( (points[idx][0]-points[idx+1][0]) ** 2 +
                                    (points[idx][1]-points[idx+1][1]) ** 2)
            total_distance += shape_dist
            # this is the right sublink, or goPastEnd and it's the last one
            if (distance_left <= shape_dist) or (goPastEnd and (idx+1)==(len(points)-1)):
                return (points[idx][0] + (distance_left/shape_dist)*(points[idx+1][0]-points[idx][0]),
                        points[idx][1] + (distance_left/shape_dist)*(points[idx+1][1]-points[idx][1]),
                        idx)
            
            # next sublink
            distance_left -= shape_dist
            idx += 1
            
        # didn't find anything
        raise DtaError("coordinatesAlongLink: distance %.2f too long for link %d (%d-%d) with total distance %.2f" % 
                       (distance, self._id, self._startNode.getId(), self._endNode.getId(), total_distance))

    def findOutgoingMovement(self, nodeId):
        """
        Returns the outgoing movement ending in the given *nodeId*.
        
        If None found, returns None.
        """
        for mov in self.iterOutgoingMovements():
            if mov.getEndNode().getId() == nodeId:
                return mov
        return None        

    def hasOutgoingMovement(self, nodeId, vehicleClassGroup=None):
        """
        Return True if the link has an outgoing movement towards nodeId.
        Please note that the movement may be prohibited.
        """
        movement = self.findOutgoingMovement(nodeId)
        
        if not movement:
            return False
                
        if (not vehicleClassGroup) or (vehicleClassGroup and mov.getVehicleClassGroup() == vehicleClassGroup):
            return True
        
        return False

    
    def addOutgoingMovement(self, movement):
        """
        Adds the given movement.
        """
        if not isinstance(movement, Movement):
            raise DtaError("RoadLink addOutgoingMovement() called with invalid movement %s" % str(movement))
        
        if movement.getIncomingLink() != self:
            raise DtaError("RoadLink addOutgoingMovement() called with inconsistent movement" % str(movement))

        if self.hasOutgoingMovement(movement.getEndNode().getId()):
            raise DtaError("RoadLink %s addOutgoingMovement() called to add already "
                           "existing movement" % str(movement))

        self._outgoingMovements.append(movement)
        movement.getOutgoingLink()._incomingMovements.append(movement)
    
    def iterOutgoingMovements(self):
        """
        Iterator for the outgoing movements of this link
        """
        return iter(self._outgoingMovements)

    def iterIncidentMovements(self):
        """
        Return an iterator to all the incident movemements
        of this link
        """
        for mov in self.getStartNode().iterMovements():
            if mov.getOutgoingLink() == self:
                yield mov
            
    def getNumIncomingMovements(self):
        """
        Returns the number of incoming movements
        """
        return len(self._incomingMovements)
    
    def prohibitOutgoingMovement(self, movementToProhibit):
        """
        Prohibit the input movement
        """
        if not isinstance(movementToProhibit, Movement):
            raise DtaError("RoadLink %s deleteOutgoingMovement() "
                           "called with invalid movement %s" % str(movementToProhibit))
        
        if movementToProhibit.getIncomingLink() != self:
            raise DtaError("RoadLink %s deleteOutgoingMovement() called with inconsistent movement" % str(movementToProhibit))

        if not movementToProhibit in self._outgoingMovements:
            raise DtaError("RoadLink %s deleteOutgoingMovement() called to delete "
                           "inexisting movement" % str(movementToProhibit))

        movementToProhibit.prohibitAllVehicleClassGroups()        
        
    def _removeOutgoingMovement(self, movementToRemove):
        """
        Delete the input movement
        """
        if not isinstance(movementToRemove, Movement):
            raise DtaError("RoadLink %s _removeOutgoingMovement() "
                           "called with invalid movement %s" % str(movementToRemove))
        
        if movementToRemove.getIncomingLink() != self:
            raise DtaError("RoadLink %s _removeOutgoingMovement() called with inconsistent movement" % str(movementToRemove))

        if not movementToRemove in self._outgoingMovements:
            raise DtaError("RoadLink %s _removeOutgoingMovement() called to delete "
                           "invalid movement" % str(movementToRemove))

        #movementToRemove.setProhibited()
        self._outgoingMovements.remove(movementToRemove)
        movementToRemove.getOutgoingLink()._incomingMovements.remove(movementToRemove)

    def iterIncomingMovements(self):
        """
        Iterator for the incoming movements of this link
        """
        return iter(self._incomingMovements)

    def getFacilityType(self):
        """
        Returns the facility type; see :py:meth:`RoadLink.__init__` for more on that variable.
        """
        return self._facilityType

    def getNumLanes(self):
        """
        Return the number of lanes.
        """
        return self._numLanes

    def euclideanLength(self, includeShape=False):
        """
        Calculates the length based on simple Euclidean distance.
        
        If this link has shape points and *includeShape* is True, then the shape is taken into account.
        
        This will be in the units specified by :py:attr:`Node.COORDINATE_UNITS`.
        """
        if not includeShape or self.getNumShapePoints() == 0:
            return Link.euclideanLength(self)
        
        points = [[self._startNode.getX(),self._startNode.getY()]]
        points.extend(self._shapePoints)
        points.append([self._endNode.getX(), self._endNode.getY()])

        distance = 0.0
        for point_idx in range(len(points)-1):
            pointA = points[point_idx]
            pointB = points[point_idx+1]
            distance += math.sqrt( (pointA[0]-pointB[0])*(pointA[0]-pointB[0]) + 
                                   (pointA[1]-pointB[1])*(pointA[1]-pointB[1]))
        return distance
    
    def euclideanLengthInLengthUnits(self, includeShape=False):
        """
        Return the length of the link in :py:attr:`RoadLink.LENGTH_UNITS` units.
        
        """
        if RoadLink.LENGTH_UNITS == "miles" and Node.COORDINATE_UNITS == "feet":
            return (self.euclideanLength(includeShape) / 5280.0)
        
        if RoadLink.LENGTH_UNITS == "kilometers" and Node.COORDINATE_UNITS == "meters": 
            return (self.euclideanLength(includeShape) / 1000.0)
        
        raise DtaError("RoadLink.getLength() doesn't support RoadLink.LENGTH_UNITS %s and Node.COORDINATE_UNITS %s" % 
                       (str(RoadLink.LENGTH_UNITS), str(Node.COORDINATE_UNITS)))

        
    def getLength(self):
        """
        Return the length of the link in :py:attr:`RoadLink.LENGTH_UNITS` units.
        
        Uses the user input length, if there is one; otherwise calculates the euclidean length including the shape.        
        """
        if self._length != -1:
            return self._length
        else:
            return self.euclideanLengthInLengthUnits(includeShape=True)
        
        
    def getLengthInCoordinateUnits(self):
        """
        Returns the length of the link in :py:attr:`Node.COORDINATE_UNITS` units.
        
        Uses the asserted length, if there is one; otherwise calculates the euclidean length.
        """
        if self._length != -1:
            
            if RoadLink.LENGTH_UNITS == "miles" and Node.COORDINATE_UNITS == "feet":
                return (self._length * 5280.0)
            
            if RoadLink.LENGTH_UNITS == "kilometers" and Node.COORDINATE_UNITS == "meters": 
                return (self._length * 1000.0)
            
            raise DtaError("RoadLink.getLengthInCoordinateUnits() doesn't support RoadLink.LENGTH_UNITS %s and Node.COORDINATE_UNITS %s" % 
                           (str(RoadLink.LENGTH_UNITS), str(Node.COORDINATE_UNITS)))
            
        return self.euclideanLength()
       
    def setLength(self, newLength):
        """
        Sets the asserted length of this link; the *newLength* should be in units specified by `RoadLink.LENGTH_UNITS`
        """
        self._length = newLength 
        

    def getCenterLine(self, atStart=False, atEnd=False, wholeLineShapePoints=False):
        """
        Offset the link to the right 0.5*numLanes*:py:attr:`RoadLink.DEFAULT_LANE_WIDTH` and 
        return a tuple of two points (each one being a tuple of two floats) representing the centerline
        
        If *atStart* is True, then shapepoints are included and the first section of the line is used.
        If *atEnd* is True, then shapepoints are included and the last section of the line is used.
        
        If neither is True, then shapepoints are included iff *wholeLineShapePoints* (and a list is
        returned rather than a tuple of two points). 
        """

        start_point = [ self._startNode.getX(), self._startNode.getY() ]
        end_point   = [ self._endNode.getX()  , self._endNode.getY()   ]
        
        if atEnd and len(self._shapePoints) > 0:
            start_point = self._shapePoints[-1]
        elif atStart and len(self._shapePoints) > 0:
            end_point = self._shapePoints[0]
            
        # base shift of the num lanes
        start_shift = self.getNumLanes() * RoadLink.DEFAULT_LANE_WIDTH / 2.0
        end_shift   = self.getNumLanes() * RoadLink.DEFAULT_LANE_WIDTH / 2.0
        
        # additional shift
        if (len(self._shapePoints) == 0 or atStart) and self._startShift:
            start_shift += RoadLink.DEFAULT_LANE_WIDTH*self._startShift
        if (len(self._shapePoints) == 0 or atEnd) and self._endShift:
            end_shift   += RoadLink.DEFAULT_LANE_WIDTH*self._endShift
        
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]

        length = self.getLengthInCoordinateUnits()

        #TODO: throw an error if the length is Zero. In fact, you should have thrown an error long time ago
        if length == 0:
            length = 1

        centerline = ((start_point[0] + dy*(start_shift/length), start_point[1] - dx*(start_shift/length)),
                      (end_point[0]   + dy*(end_shift  /length), end_point[1]   - dx*(end_shift  /length)))
        
        if not atStart and not atEnd:
            if wholeLineShapePoints:
                centerline_with_shape = copy.deepcopy(self._shapePoints)
                centerline_with_shape.insert(0, centerline[0])
                centerline_with_shape.append(centerline[1])
                return centerline_with_shape
            
        return centerline

    def getDistanceFromPoint(self, x, y):
        """
        Projects (*x*, *y*) onto the road link center line (including the shape points).
        Returns (distance, t) where t is in [0,1] and indicates how far between the
        road links start point and end point lies the closest point to (*x*, *y*).
                
        *x*,*y* are in :py:attr:`Node.COORDINATE_UNITS`
        """
        centerline = self.getCenterLine(wholeLineShapePoints = True)
       
        # do it for real
        min_dist_sq = sys.float_info.max
        dist_along_segments = 0.0
        
        total_dist = 0.0
        for segment_num in range(len(centerline)-1):
            pointA              = centerline[segment_num]
            pointB              = centerline[segment_num+1]
            segment_length_sq   = (pointA[0]-pointB[0])**2 + (pointA[1]-pointB[1])**2
            segment_length      = math.sqrt(segment_length_sq)
            
            # looking at the line segment as parameterized: pointA + t(pointB-pointA)
            # t = dot( point - pointA, pointB - pointA)
            t = ((x - pointA[0])*(pointB[0]-pointA[0]) + (y - pointA[1])*(pointB[1]-pointA[1]))/segment_length_sq
                
            if t < 0.0: 
                projection = pointA
            elif t > 1.0:
                projection = pointB
            else:
                projection = (pointA[0] + t*(pointB[0]-pointA[0]),
                              pointA[1] + t*(pointB[1]-pointA[1]))
            dist_from_seg_sq =(projection[0]-x)**2 + (projection[1]-y)**2

            # if it's a minimum, keep
            if dist_from_seg_sq < min_dist_sq:
                min_dist_sq = dist_from_seg_sq
                dist_along_segments = total_dist + (t*segment_length)
                
            total_dist         += segment_length
        
        return_t = dist_along_segments/total_dist
        if return_t > 1.0: return_t = 1.0
        if return_t < 0.0: return_t = 0.0
        return (math.sqrt(min_dist_sq), return_t)

    def getOutline(self, scale=1):
        """
        Return the outline of the link as a linearRing of points
        in clockwise order. If scale the physical outline of the link
        will be return using the number of lanes attribute to determine
        the boundaries of the outline.
        """

        dx = self._endNode.getX() - self._startNode.getX()
        dy = self._endNode.getY() - self._startNode.getY() 

        length = self.getLengthInCoordinateUnits()

        if length == 0:
            length = 1

        scale = self.getNumLanes() * RoadLink.DEFAULT_LANE_WIDTH / length * scale

        xOffset = dy * scale
        yOffset = - dx * scale 

        outline = ((self._startNode.getX(), self._startNode.getY()),
                   (self._endNode.getX(), self._endNode.getY()),
                   (self._endNode.getX() + xOffset, self._endNode.getY() + yOffset),
                   (self._startNode.getX() + xOffset, self._startNode.getY() + yOffset))
        return outline

    def getMidPoint(self):
        """
        Return the midpoint of the link's centerline as a tuple of two floats
        
        This uses :py:meth:`RoadLink.coordinatesAlongLink` and includes shapepoints.
        """
        return self.coordinatesAlongLink(fromStart = True, 
                                         distance = 0.5*self.euclideanLength(includeShape=True), goPastEnd=False)
                
    def isRoadLink(self):
        """
        Return True this Link is RoadLink
        """
        return True

    def isConnector(self):
        """
        Return True if this Link is a Connector
        """
        return False 

    def isVirtualLink(self):
        """
        Return True if this LInk is a VirtualLink
        """
        return False

    def getOutgoingMovement(self, nodeId):
        """
        Returns the outgoing movement with an end node specified by the given *nodeId*
        (and this link as the incoming link).
        """
        for mov in self.iterOutgoingMovements():
            if mov.getEndNode().getId() == nodeId:
                return mov
        raise DtaError("RoadLink from %d to %d does not have a movement to node %d" % (self._startNode.getId(),
                                                                                       self._endNode.getId(),
                                                                                       nodeId))
    def getOutgoingMovementForLinkId(self, linkId):
        """
        Returns the outgoing movement with the outgoing link specified by the given *linkId*
        (and this link as the incoming link).
        """
        for mov in self.iterOutgoingMovements():
            if mov.getOutgoingLink().getId() == linkId:
                return mov
        raise DtaError("RoadLink from %d to %d does not have a movement to link %d" % (self._startNode.getId(),
                                                                                       self._endNode.getId(),
                                                                                       linkId))  
        
    def setNumLanes(self, numLanes):
        """
        Sets the number of lanes to the given value
        """ 
        self._numLanes = numLanes 
    
    def getAngle(self, other, usingShapepoints=False):
        """
        Return the angle in degrees (in the range (-180, 180]) between this link and *other*, 
        an instance of :py:class:`Link` (where positive angles means the other is clockwise from this,
        and negative angles means the other is counter-clockwise from self.)
        
        If *usingShapepoints*, links must have a node in common, and the section of the link involving
        that common node is examined.
        
        If *usingShapepoints* is False, both links are considered as vectors from the
        start node to end node.
        """
        
        if not usingShapepoints or self.getStartNode() == other.getStartNode():
            self_at_start   = True
            other_at_start  = True
        elif self.getStartNode() == other.getEndNode():
            self_at_start   = True
            other_at_start  = False
        elif self.getEndNode() == other.getStartNode():
            self_at_start   = False
            other_at_start  = True
        elif self.getEndNode() == other.getEndNode():
            self_at_start   = False
            other_at_start  = False
        else:
            raise DtaError("RoadLink.getAngle() called on links %d and %d, which have no nodes in common" %
                           (self.getId(), other.getId()))        
        
        self_angle = self.getOrientation(atEnd=(not self_at_start), usingShapepoints=usingShapepoints)
        other_angle = other.getOrientation(atEnd=(not other_at_start), usingShapepoints=usingShapepoints)
        
        angle_between = other_angle - self_angle
        if angle_between > 180: 
            angle_between -= 360.0
        elif angle_between <= -180:
            angle_between += 360.0

        return angle_between

    
    def isOverlapping(self, other, usingShapepoints=False):
        """
        Return True if the given link and *other* overlap.  Assumes they share an endpoint.
        See :py:meth:`RoadLink.getAngle()` for explanation of *usingShapePoints*.
        """
        # oriented the same way -- small angle
        if abs(self.getAngle(other, usingShapepoints)) <= 0.86:
            return True

        return False

    def getOrientation(self, atEnd=True, usingShapepoints=True):
        """
        Returns the angle of the link in degrees from the North
        measured clockwise.  The result is in [0, 360) 
        
        The link shape is taken into account if *usingShapepoints* is True.
        
        If there are shape points, and *atEnd* is True, then the orientation
        is evaluated at the end point of the link, otherwise it's evaluated at
        the start of the link.
        """
        if self._shapePoints and usingShapepoints:
            if atEnd:
                x1, y1 = self._shapePoints[-1]
                x2, y2 = self.getEndNode().getX(), self.getEndNode().getY()
            else:
                x1, y1 = self.getStartNode().getX(), self.getStartNode().getY()
                x2, y2 = self._shapePoints[0]  
        else:
            x1 = self.getStartNode().getX()
            y1 = self.getStartNode().getY()
            x2 = self.getEndNode().getX()
            y2 = self.getEndNode().getY()

        if x2 > x1 and y2 <= y1:   # 2nd quarter
            orientation = math.atan(math.fabs(y2-y1)/math.fabs(x2-x1)) + math.pi/2
        elif x2 <= x1 and y2 < y1:   # 3th quarter
            orientation = math.atan(math.fabs(x2-x1)/math.fabs(y2-y1)) + math.pi
        elif x2 < x1 and y2 >= y1:  # 4nd quarter 
            orientation = math.atan(math.fabs(y2-y1)/math.fabs(x2-x1)) + 3 * math.pi/2
        elif x2 >= x1 and y2 > y1:  # 1st quarter
            orientation = math.atan(math.fabs(x2-x1)/math.fabs(y2-y1))
        else:
            orientation = 0.0

        return orientation * 180 / math.pi
        
    def getDirection(self, atEnd=True):
        """
        Returns the direction of the link as one of :py:attr:`RoadLink.DIR_EB`,  :py:attr:`RoadLink.DIR_NB`,
        :py:attr:`RoadLink.DIR_WB` or :py:attr:`RoadLink.DIR_SB`.  Uses :py:meth:`getOrientation` so the
        shape points are used with the *atEnd* argument.
        """

        orientation = self.getOrientation(atEnd)
        if 315 <= orientation or orientation < 45:
            return RoadLink.DIR_NB
        elif 45 <= orientation < 135:
            return RoadLink.DIR_EB
        elif 135 <= orientation < 225:
            return RoadLink.DIR_SB
        else:
            return RoadLink.DIR_WB
    
    def hasDirection(self, dir, atEnd=True):
        """
        Returns True if the link is going in that direction at all.  That is, if a link is oriented to the
        southwest, this will return True for *dir* :py:attr:`RoadLink.DIR_SB` and *dir* :py:attr:`RoadLink.DIR_WB` but
        False otherwise.  *atEnd* is interpreted by the :py:meth:`getOrientation` method.
        """
        orientation = self.getOrientation(atEnd)
        if dir==RoadLink.DIR_NB:
            if orientation > 270 or orientation < 90: return True
            return False
        
        if dir==RoadLink.DIR_SB:
            if orientation > 90 and orientation < 270: return True
            return False
        
        if dir==RoadLink.DIR_EB:
            if orientation < 180: return True
            return False
        
        if dir==RoadLink.DIR_WB:
            if orientation > 180: return True
            return False
        
        raise DtaError("RoadLink.hasDirection called with invalid dir: %s" % str(dir))


    def hasRightTurn(self):
        """
        Return True if the link has a through turn
        """
        try:
            mov = self.getRightTurn()
            return True
        except:
            return False

    def getRightTurn(self):
        """
        Return the thru movement of the link or raise an error if it does not exist
        """
        for mov in self.iterOutgoingMovements():
            if mov.isRightTurn():
                return mov
        raise DtaError("Link %d does not have a right turn movement" % self.getId())

    def hasThruTurn(self):
        """
        Return True if the link has a through turn
        """
        try:
            mov = self.getThruTurn()
            return True
        except:
            return False

    def getThruTurn(self):
        """
        Return the thru movement of the link or raise an error if it does not exist
        """
        for mov in self.iterOutgoingMovements():
            if mov.isThruTurn():
                return mov
        raise DtaError("Link %d does not have a thru movement" % self.getId())

    def hasLeftTurn(self):
        """
        Return True if the link has a through turn
        """
        try:
            mov = self.getLeftTurn()
            return True
        except:
            return False

    def getLeftTurn(self):
        """
        Return the left turn movement of the link or raise an error if it does not exist
        """
        for mov in self.iterOutgoingMovements():
            if mov.isLeftTurn():
                return mov
        raise DtaError("Link %d does not have a left turn movement" % self.getId())
        
    def getFreeFlowSpeedInMPH(self):
        """
        Return the free flow speed in MPH
        """
        return self._freeflowSpeed

    def getFreeFlowTTInMin(self):
        """
        Return the free flow travel time in minutes
        """
        return (self.getLength() / self._freeflowSpeed) * 60.0
            
    def getGroup(self):
        """
        Return the group number for the link
        """
        return self._group
    
    def setGroup(self, group):
        """
        Set the group number for the link
        """
        self._group = group
                
    def setObsCount(self, startTimeInMin, endTimeInMin, count):
        """
        Set the number of vehicles Traversing the link 
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
        """Return the number of vehicles traversing the
        link in the input time window. 
        """

        self._validateInputTimes(startTimeInMin, endTimeInMin)
        self._checkOutputTimeStep(startTimeInMin, endTimeInMin)

        try:
            return self._obsCount[startTimeInMin, endTimeInMin]            
        except KeyError:
            return None

    def getSumOfAllMovementCounts(self, startTimeInMin, endTimeInMin):
        """Return the sum of all outgoing movement counts"""
        if not self.hasAllMovementCounts(startTimeInMin, endTimeInMin): 
            return -1
        else: 
            totalCount = 0
            for mov in self.iterOutgoingMovements():
                    totalCount = totalCount + mov.getObsCount(startTimeInMin, endTimeInMin)
        return totalCount       
    
    def hasCountInfo(self):
        """Return True if the link contains count information else false"""
        return True if len(self._obsCount) else False
        
    def hasMovementCountInfo(self):
        """Return True if any outgoing movement on the link
        contains count information else false
        """
        if self.hasCountInfo(): 
            return True
        for mov in self.iterOutgoingMovements():
            if mov.hasCountInfo():
                return True
        return False

    def hasObsCount(self, startTimeInMin, endTimeInMin):
        """Return True if there is a count for the input time period  
        """
        return True if self.getObsCount(startTimeInMin, endTimeInMin) else False 

    def hasAllMovementCounts(self, startTimeInMin, endTimeInMin):
        """Return True if there is a count for all outgoing movements
        in the input time period  
        """
        status = True
        for mov in self.iterOutgoingMovements():
            if not mov.hasObsCount(startTimeInMin, endTimeInMin):   
                  status = False
        return status

    def disallowSplitForConnector(self, disallowConnectorEvalStr):
        """
        Returns True if this road link should *not* be split for a :py:class:`Connector`.
        
        Used by :py:meth:`RoadNode.getCandidateLinksForSplitting`, which is used by
        :py:meth:`Network.moveCentroidConnectorsFromIntersectionsToMidblocks`.
        
        Basically this DTA Anyway user defines this functionality by passing in *disallowConnectorEvalStr*.
        """
        return eval(disallowConnectorEvalStr)

    def setResTimeFac(self, newResFac):
        """
        Sets the response time factor to the given value
        """ 
        self._responseTimeFactor = newResFac 

    def setTollLink(self, newTollLink):
        """
        Sets the tollLink field (dummy var indicating tolled link) to specified value (should be zero or one)
        """
        self._tollLink = newTollLink     

    def getTollLink(self):
        """
        Return the tollLink value for the link
        """
        return self._tollLink
