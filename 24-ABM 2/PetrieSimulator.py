"""
Comments to start
"""

# imports
import random

class PetrieSimulation():
    '''
    Comment about what I do
    '''
    
        
    # actions
    def __init__(self, num_people, pct_women, pct_making_sexist_comments):
        '''
        Create a new Petrie Simulation
        '''
        
        # attributes
        men = []
        women = []
        
        # create an initial list of men and women
        for i in range(0, num_people):
            if random.random() < pct_women: 
                if random.random() < pct_making_sexist_comments: 
                    # create a sexist woman
                    p = Person('Female', True)
                else: 
                    # create a not sexist woman   
                    p = Person('Female')
                women.append(p)
            else: 
                if random.random() < pct_making_sexist_comments: 
                    # create a sexist man
                    p = Person('Male', True)
                else: 
                    # create a not sexist man   
                    p = Person('Male')
                men.append(p)
                
    def run(self, num_iterations):
        for i in range(0, num_iterations): 
            self.run_iteration()
            self.print_model_statistics()
                
    def run_iteration(self):
        # loop through men and have them make sexists where relevant
        for m in men: 
            if m.is_sexist:
                m.make_sexist_comment(women)
                                
        # loop through the women and have them make sexist comments where relevant
        for w in women: 
            if w.is_sexist:
                w.make_sexist_comment(men)
    
    def print_model_statistics():
        '''
        print percent_receiving_sexist_comments by sex
        print percent making sexist comments by sex
        print other stats of interest
        ''' 
        print('Print something')
    