"""
gde 4.2.2018
Adapted from Project Mesa Schelling Model example: 
https://github.com/projectmesa/mesa-schelling-example/blob/master/analysis.ipynb
but changed to run stand-alone. 
""" 

import random
import SchellingAgent

class SchellingModel():
    '''
    Model class for the Schelling segregation model.
    '''

    def __init__(self, height, width, density, minority_pc):
        '''
        '''

        self.height = height
        self.width = width
        self.density = density
        self.minority_pc = minority_pc

        # set up an empty grid
        # 0 = empty, 1=minority agent, 2=majority agent
        self.grid = [[0] * self.height] * self.width
        
        # this is the list of all agents in the model
        agents = []
        
        # Set up agents
        for x in range(0,self.width): 
            for y in range(0, self.height): 
                if random.random() < self.density:
                    if random.random() < self.minority_pc:
                        agent_type = 1
                    else:
                        agent_type = 2

                    self.grid[x][y] = agent_type
                    a = SchellingAgent((x, y), self, agent_type)
                    self.agents.append(a)

    def __str__(self):
        '''
        This method gets called when you print the object.  
        '''
        return('Implement __str__()')
        
    def step(self):
        '''
        Run one step of the model. If All agents are happy, halt the model.
        '''
        print('Implement step')
        
