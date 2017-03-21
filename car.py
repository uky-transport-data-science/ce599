# Define the class
class car():
    """
    It is a car with certain given attributes like location, color and direction it is facing.     
    """
    
    #Constants   
    #: Static variable representing the units of the color variable
    #: Should be a color - green or yellow
    # Constructor
    # this says what happens when a new road is created
    def __init__(self, color,locx=0,locy=0,ffdir=1):
	
        """
        Car attributes: color is imput by user, default (x,y) coordinates are (0,0)
		Default final facing direction is north. Final facing direction (ffdir) is calculated by the number of spaces the car has moved.
        """
        
        # some error checks are nice here...
        # if lanes <= 0: 
        #   raise RuntimeError("Cannot have negative lanes!")

        # the scope of lanes is limited to this method
        # to use it more broadly, we need to assign it to self.lanes
        # then we can use the dot notation. 
        self.color = color
        
        # can set stuff automatically
        # self.locx = locx
		# self.locy = locy
		# self.ffdir = ffdir
        
    # other methods
    def moveCar(self): 
        """
        A docstring comment describing all inputs and any returns (i.e. the API). 
        And basically what it does. 
        """
        if self.color=='yellow':
            self.locx=-1
            self.locy=2
            self.ffdir=4
            print("Yellow car faces westwards!")
        elif self.color=='green':
            self.locx=-1
            self.locy=2
            self.ffdir=1
            print("Green car faces northwards!")

