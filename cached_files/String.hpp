#ifndef STRING_H
#define STRING_H

#include "BaseClass.hpp"
#include "string"

/*
A string consisting of a sequence of characters. The character encoding is UTF-8. The string length is unspecified and unlimited.
*/
class String: public BaseClass
{
private:
	std::string data;
public:

	/* constructor initialising all attributes to null */
	String();
	String(std::string*);
	virtual ~String();
};

BaseClass* String_factory();

#endif
