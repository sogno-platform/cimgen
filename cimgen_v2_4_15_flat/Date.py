from cimpy.cimgen_v2_4_15_flat_9.Base import Base


class Date(Base):
	'''
	Date as "yyyy-mm-dd", which conforms with ISO 8601. UTC time zone is specified as "yyyy-mm-ddZ". A local timezone relative UTC is specified as "yyyy-mm-dd(+/-)hh:mm".

		'''

	possibleProfileList = {'class': ['DI', 'DY', 'EQ', 'GL', 'SV', 'SSH', 'TP', ],
												}

	

	def __init__(self,  ):
	
		pass
	
	def __str__(self):
		str = 'class=Date\n'
		attributes = self.__dict__
		for key in attributes.keys():
			str = str + key + '={}\n'.format(attributes[key])
		return str
