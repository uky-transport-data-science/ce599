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
import copy
import csv
import datetime
from itertools import izip 

import numpy as np

import dta
from dta.Algorithms import hasPath, getClosestCentroid 
from dta.DtaError import DtaError
from dta.MultiArray import MultiArray
from dta.Utils import Time

class Demand(object):
    """
    Class that represents the demand matrix for a :py:class:`Network`
    """

    @classmethod
    def readCubeODTable(cls, fileName, net, vehicleClassName, 
                        startTime, endTime, timeStep, demandPortion):
        """
        Reads the demand (linear format) from the input csv file and returns a demand instance.
        
        :param fileName: the file containing the demand; this will be a CSV containing 
           ``Origin, Destination, VehicleClassDemand1, VehicleClassDemand2, ...``.  The header line will be used
           to determine which column is relevant to which Vehicle Class.
        :param net: the Network for which this demand is relevant, used to get TAZ numbers.
        :type net: a :py:class:`Network` instance
        :param vehClassName: a string that must match the relevant :py:class:`VehicleClass` exactly (it's case-sensitive!)
        :param startTime: the simulation start time for when this demand will get added to the network.
        :type startTime: a :py:class:`dta.Utils.Time` instance
        :param endTime: the simulation end time for this demand will stop being added to the network.
        :type endTime: a :py:class:`dta.Utils.Time` instance
        :param timeStep: the granularity of time steps at which the demand is represented.
        :type timeStep: a :py:class:`dta.Utils.Time` instance
        
        """
        timeSpan = endTime - startTime
        demand = Demand(net, vehicleClassName, startTime, endTime, timeStep)
        #demand = Demand(net, vehicleClassName, startTime, endTime, timeSpan)
        totTrips = 0
        numIntrazonalTrips = 0
        inputStream = open(fileName, "r")
        checkSum = 0 
    
        for record in csv.DictReader(inputStream):
            
            origin = int(record["O"])
            destination = int(record["D"])
            trips = demandPortion*float(record[vehicleClassName])
            totTrips += trips
            tripsInHourlyFlows = trips * (60.0 / timeSpan.getMinutes())
            
            if tripsInHourlyFlows == 0:
                continue
            if origin == destination:
                origCent = net.getNodeForId(origin)
                destCent, dist = getClosestCentroid(net, origCent)
                tripsIntrazonal = tripsInHourlyFlows/2
                tripsBefore = demand.getTotalNumTrips()
                for i,timeSlice in enumerate(demand._timePeriods):
                    tripsOD = demand.getValue(timeSlice, origCent.getId(), destCent.getId())
                    tripsDO = demand.getValue(timeSlice, destCent.getId(), origCent.getId())
                    tripsOD += tripsIntrazonal
                    tripsDO += tripsIntrazonal
                    demand.setValue(timeSlice, origCent.getId(), destCent.getId(), tripsOD)
                    demand.setValue(timeSlice, destCent.getId(), origCent.getId(), tripsDO)
                #dist = dist/5280
                #dta.DtaLogger.debug("Assigning %f intrazonal trips from zone %s to zone %s, %8.4f miles away." % (tripsInHourlyFlows,origCent.getId(),destCent.getId(),dist))
                numIntrazonalTrips += trips
                continue
            if not net.hasCentroidForId(origin):
                dta.DtaLogger.error("Origin zone %d does not exist" % origin)
                continue 
            if not net.hasCentroidForId(destination):
                dta.DtaLogger.error("Destination zone %s does not exist" % destination)
                continue
            for i,timeSlice in enumerate(demand._timePeriods):
                tripsOD = demand.getValue(timeSlice, origin, destination)
                tripsOD += tripsInHourlyFlows
                demand.setValue(timeSlice, origin, destination, tripsOD)
            #if destination == 7973:
            #    checkSum += trips

        dta.DtaLogger.info("The cube table has the following fields: %s" % ",".join(record.keys()))
          
        dta.DtaLogger.info("Read %10.2f %-16s from %s" % (totTrips, "%s TRIPS" % vehicleClassName, fileName))
        if numIntrazonalTrips > 0:
            dta.DtaLogger.info("Reassigned %f intrazonal Trips" % numIntrazonalTrips)
        if totTrips - demand.getTotalNumTrips() > 1:
            dta.DtaLogger.error("The total number of trips in the Cube table = %d not equal to the number of trips transfered to Dynameq = %d." % (totTrips,demand.getTotalNumTrips()))
        #dta.DtaLogger.info("There are %10.2f trips to zone 7973" % checkSum)
                    
        return demand
       
    @classmethod
    def readDynameqTable(cls, net, fileName):
        """
        Read the dynameq demand stored in the *fileName* that pertains to *net*, a :py:class:`Network` instance.
        This method reads only rectangular demand tables. 
        """
        DYNAMEQ_FORMAT_FULL = "FORMAT:full" 
        
        input = open(fileName, "rb")
        
        input.next() # <DYNAMEQ>
        input.next() # <VERSION> 
        input.next() # <MATRIX_FILE> 
        input.next() # * comment 
        line = input.next().strip() 
        if line != DYNAMEQ_FORMAT_FULL:
            raise DtaError("I cannot read a demand format other than %s" % Demand.FORMAT_FULL)
        input.next() # VEH_CLASS 
        line = input.next().strip() 

        vehClassName = line
        input.next() #DATA 
        line = input.next().strip()         

        startTime = Time.readFromString(line)
        line = input.next().strip()
        endTime = Time.readFromString(line)        
    
        line = input.next().strip() #SLICE 
        assert line == "SLICE"        
        line = input.next().strip() # first time slice
        
        timeSlice1 = Time.readFromString(line)

        timeStep = timeSlice1 - startTime 
        if timeStep.getMinutes() == 0:
            raise DtaError("The time step defined by the first slice cannot be zero") 
        
        demand = Demand(net, vehClassName, startTime, endTime, timeStep)
        _npyArray = demand._demandTable.getNumpyArray()

        timeStepInMin = timeStep.getMinutes()

        for i, timePeriod in enumerate(demand.iterTimePeriods()):
            if timePeriod != demand.startTime + demand.timeStep: 
                line = input.next().strip()
                assert line == "SLICE"
                line = input.next().strip()            
            destinations = map(int, input.next().strip().split())
            for j, origin in enumerate(range(net.getNumCentroids())):
                fields = map(float, input.next().strip().split()) 
                #_npyArray[i,j,:] = np.array(fields[1:]) / ( 60.0 / timeStepInMin)
                _npyArray[i,j,:] = np.array(fields[1:])
                
        return demand



    def __init__(self, net, vehClassName, startTime, endTime, timeStep):
        """
        Constructor that initializes an empty Demand table that has three dimensions:
        time, origin taz, destination taz. 
        
        :param net: the Network for which this demand is relevant, used to get TAZ numbers.
        :type net: a :py:class:`Network` instance
        :param vehClassName: a string that must match the relevant :py:class:`VehicleClass` exactly (it's case-sensitive!)
        :param startTime: the simulation start time for when this demand will get added to the network.
        :type startTime: a :py:class:`dta.Utils.Time` instance
        :param endTime: the simulation end time for this demand will stop being added to the network.
        :type endTime: a :py:class:`dta.Utils.Time` instance
        :param timeStep: the granularity of time steps at which the demand is represented.
        :type timeStep: a :py:class:`dta.Utils.Time` instance
        """
        self._net = net 

        if startTime >= endTime:
            raise DtaError("Start time %s is grater or equal to the end time %s" %
                           startTime, endTime)
        if timeStep.getMinutes() == 0:
            raise DtaError("Time step %s cannot be zero" % timeStep)         

        if ((endTime - startTime) % timeStep) != 0:
            raise DtaError("Demand interval is not divisible by the demand time step") 

        self.startTime      = startTime
        self.endTime        = endTime
        self.timeStep       = timeStep
        self.vehClassName   = vehClassName

        self._timePeriods   = self._getTimePeriods(startTime, endTime, timeStep)
        self._timeLabels    = self._timePeriods # map(self._datetimeToMilitaryTime, self._getTimePeriods(startTime, endTime, timeStep))

        self._centroidIds   = sorted([c.getId() for c in net.iterNodes() if c.isCentroid()]) 

        self._demandTable   = MultiArray("d", [self._timeLabels, self._centroidIds, self._centroidIds])
                                             
        #TODO: what are you going to do with vehicle class names? 
        #self._vehicleClassNames = [vehClass.name for vehClass in self._net.getScenario().vehicleClassNames]

    def iterTimePeriods(self):
        """
        Return an iterator to the time periods associated with the demand time slices
        """
        return iter(self._timePeriods)

    def getNumSlices(self):
        """
        Return the number of time slices the demand has been split
        """
        return len(self._timePeriods)
        
    def _getTimePeriods(self, startTime, endTime, timeStep):
        """
        Return the time labels of the different time slices as a list of :py:class:`dta.Utils.Time` instances.
        Each time in the list is the *end* of the time slice.
        """        
        if ((endTime - startTime) % timeStep) != 0:
            raise DtaError("Demand interval is not divisible by the demand time step") 
                           
        result = []
        #TODO: this is interesting. The following line fails
        #time = copy.deepcopy(startTime)
        time = Time(startTime.hour, startTime.minute)
        while time != endTime:
            time += timeStep
            result.append(time)

        return result 

    def _timeInMin(self, time):
        """
        Return input time in minutes. Input time should be a datetime.datetime or 
        datetime.timedelta object
        """
        
        if isinstance(time, datetime.datetime):
            return time.hour * 60 + time.minute 
        elif isinstance(time, datetime.timedelta):
            return time.seconds / 60     
                                               
    def setValue(self, timeLabel, origin, destination, value):
        """
        Set the value of the given timeLabel, origin, and destination
        """
        self._demandTable[timeLabel, origin, destination] = value  
    
    def getValue(self, timeLabel, origin, destination):
        """
        Return the value of the given time period, origin, and destination
        """
        return self._demandTable[timeLabel, origin, destination]

    @classmethod
    def writeDynameqDemandHeader(cls, outputStream, startTime, endTime, vehClassName, format='full'):
        """
        Write the demand header in the dynameq format
        .. todo:: implement linear writing
        """
        
        if format != 'full':
            raise DtaError("Unimplemented Matrix Format specified: %s" % (format))
            
        FORMAT_LINEAR    = 'FORMAT:linear'
        FORMAT_FULL      = 'FORMAT:full'    
        HEADER_LINE1     = '*DEMAND MATRIX ASCII FILE [FULL FORMAT]- GENERATED'
        VEHCLASS_SECTION = 'VEH_CLASS'
        DEFAULT_VEHCLASS = 'Default'
        DATA_SECTION     = 'DATA'
        

        outputStream.write("<DYNAMEQ>\n<VERSION_1.8>\n<MATRIX_FILE>\n")
        outputStream.write('%s %s %s\n' % ("Created by python DTA by SFCTA", 
                                           datetime.datetime.now().strftime("%x"), 
                                           datetime.datetime.now().strftime("%X")))
        if format == 'full':
            outputStream.write('%s\n' % FORMAT_FULL)
        elif format == 'linear':
            outputStream.write('%s\n' % FORMAT_LINEAR)
        else:
             raise DtaError("Don't understand Dynameq Output Matrix Format: %s" % (format))
             
        outputStream.write('%s\n' % VEHCLASS_SECTION)
        outputStream.write('%s\n' % vehClassName)
        outputStream.write('%s\n' % DATA_SECTION)
        outputStream.write("%s\n%s\n" % (startTime.strftime("%H:%M"),
                                         endTime.strftime("%H:%M"))) 

    def writeDynameqTable(self, outputStream, format='full'):
        """
        Write the demand in Dynameq format
        .. todo:: implement linear writing
        """
        
        if format != 'full':
            raise DtaError("Unimplemented Matrix Format specified: %s" % (format))
            
        SLICE_SECTION    = 'SLICE'
       
        timeStepInMin = self.timeStep.getMinutes()

        _npyArray = self._demandTable.getNumpyArray()
        
        for i, timePeriod in enumerate(self._timePeriods):
            outputStream.write("SLICE\n%s\n" % timePeriod.strftime("%H:%M"))
            outputStream.write("\t%s\n" % '\t'.join(map(str, self._centroidIds)))

            for j, cent in enumerate(self._centroidIds):
                outputStream.write("%d\t%s\n" % (cent, "\t".join("%.2f" % elem for elem in _npyArray[i, j, :])))                
                


    def __eq__(self, other):
        """
        Implementation of the == operator. The comparison of the 
        two demand objects is made using both the data and the labels 
        of the underlying multidimensional arrays. 
        """        
        if self.startTime != other.startTime or self.endTime != other.endTime or \
                self.timeStep != other.timeStep:
            return False 

        if self._timePeriods != other._timePeriods or self._timeLabels != \
                other._timeLabels or self._centroidIds != other._centroidIds:
            return False

        if self.vehClassName != other.vehClassName:
            return False

        if not self._demandTable == other._demandTable:
            return False 

        return True

    def applyTimeOfDayFactors(self, factorsInAList):
        """
        Apply the given time of day factors to the existing 
        demand object and return a new demand object with as many 
        time slices as the number of factors. Each time slice is 
        the result of the original table multiplied by a factor 
        in the list. 
        """
        #raise Exception("This is not the correct implementation. Change it") 
        if self.getNumSlices() != 1:
            raise DtaError("Time of day factors can be applied only to a demand that has only"
                           " one time slice")
        for i in range(0,len(factorsInAList)):
            factorsInAList[i] = float(factorsInAList[i])
            
        if abs(sum(factorsInAList) - 1.) > 0.0000001:
            raise DtaError("The input time of day factors should sum up to 1.0.  Factors are %s" % factorsInAList) 
        
        newTimeStepInMin = self.timeStep.getMinutes() / len(factorsInAList)
        newTimeStep = Time.fromMinutes(newTimeStepInMin)
        
        newDemand = Demand(self._net, self.vehClassName, self.startTime, self.endTime, newTimeStep)
        #timeSpan = (newDemand.endTime - newDemand.startTime).getMinutes()/60.0
        oldDemand = 0
        sliceDemand = []
        for k, timeSlice in enumerate(newDemand._timePeriods):
            sliceDemand.append(0)
        for origin in self._centroidIds:
            for destination in self._centroidIds:
                tripsOD_Old = self.getValue(self.endTime, origin, destination)*len(factorsInAList)
                for k, timeSlice in enumerate(newDemand._timePeriods):
                    tripsOD = factorsInAList[k]*tripsOD_Old
                    newDemand.setValue(timeSlice, origin, destination, tripsOD)
                               
        return newDemand                            

    def removeInvalidODPairs(self):
        """
        Examine all the OD interchanges and remove those for which 
        a path does not exist from origin to destination
        """
        
        for originId in self._centroidIds:
            for destinationId in self._centroidIds:
                for timeLabel in self._timeLabels:
                    if self.getValue(timeLabel, originId, destinationId) > 0:
                        origin = self._net.getNodeForId(originId)
                        destination = self._net.getNodeForId(destinationId)
                        if not hasPath(self._net, origin, destination):
                            self.setValue(timeLabel, originId, destinationId, 0) 
                        
    def getTotalNumTrips(self):
        """
        Return the total number of trips for all time periods
        """
        return self._demandTable.getSum() * self.timeStep.getMinutes() / 60.0


