"""
 Some text here to say what this is script does and how to call it.
 
 Usage: 
 
    python move_cars.py [car class]
  
 e.g.
 
    python move_cars.py yellow
 
"""

#----------------------------------------------------------------------------------------------------
# IMPORTS
#----------------------------------------------------------------------------------------------------
import sys
# make sure we can find our class files
sys.path.append('C:/Users/shyamalroy/Documents/GitHub/ce599-s17/18-Design and Classes/transport')

# now our own specific imports
from car import car

#----------------------------------------------------------------------------------------------------
# User inputs next, so they are easy to find and change.
#  Keep these out of your classes, so the classes are more general. 
#  The capital letters are a convention for a constant. 
#------------------------------------    

#----------------------------------------------------------------------------------------------------
# Main function call. 
#----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    
    # this lets you specify a command line argument.  The first argument is the 
    # name of the script.  LANES is capital because it won't change during the script. 
    
    color = input("please enter car color: ")
    
    # do some stuff
    coloredCar = car(color,locx=0,locy=0,ffdir=1)
    coloredCar.moveCar()
    print(color, " car at x=", coloredCar.locx)
    print(color, " car at y=", coloredCar.locy)
    print(color, " car at ffdir=", coloredCar.ffdir)
	
    #greenCar = car(color='green',locx=0,locy=0,ffdir=1)
    #greenCar.moveCar()
    #print("Green car at x=", greenCar.locx)
    #print("Green car at y=", greenCar.locy)
    #print("Green car at ffdir=", greenCar.ffdir)
	
	#yellowCar = car(color='yellow',locx=0,locy=0,ffdir=1)
    #yellowCar.moveCar()
    #print("Yellow car at x=", yellowCar.locx)
    #print("Yellow car at y=", yellowCar.locy)
    #print("Yellow car at ffdir=", yellowCar.ffdir)
    
    # all done
    print('Run complete!  Woohoo!')
