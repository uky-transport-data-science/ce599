__copyright__   = "Copyright 2011-2012 SFCTA"
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

from .Phase import Phase
from .DtaError import DtaError
from .Logger import DtaLogger
from .Utils import Time


__all__ = ["PlanCollectionInfo", "TimePlan"]

class PlanCollectionInfo(object):
    """
    Contains user information for a collection of signals belonging to the
    same time period
    """
    
    def __init__(self, startTime, endTime, name, description):
        """
        A PlanCollectionInfo object has some general info for all the time plans that are
        active between startTime and endTime. The inputs to the constructor are:
        
        * *startTime*: a :py:class:`dta.Utils.Time` object representing the start time of the time plan collection
        * *endTime*: a :py:class:`dta.Utils.Time` object representing the end time of the time plan collection
        * *name*: a string containing the name of the plan collection
        * *description*: a string containing the description of the plan collection
         
        """
        self._startTime = startTime
        self._endTime = endTime
        self._name = name
        self._description = description

    def getDynameqStr(self):
        """
        Return a Dynameq parsable string containing information about the time plan such as
        the start time, the end time, its name, and description
        """ 
        return ("PLAN_INFO\n%s %s\n%s\n%s\n" %  
                (self._startTime.strftime("%H:%M"), 
                 self._endTime.strftime("%H:%M"),
                 self._name, self._description))
                    
    def getTimePeriod(self):
        """
        Return a tuple of two :py:class:`dta.Utils.Time` objects corresponding to the
        start and end time of the plan collection
        """
        return self._startTime, self._endTime

