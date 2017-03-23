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
import shapefile

import copy
import os
import shutil
import subprocess
import sys
import tempfile
from itertools import izip 

from .Centroid import Centroid
from .Connector import Connector
from .DtaError import DtaError
from .Logger import DtaLogger
from .Movement import Movement
from .Network import Network
from .Node import Node
from .RoadLink import RoadLink
from .RoadNode import RoadNode
from .VirtualLink import VirtualLink
from .VirtualNode import VirtualNode

class CubeNetwork(Network):
    """
    A DTA Network originating from a Cube network.
    """
    
    EXPORT_SCRIPTNAME = "ExportCubeForDta.s"
    EXPORT_SCRIPT = r"""
RUN PGM=NETWORK

NETI[1]=%s
 NODEO=%s\nodes.csv,FORMAT=SDF, INCLUDE=%s
 LINKO=%s\links.csv ,FORMAT=SDF, INCLUDE=%s
ENDRUN    
"""
    
    def __init__(self, scenario):
        """
        Constructor.  Initializes to an empty network.
        
        Keeps a reference to the given Scenario (a :py:class:`Scenario` instance)
        for :py:class:`VehicleClassGroup` lookups        
        """ 
        Network.__init__(self, scenario)
        #: (nodeA id, nodeB id) -> { dictionary } in case the caller wants to do anything else
        self.additionalLinkVariables = {}

    def readNetfile(self, netFile, 
                    nodeVariableNames,
                    linkVariableNames,
                    **kwargs):
        """
        Reads the given netFile by exporting to CSV files and reading those.
        *nodeVariableNames* is a list of variable names for the nodes and
        *linkVariableNames* is a list of variable names for the links.
        See :py:meth:`CubeNetwork.readCSVs` for the description of the rest of the arguments.
        """
        tempdir = tempfile.mkdtemp()
        scriptFilename = os.path.join(tempdir, CubeNetwork.EXPORT_SCRIPTNAME)
        
        DtaLogger.info("Writing export script to %s" % scriptFilename)
        scriptFile = open(scriptFilename, "w")
        scriptFile.write(CubeNetwork.EXPORT_SCRIPT % 
                         (netFile, 
                          tempdir, ",".join(nodeVariableNames), 
                          tempdir, ",".join(linkVariableNames)))
        scriptFile.close()
        
        # run the script file
        DtaLogger.info("Running %s" % scriptFilename)
        cmd = "runtpp " + scriptFilename
        proc = subprocess.Popen( cmd, 
                                 cwd = tempdir, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE )
        for line in proc.stdout:
            line = line.strip('\r\n')
            DtaLogger.info("  stdout: " + line)

        for line in proc.stderr:
            line = line.strip('\r\n')
            DtaLogger.info("stderr: " + line)
        retcode  = proc.wait()
        if retcode ==2:
            raise DtaError("Failed to export CubeNetwork using %s" % scriptFilename)

        DtaLogger.info("Received %d from [%s]" % (retcode, cmd))
        self.readCSVs(os.path.join(tempdir, "nodes.csv"), nodeVariableNames,
                      os.path.join(tempdir, "links.csv"), linkVariableNames,
                      **kwargs)
        shutil.rmtree(tempdir) 
        
    def readCSVs(self, 
                 nodesCsvFilename, nodeVariableNames,
                 linksCsvFilename, linkVariableNames,
                 centroidIds,
                 useOldNodeForId,
                 nodeGeometryTypeEvalStr,
                 nodeControlEvalStr,
                 nodePriorityEvalStr,
                 nodeLabelEvalStr,
                 nodeLevelEvalStr,
                 linkReverseAttachedIdEvalStr,
                 linkFacilityTypeEvalStr,
                 linkLengthEvalStr,
                 linkFreeflowSpeedEvalStr,
                 linkEffectiveLengthFactorEvalStr,
                 linkResponseTimeFactorEvalStr,
                 linkNumLanesEvalStr,
                 linkRoundAboutEvalStr,
                 linkLevelEvalStr,
                 linkLabelEvalStr,
                 linkGroupEvalStr,
                 linkSkipEvalStr=None,
                 additionalLocals={}):
        """
        Reads the network from the given csv files.
        
        :param nodesCsvFilename: the csv with the node data
        :param nodeVariableNames: the column names in the file specified by *nodesCsvFilename*
        :param linksCsvFilename: the csv with the link data
        :param linkVariableNames: the column names in the file specified by *linksCsvFilename*
        :param centroidIds: a list of the node Ids that should be interpreted as centroids
        
        The following strings are used to indicate how the **nodes** should be interpreted.  These
        will be eval()ed by python, and so they can reference one of the *nodeVariableNames*, or they
        can be constants.  
        
        For example, *nodeControlEvalStr* can be ``"RoadNode.CONTROL_TYPE_SIGNALIZED"`` if
        there are no useful node variables and we just want to default the control attribute of **all**
        :py:class:`RoadNode` to :py:attr:`RoadNode.CONTROL_TYPE_SIGNALIZED`.
        
        Alternatively, if a column in the file given by *nodesCsvFilename* could be used, then
        it can be referenced.  So if there is a column called "SIGNAL" which is 1 for signalized
        intersections and 0 otherwise, the *nodeControlEvalStr* could be 
        ``"RoadNode.CONTROL_TYPE_SIGNALIZED if int(SIGNAL)==1 else RoadNode.CONTROL_TYPE_UNSIGNALIZED"``.
        
        Note that the CSV fields are all strings, which is why SIGNAL is cast to an int here.
        
        :param useOldNodeForId: indicates that the ``OLD_NODE`` variable is to be used for the ID (rather than ``N``).
        :param nodeGeometryTypeEvalStr: indicates how to set the *geometryType* for each :py:class:`RoadNode`
        :param nodeControlEvalStr: indicates how to set the *control* for each :py:class:`RoadNode`
        :param nodePriorityEvalStr: indicates how to set the *priority* for each :py:class:`RoadNode`
        :param nodeLabelEvalStr: indicates how to set the *label* for each :py:class:`Node`
        :param nodeLevelEvalStr: indicates how to set the *level* for each :py:class:`Node`

        Similarly, the following strings are used to indicate how the **links** should be interpreted.
        
        :param linkReverseAttachedIdEvalStr: indicates how to set the *reversedAttachedId* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkFacilityTypeEvalStr: indicates how to set the *facilityType* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkLengthEvalStr: indicates how to set the *length* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkFreeflowSpeedEvalStr: indicates how to set the *freeflowSpeed* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkEffectiveLengthFactorEvalStr: indicates how to set the *effectiveLengthFactor* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkResponseTimeFactorEvalStr: indicates how to set the *responseTimeFactor* for :py:class:`RoadLink`
          and :py:class:`Connector` instances 
        :param linkNumLanesEvalStr: indicates how to set the *numLanes* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkRoundAboutEvalStr: indicates how to set the *roundAbout* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkLevelEvalStr: indicates how to set the *level* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkLabelEvalStr: indicates how to set the *label* for :py:class:`RoadLink`
          and :py:class:`Connector` instances
        :param linkGroupEvalStr: indicates how to set the *group* for :py:class:`RoadLink`
          and :py:class:`Connector` instances.
        :param linkSkipEvalStr: specifies links to skip in the import
        :param additionalLocals: a dictionary to add to the locals dict for the ``eval`` calls above.
        
        Note that the dictionary of available variables from *linkVariableNames* is saved into
        :py:attr:`CubeNetwork.additionalLinkVariables`, keyed by the tuple of link's node IDs,
        in case the caller needs to do additional postprocessing of attributes on the network using those variables.
        """
        # need to keep this for reading links
        N_to_OldNode = {}
            
        idIndex = nodeVariableNames.index("OLD_NODE" if useOldNodeForId else "N")
        nIndex = nodeVariableNames.index("N")
        xIndex = nodeVariableNames.index("X")
        yIndex = nodeVariableNames.index("Y")
        
        aIndex = linkVariableNames.index("A")
        bIndex = linkVariableNames.index("B")
        
        countCentroids = 0
        countRoadNodes = 0        
        nodesFile = open(nodesCsvFilename, "r")
        for line in nodesFile:
            fields = line.strip().split(",")
            
            id = int(fields[idIndex])
            n  = int(fields[nIndex])
            x  = float(fields[xIndex])
            y  = float(fields[yIndex])
            
            localsdict = dict(additionalLocals.items())
            for i,nodeVarName in enumerate(nodeVariableNames):
                localsdict[nodeVarName] = fields[i].strip("' ") # Cube csv strings are in single quotes
            
            newNode = None
            if id in centroidIds:
                newNode = Centroid(id=id,x=x,y=y,
                                   label=eval(nodeLabelEvalStr, globals(), localsdict),
                                   level=eval(nodeLevelEvalStr, globals(), localsdict))
                countCentroids += 1
            else:
                #TODO: allow user to set the defaults
                newNode = RoadNode(id=id,x=x,y=y,
                                   geometryType=eval(nodeGeometryTypeEvalStr, globals(), localsdict),
                                   control=eval(nodeControlEvalStr, globals(), localsdict),
                                   priority=eval(nodePriorityEvalStr, globals(), localsdict),
                                   label=eval(nodeLabelEvalStr, globals(), localsdict),
                                   level=eval(nodeLevelEvalStr, globals(), localsdict))
                countRoadNodes += 1
            self.addNode(newNode)
            
            if useOldNodeForId: N_to_OldNode[n] = id

        DtaLogger.info("Read  %8d %-16s from %s" % (countCentroids, "centroids", nodesCsvFilename))
        DtaLogger.info("Read  %8d %-16s from %s" % (countRoadNodes, "roadnodes", nodesCsvFilename))
        nodesFile.close()
        
        linksFile = open(linksCsvFilename, "r")
        countConnectors = 0
        countRoadLinks  = 0
        for line in linksFile:
            fields = line.strip().split(",")
            
            a = int(fields[aIndex])
            b = int(fields[bIndex])
            
            if useOldNodeForId:
                a = N_to_OldNode[a]
                b = N_to_OldNode[b]
                
            nodeA = self.getNodeForId(a)
            nodeB = self.getNodeForId(b)
            
            localsdict = dict(additionalLocals.items())
            for i,linkVarName in enumerate(linkVariableNames):
                localsdict[linkVarName] = fields[i].strip("' ") # Cube csv strings are in single quotes

            if linkSkipEvalStr and eval(linkSkipEvalStr, globals(), localsdict): continue
                            
            newLink = None
            if isinstance(nodeA, Centroid) or isinstance(nodeB, Centroid):
                localsdict['isConnector'] = True
                try: 
                    newLink = Connector \
                       (id                      = self._maxLinkId+1,
                        startNode               = nodeA,
                        endNode                 = nodeB,
                        reverseAttachedLinkId   = eval(linkReverseAttachedIdEvalStr, globals(), localsdict),
                        # facilityType            = eval(linkFacilityTypeEvalStr, globals(), localsdict),
                        length                  = eval(linkLengthEvalStr, globals(), localsdict),
                        freeflowSpeed           = eval(linkFreeflowSpeedEvalStr, globals(), localsdict),
                        effectiveLengthFactor   = eval(linkEffectiveLengthFactorEvalStr, globals(), localsdict),
                        responseTimeFactor      = eval(linkResponseTimeFactorEvalStr, globals(), localsdict),
                        numLanes                = eval(linkNumLanesEvalStr, globals(), localsdict),
                        roundAbout              = eval(linkRoundAboutEvalStr, globals(), localsdict),
                        level                   = eval(linkLevelEvalStr, globals(), localsdict),
                        label                   = eval(linkLabelEvalStr, globals(), localsdict),
                        group                   = eval(linkGroupEvalStr, globals(), localsdict))
                    countConnectors += 1
                except DtaError, e:
                    DtaLogger.error("Error adding Connector from %d to %d - skipping: %s" %
                                    (nodeA.getId(), nodeB.getId(), str(e)))
                    continue
            else:
                localsdict['isConnector'] = False
                try: 
                    newLink = RoadLink \
                       (id                      = self._maxLinkId+1,
                        startNode               = nodeA,
                        endNode                 = nodeB,
                        reverseAttachedLinkId   = eval(linkReverseAttachedIdEvalStr, globals(), localsdict),
                        facilityType            = eval(linkFacilityTypeEvalStr, globals(), localsdict),
                        length                  = eval(linkLengthEvalStr, globals(), localsdict),
                        freeflowSpeed           = eval(linkFreeflowSpeedEvalStr, globals(), localsdict),
                        effectiveLengthFactor   = eval(linkEffectiveLengthFactorEvalStr, globals(), localsdict),
                        responseTimeFactor      = eval(linkResponseTimeFactorEvalStr, globals(), localsdict),
                        numLanes                = eval(linkNumLanesEvalStr, globals(), localsdict),
                        roundAbout              = eval(linkRoundAboutEvalStr, globals(), localsdict),
                        level                   = eval(linkLevelEvalStr, globals(), localsdict),
                        label                   = eval(linkLabelEvalStr, globals(), localsdict),
                        group                   = eval(linkGroupEvalStr, globals(), localsdict))
                    countRoadLinks += 1
                except DtaError, e:
                    DtaLogger.error("Error adding RoadLink from %d to %d - skipping: %s" %
                                    (nodeA.getId(), nodeB.getId(), str(e)))
                    continue 
            self.addLink(newLink)
            self.additionalLinkVariables[(a,b)] = copy.deepcopy(localsdict)
            
        DtaLogger.info("Read  %8d %-16s from %s" % (countConnectors, "connectors", linksCsvFilename))
        DtaLogger.info("Read  %8d %-16s from %s" % (countRoadLinks, "roadlinks", linksCsvFilename))
        linksFile.close()
        
    def readFromShapefiles(self, nodesShpFilename, nodeVariableNames,
                 linksShpFilename, linkVariableNames,
                 centroidIds,
                 nodeGeometryTypeEvalStr,
                 nodeControlEvalStr,
                 nodePriorityEvalStr,
                 nodeLabelEvalStr,
                 nodeLevelEvalStr,
                 linkReverseAttachedIdEvalStr,
                 linkFacilityTypeEvalStr,
                 linkLengthEvalStr,
                 linkFreeflowSpeedEvalStr,
                 linkEffectiveLengthFactorEvalStr,
                 linkResponseTimeFactorEvalStr,
                 linkNumLanesEvalStr,
                 linkRoundAboutEvalStr,
                 linkLevelEvalStr,
                 linkLabelEvalStr):

        sf = shapefile.Reader(nodesShpFilename)
        shapes = sf.shapes()
        records = sf.records()

        fields = [field[0] for field in sf.fields[1:]]
        for shape, recordValues in izip(shapes, records):
            x, y = shape.points[0]
            localsdict = dict(izip(fields, recordValues))
            n = int(localsdict["N"])
            
            newNode = None
            if n in centroidIds:
                newNode = Centroid(id=n,x=x,y=y,
                                   label=eval(nodeLabelEvalStr, globals(), localsdict),
                                   level=eval(nodeLevelEvalStr, globals(), localsdict))
            else:
                newNode = RoadNode(id=n,x=x,y=y,
                                   geometryType=eval(nodeGeometryTypeEvalStr, globals(), localsdict),
                                   control=eval(nodeControlEvalStr, globals(), localsdict),
                                   priority=eval(nodePriorityEvalStr, globals(), localsdict),
                                   label=eval(nodeLabelEvalStr, globals(), localsdict),
                                   level=eval(nodeLevelEvalStr, globals(), localsdict))
            try:
                self.addNode(newNode)
            except DtaError, e:
                print e

        sf = shapefile.Reader(linksShpFilename)
        shapes = sf.shapes()
        records = sf.records()

        fields = [field[0] for field in sf.fields[1:]]
        for shape, recordValues in izip(shapes, records):

            localsdict = dict(zip(fields, recordValues))
            startNodeId = int(localsdict["A"])
            endNodeId = int(localsdict["B"])

            try:
                startNode = self.getNodeForId(startNodeId)
                endNode = self.getNodeForId(endNodeId)
            except DtaError, e:
                print e 
                continue

            newLink = None
            if isinstance(startNode, Centroid) or isinstance(endNode, Centroid):
                localsdict['isConnector'] = True
                try: 
                    newLink = Connector \
                        (id                      = self.getMaxLinkId() + 1,
                        startNode               = startNode,
                        endNode                 = endNode,
                        reverseAttachedLinkId   = eval(linkReverseAttachedIdEvalStr, globals(), localsdict),
                        #facilityType            = eval(linkFacilityTypeEvalStr, globals(), localsdict),
                        length                  = -1, # eval(linkLengthEvalStr, globals(), localsdict),
                        freeflowSpeed           = 30, #eval(linkFreeflowSpeedEvalStr, globals(), localsdict),
                        effectiveLengthFactor   = 1.0, #eval(linkEffectiveLengthFactorEvalStr, globals(), localsdict),
                        responseTimeFactor      = 1.0, # eval(linkResponseTimeFactorEvalStr, globals(), localsdict),
                        numLanes                = 1, # eval(linkNumLanesEvalStr, globals(), localsdict),
                        roundAbout              = 0, # eval(linkRoundAboutEvalStr, globals(), localsdict),
                        level                   = 0, #eval(linkLevelEvalStr, globals(), localsdict),
                        label                   = "") # eval(linkLabelEvalStr, globals(), localsdict))
                except DtaError, e:
                    DtaLogger.error("%s" % str(e))
                    continue
            else:
                localsdict['isConnector'] = False
                try: 
                    newLink = RoadLink \
                       (id                      = self.getMaxLinkId()+1,
                        startNode               = startNode,
                        endNode                 = endNode,
                        reverseAttachedLinkId   = eval(linkReverseAttachedIdEvalStr, globals(), localsdict),
                        facilityType            = eval(linkFacilityTypeEvalStr, globals(), localsdict),
                        length                  = -1, # eval(linkLengthEvalStr, globals(), localsdict),
                        freeflowSpeed           = 30, #eval(linkFreeflowSpeedEvalStr, globals(), localsdict),
                        effectiveLengthFactor   = 1.0, #eval(linkEffectiveLengthFactorEvalStr, globals(), localsdict),
                        responseTimeFactor      = 1.0, #eval(linkResponseTimeFactorEvalStr, globals(), localsdict),
                        numLanes                = 1, #eval(linkNumLanesEvalStr, globals(), localsdict),
                        roundAbout              = 0, #eval(linkRoundAboutEvalStr, globals(), localsdict),
                        level                   = 0, #eval(linkLevelEvalStr, globals(), localsdict),
                        label                   = 0) #eval(linkLabelEvalStr, globals(), localsdict))
                except DtaError, e:
                    DtaLogger.error("%s" % str(e))
                    continue
            newLink._shapePoints = shape.points
            self.addLink(newLink)
            
    def applyTurnProhibitions(self, fileName):
        """
        Apply the turn prohibitions found in the filename
        """
        inputStream = open(fileName, 'r')
        movements_removed = 0
        lines_read        = 0
        
        for line in inputStream:
            fields      = line.strip().split()
            if len(fields) == 0: continue # blank line
            startNodeId = int(fields[0])
            nodeId      = int(fields[1])
            endNodeId   = int(fields[2])
            setNum      = int(fields[3])
            turnPen     = int(fields[4])
            lines_read += 1
            
            try:
                link = self.getLinkForNodeIdPair(startNodeId, nodeId)
                mov = link.getOutgoingMovement(endNodeId)                
            except DtaError, e:
                DtaLogger.error("Error finding movement %d %d %d - skipping: %s" %
                                (startNodeId, nodeId, endNodeId, str(e)))                
                continue
            
            # a negative one means prohibited
            if turnPen == -1:
                # DtaLogger.info("Removing movement %d-%d-%d found in turn prohibition file" % (startNodeId, nodeId, endNodeId))
                mov.prohibitAllVehicleClassGroups()
                # mov.prohibitAllVehiclesButTransit()
                movements_removed += 1
            
            elif turnPen > 0:
                # apply a time penalty to the movement?
                # punting on this for now, not sure if it's possible with Dynameq
                pass
        
        DtaLogger.info("Removed %d movements out of %d found in %s" % (movements_removed, lines_read, fileName))
        
