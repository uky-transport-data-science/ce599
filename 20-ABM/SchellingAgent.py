"""
gde 4.2.2018
Adapted from Project Mesa Schelling Model example: 
https://github.com/projectmesa/mesa-schelling-example/blob/master/analysis.ipynb
but changed to run stand-alone. 
""" 

import random

class SchellingAgent():
    '''
    Schelling segregation agent
    '''
    def __init__(self, pos, model, agent_type):
        '''
         Create a new Schelling agent.

         Args:
            pos: (x, y) Agent initial location.
            model: a SchellingModel to tell the agent its environment. 
            agent_type: Indicator for the agent's type (minority=1, majority=2)
        '''
        self.pos = pos
        self.model = model
        self.type = agent_type
        

    def is_happy(self): 
        '''
        The agent is happy if at least 3 of its neighbors are of the same type. 
        '''
        print('Implement is_happy()')
        
    def move(self):
        '''
        Moves the agent to a randomly selected empty square.  
        '''
        print('Implement move')
        