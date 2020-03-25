#ifndef BOOLEAN_H
#define BOOLEAN_H

#include <string>
#include <iostream>
#include <istream>

#include "BaseClass.hpp"

/**
 * A type with the value space "true" and "false".
 */
class Boolean
{
public:
	Boolean();
	virtual ~Boolean();
	static const BaseClassDefiner define();

	Boolean(bool value);
	Boolean& operator=(bool &rop);
	friend std::istream& operator>>(std::istream& lop, Boolean& rop);
	operator bool();

	bool value = false;
	bool initialized = false;

	static const char debugName[];
	virtual const char* debugString();
	
	static void addConstructToMap(std::unordered_map<std::string, BaseClass* (*)()>& factory_map);
	static void addPrimitiveAssignFnsToMap(std::unordered_map<std::string, assign_function>&);
	static void addClassAssignFnsToMap(std::unordered_map<std::string, class_assign_function>&);
};

#endif
