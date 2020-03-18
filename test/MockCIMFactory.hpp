#ifndef MOCKCIMFACTORY_HPP
#define MOCKCIMFACTORY_HPP

#include "gmock/gmock.h"

#include <string>
#include <unordered_map>
#include "CIMFactory.hpp"


class MockCIMFactory: public CIMFactory
{
public:
    MockCIMFactory() { }
    ~MockCIMFactory() { }
    BaseClass* CreateNew(const std::string& name) override {
        return CIMFactory::CreateNew(name);
    }
    bool IsCIMClass(std::string& name) {
        return CIMFactory::CreateNew(name);
    }
};

#endif // MOCKCIMFACTORY_HPP
