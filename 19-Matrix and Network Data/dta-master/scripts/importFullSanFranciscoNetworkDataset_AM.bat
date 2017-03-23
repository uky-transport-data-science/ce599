:: This file should run in an empty directory, all the way through.
:: Set DTA_CODE_DIR, DTA_NET_DIR and DTA_NET_FILE before you start the run. E.g.:

::set DTA_CODE_DIR=C:\DTAAnyway\dta
::set DTA_NET_DIR=Y:\dta\SanFrancisco\2012_Dynameq3_July2014
::set DTA_NET_FILE=SanFranciscoSubArea_2012_Base.net

:: DTA Anyway code location is required
IF NOT DEFINED DTA_CODE_DIR (
  echo Please set the DTA_CODE_DIR environment variable to the directory where DTA Anyway is installed.
  echo e.g. set DTA_CODE_DIR=C:\dta
  goto done
)

:: DTA Anyway supply/demand location is required
IF NOT DEFINED DTA_NET_DIR (
  echo Please set the DTA_NET_DIR environment variable to the directory where DTA network and matrix data are located.
  echo e.g. set DTA_NET_DIR=Y:\dta\SanFrancisco\2010
  goto done
)

:: DTA Anyway Cube network filename is required
IF NOT DEFINED DTA_NET_FILE (
  echo Please set the DTA_NET_DIR environment variable to the directory where DTA network and matrix data are located.
  echo e.g. set DTA_NET_FILE=SanFranciscoSubArea_2010.net
  goto done
)

:: Default to Cube transit networks if not defined
IF NOT DEFINED TRANSIT_IMPORT (
  set TRANSIT_IMPORT=CUBE
)

:: let PYTHON know where to find it
set PYTHONPATH=%DTA_CODE_DIR%

::
:: 1) create the network from the Cube network
::
:convertStaticNetwork
python %DTA_CODE_DIR%\scripts\createSFNetworkFromCubeNetwork_AM.py -n sf_nodes.shp -l sf_links.shp %DTA_NET_DIR%\%DTA_NET_FILE% %DTA_NET_DIR%\network\turnsam.pen Q:\GIS\Transportation\Roads\San_Francisco\Street_Centerlines\AttachToCube\stclines.shp
:: primary output: Dynameq files sf_{scen,base,advn,ctrl}.dqt
:: log     output: createSFNetworkFromCubeNetwork.{DEBUG,INFO}.log
:: debug   output: sf_{links,nodes}.shp
IF ERRORLEVEL 1 goto done

::
:: 2) attach the transit lines to the DTA network
:: 
:importTransit
if %TRANSIT_IMPORT% == CUBE (
  python %DTA_CODE_DIR%\scripts\importTPPlusTransitRoutes_AM.py . sf %DTA_NET_DIR%\transit\sfmuni.lin %DTA_NET_DIR%\transit\bus.lin
  :: primary output: Dynameq files sf_trn_{scen,base,advn,ptrn}.dqt
  :: log     output: importTPPlusTransitRoutes.{DEBUG,INFO}.log
  IF ERRORLEVEL 1 goto done
)
if %TRANSIT_IMPORT% == GTFS (
  set PYTHONPATH=%DTA_CODE_DIR%;Y:\lmz\googletransitdatafeed-read-only\python
  python %DTA_CODE_DIR%\scripts\importGTFS.py -s sf_gtfs_stops.shp -l sf_gtfs_links.shp . sf %DTA_NET_DIR%\transit\google_transit_sfmta_20120609_20120914.zip
  :: primary output: Dynameq files sf_trn_{scen,base,adv,ptrn}.dqt
  :: log     output: importGTFS.{DEBUG,INFO}.log
  IF ERRORLEVEL 1 goto done
)


