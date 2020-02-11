///////////////////////////////////////////////////////////
//  IEC61970CIMVersion.h
//  Implementation of the Class IEC61970CIMVersion
///////////////////////////////////////////////////////////

#ifndef IEC61970CIMVERSION_H
#define IEC61970CIMVERSION_H

#include "BaseClass.hpp"
#include "Date.hpp"
#include "String.hpp"

namespace IEC61970
{
	/**
	 * This is the IEC 61970 CIM version number assigned to this UML model.
	 */
	class IEC61970CIMVersion : public BaseClass
	{

	public:
		IEC61970CIMVersion();
		virtual ~IEC61970CIMVersion();
		/**
		 * Form is YYYY-MM-DD for example for January 5, 2009 it is 2009-01-05.
		 */
		static const Date date;
		/**
		 * Form is IEC61970CIMXXvYY where XX is the major CIM package version and the YY
		 * is the minor version. For example IEC61970CIM13v18.
		 */
		static const String version;
	};
}
#endif // IEC61970CIMVERSION_H
