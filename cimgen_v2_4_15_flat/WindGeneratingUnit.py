from cimpy.cimgen_v2_4_15_flat_9.GeneratingUnit import GeneratingUnit


class WindGeneratingUnit(GeneratingUnit):
	'''
	A wind driven generating unit.  May be used to represent a single turbine or an aggregation.

	:windGenUnitType: The kind of wind generating unit Default: None
		'''

	possibleProfileList = {'class': ['EQ', 'SSH', ],
						'windGenUnitType': ['EQ', ],
												}

	__doc__ += '\n Documentation of parent class GeneratingUnit: \n' + GeneratingUnit.__doc__ 

	def __init__(self, windGenUnitType = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.windGenUnitType = windGenUnitType
		
	def __str__(self):
		str = 'class=WindGeneratingUnit\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
