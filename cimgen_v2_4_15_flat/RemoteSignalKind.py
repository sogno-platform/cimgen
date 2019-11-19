from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class RemoteSignalKind(Base):
	'''
	Type of input signal coming from remote bus.

		'''

	possibleProfileList = {'class': ['DY', ],
												}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=RemoteSignalKind\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
