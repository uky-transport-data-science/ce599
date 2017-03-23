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
import os

from itertools import izip
import random

import dta
from dta.Utils import Time
from dta.PhaseMovement import PhaseMovement 

dta.VehicleType.LENGTH_UNITS= "feet"
dta.Node.COORDINATE_UNITS   = "feet"
dta.RoadLink.LENGTH_UNITS   = "miles"

mainFolder = os.path.join(os.path.dirname(__file__), "..", "testdata") 

def getGearySubNet():

    projectFolder = os.path.join(mainFolder, 'dynameqNetwork_gearySubset')
    prefix = 'smallTestNet' 

    scenario = dta.DynameqScenario(dta.Time(0,0), dta.Time(12,0))
    scenario.read(projectFolder, prefix) 
    net = dta.DynameqNetwork(scenario) 
    net.read(projectFolder, prefix)

    simStartTimeInMin = 0
    simEndTimeInMin = 60
    simTimeStepInMin = 15
    
    net._simStartTimeInMin = simStartTimeInMin
    net._simEndTimeInMin = simEndTimeInMin
    net._simTimeStepInMin = simTimeStepInMin

    for link in net.iterLinks():
        if link.isVirtualLink():
            continue
        link.simTimeStepInMin = simTimeStepInMin
        link.simStartTimeInMin = simStartTimeInMin
        link.simEndTimeInMin = simEndTimeInMin
        for mov in link.iterOutgoingMovements():
            mov.simTimeStepInMin = simTimeStepInMin
            mov.simStartTimeInMin = simStartTimeInMin
            mov.simEndTimeInMin = simEndTimeInMin

    for link in net.iterLinks():
        if link.isVirtualLink():
            continue
        if link.isConnector():
            continue
        link._label  = str(link.getId())

        link.setObsCount(0, 60, random.randint(150, 450))
        
        for mov in link.iterOutgoingMovements():
            
            mov.setObsCount(0, 60, random.randint(50, 150))
            
            for start, end in izip(range(0, 60, 15), range(15, 61, 15)):
                mov.setSimOutVolume(start, end, random.randint(20, 50))
                mov.setSimInVolume(start, end, random.randint(20, 50))
                mov.cost = link.euclideanLength()
                randInt = random.randint(2,4) 
                tt = mov.getFreeFlowTTInMin() * float(randInt)
                mov.setSimTTInMin(start, end, tt)

    
    return net 

#def getTestNet():
#
#
#    projectFolder = "/Users/michalis/Documents/sfcta/ASCIIFiles"
#    prefix = 'Base'
#
#    scenario = dta.DynameqScenario(dta.Time(0,0), dta.Time(12,0))
#    scenario.read(projectFolder, prefix) 
#    net = dta.DynameqNetwork(scenario) 
#    net.read(projectFolder, prefix) 
#    return net 

class TestCorridorPlots:

    def test_volumes(self):

        net = getGearySubNet()
        
        net.addPlanCollectionInfo(Time(7, 0), Time(9, 0), "test1", "test1")
        pi = net.getPlanCollectionInfo(Time(7, 0), Time(9, 0))

        node = net.getNodeForId(25956)
                
        for link in node.iterIncomingLinks():
            for mov in link.iterOutgoingMovements(): 
                if mov.isUTurn():
                    link.prohibitOutgoingMovement(mov) 
                    
                
        tp = dta.TimePlan(node, 0, pi)
        p1 = dta.Phase(tp, 40, 3, 2)
        p1Movs = [mov for mov in net.getLinkForId(101674).iterOutgoingMovements()]
        p1Movs.extend([mov for mov in net.getLinkForId(14597).iterOutgoingMovements()])

        for mov in p1Movs:
            
            pMov = PhaseMovement(mov, 1)
            if pMov.getMovement().isUTurn():
                continue
            if mov.isLeftTurn():
                pMov.setPermitted() 
            p1.addPhaseMovement(pMov)

        p2 = dta.Phase(tp, 40, 3, 2) 
        p2Movs = [mov for mov in net.getLinkForId(14620).iterOutgoingMovements()]
        p2Movs.extend([mov for mov in net.getLinkForId(14582).iterOutgoingMovements()])

        for mov in p2Movs:
            pMov = PhaseMovement(mov, 1)
            if pMov.getMovement().isUTurn():
                continue 
            if mov.isLeftTurn():
                pMov.setPermitted()
            p2.addPhaseMovement(pMov)


        tp.addPhase(p1)
        tp.addPhase(p2)

        node.addTimePlan(tp)

        mov = net.getLinkForId(101674).getOutgoingMovement(25958)
        mov.getProtectedCapacity(planInfo=pi) 
        
        net.writeLinksToShp("gearySubnet_links")
        net.writeNodesToShp("gearySubnet_nodes")
        
        link1 = net.getLinkForId(14834)
        link2 = net.getLinkForId(14539)
        
        pathLinks = dta.Algorithms.ShortestPaths.getShortestPathBetweenLinks(net, link1, link2, runSP=True)

        path = dta.Path(net, "test", pathLinks)
        print [link.getId() for link in pathLinks]
        volumesVsCounts = dta.CorridorPlots.CountsVsVolumes(net, path, False)
        #VC = VolumesVsCounts(net, path, False)

        names = volumesVsCounts.getIntersectionNames()
        locations = volumesVsCounts.getIntersectionLocations()
        volumes = volumesVsCounts.getVolumesAlongCorridor(0, 60)

        volumes2 = volumesVsCounts.getMovementVolumesCrossingCorridor(0, 60)

        print volumes2
        
        print "names=", volumesVsCounts.getIntersectionNames()
        print "locations=", volumesVsCounts.getIntersectionLocations()

        print "volumes=", volumesVsCounts.getVolumesAlongCorridor(0, 60)
        volumesVsCounts.writeVolumesVsCounts(0, 60, 'testplot2')

        
        
        

        



