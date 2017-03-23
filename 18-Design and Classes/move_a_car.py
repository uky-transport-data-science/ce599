#imports
import sys
sys.path.append('C:/Users/Owner/Documents/0Senior Uk/CE599/ce599-s17/18-Design and Classes/transport')

#calling the cars import
from Car import Car

if __name__=="__main__":
	
	Cary= Car(color= 'yellow', location=[0,0],direction='F')
	Cary.printcar()
	Cary.go(2,'forward')
	Cary.turn_left()
	Cary.go(1,'forward')
	Cary.printcar()

	
	
	Carg=Car(color= 'green', location=[0,0],direction='F')
	Carg.printcar()
	Carg.left_turn()
	Carg.go(1,'forward')
	Carg.right_turn()
	Carg.go(2,'forward')
	Carg.printcar()
	
	print('Are you a Packers fan for picking yellow and green cars?')