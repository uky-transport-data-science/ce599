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
from itertools import izip
import numpy as np

import dta
from dta.Logger import DtaLogger
from dta.Utils import Time
from dta.DtaError import DtaError 

class CountsVsVolumes(object):
    """
    Generates corridor plots.
    """
    
    def __init__(self, net, path, reverse):
        
        self._net = net
        self._path = path
        self._reverse = reverse
        
        self._intNames, self._intLocations = self._getIntersectionNamesAndLocations()
        
        self._linkCapacities = []
        self._leftTurnCapacities = []

    def _getIntersectionNamesAndLocations(self):
        """
        Return a list of intersection names and intersection locations
        """
        intLocationsAlongRoute = [0,]
        intNamesAlongRoute = [self._path.getCrossStreetName(self._path.getFirstNode()),] 
        length = 0
        for node, link in izip(self._path.iterNodes(), self._path.iterLinks()):
            length += (link.getLength() * 5280)
            intLocationsAlongRoute.append(length)
            intNamesAlongRoute.append(self._path.getCrossStreetName(node))
        return [intNamesAlongRoute, intLocationsAlongRoute]

    def _getIntersectionNamesAndLocationsInReverse(self):
        """
        
        """
        pass

    def getIntersectionNames(self):
        """
        Return a list of the intersection names along the route
        """
        return self._intNames

    def getIntersectionLocations(self):
        """
        Return a list of intersection locations along the route
        """
        return self._intLocations

    def getMidLinkLocations(self):
        """
        Return a list of link midpoint locations
        """
        result = []
        for loc1, loc2 in izip(self._intLocations, self._intLocations[1:]):
            result.append((loc1 + loc2) / 2.0)
        return result 
    
    def getVolumesAlongCorridor(self, startTimeInMin, endTimeInMin):
        """Generator method that returns the edge, leftTurn and right turn
        volumes for all the links on the route
        """
        linkOutVolumes = []
        linkInVolumes = []
        leftTurnVolumes = []
        rightTurnVolumes = []
        thruCapacities = []

        start = Time(startTimeInMin / 60, startTimeInMin % 60)
        end = Time(endTimeInMin / 60, endTimeInMin % 60)
        if self._net.hasPlanCollectionInfo(start, end):         
            planInfo = self._net.getPlanCollectionInfo(start, end)
        else:
            planInfo = None
         
        for edge in self._path.iterLinks():
            edgeVolume = edge.getSimOutVolume(startTimeInMin, endTimeInMin)
            edgeInVolume = edge.getSimInVolume(startTimeInMin, endTimeInMin)
            leftTurnVolume = 0
            rightTurnVolume = 0
            if edge.hasLeftTurn():
                leftTurn = edge.getLeftTurn()
                leftTurnVolume = leftTurn.getSimOutVolume(startTimeInMin, endTimeInMin)
            else:
                leftTurn = 0
            if edge.hasRightTurn():
                rightTurn = edge.getRightTurn()
                rightTurnVolume = rightTurn.getSimOutVolume(startTimeInMin, endTimeInMin)
            else:
                rightTurn = 0
            if edge.hasThruTurn() and planInfo:
                thruTurn = edge.getThruTurn()
                try: 
                    thruCapacity = thruTurn.getCapacity(planInfo=planInfo)
                except DtaError, e:
                    thruCapacity = 0
            else:
                thruCapacity = 0

            linkOutVolumes.append(edgeVolume)
            linkInVolumes.append(edgeInVolume)
            leftTurnVolumes.append(leftTurnVolume)
            rightTurnVolumes.append(rightTurnVolume)
            thruCapacities.append(thruCapacity)

        return linkOutVolumes, linkInVolumes, leftTurnVolumes, rightTurnVolumes, thruCapacities

    def getCountsAlongCorridor(self, startTimeInMin, endTimeInMin):
        """Generator method that returns the edge, left turn and right turn
        counts for the specified time window along the route
        """
        linkCounts = []
        leftTurnCounts = []
        rightTurnCounts = [] 
        for edge in self._path.iterLinks():
            edgeCount = None
            leftTurnCount = None
            rightTurnCount = None
            if edge.hasObsCount(startTimeInMin, endTimeInMin):
                edgeCount = edge.getObsCount(startTimeInMin, endTimeInMin)
            if edge.hasLeftTurn():
                leftTurn = edge.getLeftTurn()
                leftTurnCount = leftTurn.getObsCount(startTimeInMin, endTimeInMin)
            if edge.hasRightTurn():
                rightTurn = edge.getRightTurn()
                rightTurnCount = rightTurn.getObsCount(startTimeInMin, endTimeInMin)

            linkCounts.append(edgeCount)
            leftTurnCounts.append(leftTurnCount)
            rightTurnCounts.append(rightTurnCount)
            
        return linkCounts, leftTurnCounts, rightTurnCounts

    def getMovementVolumesCrossingCorridor(self, startTimeInMin, endTimeInMin):
        """
        Return the left and right turn volumes 
        """        
        ltVolumes = []
        rtVolumes = []
        for edge in self._path.iterLinks():
            leftTurnVolume = None
            rightTurnVolume = None
            for incidentMovement in edge.iterIncidentMovements():                
                movementVolume = incidentMovement.getSimOutVolume(startTimeInMin, endTimeInMin)
                if incidentMovement.isLeftTurn():
                    leftTurnVolume = movementVolume
                elif incidentMovement.isRightTurn():
                    rightTurnVolume = movementVolume

            if not leftTurnVolume:
                leftTurnVolume = 0
            if not rightTurnVolume:
                rightTurnVolume = 0
            ltVolumes.append(leftTurnVolume)
            rtVolumes.append(rightTurnVolume)
            
        return ltVolumes, rtVolumes 
    
    @classmethod
    def iterMovementCountsCrossingRoute(cls, route, startTimeInMin, endTimeInMin):
        """Generator method that yields the left turn and right turn counts
        on crossing links
        """
        for edge in route.iterEdges():
            leftTurnCount = None
            rightTurnCount = None
            for incidentMovement in edge.iterIncidentMovements():
                if incidentMovement.isLeftTurn():
                    leftTurnCount = incidentMovement.getObsCount(startTimeInMin, endTimeInMin)
                elif incidentMovement.isRightTurn():
                    rightTurnCount = incidentMovement.getObsCount(startTimeInMin, endTimeInMin)

            yield edge, leftTurnCount, rightTurnCount
    
    @classmethod
    def plotEdgeCountsAlongRoute(cls, plot, route, startTimeInMin, endTimeInMin, color):
        """
        Adds count information to the provided plot
        """
        countLocations = []
        counts = []

        for edge in route.iterEdges():
            if edge.getObsCount(startTimeInMin, endTimeInMin):
                counts.append(edge.getObsCount(startTimeInMin, endTimeInMin))
            else:
                counts.append(None)

            if countLocations:
                countLocations.append(countLocations[-1] + edge.getLengthInFeet())
            else:
                countLocations.append(edge.getLengthInFeet())

        countLocationsCleaned = []
        countsCleaned = []
        for countLocation, count in zip(countLocations, counts):
            if count:
                countLocationsCleaned.append(countLocation)
                countsCleaned.append(count)

        plot.scatter(countsCleaned, countLocationsCleaned, c=color)
        return plot
        
    @classmethod
    def plotEdgeVolumesAlongRoute(cls, route, startTimeInMin, endTimeInMin, color):
        """
        Creates a scatterplot with the Y axis representing edges along the route
        and the x axis representing volumes

        .. Note:: Requires `pylab <http://www.scipy.org/PyLab>`_ module.    
        """
        import pylab as plt 

        volumes = []
        for edge in route.iterEdges():
            if volumeLocations:
                volumeLocations.append(volumeLocations[-1] + edge.getLengthInFeet())
            else:
                volumeLocations.append(edge.getLengthInFeet())

            volumes.append(edge.getSimVolume(startTimeInMin, endTimeInMin))

        plt.clf()
        plt.cla()
        plt.figure(1)
        ax = plt.subplot(111)
        ax.scatter(volumes, volumeLocations, c=color)

        yticks = [loc for loc in volumeLocations]
        #yticks.insert(0, 0)
        ax.set_yticks(yticks)

        #ax.set_yticklabels(map(str, range(len(yticks))))
        ax.set_yticklabels(["" for i in range(len(yticks))])
        return ax

    def writeVolumesVsCounts(self, startTimeInMin, endTimeInMin, outPlotFileName, svg=False):
        """
        Export the corridor volume plot to the outPlotFileName. The volumes to be summarized are from
        startTime to endTime. 
        
        .. Note:: Requires `pylab <http://www.scipy.org/PyLab>`_ module.    
        """
        import pylab as plt 

        plt.clf()
        plt.cla()
        figure = plt.figure(1)
        figure.set_size_inches((25, 16))
        BAR_WIDTH = 25        

        ###################################
        ax = plt.subplot(313)
        speedAxis = ax.twinx()

        #par2.spines["right"].set_position(("axes", 1.2))
        #par2.spines["right"].set_visible(True)

        names = self.getIntersectionNames()
        del names[0]
        locations = np.array(self.getIntersectionLocations())
        linkOutVolumes, linkInVolumes, ltVolumes, rtVolumes, thruCapacities = self.getVolumesAlongCorridor(startTimeInMin, endTimeInMin)
        linkCounts, ltCounts, rtCounts = self.getCountsAlongCorridor(startTimeInMin, endTimeInMin)
        
        
        #linkCapacities, ltCapacities = self.getCapacitiesAlongCorridor(startTimeInMin, endTimeInMin) 

        #throuCapacities = [link.getCapacity(startTimeInMin, endTimeInMin) for link in self._path.iterLinks()]

        assert len(linkOutVolumes) == len(linkInVolumes) == len(ltVolumes) == len(rtVolumes) == len(locations) - 1
        
        #crossLtVolumes, crossRtVolumes = self.getMovementVolumesCrossingCorridor(0, 60) 
        ax.set_ylabel('Vehicles Per Hour')

        speedsAlongCorridor = [link.getSimSpeedInMPH(startTimeInMin, endTimeInMin) for link in self._path.iterLinks()]
        speedValuesToPlot = []
        
        valuesToPlot = []
        newLocations = []
        for i in range(len(linkOutVolumes)):
            newLocations.append(locations[i] + BAR_WIDTH)
            newLocations.append(locations[i + 1] - BAR_WIDTH)
            valuesToPlot.append(linkInVolumes[i])
            valuesToPlot.append(linkOutVolumes[i])
            speedValuesToPlot.append(speedsAlongCorridor[i])
            speedValuesToPlot.append(speedsAlongCorridor[i])
            
        p1, = ax.plot(newLocations, valuesToPlot, c='b', label="Link Volume")

        #plot the link count info
        linkCountLoc = self.getMidLinkLocations()
        linkCountsCleaned = []
        for lCountLoc, lCount in izip(linkCountLoc, linkCounts):
            if lCount != None:
                linkCountsCleaned.append((lCountLoc, lCount))

        if linkCountsCleaned:
            ax.scatter([elem[0] for elem in linkCountsCleaned],
                       [elem[1] for elem in linkCountsCleaned],
                       c="k")
        
        ax.set_xticks(locations)
        ax.set_xticklabels(names, rotation=90)
        ax.set_xlim(newLocations[0], newLocations[len(newLocations)-1])
        ax.set_ylim(0, int(max(valuesToPlot)) + 100)

        #ax.plot(newLocations[1:9], [400, 400, 500, 500, 400, 400, 500, 500], c="r", label="Capacities")
        #ax.plot(newLocations[1:3], [400, 400], c="r", label="Capacities")        
        #ax.plot(newLocations[3:5], [500, 500], c="r", label="Capacities")
        #ax.plot(newLocations[5:7], [400, 400], c="r", label="Capacities")
        #ax.plot(newLocations[7:9], [500, 500], c="r", label="Capacities")

        ax.grid(True)

        p2, = speedAxis.plot(newLocations, speedValuesToPlot, "g-", label="Link Speed")
        speedAxis.set_ylim(0, int(max(speedsAlongCorridor)) + 10)

        #ax.legend(loc=1)
        speedAxis.set_ylabel('Link Speeds (mph)')        
        ax.legend([p1, p2], [l.get_label() for l in [p1, p2]], loc=3)
        
        #############################

        ax = plt.subplot(312)

        linkCountsCleaned = []
        for lCountLoc, lCount in izip(locations[1:], ltCounts):
            if lCount != None:
                linkCountsCleaned.append((lCountLoc - BAR_WIDTH, lCount))

        if linkCountsCleaned:            
            ax.scatter([elem[0] for elem in linkCountsCleaned],
                       [elem[1] for elem in linkCountsCleaned],
                       c="k", marker="^", s=100)

        linkCountsCleaned = []
        for rCountLoc, rCount in izip(locations[1:], rtCounts):
            if rCount != None:
                linkCountsCleaned.append((rCountLoc + BAR_WIDTH, rCount))

        if linkCountsCleaned:            
            ax.scatter([elem[0] for elem in linkCountsCleaned],
                       [elem[1] for elem in linkCountsCleaned],
                       c="k", marker="s", s=100)
        
        ax.bar(locations[1:] - BAR_WIDTH, ltVolumes, width=BAR_WIDTH,bottom=0, color='r', label="LT Volumes Off")
        ax.bar(locations[1:], rtVolumes, width=BAR_WIDTH, bottom=0, color='y', label="RT Volumes Off")

        ax.set_xticks(locations)
        ax.set_xticklabels(["" for i in range(len(names))])
        ax.set_xlim(newLocations[0], newLocations[len(newLocations)-1])
        
        ax.legend(loc=2)
        y_upper1 = max(ltVolumes)
        y_upper2 = max(rtVolumes)
        y_upper = max(y_upper1,y_upper2)
        ax.set_ylim(0, int(y_upper)+10)
        ax.set_ylabel('Vehicles Per Hour')        

        #############################

        ax = plt.subplot(311)

        ltVolumes, rtVolumes = self.getMovementVolumesCrossingCorridor(startTimeInMin, endTimeInMin)       
        ax.bar(locations[1:] - BAR_WIDTH, ltVolumes, BAR_WIDTH, color='r', label="LT Volumes On")
        ax.bar(locations[1:], rtVolumes, BAR_WIDTH, color='y', label="RT Volumes On") 

        ax.set_xticks(locations)
        ax.set_xticklabels(["" for i in range(len(names))])
        ax.set_xlim(newLocations[0], newLocations[len(newLocations)-1])


        ax.legend(loc=2)
        y_upper1 = max(ltVolumes)
        y_upper2 = max(rtVolumes)
        y_upper = max(y_upper1,y_upper2)
        ax.set_ylim(0, int(y_upper)+10)
        ax.set_ylabel('Vehicles Per Hour')

        if not svg:
            plt.savefig(outPlotFileName)
        else:
            plt.savefig(outPlotFileName, format="svg")
    
        

