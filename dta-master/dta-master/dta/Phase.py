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

from .PhaseMovement import PhaseMovement
from .DtaError import DtaError 

class Phase(object):
    """
    A phase consists of timing (green, yellow and red times) plus a set of :py:class:`PhaseMovement` instances
    that are allowed to move during the green time.
    
    A phase can be Standard, or Custom; the difference being that a custom phase movement can
    specify a subset of the movement lanes that are permitted/protected.
    
    Right now, Custom phases aren't really supported.
    """
    #: Custom phase, where the relevant movements have specified lanes that are permitted/protected
    TYPE_CUSTOM = 1
    #: Standard phase
    TYPE_STANDARD = 0

    @classmethod
    def readFromDynameqString(self, net, timeplan, lineIter):
        """
        Parses the dynameq phase string defined in multiple lines of text and returns a :py:class:`Phase` object.
         
        * *lineIter* is an iterator over the lines of a text file containing the Dynameq phase info. 
        * *net* is an instance of :py:class:`DynameqNetwork`
        * *timePlan* is an instance of :py:class:`TimePlan`
        
        """         
        endOfFile = True
        try:
            currentLine = lineIter.next().strip() 
            while not currentLine.startswith("PLAN_INFO") \
                    and not currentLine.startswith("NODE"):

                assert currentLine.startswith("PHASE")
                endOfFile = True
                currentLine = lineIter.next().strip()                 
                green, yellow, red, phaseType = map(float, currentLine.split())
                phaseType = int(phaseType)
                phase = Phase(timeplan, green, yellow, red, phaseType)
                currentLine = lineIter.next().strip()

                while not currentLine.startswith("PHASE") and \
                        not currentLine.startswith("PLAN_INFO") and \
                        not currentLine.startswith("NODE"):
                    
                    if currentLine.strip() == "":
                        raise StopIteration
                    fields = currentLine.split()
                    inLinkId, outLinkId, capacityTag = map(int, fields)
                    capacityTag = int(capacityTag) 
                    inLink = net.getLinkForId(inLinkId) 
                    outLink = net.getLinkForId(outLinkId) 
                    movement = inLink.getOutgoingMovement(outLink.getEndNodeId())
                    phase_movement = PhaseMovement(movement, capacityTag)                     
                    try:
                        phase.addPhaseMovement(phase_movement)
                    except DtaError, e:
                        print str(e)
                    currentLine = lineIter.next().strip()
                yield phase
            endOfFile = False
            raise StopIteration
        except StopIteration:
            if endOfFile:
                yield phase
            raise StopIteration

    def __init__(self, timePlan, green, yellow, red, phaseType=TYPE_STANDARD):
        """
        Constructor. 
        
        * *timeplan* is the :py:class:`TimePlan` instance to which this Phase belongs.
        * *green*, *red*, and *yellow* are numbers (int or float) representing the number of seconds
          for each light
           
        """
        self._timePlan  = timePlan
        self._node      = timePlan.getNode()
        self._green     = green
        self._yellow    = yellow
        self._red       = red
        self._phaseType = phaseType

        self._phaseMovements= []

    def getDynameqStr(self):
        """
        Return the Dynameq representation of the phase as a string.  Includes ending newline.
        """
        if int(self._green) == self._green:
            green = str(int(self._green))
        else:
            green = str(self._green)

        if int(self._yellow) == self._yellow:
            yellow = str(int(self._yellow))
        else:
            yellow = str(self._yellow)

        if int(self._red) == self._red:
            red = str(int(self._red))
        else:
            red = str(self._red)
                    
        header = "PHASE\n%s %s %s %d\n" % (green, yellow, red, self._phaseType)
        if len(self._phaseMovements) > 0:
            body = "\n".join([mov.getDynameqStr() for mov in self.iterPhaseMovements()]) + "\n"
        else:
            body = ""
        return "%s%s" % (header, body)

    def addPhaseMovement(self, phase_movement):
        """
        Add the input *movement* (an instance of :py:class:`PhaseMovement`) to the phase. 
        
        If the movement already exists a :py:class:`DtaError` will be raised.
        """
        if not self.getTimePlan().getNode().hasMovement(phase_movement.getMovement().getStartNode().getId(),
                                                        phase_movement.getMovement().getEndNode().getId()):
            raise DtaError("Phase Movement %s is not does not belong to node %d" % (phase_movement.getMovement().getId(),
                                                                                    phase_movement.getMovement().getAtNode().getId()))
        if self.hasPhaseMovement(phase_movement.getMovement().getStartNodeId(), 
                                 phase_movement.getMovement().getEndNodeId()):
            raise DtaError("Phase Movement %s already belongs to this phase" % phase_movement.getMovement().getId())
        
        self._phaseMovements.append(phase_movement)
    
    def getTimePlan(self):
        """
        Return the timeplan associated with this phase
        """
        return self._timePlan

    def getNumPhaseMovements(self):
        """
        Return the number of phase movements in the phase
        """
        return len(self._phaseMovements)
                
    def getPhaseMovement(self, startNodeId, endNodeId):
        """
        Return the :py:class:`PhaseMovement` from startNodeId to endNodeId
        """
        for movement in self.iterPhaseMovements():
            if (movement.getMovement().getStartNodeId() == startNodeId and 
                movement.getMovement().getEndNodeId() == endNodeId):
                return movement
        raise DtaError("Phase Movement from %d to %d does not exist" % (startNodeId, endNodeId))

    def hasPhaseMovement(self, startNodeId, endNodeId):
        """
        Return True iff the phase has the phase movement with the given id
        """
        try:
            self.getPhaseMovement(startNodeId, endNodeId)
            return True
        except DtaError, e:
            return False

    def hasProtectedPhaseMovement(self, startNodeId, endNodeId):
        """
        Return True if the phase has a protected movement from 
        input start node to end node
        """
        try:
            mov = self.getPhaseMovement(startNodeId, endNodeId)
            if mov.isProtected():
                return True
            return False
        except DtaError, e:
            return False 
        
    def hasPermittedPhaseMovement(self, startNodeId, endNodeId):
        """
        Return True if the phase has a permitted movement from 
        start node to end node
        """
        try:
            mov = self.getPhaseMovement(startNodeId, endNodeId)
            if mov.isPermitted():
                return True
            return False
        except DtaError, e:
            return False 
        
    def iterPhaseMovements(self):
        """
        Return an iterator the the :py:class:`PhaseMovement` instances for this Phase
        """
        return iter(self._phaseMovements)

    def getGreen(self):
        """
        Return the green time in seconds (an integer or float) 
        """
        return self._green

    def getYellow(self):
        """
        Return the yellow time in seconds (an integer or float) 
        """
        return self._yellow

    def getRed(self):
        """
        Return the red time in seconds (an integer or float) 
        """
        return self._red 
