from cimpy.cimgen_v2_4_15_flat_9.IdentifiedObject import IdentifiedObject


class DynamicsFunctionBlock(IdentifiedObject):
	'''
	Abstract parent class for all Dynamics function blocks.

	:enabled: Function block used indicator. true = use of function block is enabled false = use of function block is disabled. Default: False
		'''

	possibleProfileList = {'class': ['DY', ],
						'enabled': ['DY', ],
												}

	__doc__ += '\n Documentation of parent class IdentifiedObject: \n' + IdentifiedObject.__doc__ 

	def __init__(self, enabled = False,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.enabled = enabled
		
	def __str__(self):
		str = 'class=DynamicsFunctionBlock\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
