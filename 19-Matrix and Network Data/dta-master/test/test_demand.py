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

import dta
import os
import pdb
import random

import nose.tools 
import numpy as np

import dta
from dta.Demand import Demand
from dta.Utils import Time
from dta.DynameqNetwork import DynameqNetwork 
from dta.DynameqScenario import DynameqScenario 
from dta.Utils import Time, plotTripHistogram

dta.VehicleType.LENGTH_UNITS= "feet"
dta.Node.COORDINATE_UNITS   = "feet"
dta.RoadLink.LENGTH_UNITS   = "miles"

def getTestNet():

    projectFolder = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'dynameqNetwork_gearySubset')
    prefix = 'smallTestNet' 

    scenario = DynameqScenario(Time(0,0), Time(12,0))
    scenario.read(projectFolder, prefix) 
    #nose.tools.set_trace()

    dta.VehicleType.LENGTH_UNITS= "feet"
    dta.Node.COORDINATE_UNITS   = "feet"
    dta.RoadLink.LENGTH_UNITS   = "miles"
    
    net = DynameqNetwork(scenario) 
    net.read(projectFolder, prefix) 
    return net 


class TestDemand:

    def test_1getTimePeriods(self):

        net = getTestNet()

        startTime = Time(8, 30)
        endTime = Time(9, 30)
        timeStep = Time(0, 15)
        demand = Demand(net, "Default", startTime, endTime, timeStep)

        print [tp for tp in demand.iterTimePeriods()]
        
    def test_1read(self):
        
        fileName = os.path.join(os.path.dirname(__file__), '..', 'testdata', 
                                'dynameqNetwork_gearySubset', 'gearysubnet_matx.dqt')

        net = getTestNet() 

        demand = Demand.readDynameqTable(net, fileName)
        assert demand.getNumSlices() == 4

        assert demand.getValue(Time(0, 15), 56, 8) == 4000
        assert demand.getValue(Time(0, 45), 8, 2) == 34

        demand.setValue(Time(0, 45), 8, 2, 35)
        assert demand.getValue(Time(0, 45), 8, 2) == 35

        demand.setValue(Time(0, 15), 56, 8, 4001) 
        assert not demand.getValue(Time(0, 15), 56, 8) == 4000
        assert demand.getValue(Time(0, 15), 56, 8) == 4001

    def test_plotHistogram(self):
        
        fileName = os.path.join(os.path.dirname(__file__), '..', 'testdata', 
                                'dynameqNetwork_gearySubset', 'gearysubnet_matx.dqt')

        net = getTestNet() 
        demand = Demand.readDynameqTable(net, fileName)

        for startTime in range(0, 45, 15):
            for o in net.iterCentroids():
                for d in net.iterCentroids():
                    demand.setValue(Time(0, startTime + 15), o.getId(), d.getId(), random.random() * 10) 

        _npyArray = demand._demandTable.getNumpyArray()
            
        plotTripHistogram(_npyArray, "tripHistogram") 
            
    def test_write(self):
        """
        """

        fileName = os.path.join(os.path.dirname(__file__), '..', 'testdata', 
                                'dynameqNetwork_gearySubset', 'gearysubnet_matx.dqt')

        net = getTestNet() 
        demand = Demand.readDynameqTable(net, fileName)

        # TODO: this requires subdir test to exist.  Write this to tempfile.mkdtemp()
        outFileName = "test/testDemand.dqt" 

        demand.writeDynameqTable(outFileName)
        demand2 = Demand.readDynameqTable(net, outFileName)
        assert demand == demand2
        os.remove("test/testDemand.dqt")

    def test_readCubeDemand(self):

        fileName = os.path.join(os.path.dirname(__file__), '..', 'testdata', 
                                'dynameqNetwork_gearySubset', 'cubeTestDemand.txt')
        
        net = getTestNet()

        demand = Demand.readCubeODTable(fileName, net, "AUTO", Time(7,0), Time(8, 0))
                                     
        assert demand.getValue(Time(8, 0), 2, 6) == 1000
        assert demand.getValue(Time(8, 0), 6, 2) == 4000

    def NOtest_applyTimeOfDayFactors(self):

        fileName = os.path.join(os.path.dirname(__file__), '..', 'testdata', 
                                'dynameqNetwork_gearySubset', 'cubeTestDemand.txt')
        
        net = getTestNet()
        demand = Demand.readCubeODTable(fileName, net, "AUTO", Time(7,0), Time(8, 0))
                                     
        d2 = demand.applyTimeOfDayFactors([0.5, 0.5])

        assert d2.getValue(730, 2, 6) == 500
        assert d2.getValue(800, 2, 6) == 500

    def NOtest_rounding(self):
        """
        This method writes histograms of the input demand and can be
        used to check the differences of the row and column sums
        for two matrices
        """
        projectFolder = "/Users/michalis/Documents/sfcta/testNetworks"
        projectFolder = "/Users/michalis/Documents/sfcta/05252012/" 
        prefix = "sfCounty_lisa"
        prefix = "SF_Test_wSig_5_100pct_NetworkReview"
        scenario = DynameqScenario(Time(0,0), Time(12,0))
        scenario.read(projectFolder, prefix)
        
        net = DynameqNetwork(scenario)
        net.read(projectFolder, prefix) 

        file1 = "/Users/michalis/Documents/sfcta/05252012/car_notoll_matx.dqt"
        demand1 = Demand.readDynameqTable(net, file1)
        _npyArray1 = demand1._demandTable.getNumpyArray() * 3 
        file2 = "/Users/michalis/Documents/sfcta/05252012/vehcountorig_Car_NoToll_matx.dqt"
        demand2 = Demand.readDynameqTable(net, file2)
        pdb.set_trace()
        _npyArray1 = _npyArray1.sum(0)
        _npyArray2 = demand2._demandTable.getNumpyArray().sum(0)

        pdb.set_trace()
        
        plotTripHistogram(_npyArray1, "carNoTollHistogram1")
        plotTripHistogram(_npyArray2, "carNoTollHistogram2")        



        

        
        

