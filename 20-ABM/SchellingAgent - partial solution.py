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
        
        # set up some counters
        same_type_neighbors = 0
        total_neighbors = 0
        
        # get x, y for convenience
        x, y = self.pos
        
        # get rows, columns for convenience
        rows = len(self.grid)
        cols = len(self.grid[0])
        
        # look at each of the neighbors in the grid
        # start at the top left, put them in a logical order
        neighbors = [(x-1,y+1),(x,y+1),(x+1,y+1),
                     (x-1,y),          (x+1,y),
                     (x-1,y-1),(x,y-1),(x+1,y-1)]
                
        # make sure they are in bounds
        # increment accordingly      
        for nx, ny in neighbors:           
            if nx in range(0, rows) and ny in range(0, cols): 
                if self.grid[nx][ny] == self.type: 
                    same_type_neighbors += 1
                if self.grid[nx][ny] != 0: 
                    total_neighbors += 1
        
        if total_neighbors>0: 
            return same_type_neighbors / total_neighbors
        else:
            return 0

    def is_happy(self): 
        '''
        The agent is happy if at least 30% of its neighbors are of the same type. 
        '''
        if self.calculate_similarity() > 0.3: 
            return True
        else: 
            return False
        
    def move(self):
        '''
        Moves the agent to a randomly selected empty square.  
        '''
                
        # get rows, columns for convenience
        rows = len(self.grid)
        cols = len(self.grid[0])
        
        # get a list of the empty squares
        empty_squares = []
        
        for x in range(0,rows):
            for y in range(1,cols):
                if self.grid[x][y] == 0:
                    empty_squares.append((x,y))
        
        # define cumulative probability array
        cum_prob = 0
        cum_prob_array = []
        for i in range(0, len(empty_squares)):
            cum_prob += 1 / len(empty_squares)
            cum_prob_array.append(cum_prob)
            
        rand = random.random()
        for i in range(0, len(cum_prob_array):
            if rand < cum_prob_array[i]:
                new_pos = empty_squares[i]
                break 
        
        # update old square to zero
        self.grid[self.pos[0]][self.pos[1]] = 0
        
        # update my position
        self.pos = new_pos
        
        # update new square to my type
        self.grid[new_pos[0]][new_pos[1]] = self.type
        
        print('Implement move')
        