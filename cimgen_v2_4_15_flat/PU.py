from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class PU(Base):
	'''
	Per Unit - a positive or negative value referred to a defined base. Values typically range from -10 to +10.

	:value:  Default: 0.0
	:unit:  Default: None
	:multiplier:  Default: None
		'''

	possibleProfileList = {'class': ['DY', 'EQ', 'SSH', ],
						'value': ['DY', 'EQ', 'SSH', ],
						'unit': ['DY', 'EQ', 'SSH', ],
						'multiplier': ['DY', 'EQ', 'SSH', ],
												}

	

	def __init__(self, value = 0.0, unit = None, multiplier = None,  ):
	
		self.value = value
		self.unit = unit
		self.multiplier = multiplier
		
	def __str__(self):
		str = 'class=PU\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
