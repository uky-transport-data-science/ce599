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

from .DtaError import DtaError

class PhaseMovement(object):
    """
    Represents a movement specific to a particular phase.  This is basically a :py:class:`Movement` with an
    annotation of whether the Movement is permitted or protected.
    
    Does this really need to be its own class?  It's really just a tuple [Movement, permitted|protected]
    """

    #: The movement is protected under this phase
    PROTECTED = 1     
    #: The movement is permitted under this phase
    PERMITTED = 2
        
    def __init__(self, movement, capacityTag):
        """
        Constructor.  *movement* is an instance of :py:class:`Movement`.
        *capacityTag* is one of :py:attr:`PhaseMovement.PROTECTED` or :py:attr:`PhaseMovement.PERMITTED`         
        """
        self._movement = movement
        if not capacityTag in [PhaseMovement.PROTECTED, PhaseMovement.PERMITTED]:
            raise DtaError("Capacity tag %d does not correspond to a protected or permitted movement" % capacityTag)                            
        self._capacityTag = capacityTag

    def getDynameqStr(self): 
        """
        Return the dynameq string representaton of the phase 
        movement
        """
        return "%s %s %d" % (self._movement.getIncomingLink().getId(), 
                             self._movement.getOutgoingLink().getId(), 
                             self._capacityTag)

    def getMovement(self):
        """
        Return the underlying :py:class:`Movement` of the phase movement
        """
        return self._movement

    def isPermitted(self):
        """
        Return True if the movement is permitted otherwise False
        """
        return self._capacityTag == PhaseMovement.PERMITTED

    def isProtected(self):
        """
        Return True if the movement is protected otherwise False
        """
        return self._capacityTag == PhaseMovement.PROTECTED

    def setProtected(self):
        """
        Sets the phase movement as protected
        """
        self._capacityTag = PhaseMovement.PROTECTED

    def setPermitted(self):
        """
        Sets the phase movement as permitted
        """
        self._capacityTag = PhaseMovement.PERMITTED
    
    def __eq__(self, other):
        """
        implementation of the == operator
        """
        if self._movement == other._movement and self._capacityTag == other._capacityTag:
            return True
        return False
