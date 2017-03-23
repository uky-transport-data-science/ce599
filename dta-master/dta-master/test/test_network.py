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
import math
import difflib 
import os
import shutil

from itertools import izip 

import dta
from dta.Scenario import Scenario
from dta.DynameqScenario import DynameqScenario 
from dta.Network import Network
from dta.Node import Node
from dta.RoadNode import RoadNode
from dta.RoadLink import RoadLink
from dta.Centroid import Centroid
from dta.Link import Link
from dta.VirtualLink import VirtualLink
from dta.Movement import Movement 
from dta.VirtualNode import VirtualNode
from dta.Connector import Connector
from dta.VehicleClassGroup import VehicleClassGroup
from dta.DtaError import DtaError 
from dta.DynameqNetwork import DynameqNetwork 
from dta.Utils import lineSegmentsCross
from dta.Utils import Time

dta.VehicleType.LENGTH_UNITS= "feet"
dta.Node.COORDINATE_UNITS   = "feet"
dta.RoadLink.LENGTH_UNITS   = "miles"

mainFolder = os.path.join(os.path.dirname(__file__), "..", "testdata") 

def getTestScenario(): 

    projectFolder = os.path.join(mainFolder, 'dynameqNetwork_gearySubset')
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

def getCubeSubarea():

    projectFolder = os.path.join(mainFolder, 'cubeSubarea_downtownSF/dynameqNetwork')
    prefix = 'sf' 

    scenario = DynameqScenario(Time(0,0), Time(12,0))
    scenario.read(projectFolder, prefix) 
    net = DynameqNetwork(scenario) 
    net.read(projectFolder, prefix) 

    return net 

def getDowntownSF():

    projectFolder = os.path.join(mainFolder, 'dynameqNetwork_downtownSF')
    prefix = 'sfDowntown' 

    scenario = DynameqScenario(Time(0,0), Time(12,0))
    scenario.read(projectFolder, prefix) 
    net = DynameqNetwork(scenario) 
    net.read(projectFolder, prefix) 

    return net

def getCubeSubarea():

    projectFolder = os.path.join(mainFolder, 'cubeSubarea_downtownSF/dynameqNetwork')
    prefix = 'sf' 

    scenario = DynameqScenario(Time(0,0), Time(12,0))
    scenario.read(projectFolder, prefix) 
    net = DynameqNetwork(scenario) 
    net.read(projectFolder, prefix) 

    return net 

def simpleRoadNodeFactory(id_, x, y):

    rn = RoadNode(id_,
                  x,
                  y,
                  Node.GEOMETRY_TYPE_INTERSECTION,
                  RoadNode.CONTROL_TYPE_UNSIGNALIZED, 
                  RoadNode.PRIORITY_TEMPLATE_NONE)

    return rn

def simpleRoadLinkFactory(id_, startNode, endNode):

    length = math.sqrt((endNode.getX()  - startNode.getX()) ** 2 + (endNode.getY() - startNode.getY()) ** 2)
    length = length / 5280.0

    return RoadLink(id_, startNode, endNode,
                    None, 0, length, 30, 1.0, 1.0, 3,
                    0, 0, "", id_)

def simpleConnectorFactory(id_, startNode, endNode):

    length = math.sqrt((endNode.getX()  - startNode.getX()) ** 2 + (endNode.getY() - startNode.getY()) ** 2)

    length = length / 5280.0    
    return Connector(id_, startNode, endNode,
                    None, length, 30, 1.0, 1.0, 3,
                    0, 0, "", id_)

def simpleVirtualLinkFactory(id_, startNode, endNode):

    return VirtualLink(id_, startNode, endNode, "")

def simpleMovementFactory(incomingLink, outgoingLink):

    mov = Movement(incomingLink.getEndNode(),
                   incomingLink,
                   outgoingLink,
                   30,
                   VehicleClassGroup("all", "-", "#ffff00"))

    return mov                                                                                           

def getSimpleNet():


    sc = getTestScenario() 
    net = DynameqNetwork(sc)
    
    v1 = simpleRoadNodeFactory(1, 0,   100)
    v2 = simpleRoadNodeFactory(2, 100, 200)
    v3 = simpleRoadNodeFactory(3, 100, 0)
    v4 = simpleRoadNodeFactory(4, 200, 100)
    v5 = simpleRoadNodeFactory(5, 100, 100)
    v6 = simpleRoadNodeFactory(6, 200, 200)
    v7 = simpleRoadNodeFactory(7, 300, 100)
    v8 = simpleRoadNodeFactory(8, 200, 0)

    net.addNode(v1)
    net.addNode(v2)
    net.addNode(v3)
    net.addNode(v4)
    net.addNode(v5)
    net.addNode(v6)
    net.addNode(v7)
    net.addNode(v8) 

