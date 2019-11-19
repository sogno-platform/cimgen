from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class AngleDegrees(Base):
	'''
	Measurement of angle in degrees.

	:value:  Default: 0.0
	:unit:  Default: None
	:multiplier:  Default: None
		'''

	possibleProfileList = {'class': ['DI', 'DY', 'EQ', 'SV', 'SSH', ],
						'value': ['DI', 'DY', 'EQ', 'SV', 'SSH', ],
						'unit': ['DI', 'DY', 'EQ', 'SV', 'SSH', ],
						'multiplier': ['DI', 'DY', 'EQ', 'SV', 'SSH', ],
												}

	

	def __init__(self, value = 0.0, unit = None, multiplier = None,  ):
	
		self.value = value
		self.unit = unit
		self.multiplier = multiplier
		
	def __str__(self):
		str = 'class=AngleDegrees\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
