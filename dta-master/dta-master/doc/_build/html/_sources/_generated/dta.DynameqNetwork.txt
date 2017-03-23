dta.DynameqNetwork
==================

.. currentmodule:: dta

.. autoclass:: DynameqNetwork

   
   .. automethod:: __init__

   
   .. rubric:: Methods

   .. autosummary::
   
      ~DynameqNetwork.__init__
      ~DynameqNetwork.addAllMovements
      ~DynameqNetwork.addLink
      ~DynameqNetwork.addMovement
      ~DynameqNetwork.addNode
      ~DynameqNetwork.addPlanCollectionInfo
      ~DynameqNetwork.addTwoWayStopControlToConnectorsAtRoadlinks
      ~DynameqNetwork.areIDsUnique
      ~DynameqNetwork.cleanStreetNames
      ~DynameqNetwork.deepcopy
      ~DynameqNetwork.findLinksForRoadLabels
      ~DynameqNetwork.findMovementForRoadLabels
      ~DynameqNetwork.findNRoadLinksNearestCoords
      ~DynameqNetwork.findNodeForRoadLabels
      ~DynameqNetwork.findNodeNearestCoords
      ~DynameqNetwork.getCleanStreetName
      ~DynameqNetwork.getLinkForId
      ~DynameqNetwork.getLinkForNodeIdPair
      ~DynameqNetwork.getLinkType
      ~DynameqNetwork.getMaxLinkId
      ~DynameqNetwork.getMaxNodeId
      ~DynameqNetwork.getNodeForId
      ~DynameqNetwork.getNodeType
      ~DynameqNetwork.getNumCentroids
      ~DynameqNetwork.getNumConnectors
      ~DynameqNetwork.getNumLinks
      ~DynameqNetwork.getNumNodes
      ~DynameqNetwork.getNumOverlappingConnectors
      ~DynameqNetwork.getNumRoadLinks
      ~DynameqNetwork.getNumRoadNodes
      ~DynameqNetwork.getNumTimePlans
      ~DynameqNetwork.getNumVirtualLinks
      ~DynameqNetwork.getNumVirtualNodes
      ~DynameqNetwork.getPlanCollectionInfo
      ~DynameqNetwork.getScenario
      ~DynameqNetwork.handleOverlappingLinks
      ~DynameqNetwork.handleShortLinks
      ~DynameqNetwork.hasCentroidForId
      ~DynameqNetwork.hasCustomPriorities
      ~DynameqNetwork.hasLinkForId
      ~DynameqNetwork.hasLinkForNodeIdPair
      ~DynameqNetwork.hasNodeForId
      ~DynameqNetwork.hasPlanCollectionInfo
      ~DynameqNetwork.insertVirtualNodeBetweenCentroidsAndRoadNodes
      ~DynameqNetwork.iterCentroids
      ~DynameqNetwork.iterConnectors
      ~DynameqNetwork.iterLinks
      ~DynameqNetwork.iterMovements
      ~DynameqNetwork.iterNodes
      ~DynameqNetwork.iterPlanCollectionInfo
      ~DynameqNetwork.iterRoadLinks
      ~DynameqNetwork.iterRoadNodes
      ~DynameqNetwork.iterVirtualLinks
      ~DynameqNetwork.iterVirtualNodes
      ~DynameqNetwork.mergeLinks
      ~DynameqNetwork.mergeSecondaryNetwork
      ~DynameqNetwork.mergeSecondaryNetworkBasedOnLinkIds
      ~DynameqNetwork.mergeSecondaryNetworkBasedOnLinkIds2
      ~DynameqNetwork.moveCentroidConnectorFromIntersectionToMidblock
      ~DynameqNetwork.moveCentroidConnectorsFromIntersectionsToMidblocks
      ~DynameqNetwork.moveVirtualNodesToAvoidShortConnectors
      ~DynameqNetwork.read
      ~DynameqNetwork.readLinkShape
      ~DynameqNetwork.readObsLinkCounts
      ~DynameqNetwork.readObsMovementCounts
      ~DynameqNetwork.readSimResults
      ~DynameqNetwork.removeLink
      ~DynameqNetwork.removeNode
      ~DynameqNetwork.removeShapePoints
      ~DynameqNetwork.removeUnconnectedNodes
      ~DynameqNetwork.renameLink
      ~DynameqNetwork.renameNode
      ~DynameqNetwork.setMovementTurnTypeOverrides
      ~DynameqNetwork.splitLink
      ~DynameqNetwork.write
      ~DynameqNetwork.writeCountListToFile
      ~DynameqNetwork.writeLinksToShp
      ~DynameqNetwork.writeMovementsToShp
      ~DynameqNetwork.writeNodesToShp
   
   

   
   
   .. rubric:: Attributes

   .. autosummary::
   
      ~DynameqNetwork.ADVANCED_FILE
      ~DynameqNetwork.ADVANCED_HEADER
      ~DynameqNetwork.BASE_FILE
      ~DynameqNetwork.BASE_HEADER
      ~DynameqNetwork.CONTROL_FILE
      ~DynameqNetwork.CTRL_HEADER
      ~DynameqNetwork.LINK_FLOW_OUT
      ~DynameqNetwork.LINK_SPEED_OUT
      ~DynameqNetwork.LINK_TIME_OUT
      ~DynameqNetwork.MOVEMENT_FLOW_IN
      ~DynameqNetwork.MOVEMENT_FLOW_OUT
      ~DynameqNetwork.MOVEMENT_SPEED_OUT
      ~DynameqNetwork.MOVEMENT_TIME_OUT
      ~DynameqNetwork.PRIORITIES_FILE
      ~DynameqNetwork.PRIORITIES_HEADER
      ~DynameqNetwork.TRANSIT_FILE
   
   