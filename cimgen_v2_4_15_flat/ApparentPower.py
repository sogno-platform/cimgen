from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class ApparentPower(Base):
	'''
	Product of the RMS value of the voltage and the RMS value of the current.

	:value:  Default: 0.0
	:unit:  Default: None
	:multiplier:  Default: None
		'''

	possibleProfileList = {'class': ['DY', 'EQ', ],
						'value': ['DY', 'EQ', ],
						'unit': ['DY', 'EQ', ],
						'multiplier': ['DY', 'EQ', ],
												}

	

	def __init__(self, value = 0.0, unit = None, multiplier = None,  ):
	
		self.value = value
		self.unit = unit
		self.multiplier = multiplier
		
	def __str__(self):
		str = 'class=ApparentPower\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
