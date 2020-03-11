#ifndef MOCKCIMFACTORY_HPP
#define MOCKCIMFACTORY_HPP

#include "gmock/gmock.h"

#include <string>
#include <unordered_map>
#include "CIMFactory.hpp"


class MockCIMFactory: public CIMFactory
{
public:
	MockCIMFactory() {}
	~MockCIMFactory() {}
	MOCK_METHOD((BaseClass*), CreateNew, (const std::string& name), (override));
	//MOCK_METHOD(bool, IsCIMClass, std::string& name);
};

#endif // MOCKCIMFACTORY_HPP
