#include "CIMFactory.hpp"
#include "Folders.hpp"

static std::unordered_map<std::string, BaseClass* (*)()> initialize();
std::unordered_map<std::string, BaseClass* (*)()> CIMFactory::factory_map = initialize();

BaseClass* CIMFactory::CreateNew(const std::string& name)
{
    std::unordered_map<std::string, BaseClass* (*)()>::iterator it = factory_map.find(name);
    if(it != factory_map.end())
        return (*it->second)();
    else
        return nullptr;
}

bool CIMFactory::IsCIMClass(const std::string& name)
{
    std::unordered_map<std::string, BaseClass* (*)()>::iterator it = factory_map.find(name);
    if(it == factory_map.end())
        return false;
    else
        return true;
}

static std::unordered_map<std::string, BaseClass* (*)()> initialize()
{
    std::unordered_map<std::string, BaseClass* (*)()> map;
    std::for_each(std::begin(whitelist), std::end(whitelist)
    [] (typename Container::const_reference element)
    {
        map.insert(element);
    });
}