#
#                2         6
#                |         |
#                |         |
#      1 ------- 5 ------- 4 -------- 7
#                |         |
#                |         |
#                |         |
#                3         8
#


    e15 = simpleRoadLinkFactory(1, v1, v5)
    e51 = simpleRoadLinkFactory(2, v5, v1)
    e35 = simpleRoadLinkFactory(3, v3, v5)
    e53 = simpleRoadLinkFactory(4, v5, v3)
    e45 = simpleRoadLinkFactory(5, v4, v5)
    e54 = simpleRoadLinkFactory(6, v5, v4)
    e52 = simpleRoadLinkFactory(7, v5, v2)
    e25 = simpleRoadLinkFactory(8, v2, v5)

    e48 = simpleRoadLinkFactory(9, v4, v8)
    e84 = simpleRoadLinkFactory(10, v8, v4)
    e74 = simpleRoadLinkFactory(11, v7, v4)
    e47 = simpleRoadLinkFactory(12, v4, v7)
    e46 = simpleRoadLinkFactory(13, v4, v6)
    e64 = simpleRoadLinkFactory(14, v6, v4)

    links = [e15, e51, e35, e53, e45, e54, e52, e25, e48, e84, e74, e47, 
             e46, e64]

    net.addLink(e15)
    net.addLink(e51)
    net.addLink(e35)
    net.addLink(e53)
    net.addLink(e45)
    net.addLink(e54)
    net.addLink(e52)
    net.addLink(e25)
    net.addLink(e48)
    net.addLink(e84)
    net.addLink(e74)
    net.addLink(e47)
    net.addLink(e46)
    net.addLink(e64)

    #net.checkAdjacentNodesExist()
    #net.checkAdjacentLinksExist() 

    return net

def addAllMovements(net):
    
    for node in net.iterNodes():
        for incomingLink in node.iterIncomingLinks():
            for outgoingLink in node.iterOutgoingLinks():
                    mov = simpleMovementFactory(incomingLink, outgoingLink)
                    incomingLink.addOutgoingMovement(mov) 

