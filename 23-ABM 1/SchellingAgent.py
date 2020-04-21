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
    def __init__(self, pos, grid, agent_type):
        '''
         Create a new Schelling agent.

         Args:
            pos: (x, y) Agent initial location.
            grid: a grid of the city, where 0=empty, 1=minority, 2=majority 
            agent_type: Indicator for the agent's type (minority=1, majority=2)
        '''
        self.pos = pos
        self.grid = grid
        self.type = agent_type
        
        self.grid[pos[0]][pos[1]] = self.type
        
    
    def calculate_similarity(self):
        '''
        Calculates the similarity ratio for the agent.  Defined as:
            similarity = neighbors of same type / total (non-empty) neighbors
        '''
        print('Implement calculate_similarity()')

    def is_happy(self): 
        '''
        The agent is happy if at least 30% of its neighbors are of the same type. 
        '''
        print('Implement is_happy()')
        
    def move(self):
        '''
        Moves the agent to a randomly selected empty square.  
        '''
        print('Implement move')
        