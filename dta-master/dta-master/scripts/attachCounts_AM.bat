:: Set DTA_CODE_DIR, DTA_NET_DIR and DTA_NET_FILE before you start the run. E.g.:
::set DTA_CODE_DIR=C:\DTAAnyway\dta
::set DYNAMEQ_NET_PREFIX=Base_2012_AM
set COUNTDRACULA_CODE_DIR=C:\CountDracula

:importCounts
:: unfortunately GeoDjango is python 2.7
set OLDPATH=%PATH%
set PATH=C:\Python27;C:\Python27\Scripts;C:\OSGeo4W\bin;C:\Program Files (x86)\PostgreSQL\9.0\bin;C:\Program Files (x86)\Citilabs\CubeVoyager;C:\Program Files (x86)\Git\bin;C:\CountDracula\geodjango
set PYTHONPATH=%DTA_CODE_DIR%;%COUNTDRACULA_CODE_DIR%;C:\CountDracula\geodjango
python %DTA_CODE_DIR%\scripts\attachCountsFromCountDracula_AM.py -l sf_links.shp -m sf_movements.shp -n sf_nodes.shp . %DYNAMEQ_NET_PREFIX%
set PATH=%OLDPATH%
IF ERRORLEVEL 1 goto done

:done