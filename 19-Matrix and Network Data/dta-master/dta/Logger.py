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

import logging

__all__ = ['DtaLogger', 'setupLogging']


#: This is the instance of :py:class:`Logger` that gets used for all dta logging needs!
DtaLogger = logging.getLogger("DTALogger")

def setupLogging(infoLogFilename, debugLogFilename, logToConsole=True):
    """ 
    Sets up the logger.
    
    :param infoLogFilename: info log file, will receive log messages of level INFO or more important.
       Pass None for no info log file.
    :param debugLogFilename: debug log file, will receive log messages of level DEBUG or more important.
       Pass None for no debug log file.
    :param logToConsole: if true, INFO and above will also go to the console.

    """
    # already setup - don't setup more
    if len(DtaLogger.handlers) == 3:
        return
    
    # create a logger
    DtaLogger.setLevel(logging.DEBUG)

    if infoLogFilename:
        infologhandler = logging.StreamHandler(open(infoLogFilename, 'w'))
        infologhandler.setLevel(logging.INFO)
        infologhandler.setFormatter(logging.Formatter('%(message)s'))
        DtaLogger.addHandler(infologhandler)
    
    if debugLogFilename:
        debugloghandler = logging.StreamHandler(open(debugLogFilename,'w'))
        debugloghandler.setLevel(logging.DEBUG)
        debugloghandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M'))
        DtaLogger.addHandler(debugloghandler)
    
    if logToConsole:
        consolehandler = logging.StreamHandler()
        consolehandler.setLevel(logging.INFO)
        consolehandler.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
        DtaLogger.addHandler(consolehandler)
        
        
