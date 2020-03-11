#ifndef CIMFACTORY_HPP
#define CIMFACTORY_HPP

#include <string>
#include <unordered_map>
#include "BaseClass.h"

class CIMFactory
{
public:
	CIMFactory();
	virtual ~CIMFactory();
	virtual BaseClass* CreateNew(const std::string& name);
	virtual bool IsCIMClass(const std::string& name);
	static CIMFactory* GetCIMFactory();

private:
	static std::unordered_map<std::string, BaseClass* (*)()> factory_map;
};

#endif // CIMFACTORY_HPP
