:: Prior to running this script, the user must:
::  1. Run the DTA model in Dynameq
::  2. Export the loaded Dynameq network files: {scenario_prefix}_{scen,base,advn,ctrl,ptrn}.dqt
::  3. Export the movement flow files: movement_alowi.dqt, movement_aflowo.dqt, movement_atime.dqt
::  4. Export the link flow files: link_aflowi.dqt, link_aflowo.dqt, link_atime.dqt

::  This file should be run in a directory containing these exported results. 

::Set the DTA_CODE_DIR, INPUT_DYNAMEQ_NET_DIR and DYNAMEQ_NET_PREFIX. E.g.:
::SET DTA_CODE_DIR=C:\DTAAnyway\dta
::SET INPUT_DYNAMEQ_NET_DIR="Q:\Model Projects\Broadway Traffic Calming\2.7\Validation_2012_AM"
::SET DYNAMEQ_NET_PREFIX=Base_2012_AM

:: DTA Anyway code location is required
IF NOT DEFINED DTA_CODE_DIR (
  echo Please set the DTA_CODE_DIR environment variable to the directory where DTA Anyway is installed.
  echo e.g. set DTA_CODE_DIR=Y:\Users\neema\dta
  goto done
)

:: Dynameq network prefix is required
IF NOT DEFINED DYNAMEQ_NET_PREFIX (
  echo Please set the DYNAMEQ_NET_PREFIX environment variable to the name of the network you exported.
  echo e.g. set DYNAMEQ_NET_PREFIX=sf_jun18_630p
  goto done
)

:: let PYTHON know where to find it
set PYTHONPATH=%DTA_CODE_DIR%

::
:: 1) export the 15-minute a CSV file
::
:export15MinCounts
python %DTA_CODE_DIR%\scripts\visualizeDTAResults_AM.py %INPUT_DYNAMEQ_NET_DIR% %DYNAMEQ_NET_PREFIX% 15 link15min.csv movement15min.csv %INPUT_DYNAMEQ_NET_DIR% counts_links_15min_0700_0930_all_midweek.dat counts_movements_15min_0700_0930_all_midweek.dat counts_movements_5min_0700_0900_all_midweek.dat 06:30 09:30
:: primary output: link15min.csv movement15min.csv
:: log     output: visualizeDTAResults.{DEBUG,INFO}.log
IF ERRORLEVEL 1 goto done

::
:: 2) export the 60-minute a CSV file
::
:export60MinCounts
python %DTA_CODE_DIR%\scripts\visualizeDTAResults_AM.py %INPUT_DYNAMEQ_NET_DIR% %DYNAMEQ_NET_PREFIX% 60 link60min.csv movement60min.csv %INPUT_DYNAMEQ_NET_DIR% counts_links_15min_0700_0930_all_midweek.dat counts_movements_15min_0700_0930_all_midweek.dat counts_movements_5min_0700_0900_all_midweek.dat 06:30 09:30
:: primary output: link60min.csv movement60min.csv
:: log     output: visualizeDTAResults.{DEBUG,INFO}.log
IF ERRORLEVEL 1 goto done

::
:: 2) create the corridor plots
::
:createCorridorPlots
python %DTA_CODE_DIR%\scripts\createCorridorPlots_AM.py %INPUT_DYNAMEQ_NET_DIR% %DYNAMEQ_NET_PREFIX% 08:00 09:00 2011_LOS_Monitoring_Fixed.csv %INPUT_DYNAMEQ_NET_DIR% counts_links_15min_0700_0930_all_midweek.dat counts_movements_15min_0700_0930_all_midweek.dat counts_movements_5min_0700_0900_all_midweek.dat ObsVsSimulatedRouteTravelTimes.csv
:: primary output: 
:: log     output: createCorridorPlots.{DEBUG,INFO}.log
IF ERRORLEVEL 1 goto done

:done