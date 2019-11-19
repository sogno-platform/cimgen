from cimpy.cimgen_v2_4_15_flat_9.IdentifiedObject import IdentifiedObject


class DCTopologicalNode(IdentifiedObject):
	'''
	DC bus.

	:DCTopologicalIsland:  Default: None
	:DCTerminals: See association end Terminal.TopologicalNode. Default: []
	:DCEquipmentContainer:  Default: None
	:DCNodes: See association end ConnectivityNode.TopologicalNode. Default: []
		'''

	possibleProfileList = {'class': ['SV', 'TP', ],
						'DCTopologicalIsland': ['SV', ],
						'DCTerminals': ['TP', ],
						'DCEquipmentContainer': ['TP', ],
						'DCNodes': ['TP', ],
												}

	__doc__ += '\n Documentation of parent class IdentifiedObject: \n' + IdentifiedObject.__doc__ 

	def __init__(self, DCTopologicalIsland = None, DCTerminals = [], DCEquipmentContainer = None, DCNodes = [],  *args, **kw_args):
		super().__init__(*args, **kw_args)
	
		self.DCTopologicalIsland = DCTopologicalIsland
		self.DCTerminals = DCTerminals
		self.DCEquipmentContainer = DCEquipmentContainer
		self.DCNodes = DCNodes
		
	def __str__(self):
		str = 'class=DCTopologicalNode\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
