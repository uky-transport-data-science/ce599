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
import os
from .DtaError import DtaError
from .Logger import DtaLogger
from .Scenario import Scenario
from .Utils import Time
from .VehicleClassGroup import VehicleClassGroup
from .VehicleType import VehicleType

class DynameqScenario(Scenario):
    """
    A Dynameq Scenario.
    """
    SCENARIO_FILE   = '%s_scen.dqt'
    ADVANCED_HEADER     = """<DYNAMEQ>
<VERSION_1.7>
<SCENARIO_FILE>
* CREATED by DTA Anyway http://code.google.com/p/dta/    
""" 

    @classmethod
    def read(cls, dir, prefix):
        """
        Read the scenario file from disk and return the corresponding
        scnario object.
        """
        sc = Scenario()
        sc.read(dir, prefix)        

    def __init__(self, startTime = Time(0,0), endTime=Time(23,0)):
        """
        Constructor of a Scenario for Dynameq.

        :param startTime: the start time of the scenario.
        :type startTime: a :py:class:`dta.Time` instance
        :param endTime: the end time of the scenario.
        :type endTime: a :py:class:`dta.Time` instance
        
        """
        Scenario.__init__(self, startTime, endTime)

        # for now just a list: (name, units, turn_expr, link_expr, desc)
        self._generalizedCosts = []
    
    def read(self, dir, file_prefix):
        """
        Reads the scenario configuration from the Dynameq scenario file.
        """
        # scenario file processing
        scenariofile = os.path.join(dir, DynameqScenario.SCENARIO_FILE % file_prefix)
        if not os.path.exists(scenariofile):
            raise DtaError("Scenario file %s does not exist" % scenariofile)
        
        for fields in self._readSectionFromFile(scenariofile, "STUDY_PERIOD", "EVENTS"):
            self._readStudyPeriodFromFields(fields)
            DtaLogger.info("Read  %8d %-16s from %s" % (1, "STUDY_PERIOD", scenariofile))
        
        count = 0
        for fields in self._readSectionFromFile(scenariofile, "EVENTS",       "VEH_CLASSES"):
            #self._addEventFromFields(fields)
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "EVENTS", scenariofile))
                
        count = 0
        for fields in self._readSectionFromFile(scenariofile, "VEH_CLASSES",  "VEH_TYPES"):
            self._readVehicleClassFromFields(fields)
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "VEH_CLASSES", scenariofile))
        
        count = 0
        for fields in self._readSectionFromFile(scenariofile, "VEH_TYPES",  "VEH_CLASS_GROUPS"):
            self.addVehicleType(self._readVehicleTypeFromFields(fields))
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "VEH_TYPES", scenariofile))

        count = 0
        for fields in self._readSectionFromFile(scenariofile, "VEH_CLASS_GROUPS",  "GENERALIZED_COSTS"):
            self.addVehicleClassGroup(self._readVehicleClassGroupFromFields(fields))
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "VEH_CLASS_GROUPS", scenariofile))
                 
        count = 0
        for fields in self._readSectionFromFile(scenariofile, "GENERALIZED_COSTS", "ENDOFFILE"):
            self._readGeneralizedCostFromFields(fields)
            count += 1
        DtaLogger.info("Read  %8d %-16s from %s" % (count, "GENERALIZED_COSTS", scenariofile))


    def write(self, dir, file_prefix):
        scenariofile = os.path.join(dir, DynameqScenario.SCENARIO_FILE % file_prefix)
        
        scenariofile_object = open(scenariofile, "w")
        scenariofile_object.write(DynameqScenario.ADVANCED_HEADER)
        self._writeStudyPeriodToScenarioFile(scenariofile_object)
        self._writeEventsToScenarioFile(scenariofile_object)
        self._writeVehicleClassesToScenarioFile(scenariofile_object)
        self._writeVehicleTypesToScenarioFile(scenariofile_object)
        self._writeVehicleClassGroupsToScenarioFile(scenariofile_object)
        self._writeGeneralizedCostsToScenarioFile(scenariofile_object)
        scenariofile_object.close()
        
    def _readSectionFromFile(self, filename, sectionName, nextSectionName):
        """
        Generator function, yields fields (array of strings) from the given section of the given file.
        """
        lines = open(filename, "r")
        curLine = ""
        try:
            # find the section
            while curLine != sectionName:
                curLine = lines.next().strip()
        except StopIteration:
            raise DtaError("DynameqNetwork _readSectionFromFile failed to find %s in %s" % 
                           (sectionName,filename))
        
        # go past the section name
        curLine = lines.next().strip()
        # skip any comments
        while curLine[0] == "*":
            curLine = lines.next().strip()
        
        # these are the ones we want
        while not curLine == nextSectionName:
            fields  = curLine.split()
            yield fields
            
            curLine = lines.next().strip()
        lines.close()
        raise StopIteration

    def _readStudyPeriodFromFields(self, fields):
        """ 
        Reads the study period and sets the :py:attr:`Scenario.startTime` and :py:attr:`Scenario.endTime`
        """  
        time1 = fields[0].split(":")
        time2 = fields[1].split(":")
        
        self.startTime  = Time(hour=int(time1[0]), minute=int(time1[1]))
        self.endTime    = Time(hour=int(time2[0]), minute=int(time2[1]))
    
    def _writeStudyPeriodToScenarioFile(self, scenariofile_object):
        """
        Write version of _readStudyPeriodFromScenarioFile().  *scenariofile_object* is the file object,
        ready for writing.
        """
        scenariofile_object.write("STUDY_PERIOD\n")
        scenariofile_object.write("*   start      end\n")
        scenariofile_object.write("    %02d:%02d    %02d:%02d\n" % (self.startTime.hour, self.startTime.minute,
                                                                    self.endTime.hour,   self.endTime.minute))
        
    def _readEventsFromFields(self, scenariofile):
        """
        Generator function, yields (eventTime, eventDescription) to the caller
        
        TODO: update to use dta.Time rather than datetime.time for consistency.
        """
        timestrs = fields[0].split(":")
        eventTime = datetime.time(hour=int(timestrs[0]), minute=int(timestrs[1]))
        eventDesc = fields[1]
        self.events[eventTime] = self.eventDesc
        
    def _writeEventsToScenarioFile(self, scenariofile_object):
        """
        Write version of _readEventsFromScenarioFile().  *scenariofile_object* is the file object,
        ready for writing.
        """
        scenariofile_object.write("EVENTS\n")
        scenariofile_object.write("*    time                                                     desc\n")
        count = 0
        for eventTime in sorted(self.events.keys()):
            scenariofile_object.write("    %02d:%02d %56s\n" % (eventTime.hour, eventTime.minute,
                                                                self.events[eventTime]))
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "EVENTS", scenariofile_object.name))

                
    def _readVehicleClassFromFields(self, fields):
        self.addVehicleClass(fields[0])
        
    def _writeVehicleClassesToScenarioFile(self, scenariofile_object):
        """
        Write version of _readVehicleClassesFromScenarioFile().  *scenariofile_object* is the file object,
        ready for writing.
        """
        scenariofile_object.write("VEH_CLASSES\n")
        scenariofile_object.write("*      class_name\n")
        count = 0
        for vehicleClassName in self.vehicleClassNames:
            scenariofile_object.write("%17s\n" % vehicleClassName)
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "VEH_CLASSES", scenariofile_object.name))

        
    def _readVehicleTypeFromFields(self, fields):
        """
        Returns a VehicleType
        """
        vehicleClassName    = fields[0]
        vehicleTypeName     = fields[1]
        length              = float(fields[2])
        responseTime        = float(fields[3])
        maxSpeed            = float(fields[4])
        speedRatio          = float(fields[5])
        
        return VehicleType(vehicleTypeName,
                           vehicleClassName,
                           length,
                           responseTime,
                           maxSpeed,
                           speedRatio)

    
    def _writeVehicleTypesToScenarioFile(self, scenariofile_object):
        """
        Write version of _readVehicleTypesFromScenarioFile().  *scenariofile_object* is the file object,
        ready for writing.
        """
        scenariofile_object.write("VEH_TYPES\n")
        scenariofile_object.write("*class_name       type_name   length res_time max_speed speed_ratio\n")
        count = 0
        for vehicleType in self.vehicleTypes:
            scenariofile_object.write("%13s %13s %8.2f %8.2f %8.2f %8.2f\n" % (vehicleType.className,
                                                                              vehicleType.name,
                                                                              vehicleType.length,
                                                                              vehicleType.responseTime,
                                                                              vehicleType.maxSpeed,
                                                                              vehicleType.speedRatio))
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "VEH_TYPES", scenariofile_object.name))

        
    def _readVehicleClassGroupFromFields(self, fields):
        """
        Returns a VehicleClassGroup
        """
        groupName     = fields[0]
        classDef      = fields[1]
        colorCode     = fields[2]
        return VehicleClassGroup(groupName, classDef, colorCode)

    def _writeVehicleClassGroupsToScenarioFile(self, scenariofile_object):
        """
        Write version of _readVehicleClassGroupsFromScenarioFile().  *scenariofile_object* is the file object,
        ready for writing.
        """
        scenariofile_object.write("VEH_CLASS_GROUPS\n")
        scenariofile_object.write("*      name   class      color\n")
        count = 0
        for groupname in sorted(self.vehicleClassGroups.keys()):
            scenariofile_object.write("%11s %7s %10s\n" % (groupname,
                                                           self.vehicleClassGroups[groupname].classDefinitionString,
                                                           self.vehicleClassGroups[groupname].colorCode))
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "VEH_CLASS_GROUPS", scenariofile_object.name))

    def addGeneralizedCost(self, name, units, turn_expr, link_expr, desc):
        """
        TODO: need more documentation on these terms.
        """
        self._generalizedCosts.append((name, units, turn_expr, link_expr, desc))
    
    def _readGeneralizedCostFromFields(self, fields):
        self._generalizedCosts.append(fields)
    
    def _writeGeneralizedCostsToScenarioFile(self, scenariofile_object):
        """
        Write version of _readGenarlizedCostFromFields().
        *scenariofile_object* should be ready for writing
        """
        scenariofile_object.write("GENERALIZED_COSTS\n")
        scenariofile_object.write("*        name   units                                                 turn_expr link_expr desc\n")
        count = 0
        for gc in self._generalizedCosts:
            scenariofile_object.write(" ".join(gc) + "\n")
            count += 1
        DtaLogger.info("Wrote %8d %-16s to %s" % (count, "GENERALIZED_COSTS", scenariofile_object.name))