class TimePlan(object):
    """
    Represents generic signal timeplan
    
    """

    CONTROL_TYPE_CONSTANT = 0
    CONTROL_TYPE_PRETIMED = 1
    
    #: Turn on red is allowed
    TURN_ON_RED_YES = 1
    #: Turn on red is not allowed
    TURN_ON_RED_NO = 0

    @classmethod
    def readDynameqPlans(cls, net, fileName):
        """
        This method reads the Dynameq time plans contained in the input
        ascii filename and adds them to the provided dynameq network object.
        #TODO: add version number
        """

        try:
            lineIter = open(fileName, "r")
            while not lineIter.next().strip().startswith("PLAN_INFO"):
                continue
            currentLine = lineIter.next().strip()
 
            militaryStartStr, militaryEndStr = currentLine.split()
            
            startTime = Time.readFromString(militaryStartStr)
            endTime = Time.readFromString(militaryEndStr) 

            name = lineIter.next().strip()
            description = ""
            currentLine = lineIter.next()
            while not currentLine.startswith("NODE"):
                description += currentLine
                currentLine = lineIter.next()

            if not net.hasPlanCollectionInfo(startTime, endTime):                
                planCollectionInfo = net.addPlanCollectionInfo(startTime, endTime,
                                                    name, description)
            else:
                planCollectionInfo = net.getPlanCollectionInfo(startTime, endTime)
                                                                                         
            while True:
                currentLine = lineIter.next().strip()
                if currentLine == "":
                    raise StopIteration
                nodeId = int(currentLine)
                node = net.getNodeForId(nodeId)
                
                # PLAN keyword
                planKeyword = lineIter.next().strip()
                assert(planKeyword == "PLAN")
                
                type_, offset, sync, tor = map(int, lineIter.next().strip().split())
                
                timePlan = TimePlan(node, offset, planCollectionInfo, 
                                    syncPhase=sync, 
                                    turnOnRed=tor)
                                     
                for phase in Phase.readFromDynameqString(net, timePlan, lineIter):
                    timePlan.addPhase(phase)
                yield timePlan
        except StopIteration:
            lineIter.close()
                    
    def __init__(self, node, offset, planCollectionInfo,
                 syncPhase=1, turnOnRed=TURN_ON_RED_YES):
        """
        Constructor.
        
        * *node* is a :py:class:`RoadNode` instance, the node at which the signal resides
        * *offset* is a positive integer representing the synchronization offset, in seconds
        * *planCollectionInfo* is a :py:class:`PlanCollectionInfo` instance, containing information about
          the start and end times of the time plan
        * *syncPhase* is an integer, the synchronization phase to which the offset applies
        * *turnOnRed* is either :py:attr:`TimePlan.TURN_ON_RED_YES` or :py:attr:`TimePlan.TURN_ON_RED_NO`
        
        """
        self._node = node
        self._planCollectionInfo = planCollectionInfo
        self._type = TimePlan.CONTROL_TYPE_PRETIMED
        self._offset = offset
        self._syncPhase = syncPhase
        self._turnOnRed = turnOnRed

        self._phases = []

    def getDynameqStr(self):
        """
        Return a Dynameq parsable string that represents the time plan
        """
        nodeInfo = "NODE\n%s\n" % self.getNode().getId()
        planInfo = "PLAN\n%d %d %d %d\n" % (self._type, self._offset, self._syncPhase, self._turnOnRed)
        # ending newlines included in phases
        phases = "".join([phase.getDynameqStr() for phase in self.iterPhases()])
        return "%s%s%s" % (nodeInfo, planInfo, phases)

    def addPhase(self, phase):
        """
        Add the given *phase* (an instance of :py:class:`Phase`) to the timeplan
        """
        assert isinstance(phase, Phase)
        self._phases.append(phase)

    def iterPhases(self):
        """
        Return an iterator to the :py:class:`Phase` instances in the timeplan
        """
        return iter(self._phases)

    def isValid(self):
         """
         Return True if the plan is valid otherwise return false.  See :py:meth:`TimePlan.validate` for
         details on the checks performed.
         """
         try:
             self.validate()
             return True
         except DtaError:
             return False

    def getNodeId(self):
        """
        Return the id of the node the timeplan applies
        """
        return self._node.id

    def getOffset(self):
        """
        Return the offset as an integer or float
        """
        return self._offset

    def getNumPhases(self):
        """
        Return the number of phases
        """
        return len(self._phases)

    def getNode(self):
        """
        Return the node instance the timeplan applies
        """
        return self._node

    def getPhase(self, phaseNum):
        """
        Return the :py:class:`Phase` instance with the given index.
        Throws a :py:class:`DtaError` if the *phaseNum* is invalid.
        """
        if phaseNum <= 0 or phaseNum > self.getNumPhases():
            return DtaError("Timeplan for node %s does not have a phase "
                                 "with index %d" % (self._node.id, phaseNum))
        return self._phases[phaseNum - 1]

    def getCycleLength(self):
        """
        Return the cycle length in seconds as an integer or float
        """
        return sum([phase._green + phase._yellow + phase._red for phase in self.iterPhases()])

    def getPlanInfo(self):
        """
        Return the plan info associated with this time plan, an instance of :py:class:`PlanCollectionInfo`.
        """
        return self._planCollectionInfo

    def setSyncPhase(self, phaseId):
        """
        Set the phase with input id (an integer) the as the sync phase.  
        """
        if syncPhase <= 0:
            raise DtaError("Node %s. The sync phase %d cannot be less than 1 or greater than "
                               "the number of phases %d" % (self.getNodeId(), syncPhase, self.getNumPhases()))
        self._syncPhase = syncPhase 

    def validate(self, allRedPhaseOK=True):
        """
        Make the following checks to the timeplan. If any of them fails raise a :py:class:`DtaError`
        
        1. Sync phase is a valid phase
        2. Number of phases is equal or greater than two
        3. The number of movements each phase has should be greater than zero.  This check
           is only performed if *allRedPhaseOK* is False.  All red phases may be reasonable when
           there is a pedestrian scramble.
        4. The phase movements are exactly the same as the node movements:
           there is no node movement that is not served by a phase and there is
           not a phase movement that does not exist in the node. 
        5. If two movements conflict with each other then they can't both be protected
        
        """
        if self._offset < 0:
            raise DtaError("Node %s. The offset cannot be less than 0" % self.getNode().getId())
                   
        if self._syncPhase <= 0 or self._syncPhase > self.getNumPhases():
            raise DtaError("Node %s. The sync phase %d cannot be less than 1 or greater than "
                               "the number of phases %d" % (self.getNodeId(), self._syncPhase, self.getNumPhases()))
            
        if self.getNumPhases() < 2:
            raise DtaError("Node %s has a timeplan with less than 2 phases" % self._node.getId())

        if allRedPhaseOK == False:
            for phase in self.iterPhases():
                if phase.getNumPhaseMovements() < 1:
                    raise DtaError("Node %s The number of movements in a phase "
                                   "cannot be less than one" % self._node.getId())

        phaseMovements = set([mov.getMovement().getId() for phase in self.iterPhases() 
                              for mov in phase.iterPhaseMovements()]) 

        #if right turns on red add the right turns 
        if self._turnOnRed == TimePlan.TURN_ON_RED_YES:
            for mov in self._node.iterMovements():
                if mov.isRightTurn() and not mov.isProhibitedToAllVehicleClassGroups():
                    phaseMovements.add(mov.getId())

        nodeMovements = set([mov.getId() for mov in self._node.iterMovements() 
                            if not mov.isProhibitedToAllVehicleClassGroups()])
        
        if phaseMovements != nodeMovements:
            nodeMovsNotInPhaseMovs = nodeMovements.difference(phaseMovements)
            phaseMovsNotInNodeMovs = phaseMovements.difference(nodeMovements)
            error_str = ""
            if len(nodeMovsNotInPhaseMovs) > 0:
                error_str += "; Node movements missing from the phase movements: "
                error_str += ",".join(map(str, nodeMovsNotInPhaseMovs))
            if len(phaseMovsNotInNodeMovs) > 0:
                error_str += "; Phase movements not registered as node movements: "
                error_str += ",".join(map(str, phaseMovsNotInNodeMovs))
            raise DtaError("Node %s. The phase movements != node movements. %s" %
                           (self._node.getId(), error_str))
        
        #check that if two conflicting movements exist one of them is permitted or right turn
        for phase in self.iterPhases():
            for mov1 in phase.iterPhaseMovements():
                for mov2 in phase.iterPhaseMovements():
                    
                   if mov1.getMovement().getId() == mov2.getMovement().getId(): continue
                   if not mov1.getMovement().isInConflict(mov2.getMovement()): continue
                   
                   if mov1.isProtected() and mov2.isProtected():
                       if mov1.getMovement().isRightTurn() or mov2.getMovement().isRightTurn(): continue
                       raise DtaError("Movements %s, %s and %s, %s are in conflict and are both protected " % 
                                      (mov1.getMovement().getId(), mov1.getMovement().getTurnType(), 
                                       mov2.getMovement().getId(), mov2.getMovement().getTurnType()))  
                                                                      
    def setPermittedMovements(self):
        """
        Examines all the movements in the timeplan pairwise and if two movements
        conflict with each other it sets the lower priority movement as
        permitted. For example, if a protected left turn conflicts with a
        protected through movement it sets the left turn as permitted.
        If two through movements conflict with each other and are both
        protected an error is being raised.
        """
        for phase in self.iterPhases():
            for mov1 in phase.iterPhaseMovements():
                for mov2 in phase.iterPhaseMovements():
                    
                    # same movement
                    if mov1.getMovement().getId() == mov2.getMovement().getId(): continue
                    
                    # no conflict
                    if not mov1.getMovement().isInConflict(mov2.getMovement()):  continue
                   
                    # two thru movements in conflict
                    if mov1.getMovement().isThruTurn() and mov2.getMovement().isThruTurn():
                        raise DtaError("Movements %s and %s are in conflict and are both protected and thru movements" %
                                       (mov1.getMovement().getId(), mov2.getMovement().getId()))
                    
                    
                    if mov1.getMovement().isLeftTurn() and (mov2.getMovement().isThruTurn() or mov2.getMovement().isRightTurn()):
                        # left is lower priority than through or right
                        mov1.setPermitted()
                        
                    if mov1.getMovement().isLeftTurn() and mov2.getMovement().isLeftTurn():
                        # two left turns - first takes priority (?)
                         if not mov1.isPermitted():
                            mov2.setPermitted()


