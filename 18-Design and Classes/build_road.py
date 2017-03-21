"""
 Some text here to say what this is script does and how to call it.
 
 Usage: 
 
    python build_road.py [num_lanes]
  
 e.g.
 
    python build_road.py 2
 
"""

#----------------------------------------------------------------------------------------------------
# IMPORTS
#----------------------------------------------------------------------------------------------------

# general imports first
import sys
import time

# make sure we can find our class files
sys.path.append('C:/WORKSPACE/uky-transport-data-science/ce599-s17/18-Design and Classes/transport')

# now our own specific imports
from Road import Road

#----------------------------------------------------------------------------------------------------
# User inputs next, so they are easy to find and change.
#  Keep these out of your classes, so the classes are more general. 
#  The capital letters are a convention for a constant. 
#----------------------------------------------------------------------------------------------------
# Add comments to say what these are
DEFAULT_SPEEDS = {'Freeway' : 65, 
                  'Arterial' : 35, 
                  'Collector' : 30, 
                  'Local' : 20}

# FILES--change as needed
INFILE = "C:/temp/blueprints.txt"
OUTFILE = "C:/temp/finished_road.txt"
    

#----------------------------------------------------------------------------------------------------
# Main function call. 
#----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    
    # this lets you specify a command line argument.  The first argument is the 
    # name of the script.  LANES is capital because it won't change during the script. 
    if len(sys.argv) < 2:
        print('Enter the number of lanes: python build_road.py 2')
        sys.exit(2)
    LANES = int(sys.argv[1])
    
    # do some stuff
    limestone = Road(LANES)
    print('Repaved at: ', limestone.repave_date)
    time.sleep(3)
    limestone.repave()
    print('Repaved at: ', limestone.repave_date)
    
    # all done
    print('Run complete!  Woohoo!')
