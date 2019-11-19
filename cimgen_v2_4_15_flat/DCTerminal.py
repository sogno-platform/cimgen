from cimpy.cimgen_v2_4_15_flat_9.DCBaseTerminal import DCBaseTerminal


class DCTerminal(DCBaseTerminal):
	'''
	An electrical connection point to generic DC conducting equipment.

	:DCConductingEquipment:  Default: None
		'''

	possibleProfileList = {'class': ['EQ', 'SSH', 'TP', ],
						'DCConductingEquipment': ['EQ', ],
												}

	__doc__ += '\n Documentation of parent class DCBaseTerminal: \n' + DCBaseTerminal.__doc__ 

	def __init__(self, DCConductingEquipment = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.DCConductingEquipment = DCConductingEquipment
		
	def __str__(self):
		str = 'class=DCTerminal\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
