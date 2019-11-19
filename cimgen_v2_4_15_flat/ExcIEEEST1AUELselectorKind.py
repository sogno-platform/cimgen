from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class ExcIEEEST1AUELselectorKind(Base):
	'''
	Type of connection for the UEL input used in ExcIEEEST1A.

		'''

	possibleProfileList = {'class': ['DY', ],
												}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=ExcIEEEST1AUELselectorKind\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