class TestNetwork(object):

    def test_1iterPlanInfo(self):

        net = getSimpleNet()
        net.addPlanCollectionInfo(Time(7, 0), Time(9, 0), "test1", "test1")
        net.addPlanCollectionInfo(Time(6, 0), Time(8, 0), "test2", "test2")

        for pInfo in net.iterPlanCollectionInfo():
            pInfo

    def test_getPlanInfo(self):

        net = getSimpleNet()
        net.addPlanCollectionInfo(Time(7, 0), Time(9, 0), "test1", "test1")

        pi = net.getPlanCollectionInfo(Time(7, 0), Time(9, 0))

        start, end = pi.getTimePeriod()
        assert start.getMinutes() == 7 * 60
        assert end.getMinutes() == 9 * 60 
              
    def test_1getNum(self):

        net = getSimpleNet() 
        assert net.getNumNodes() == 8
        assert net.getNumLinks() == 14

        assert net.getNumRoadNodes() == 8
        assert net.getNumCentroids() == 0
        assert net.getNumVirtualNodes() == 0

    def test_2hasMethods(self):

        net = getSimpleNet()
        assert net.hasNodeForId(1)
        #assert not net.hasNodeForId("1")
        assert not net.hasNodeForId(-1)

        assert net.hasLinkForId(1)
        #assert not net.hasLinkForId("1")

        assert net.hasLinkForNodeIdPair(1, 5)
        assert not net.hasLinkForNodeIdPair(1, 4)

            

    def NOtest_3addMovements(self):

        net = getSimpleNet()
        mov = simpleMovementFactory(net.getLinkForNodeIdPair(1, 5),
                                       net.getLinkForNodeIdPair(5, 2))

        link_15 = net.getLinkForNodeIdPair(1, 5)
        link_51 = net.getLinkForNodeIdPair(5, 1)

        #nose.tools.assert_raises(DtaError, link_51.addOutgoingMovement, "")


        #add the movement to a different link 
        #nose.tools.assert_raises(DtaError, link_51.addOutgoingMovement, mov)

        

        
        link_15.addOutgoingMovement(mov)
        assert link_15.getNumOutgoingMovements() == 1

        #add the movement twice 
        nose.tools.assert_raises(DtaError, link_15.addOutgoingMovement, mov)

    def test_4removeMovement(self):

        net = getSimpleNet()
        mov = simpleMovementFactory(net.getLinkForNodeIdPair(1, 5),
                                       net.getLinkForNodeIdPair(5, 2))

        link_15 = net.getLinkForNodeIdPair(1, 5)
        link_51 = net.getLinkForNodeIdPair(5, 1)
        link_52 = net.getLinkForNodeIdPair(5, 2)

        link_15.addOutgoingMovement(mov)
        assert link_15.getNumOutgoingMovements() == 1

        assert link_52.getNumIncomingMovements() == 1

        nose.tools.assert_raises(DtaError, link_51._removeOutgoingMovement, mov)
        
        link_15._removeOutgoingMovement(mov)
        assert link_15.getNumOutgoingMovements() == 0
        assert link_52.getNumIncomingMovements() == 0

        #net.checkAdjacentNodesExist()
        #net.checkAdjacentLinksExist() 

    def test_5node_has(self):

        net = getSimpleNet()
        #link_15 = net.getLinkForNodeIdPair(1, 5)

        n = net.getNodeForId(5)
        assert n.hasIncomingLinkForNodeId(1)
        assert n.hasIncomingLinkForNodeId(4)
        assert n.hasIncomingLinkForNodeId(3)
        assert not n.hasIncomingLinkForNodeId(5)

        assert n.hasOutgoingLinkForNodeId(1)
        assert n.hasOutgoingLinkForNodeId(4)
        assert n.hasOutgoingLinkForNodeId(3)
        assert not n.hasOutgoingLinkForNodeId(18)
        

    def test_6removeLink(self):

        net = getSimpleNet()
        link_15 = net.getLinkForNodeIdPair(1, 5)

        assert net.hasLinkForNodeIdPair(1, 5)
        assert net.getNumLinks() == 14        
        net.removeLink(link_15) 
    
        assert not net.hasLinkForNodeIdPair(1, 5) 
        assert net.getNumLinks() == 13

        #net.checkAdjacentNodesExist()
        #net.checkAdjacentLinksExist() 
        
    def NOtest_7removeLink2(self):

        net = getSimpleNet()
        addAllMovements(net)

        link_15 = net.getLinkForNodeIdPair(1, 5)
        link_51 = net.getLinkForNodeIdPair(5, 1)
        link_52 = net.getLinkForNodeIdPair(5, 2)

        assert link_15.hasOutgoingMovement(2)
        assert link_15.hasOutgoingMovement(4)
        assert link_15.hasOutgoingMovement(3)

        #net.checkAdjacentNodesExist()
        #net.checkAdjacentLinksExist() 

    def test_removeConnector(self):

        net = getSimpleNet()
        
        vn = VirtualNode(9, 0, 200) 
        n5 = net.getNodeForId(5) 

        net.addNode(vn) 
        con = simpleConnectorFactory(15, vn, n5)
        con2 = simpleConnectorFactory(16, n5, vn) 

        net.addLink(con)
        net.addLink(con2)
        assert net.getNumLinks() == 16

        assert n5.getNumAdjacentLinks() == 10 
        assert n5.getNumAdjacentNodes() == 5

        net.removeLink(con) 
        assert net.getNumLinks() == 15
        net.removeLink(con2)
        assert net.getNumLinks() == 14

        assert n5.getNumAdjacentLinks() == 8 
        assert n5.getNumAdjacentNodes() == 4

        #net.checkAdjacentNodesExist()
        #net.checkAdjacentLinksExist() 

    def test_8removeNode(self):

        net = getSimpleNet()
        addAllMovements(net)

        n = net.getNodeForId(5)
        net.removeNode(n)

        assert not net.hasNodeForId(5)
        assert net.getNumNodes() == 7
        assert not net.hasLinkForNodeIdPair(1, 5)
        assert not net.hasLinkForNodeIdPair(5, 2)

        #net.checkAdjacentNodesExist()
        #net.checkAdjacentLinksExist() 
        
    def NOtest_9splitLink(self):

        net = getSimpleNet()
        addAllMovements(net)

        l = net.getLinkForNodeIdPair(1, 5)

        assert net.getNumNodes() == 8 
        assert net.getNumLinks() == 14

        net.splitLink(l, splitReverseLink=True) 

        assert net.getNumNodes() == 9
        assert net.getNumLinks() == 16

        link1 = net.getLinkForNodeIdPair(1, 9) 
        link2 = net.getLinkForNodeIdPair(9, 5) 


        assert link1.hasOutgoingMovement(5)
        assert link2.hasOutgoingMovement(2) 
        assert link2.hasOutgoingMovement(4)
        assert link2.hasOutgoingMovement(3)
    
    def test_10link_getCenterline(self):

        net = getSimpleNet()

        link = net.getLinkForNodeIdPair(1, 5) 

        link.getLength()
        
        assert link.getCenterLine() == ((0.0, 82.0), (100.0, 82.0))

        link = net.getLinkForNodeIdPair(3, 5) 
        
        assert link.getCenterLine() == ((118.0, 0.0), (118.0, 100.0))

    def test_11link_lineSegmentsIntersect(self):

        net = getSimpleNet() 

        link51 = net.getLinkForNodeIdPair(5, 1) 
        p1, p2 = link51.getCenterLine() 

        link25 = net.getLinkForNodeIdPair(2, 5) 
        p3, p4 = link25.getCenterLine() 

        assert lineSegmentsCross(p1, p2, p3, p4)

        link15 = net.getLinkForNodeIdPair(1, 5) 
        p5, p6 = link15.getCenterLine()

        assert not lineSegmentsCross(p5, p6, p3, p4)
        assert not lineSegmentsCross(p3, p4, p5, p6)

        p7 = (50, 0)
        p8 = (50, 100 - 18) 
    
        assert not lineSegmentsCross(p7, p8, p5, p6)

        p9 = (50, 0)
        p10 = (50, 100 - 17) 

        assert lineSegmentsCross(p9, p10, p5, p6)

    def test_12getNumAdjacentNodesAndLinks(self):

        net = getSimpleNet() 

        n5 = net.getNodeForId(5) 

        assert n5.getNumAdjacentLinks() == 8
        assert n5.getNumAdjacentNodes() == 4

        n1 = net.getNodeForId(1) 

        link51 = net.getLinkForNodeIdPair(5, 1) 

        assert not link51.hasOutgoingMovement(5) 

        assert n1.getNumAdjacentLinks() == 2
        assert n1.getNumAdjacentNodes() == 1

    def test_13isMidblockNode(self):

        net = getSimpleNet() 

        n5 = net.getNodeForId(5) 
        n1 = net.getNodeForId(1) 
        assert not n5.isMidblockNode() 
        assert not n1.isMidblockNode()

        link15 = net.getLinkForNodeIdPair(1, 5) 

        midNode = net.splitLink(link15, splitReverseLink=True) 

        assert midNode.isMidblockNode()

        net = getGearySubNet() 

    def test_hasConnector(self):

        net = getSimpleNet()

        n5 = net.getNodeForId(5) 

        assert not n5.hasConnector()
        
        vn = VirtualNode(9, 0, 200) 

        net.addNode(vn) 
        assert isinstance(n5, RoadNode) 
        assert isinstance(vn, VirtualNode)
        con = simpleConnectorFactory(15, vn, n5)

        net.addLink(con)
        assert net.getNumLinks() == 15 

        assert n5.hasConnector()

        #net.checkAdjacentNodesExist()
        #net.checkAdjacentLinksExist() 

    def test_getCandidateLinks(self):

        net = getSimpleNet()
        n5 = net.getNodeForId(5) 

        assert not n5.hasConnector()
        
        vn = VirtualNode(9, 0, 200) 

        net.addNode(vn) 
        con = simpleConnectorFactory(15, vn, n5)
        con2 = simpleConnectorFactory(16, n5, vn) 

        net.addLink(con)
        net.addLink(con2)
        assert net.getNumLinks() == 16

        assert n5.hasConnector()

        clinks = n5.getCandidateLinksForSplitting(con) 
        assert len(clinks) == 2
        assert 2 in [link.getId() for link in clinks]
        assert 8 in [link.getId() for link in clinks]

        clinks = n5.getCandidateLinksForSplitting(con2) 
        assert len(clinks) == 2
        assert 2 in [link.getId() for link in clinks]
        assert 8 in [link.getId() for link in clinks]

    def NOtest_removeConnectorFromIntersection(self):
        
        net = getSimpleNet()
        n5 = net.getNodeForId(5) 

        assert not n5.hasConnector()
        
        vn = VirtualNode(9, 0, 200) 
        cen = Centroid(10, 0, 200)
        
        net.addNode(vn)
        net.addNode(cen)
        
        con = simpleConnectorFactory(15, vn, n5)
        con2 = simpleConnectorFactory(16, n5, vn) 

        vl1 = simpleVirtualLinkFactory(17, cen, vn)
        vl2 = simpleVirtualLinkFactory(18, vn, cen) 
        net.addLink(vl1)
        net.addLink(vl2)

        pdb.set_trace()
        
        net.addLink(con)
        net.addLink(con2)
        assert net.getNumLinks() == 16
        
        
        assert net.getNumLinks() == 16
        assert n5.hasConnector()
        #this is the connector to be removed 
        assert net.hasLinkForNodeIdPair(9, 5) 
        assert net.hasLinkForNodeIdPair(5, 9)
        assert net.hasLinkForId(15) 
        assert net.hasLinkForId(16)

        newConnector = net.removeCentroidConnectorFromIntersection(n5, con, splitReverseLink=False) 
        #the old connector is no longer there 
        assert not net.hasLinkForNodeIdPair(9, 5) 
        #but a connector with the same id is attached to newly created midblock 
        assert net.hasLinkForId(15) 
        assert net.getNumLinks() == 17  #one more link than before
        assert net.getNumNodes() == 10  #one more node than before 

        assert n5.hasConnector()         #there is still one connector at intersection 5 
        newConnector.getRoadNode().getX(), newConnector.getRoadNode().getY()
        assert newConnector.getRoadNode().isMidblockNode(countRoadNodesOnly=True) 

        newConnector2 = net.removeCentroidConnectorFromIntersection(n5, con2, splitReverseLink=True)
        #the old connector is no longer there
        assert not net.hasLinkForNodeIdPair(5, 9)
        #a new connector is there with the same id 
        assert net.hasLinkForId(16)
        assert net.getNumLinks() == 17  #same links as before the algorithm picked the newly created block 
        assert net.getNumNodes() == 10  #same nodes as before. No new link was split


        #net.checkAdjacentNodesExist()
        #net.checkAdjacentLinksExist() 
        
    def test_removeAllCentroidConnectorsFromIntersections(self):
        
        net = getSimpleNet()
        n5 = net.getNodeForId(5) 

        assert not n5.hasConnector()
        
        vn = VirtualNode(9, 0, 200) 
        cen = Centroid(10, 0, 200)
        
        net.addNode(vn)
        net.addNode(cen)
        
        con = simpleConnectorFactory(15, vn, n5)
        con2 = simpleConnectorFactory(16, n5, vn) 

        net.addLink(con)
        net.addLink(con2)

        vl1 = simpleVirtualLinkFactory(17, cen, vn)
        vl2 = simpleVirtualLinkFactory(18, vn, cen) 
        net.addLink(vl1)
        net.addLink(vl2)
        
        assert n5.hasConnector()
        #this is the connector to be removed 
        assert net.hasLinkForNodeIdPair(9, 5) 
        assert net.hasLinkForNodeIdPair(5, 9)
        assert net.hasLinkForId(15) 
        assert net.hasLinkForId(16)

        assert net.getNumConnectors() == 2 

        assert net.getNumNodes() == 10
        assert net.getNumLinks() == 18

        net.moveCentroidConnectorsFromIntersectionsToMidblocks(splitReverseLinks=True)
        #net.removeCentroidConnectorFromIntersection(n5, con, splitReverseLink=True)

        assert net.getNumNodes() == 11
        assert net.getNumLinks() == 20

        #the connectors have been removed from the intersection 
        assert not net.hasLinkForNodeIdPair(9, 5) 
        assert not net.hasLinkForNodeIdPair(5, 9)
        assert net.getNumConnectors() == 2 

        assert net.hasLinkForId(15) 
        assert net.hasLinkForId(16)
        
        assert not n5.hasConnector()         #there is no connector at intersection 5

    def test_insertVirtualNodes(self):
 
        net = getSimpleNet()
        n5 = net.getNodeForId(5) 

        assert not n5.hasConnector()
        
        centroid = Centroid(9, 0, 200) 
        net.addNode(centroid) 
        
        con = simpleConnectorFactory(15, centroid, n5)
        con2 = simpleConnectorFactory(16, n5, centroid) 

        net.addLink(con)
        net.addLink(con2)
    
        #net.moveCentroidConnectorsFromIntersectionsToMidblocks() 
        
        numLinksBefore = net.getNumLinks() 
        net.insertVirtualNodeBetweenCentroidsAndRoadNodes()
        net.write("test", "test") 
        assert numLinksBefore + 2 == net.getNumLinks()         

        scenario = getTestScenario() 
        
        net = DynameqNetwork(scenario) 
        net.read("test", "test") 


    def test_readScenario(self):

        net = getGearySubNet()
        projectFolder = os.path.join(mainFolder, 'dynameqNetwork_gearySubset')

        prefix = 'smallTestNet' 
        sc = DynameqScenario(Time(0,0), Time(12,0))
        sc.read(projectFolder, prefix) 
        
        assert 'All' in sc.vehicleClassGroups.keys() 
        assert 'Transit' in sc.vehicleClassGroups.keys() 
        assert 'Prohibited' in sc.vehicleClassGroups.keys() 

    def test_readDynameqNetwork(self):

        net = getGearySubNet()

        assert net.getNumNodes() == 299 
        assert  net.getNumLinks() == 560

    def test_writeDynameqNetwork(self): 

        projectFolder = os.path.join(mainFolder, 'dynameqNetwork_gearySubset')        
        net = getGearySubNet()

        before = (net.getNumNodes(), net.getNumRoadNodes(), net.getNumCentroids(), net.getNumVirtualNodes(),
                  net.getNumLinks(), net.getNumRoadLinks(), net.getNumConnectors(), net.getNumVirtualLinks())

        os.mkdir(os.path.join(mainFolder, 'dynameqNetwork_gearySubset_copy'))

        net.write(os.path.join(mainFolder, 'dynameqNetwork_gearySubset_copy'), 'smallTestNet')

        net2 = DynameqNetwork(net.getScenario()) 
        net2.read(os.path.join(mainFolder, 'dynameqNetwork_gearySubset_copy'), "smallTestNet") 

        after = (net2.getNumNodes(), net2.getNumRoadNodes(), net2.getNumCentroids(), net2.getNumVirtualNodes(),
                  net2.getNumLinks(), net2.getNumRoadLinks(), net2.getNumConnectors(), net2.getNumVirtualLinks())

        shutil.rmtree(os.path.join(mainFolder, 'dynameqNetwork_gearySubset_copy'))
        assert before == after 
        return
    
        originalFile = os.path.join(os.path.join(projectFolder, "smallTestNet_base.dqt"))
        copyFile = os.path.join(mainFolder, 'dynameqNetwork_gearySubset_copy', 'smallTestNet_base.dqt')
        original = open(originalFile, "r").readlines()
        copy = open(copyFile, "r").readlines()
        if original != copy:
            htmldiff = difflib.HtmlDiff()
            diff = htmldiff.make_file(original, copy)
            output = open("base_diff.html", "w")
            output.write(diff)
            output.close()
            
        assert original == copy 
                               



              
    def test_mycopy(self):

        net1 = getSimpleNet() 
        addAllMovements(net1)

        link1_15 = net1.getLinkForNodeIdPair(1, 5) 
        link1_15._label = "123" 
        
        sc = net1.getScenario() 
        net2 = DynameqNetwork(sc) 
        net2.deepcopy(net1)
        
        link2_15 = net2.getLinkForNodeIdPair(1, 5) 
        assert link2_15._label == "123"
        #now change the label of the first link 
        link1_15._label = "342"
        #make sure that the label of the copied link does not change 
        assert link2_15._label == "123"        
        #more rigorously 
        assert id(link1_15) != id(link2_15) 

        assert net1.getNumNodes() == net2.getNumNodes()
        assert net2.getNumLinks() == net2.getNumLinks() 

        #check that links from the second network contain references to nodes in the second network 
        for link2 in net2.iterLinks():
            assert id(link2._startNode) == id(net2.getNodeForId(link2._startNode._id))
            assert id(link2._endNode) == id(net2.getNodeForId(link2._endNode._id))

        node1_5 = net1.getNodeForId(5) 
        node2_5 = net2.getNodeForId(5) 

        assert node1_5.getNumIncomingLinks() == node2_5.getNumIncomingLinks() 

        for link1, link2 in izip (node1_5._incomingLinks, node2_5._incomingLinks):
            assert not id(link1) == id(link2) 
            assert id(link1) == id(net1.getLinkForId(link1.getId()))
            assert id(link2) == id(net2.getLinkForId(link2.getId()))

            assert link1.getNumIncomingMovements() == link2.getNumIncomingMovements() 
            assert link1.getNumOutgoingMovements() == link2.getNumOutgoingMovements() 

            for mov2 in link2.iterIncomingMovements():
                assert id(mov2._node) == id(net2.getNodeForId(mov2._node.getId()))
                assert id(mov2._incomingLink) == id(net2.getLinkForId(mov2._incomingLink.getId()))
                assert id(mov2._outgoingLink) == id(net2.getLinkForId(mov2._outgoingLink.getId()))

            for mov2 in link2.iterOutgoingMovements():
                assert id(mov2._node) == id(net2.getNodeForId(mov2._node.getId()))
                assert id(mov2._incomingLink) == id(net2.getLinkForId(mov2._incomingLink.getId()))
                assert id(mov2._outgoingLink) == id(net2.getLinkForId(mov2._outgoingLink.getId()))
                
    def test_readWrite(self):

        projectFolder = os.path.join(os.path.dirname(__file__), '..', "test")
        prefix = 'test' 

        scenario = DynameqScenario(Time(0,0), Time(12,0))
        scenario.read(projectFolder, prefix)

        net = DynameqNetwork(scenario) 
        net.read(projectFolder, prefix) 

        net.write("test", "crossHair")

        net.moveCentroidConnectorsFromIntersectionsToMidblocks() 

        net.write("test", "crossHair3") 
        
    def test_isJunction(self):
        
        net = getGearySubNet() 
        assert net.getNodeForId(24473).isJunction() 
        assert net.getNodeForId(26514).isIntersection()
        assert net.getNodeForId(24472).isIntersection() 
        assert net.getNodeForId(53085).isIntersection() 

    def test_Scenario(self):
        
        sc = getTestScenario() 
        assert "All" in list(sc.name for sc in sc.iterVehicleClassGroups())
        assert "Prohibited" in list(sc.name for sc in sc.iterVehicleClassGroups())
        
    def NOtest_10getAcuteAngle(self):

        net = getSimpleNet()

        link1 = net.getLinkForNodeIdPair(1, 5)
        link2 = net.getLinkForNodeIdPair(5, 4)

        assert link1.getAngle(link2) == 0
        link3 = net.getLinkForNodeIdPair(5, 1) 

        assert link3.getAngle(link1) == 180
        assert link1.getAngle(link3) == 180

        link4 = net.getLinkForNodeIdPair(5, 2)
        
        assert link4.getAngle(link1) == 90
        assert link1.getAngle(link4) == 90
        assert link3.getAngle(link3) == 0
        assert link4.getAngle(link3) == 90
        
    def test_shpwrite(self):

        net = getGearySubNet()

        net.writeNodesToShp("test/tmp_nodes")
        net.writeLinksToShp("test/tmp_links")

        os.remove("test/tmp_nodes.shp")
        os.remove("test/tmp_nodes.dbf")
        os.remove("test/tmp_nodes.shx")
        os.remove("test/tmp_links.shp")
        os.remove("test/tmp_links.shx")
        os.remove("test/tmp_links.dbf")
        
    def NOtest_mergeLink(self):
        
        net = getCubeSubarea()  
        assert net.hasNodeForId(3674)

        answer = (net.getNumNodes() - 1, net.getNumLinks() - 1) 

        net.mergeLinks(net.getLinkForId(904266), net.getLinkForId(5424))

        assert (net.getNumNodes(), net.getNumLinks()) ==  answer

        assert not net.hasNodeForId(3674)
        assert not net.hasLinkForId(904266)
        assert not net.hasLinkForId(5424)

        answer = (net.getNumNodes(), net.getNumLinks() - 1) 

        net.mergeLinks(net.getLinkForId(901888), net.getLinkForId(901893))
        assert (net.getNumNodes(), net.getNumLinks()) ==  answer

        answer = (net.getNumNodes() - 1, net.getNumLinks() - 1) 
        net.mergeLinks(net.getLinkForId(901892), net.getLinkForId(901889))
        assert (net.getNumNodes(), net.getNumLinks()) ==  answer

        numShapePoints = sum([1 for node in net.iterNodes() if node.isMidblockNode() and node.isRoadNode()])

        assert numShapePoints == 152
        
        net.removeShapePoints() 

        numShapePoints = sum([1 for node in net.iterNodes() if node.isMidblockNode() and node.isRoadNode()])        
        assert numShapePoints == 40

    def NOtest_1renameLink(self):

        net = getSimpleNet()
        addAllMovements(net)
        
        link = net.getLinkForId(1)
        
        net.renameLink(1, 100) 

        assert not net.hasLinkForId(1)
        assert net.hasLinkForId(100) 

        assert link.getId() == 100


        link_15 = net.getLinkForNodeIdPair(1, 5)
        link_51 = net.getLinkForNodeIdPair(5, 1)
        link_52 = net.getLinkForNodeIdPair(5, 2)

        assert link_15.hasOutgoingMovement(2)
        assert link_15.hasOutgoingMovement(4)
        assert link_15.hasOutgoingMovement(3)

    def NOtest_1renameNode(self):

        net = getSimpleNet()
        addAllMovements(net)
        
        node = net.getNodeForId(1) 
        
        net.renameNode(1, 100) 

        assert not net.hasNodeForId(1)
        assert net.hasNodeForId(100) 

        assert node.getId() == 100

        link_15 = net.getLinkForNodeIdPair(100, 5)
        link_51 = net.getLinkForNodeIdPair(5, 100)
        link_52 = net.getLinkForNodeIdPair(5, 2)

        assert link_15.hasOutgoingMovement(2)
        assert link_15.hasOutgoingMovement(4)
        assert link_15.hasOutgoingMovement(3)

        net.renameNode(4, 101)
        for link in net.getNodeForId(101).iterAdjacentLinks():
            assert net.hasLinkForNodeIdPair(*link.getIid())

        #net.checkAdjacentNodesExist()
        #net.checkAdjacentLinksExist() 
        

    def test_renameNodesAndLinks(self):

        net = getGearySubNet() 
        
        projectFolder = os.path.join(mainFolder, 'dynameqNetwork_gearySubset')
        prefix = 'smallTestNet2' 

        maxLinkId = net.getMaxLinkId() 
        counter = 1

        for link in net.iterLinks():
            counter += 1
            net.renameLink(link.getId(), maxLinkId + counter)

        maxNodeId = net.getMaxNodeId() 
        counter = 1
        for node in net.iterNodes():
            if node.isCentroid():
                continue
            counter += 1
            net.renameNode(node.getId(), maxNodeId + counter)

        net.write(projectFolder, prefix)
        
    def test_deleteCentroid(self):

        net = getGearySubNet()
    

        cent = net.getNodeForId(9)
        net.removeNode(cent)
        
        assert not net.hasLinkForId(104874)
        assert not net.hasLinkForId(104875)
        #the following two are the connectors
        #assert not net.hasLinkForId(16432)
        #assert not net.hasLinkForId(16425)
        #and this is the virtual node
        #assert not net.hasNodeForId(26626)
        


    def test_linkOrientation(self):

        net = getSimpleNet()

        link15 = net.getLinkForNodeIdPair(1, 5)
        assert link15.getOrientation() == 90
        assert link15.getDirection() == "EB"

        link25 = net.getLinkForNodeIdPair(2, 5)
        assert link25.getOrientation() == 180
        assert link25.getDirection() == "SB"

        link52 = net.getLinkForNodeIdPair(5, 2)
        assert link52.getOrientation() == 0
        assert link52.getDirection() == "NB"
        
    def test_movementDirection(self):

        net = getSimpleNet()
        addAllMovements(net)

        link15 = net.getLinkForNodeIdPair(1, 5)
        mov152 = link15.getOutgoingMovement(2)
        mov154 = link15.getOutgoingMovement(4)
        mov153 = link15.getOutgoingMovement(3)

        assert mov152.getDirection() == "EBLT"

    def test_movementGetCenterLine(self):

        net = getSimpleNet()
        addAllMovements(net)

        l35 = net.getLinkForNodeIdPair(3,5)
        l54 = net.getLinkForNodeIdPair(5, 4)
        
        mov354 = net.getLinkForNodeIdPair(3, 5).getOutgoingMovement(4)
        mov351 = net.getLinkForNodeIdPair(3, 5).getOutgoingMovement(1)
        mov352 = net.getLinkForNodeIdPair(3, 5).getOutgoingMovement(2)

        assert l35.getCenterLine() == ((118.0, 0.0), (118.0, 100.0))
        assert l54.getCenterLine() == ((100.0, 82.0), (200.0, 82.0))
        assert mov354.getCenterLine() == [(118.0, 0.0), (118.0, 50.0), (150.0, 82.0), (200.0, 82.0)]
        
    def test_conflictingMovements(self):

        net = getSimpleNet()
        addAllMovements(net)

        mov154 = net.getLinkForNodeIdPair(1, 5).getOutgoingMovement(4)
        mov152 = net.getLinkForNodeIdPair(1, 5).getOutgoingMovement(2)
        mov253 = net.getLinkForNodeIdPair(2, 5).getOutgoingMovement(3)
        mov251 = net.getLinkForNodeIdPair(2, 5).getOutgoingMovement(1)
        mov254 = net.getLinkForNodeIdPair(2, 5).getOutgoingMovement(4)
        mov451 = net.getLinkForNodeIdPair(4, 5).getOutgoingMovement(1)
        
        mov354 = net.getLinkForNodeIdPair(3, 5).getOutgoingMovement(4)
        mov351 = net.getLinkForNodeIdPair(3, 5).getOutgoingMovement(1)
        mov352 = net.getLinkForNodeIdPair(3, 5).getOutgoingMovement(2)

        #thru mov with thru 
        assert mov154.isInConflict(mov253)
        #thru mov with left turn 
        assert not mov154.isInConflict(mov251)
        #thru mov with left turn of same dest 
        assert not mov154.isInConflict(mov254)
        #thru mov with left turn of same dest         
        assert not mov254.isInConflict(mov154)
        #left turn with opposing thru 
        assert mov152.isInConflict(mov451)
        #thru with opposing thru 
        assert not mov154.isInConflict(mov451)

        #right turn with left turn with same dest 
        assert not mov354.isInConflict(mov154)
        #right turn with left turn with same dest 
        assert not mov354.isInConflict(mov254)
        #left turn with thru from same link 
        assert not mov351.isInConflict(mov352)
        #left turn with right from same link 
        assert not mov351.isInConflict(mov354)

    def NOtest_movementCapacity(self):

        net = getGearySubNet()

        pi = net._planInfo.values()[0]
        
        node = net.getNodeForId(24467)

        for mov in node.iterMovements():
            print "protected capacity", mov.getTurnType(), mov.getProtectedCapacity(pi)
        
        print "num time plans", net.getNumTimePlans()

    def NOtest_movementVehClassGrous(self):

        net = getGearySubNet()

        node = net.getNodeForId(24467)

        i = 0
        for mov in node.iterMovements():
            mov.allowVehicleClassGroup("All")
            if i % 2 == 0:
                mov.prohibitVehicleClassGroup("Transit")                

            else:
                mov.allowVehicleClassGroup("Truck")                

        mov.isVehicleClassGroupProhibited("Transit")
        mov.prohibitAllVehicleClassGroups()

    def test_getNodeByStreetNames(self):

        net = getDowntownSF()

        node = net.getNodeForId(25261)
        answer = net.findNodeForRoadLabels(['HYDE', 'WASHINGTON'], 0.7)
        assert node == answer
        answer = net.findNodeForRoadLabels(['HYDE ST', 'WASHINGTON ST'], 1.0)
        assert node == answer        

        nose.tools.assert_raises(DtaError, net.findNodeForRoadLabels, ['HYDE', 'WASHINGTON'], 1.0)

          
