#Starting Factors
START_NORTH = 0
START_SOUTH = 0
START_EAST = 0
START_WEST = 0

# Define the class
class Car(object):
    """
    This class is titled car that has attributes: color, location (x,y), and direction..     
    """
    
    def __init__(self, color,location=[0,0],direction= 0):
		if len(location) !=2:
			print('this is a 2D system so only 2 please')
		else:
			self.color= color
			self.location = location 
			self.x = location[0]
			self.y = location [1]
			self.direction = direction 
		
    def go(self,units,movement): 
        """
		This is the section of the script where the car moves in vector form.
        """
        if movement == 'forward':
			
			if self.direction== 'F':
				self.y = self.y + units
			elif self.direction =='B':
				self.y = self.y- units
			elif self.direction == 'L':
				self.x = self.x - units
			elif self.direction == 'R':
				self.x =self.x+ units
			else:
				print('Please enter F for forward, B for backwards, L for left, or R for right.')
			self.location=[self.x,se;f.y]
		elif movement == 'backward':
			
			if self.direction == 'B':
				self.y = self.y- units
			elif self.direction == 'F':
				self.y = self.y + units
			elif self.direction==' L':
				self.x =self.x - units
			elif self.direction=='E':
				self.x = self.x + units
			else:
				print('Again please enter F for forward, B for backwards, L for left, or R for right.')
			self.location = [self.x,self.y]
		else:
			print('Please enter possible movements')
	def left_turn(self):
		if self.direction =='F':
			self.direction= 'L'
		elif self.direction =='B':
			self.direction= 'R'
		elif self.direction == 'L':
			self.direction= 'B'
		elif self.direction =='R':
			self.direction='F'
		else:
			print('Wrong direction please try again')
	def right_turn(self):
		if self.direction =='F':
			self.direction= 'R'
		elif self.direction == 'B':
			self.direction = 'L'
		elif self.direction == 'L':
			self.direction= 'F'
		elif self.direction == 'R':
			self.direction = 'B'
		else:
			print('Wrong direction please try again')
			
    def printcar(self):
		print('Car color is' + self.color)
		print('at'+ self.location)
		print('and facing' + self.direction)
        

