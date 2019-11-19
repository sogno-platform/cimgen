from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class DroopSignalFeedbackKind(Base):
	'''
	Governor droop signal feedback source.

		'''

	possibleProfileList = {'class': ['DY', ],
												}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=DroopSignalFeedbackKind\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
