from cimpy.cimgen_v2_4_15_flat_9.Equipment import Equipment


class ConductingEquipment(Equipment):
	'''
	The parts of the AC power system that are designed to carry current or that are conductively connected through terminals.

	:Terminals: Conducting equipment have terminals that may be connected to other conducting equipment terminals via connectivity nodes or topological nodes. Default: []
	:BaseVoltage: All conducting equipment with this base voltage.  Use only when there is no voltage level container used and only one base voltage applies.  For example, not used for transformers. Default: None
	:SvStatus: The status state variable associated with this conducting equipment. Default: None
		'''

	possibleProfileList = {'class': ['DY', 'EQ', 'SV', 'SSH', ],
						'Terminals': ['DY', 'EQ', ],
						'BaseVoltage': ['EQ', ],
						'SvStatus': ['SV', ],
												}

	__doc__ += '\n Documentation of parent class Equipment: \n' + Equipment.__doc__ 

	def __init__(self, Terminals = [], BaseVoltage = None, SvStatus = None,  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.Terminals = Terminals
		self.BaseVoltage = BaseVoltage
		self.SvStatus = SvStatus
		
	def __str__(self):
		str = 'class=ConductingEquipment\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