::
:: 3) attach the signal data to the DTA network
:: 
:: This step needs to go after the transit step because the transit step enables all movements for transit (so if there is a transit line
:: turning left at an intersection and the left was prohibited, it will become transit-only.)  That way, the signal validation will make
:: sure that transit gets green time.
::
:importSignals
python %DTA_CODE_DIR%\scripts\importExcelSignals.py . sf_trn %DTA_NET_DIR%\network\excelSignalCards 06:30 09:30 %DTA_NET_DIR%\network\movement_override.csv %DTA_NET_DIR%\network\uturnPros.csv
:: primary output: Dynameq files sf_signals_{scen,base,advn,ctrl}.dqt
:: log     output: importExcelSignals.{DEBUG,INFO}.log
IF ERRORLEVEL 1 goto done

::
:: 4) attach the stop sign data to the DTA network
::
:: This step needs to go after import signals because signals win over stop signs; if a node has a signal, we'll leave it alone.
::
:importStopSigns
python %DTA_CODE_DIR%\scripts\importUnsignalizedIntersections.py . sf_signals Q:\GIS\Transportation\Roads\San_Francisco\Traffic_Control\2012\StopSigns\stops_signs.shp 
IF ERRORLEVEL 1 goto done
:: primary output: Dynameq files sf_stops_{scen,base,advn,??}.dqt
:: log     output: importUnsignalizedIntersections.{DEBUG,INFO}.log

::
:: 4) create the car demand
::
:createDemand
python %DTA_CODE_DIR%\scripts\importCubeDemand.py -f %DTA_NET_DIR%\demand\DemandProfile_AM.csv . sf_stops Car_NoToll demand_Car_NoToll.dat 05:30 10:30 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_EA.csv 05:30 06:30 01:00 0.13364 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_AM.csv 06:30 09:30 03:00 1.00 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_MD.csv 09:30 10:30 01:00 0.22594
IF ERRORLEVEL 1 goto done
python %DTA_CODE_DIR%\scripts\importCubeDemand.py -f %DTA_NET_DIR%\demand\DemandProfile_AM.csv . sf_stops Car_Toll demand_Car_Toll.dat 05:30 10:30 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_EA.csv 05:30 06:30 01:00 0.13364 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_AM.csv 06:30 09:30 03:00 1.00 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_MD.csv 09:30 10:30 01:00 0.22594
IF ERRORLEVEL 1 goto done
:: primary output: demand_Car_NoToll.dat & demand_Car_Toll.dat
:: log     output: importCubeDemand.{DEBUG,INFO}.log

:: 5) create the truck demand
::
:createDemand
python %DTA_CODE_DIR%\scripts\importCubeDemand.py -f %DTA_NET_DIR%\demand\DemandProfile_Truck_AM.csv . sf_stops Truck_NoToll demand_Truck_NoToll.dat 05:30 10:30 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_EA.csv 05:30 06:30 01:00 0.051282 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_AM.csv 06:30 09:30 03:00 1.00 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_MD.csv 09:30 10:30 01:00 0.039216
IF ERRORLEVEL 1 goto done
python %DTA_CODE_DIR%\scripts\importCubeDemand.py -f %DTA_NET_DIR%\demand\DemandProfile_Truck_AM.csv . sf_stops Truck_Toll demand_Truck_Toll.dat 05:30 10:30 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_EA.csv 05:30 06:30 01:00 0.051282 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_AM.csv 06:30 09:30 03:00 1.00 %DTA_NET_DIR%\demand\SanFranciscoSubArea_2010_MD.csv 09:30 10:30 01:00 0.039216
IF ERRORLEVEL 1 goto done
:: primary output: demand_Truck_NoToll.dat & demand_Truck_Toll.dat
:: log     output: importCubeDemand.{DEBUG,INFO}.log

:copyFinal
:: THESE are the files to import into dynameq
copy sf_stops_scen.dqt sf_final_scen.dqt
copy sf_stops_base.dqt sf_final_base.dqt
copy sf_stops_advn.dqt sf_final_advn.dqt
copy sf_stops_ctrl.dqt sf_final_ctrl.dqt
copy sf_stops_prio.dqt sf_final_prio.dqt
copy sf_trn_ptrn.dqt   sf_final_ptrn.dqt

:: This is here because countdracula is not typically setup.  If it is, then COUNTDRACULA_CODE_DIR should point to the geodjango directory within.
IF NOT DEFINED COUNTDRACULA_CODE_DIR (
  goto done
)

:done