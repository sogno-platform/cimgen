from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class Validity(Base):
	'''
	Validity for MeasurementValue.

		'''

	possibleProfileList = {'class': ['EQ', ],
												}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=Validity\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
