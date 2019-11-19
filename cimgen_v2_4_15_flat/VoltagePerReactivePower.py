from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class VoltagePerReactivePower(Base):
	'''
	Voltage variation with reactive power.

	:value:  Default: 0.0
	:unit:  Default: None
	:denominatorMultiplier:  Default: None
	:multiplier:  Default: None
	:denominatorUnit:  Default: None
		'''

	possibleProfileList = {'class': ['EQ', ],
						'value': ['EQ', ],
						'unit': ['EQ', ],
						'denominatorMultiplier': ['EQ', ],
						'multiplier': ['EQ', ],
						'denominatorUnit': ['EQ', ],
												}

	

	def __init__(self, value = 0.0, unit = None, denominatorMultiplier = None, multiplier = None, denominatorUnit = None,  ):
	
		self.value = value
		self.unit = unit
		self.denominatorMultiplier = denominatorMultiplier
		self.multiplier = multiplier
		self.denominatorUnit = denominatorUnit
		
	def __str__(self):
		str = 'class=VoltagePerReactivePower\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
