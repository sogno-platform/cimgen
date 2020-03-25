#include "Boolean.hpp"
#include "../src/CIMExceptions.hpp"

Boolean::Boolean(){

}

Boolean::~Boolean(){

}

Boolean::Boolean(bool value)
        : value(value), initialized(true)
{
}

const BaseClassDefiner Boolean::define()
{
	return BaseClassDefiner(Boolean::addConstructToMap, Boolean::addPrimitiveAssignFnsToMap, Boolean::addClassAssignFnsToMap, Boolean::debugName);
}

Boolean& Boolean::operator=(bool &rop)
{
	value = rop;
	initialized = true;
	return *this;
}

Boolean::operator bool()
{
	if(!initialized)
	{
		throw new ReadingUninitializedField();
	}
	return value;
}

void Boolean::addConstructToMap(std::unordered_map<std::string, BaseClass* (*)()>& factory_map) {
	//factory_map.insert(std::make_pair(std::string("cim:Boolean"), &Boolean_factory));
}

void Boolean::addPrimitiveAssignFnsToMap(std::unordered_map<std::string, assign_function>& assign_map) {
	//assign_map.insert(std::make_pair(std::string("cim:ActivePower.value"), &assign_ActivePower_value));
}

void Boolean::addClassAssignFnsToMap(std::unordered_map<std::string, class_assign_function>& assign_map) {
	//assign_map.insert(std::make_pair(std::string("cim:ActivePower.unit"), &assign_ActivePower_unit));
	//assign_map.insert(std::make_pair(std::string("cim:ActivePower.multiplier"), &assign_ActivePower_multiplier));
}

const char Boolean::debugName[] = "Boolean";
const char* Boolean::debugString()
{
	return Boolean::debugName;
}

std::istream& operator>>(std::istream& lop, Boolean& rop)
{
	std::string tmp;
	lop >> tmp;
	if(tmp == "true" || tmp == "True" || tmp == "TRUE")
	{
		rop.value = true;
		rop.initialized = true;
		return lop;
	}
	if(tmp == "false" || tmp == "False" || tmp == "FALSE")
	{
		rop.value = false;
		rop.initialized = true;
		return lop;
	}
	else
	{
		lop.setstate(std::ios::failbit);
		return lop;
	}
}

