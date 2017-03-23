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

class VehicleClassGroup:
    """
    Represents a group (or a set) of VehicleClasses, which are the classNames in :py:class:`VehicleType`.
    """
    CLASSDEFINITION_PROHIBITED = "Prohibited"
    CLASSDEFINITION_ALL        = "All"
    CLASSDEFINITION_TRANSIT    = "Transit"

    @classmethod
    def getProhibited(cls):
        """
        Return a vehicle class group object that prohibits all movements
        """
        prohibited = VehicleClassGroup("Prohibited",
                                       VehicleClassGroup.CLASSDEFINITION_PROHIBITED, "#ffff00")
        return prohibited

    @classmethod
    def prohibitAllMovementsButTransit(cls):
        """
        Return a vehicle class group object that prohibits all movements
        but the transit ones. 
        """
        prohibited = VehicleClassGroup("Transit",
                                       VehicleClassGroup.CLASSDEFINITION_TRANSIT, "#55ff00")
        return prohibited
    
    def __init__(self, name, classDefinitionString, colorCode):
        """
        Constructor.
        
         * *name* is the vehicle class group name (e.g. ``All``, ``No_Trucks``)
         * *classDefinitionString* defines the class (either ``-``, ``*``, or a pipe-delimited set of vehicle classes
         * *colorCode* is a hex color code for drawing (e.g. ``#ffff00``)
         
        """
        self.name                   = name
        self.classDefinitionString  = classDefinitionString
        self.colorCode              = colorCode

    def __str__(self):

        return "%s,%s,%s" % (self.name, self.classDefinitionString, self.colorCode)

    def allowsAll(self):
        """
        Return True if the vehicle class group allows all vehicle classes
        """
        return self.classDefinitionString == VehicleClassGroup.CLASSDEFINITION_ALL

    def allowsTransit(self):
        """
        Returns True if the vehicle class group allows transit
        """
        return (self.classDefinitionString == VehicleClassGroup.CLASSDEFINITION_ALL or
                self.classDefinitionString == VehicleClassGroup.CLASSDEFINITION_TRANSIT)
        
    def allowsNone(self):
        """
        Return True if the vehicle class group allows all vehicle classes
        """
        return self.classDefinitionString == VehicleClassGroup.CLASSDEFINITION_PROHIBITED
        
