"""
gde 4.2.2018
Adapted from Project Mesa Schelling Model example: 
https://github.com/projectmesa/mesa-schelling-example/blob/master/analysis.ipynb
but changed to run stand-alone. 
""" 

import random
from SchellingAgent import SchellingAgent

class SchellingModel():
    '''
    Model class for the Schelling segregation model.
    '''

    def __init__(self, height, width, density, minority_pc):
        '''
        Create a new SchellingModel. 
        
        height - rows in the city
        width - columns in the city
        density - share of cells that are occupied housing units
        minority_pc - share of agents that are of the minority type
        '''

        self.height = height
        self.width = width
        self.density = density
        self.minority_pc = minority_pc

        # set up an empty grid
        # 0 = empty, 1=minority agent, 2=majority agent
        self.grid = [[0] * self.height] * self.width
        
        # this is the list of all agents in the model
        self.agents = []
        
        # Set up agents
        for x in range(0,self.width): 
            for y in range(0, self.height): 
                if random.random() < self.density:
                    if random.random() < self.minority_pc:
                        agent_type = 1
                    else:
                        agent_type = 2

                    a = SchellingAgent((x, y), self.grid, agent_type)
                    self.agents.append(a)

    def print_status(self):
        '''
        Print relevant information about the current state of affairs.  
        '''
        return('Implement print_status()')
        
    def step(self):
        '''
        Run one step of the model.  Let unhappy agents move to an empty square. 
        '''
        print('Implement step')
        
    def run(self, max_iter=30): 
        '''
        Runs all iterations of the model. 
        max_iters - the maximum number of iterations to run. 
        If All agents are happy, halt the model.
        '''
        print('Implement run')
