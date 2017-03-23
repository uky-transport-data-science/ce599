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
import os
import pdb
import datetime
import difflib 

import dta 
from dta.Scenario import Scenario
from dta.DynameqScenario import DynameqScenario 
from dta.Network import Network
from dta.DtaError import DtaError 
from dta.DynameqNetwork import DynameqNetwork 
from dta.TimePlan import TimePlan
from dta.Utils import Time

projectFolder = os.path.join(os.path.dirname(__file__), '..', 'testdata', 'dynameqNetwork_gearySubset')

dta.VehicleType.LENGTH_UNITS= "feet"
dta.Node.COORDINATE_UNITS   = "feet"
dta.RoadLink.LENGTH_UNITS   = "miles"


mainFolder = os.path.join(os.path.dirname(__file__), "..", "testdata") 
projectFolder = os.path.join(mainFolder, 'dynameqNetwork_gearySubset')

def getTestScenario(): 

    
    prefix = 'smallTestNet' 

    scenario = DynameqScenario(Time(0,0), Time(12,0))
    scenario.read(projectFolder, prefix) 

    return scenario

def getGearySubNet():

    projectFolder = os.path.join(mainFolder, 'dynameqNetwork_gearySubset')
    prefix = 'smallTestNet' 

    scenario = DynameqScenario(Time(0,0), Time(12,0))
    scenario.read(projectFolder, prefix) 
    net = DynameqNetwork(scenario) 
    net.read(projectFolder, prefix) 
    return net 


class TestControl:

    def test_one(self):

        #net = getTestScenario()
        net = getGearySubNet() 


        #pdb.set_trace() 

        # TODO: write the test output file to a tempfile.mkdtemp()

        net.write(dir=projectFolder, file_prefix="Test")

        #The following code finds the differences between the two control files the original and
        #the one created by the code 
        fileName = os.path.join(os.path.dirname(__file__), "..", "testdata", 'dynameqNetwork_gearySubset', "smallTestNet_ctrl.dqt") 
        originalFile = os.path.join(fileName)
        copyFile = os.path.join(projectFolder, "Test_ctrl.dqt")
        original = open(fileName, "r").readlines()
        copy = open(copyFile, "r").readlines()
        original.pop(3) # this line has the dta anyway title 
        copy.pop(3) # this line has the dta anyway title 
        if original != copy:
            htmldiff = difflib.HtmlDiff()
            diff = htmldiff.make_file(original, copy)
            output = open("ctrl_diff.html", "w")
            output.write(diff)
            output.close()
                
        assert original == copy
