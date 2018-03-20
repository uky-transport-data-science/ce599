# Imports
import datetime 

# Define the class
class Road():
    """
    A comment saying what this class is.     
    """
    
    #Constants
    
    #: Static variable representing the units of the length variable
    #: Should be ``kilometers`` or ``miles``
    LENGTH_UNITS = None
    
    #: default lane width in feet
    DEFAULT_LANE_WIDTH = 12

    # Constructor
    # this says what happens when a new road is created
    def __init__(self, lanes):
        """
        Constructor.        
         * *lanes* the number of lanes
        """
        
        # some error checks are nice here...
        if lanes <= 0: 
            raise RuntimeError("Cannot have negative lanes!")

        # the scope of lanes is limited to this method
        # to use it more broadly, we need to assign it to self.lanes
        # then we can use the dot notation. 
        self.lanes = lanes
        
        # can set stuff automatically
        self.repave_date = datetime.datetime.now()
        
    # other methods
    def repave(self): 
        """
        A docstring comment describing all inputs and any returns (i.e. the API). 
        And basically what it does. 
        """
        
        self.repave_date = datetime.datetime.now()
        

