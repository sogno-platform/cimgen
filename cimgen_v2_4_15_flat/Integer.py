from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class Integer(Base):
	'''
	An integer number. The range is unspecified and not limited.

		'''

	possibleProfileList = {'class': ['DI', 'DY', 'EQ', 'GL', 'SSH', ],
												}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=Integer\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
