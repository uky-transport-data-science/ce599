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

class VehicleType:
    """
    Class that represents a vehicle type.
    """
    
    #: Static variable representing the units for length
    #: Should be ``meters`` or ``feet``
    LENGTH_UNITS = None
    
    def __init__(self, name, className, length, responseTime, maxSpeed, speedRatio):
        """
        Constructor.
        
        * *name* is the vehicle type name, e.g. ``small_truck``
        * *className* a broader class, e.g. ``truck``
        * *length* is the effective length (units?)
        * *responseTime* is the response time of the vehicle in seconds
        * *maxSpeed* is the maximum speed of the vehicle, in km/hour or miles/hr depending on the project units.
        * *speedRatio* is the ratio of this vehicle type's speed over the link speed (times 100?!)
         
        """
        self.name           = name
        self.className      = className
        self.length         = length
        self.responseTime   = responseTime
        self.maxSpeed       = maxSpeed
        self.speedRatio     = speedRatio