"""
Add a comment here about what this is....
"""

# imports

class Person():
    '''
    Represenation of a person in a Petrie Simulation
    '''
    
    # attributes
    def __init__(self, sex, is_sexist=False): 
    
        # True if makes sexist comments false if not
        self.is_sexist = is_sexist  
        
        # male or female
        self.sex = sex        
        
        # count of sexist comments received
        self.num_sexist_comments_recieved = 0    
        
        # count of sexist comments made
        self.num_sexist_comments_made = 0
    
    # actions
    make_sexist_comment()              # makes a sexist comment to someone else
    receive_sexist_comment()           # recieves a sexist comment
    intervene()                        # makes a bystander intervention
    consider_dropping_out()            # drops out if receives >N sexist comments
