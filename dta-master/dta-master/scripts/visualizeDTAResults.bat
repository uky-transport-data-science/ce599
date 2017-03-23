:: Prior to running this script, the user must:
::  1. Run the DTA model in Dynameq
::  2. Export the loaded Dynameq network files: {scenario_prefix}_{scen,base,advn,ctrl,ptrn}.dqt
::  3. Export the movement flow files: movement_alowi.dqt, movement_aflowo.dqt, movement_atime.dqt
::  4. Export the link flow files: link_aflowi.dqt, link_aflowo.dqt, link_atime.dqt
::  5. Set an environment variable for: DYNAMEQ_NET_PREFIX
::
::  This file should be run in a directory containing these exported results. 

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
python %DTA_CODE_DIR%\scripts\visualizeDTAResults.py D:\SFCTA_Validation\validation2010.pb_sept5_RS_T2\Reports\Export %DYNAMEQ_NET_PREFIX% 15 link15min.csv movement15min.csv D:\SFCTA_Validation\Counts counts_links_15min_1600_1830_recent_midweek.dat counts_movements_15min_1600_1830_recent_midweek.dat counts_movements_5min_1600_1800_recent_midweek.dat 15:30 18:30
:: primary output: link15min.csv movement15min.csv
:: log     output: visualizeDTAResults.{DEBUG,INFO}.log
IF ERRORLEVEL 1 goto done

::
:: 2) export the 60-minute a CSV file
::
:export60MinCounts
python %DTA_CODE_DIR%\scripts\visualizeDTAResults.py D:\SFCTA_Validation\validation2010.pb_sept5_RS_T2\Reports\Export %DYNAMEQ_NET_PREFIX% 60 link60min.csv movement60min.csv D:\SFCTA_Validation\Counts counts_links_15min_1600_1830_recent_midweek.dat counts_movements_15min_1600_1830_recent_midweek.dat counts_movements_5min_1600_1800_recent_midweek.dat 15:30 18:30
:: primary output: link60min.csv movement60min.csv
:: log     output: visualizeDTAResults.{DEBUG,INFO}.log
IF ERRORLEVEL 1 goto done
