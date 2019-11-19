from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class PerCent(Base):
	'''
	Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.

	:value: Normally 0 - 100 on a defined base Default: 0.0
	:unit:  Default: None
	:multiplier:  Default: None
		'''

	possibleProfileList = {'class': ['EQ', 'SSH', ],
						'value': ['EQ', 'SSH', ],
						'unit': ['EQ', 'SSH', ],
						'multiplier': ['EQ', 'SSH', ],
												}

	

	def __init__(self, value = 0.0, unit = None, multiplier = None,  ):
	
		self.value = value
		self.unit = unit
		self.multiplier = multiplier
		
	def __str__(self):
		str = 'class=PerCent\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
