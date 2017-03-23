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
import nose.tools
import os, sys
import getopt

from itertools import izip
import random

import dta
from dta import Path
from dta.Utils import Time

USAGE = r"""

 python test_path.py [-p downtown|geary|sf] dataFolder networkName
 
 e.g.  python test_path.py -p downtown dynameqNetwork_downtownSF sfDowntown
 """


dta.VehicleType.LENGTH_UNITS= "feet"
dta.Node.COORDINATE_UNITS   = "feet"
dta.RoadLink.LENGTH_UNITS   = "miles"

prefix        = "sfDowntown"
projectFolder = "dynameqNetwork_downtownSF"
path_list     = "downtown"

def test_paths(projectFolder, prefix, path_list):
    
    scenario = dta.DynameqScenario(Time(0,0), Time(12,0))
    scenario.read(projectFolder, prefix) 
    net = dta.DynameqNetwork(scenario) 
    net.read(projectFolder, prefix)
    
    TEST_PATHS = {"geary":[],
                  "downtown":[{"name" : "Mission St from 8th St to 1st St",
                               "street": "3rd St",
                               "from"  : "Folsom St",
                               "to"    : "Mission St",
                                "answer":[2150,9001847,9001848,9001871,9001872,2214]}],
                  }
                  
    TEST_PATHS["sf"] = TEST_PATHS["geary"] + TEST_PATHS["downtown"]
    
    paths = TEST_PATHS[path_list]
    
    for p in paths:
        intersection_list = [ [p["street"].upper(),p["from"].upper() ], [p["street"].upper(),p["to"].upper() ] ]
        
        testPath = Path.createPath(net, p["name"], intersection_list )
        testPathLinkList = [l.getId() for l in testPath.iterLinks()]
        print "CODE GOT :", testPathLinkList
        print "ANSWER IS:", p['answer']
        assert p['answer'] ==  testPathLinkList
               
if __name__ == '__main__':
    
    optlist, args = getopt.getopt(sys.argv[1:], "p:")

    if len(args) <= 1:
        print USAGE
        sys.exit(2)
    
    NET_DIR               = args[0] 
    DYNAMEQ_NET_PREFIX    = args[1]

    sim_results=None
    
    for (opt,arg) in optlist:
        if opt=="-s":
            sim_results=arg       
        if opt=="-p":
            path_list=arg.lower()                   

    testNetFolder = os.path.join(os.path.dirname(__file__), "..", "testdata", NET_DIR) 
    #net = getNet(testNetFolder, DYNAMEQ_NET_PREFIX, sim_results=sim_results)
    test_paths(testNetFolder, DYNAMEQ_NET_PREFIX, path_list)

        



