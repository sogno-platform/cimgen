#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "CIMFactory.hpp"
#include "MockCIMFactory.hpp"
#include "String.hpp"

using ::testing::AtLeast;
typedef BaseClass* BaseClassPtr;
typedef std::string& StringRef;

TEST(CIMFactory, CanCreateSomething) {
  MockCIMFactory factory;
  String name("ACLineSegment");
  EXPECT_CALL(factory, CreateNew(name));

  //EXPECT_TRUE(factory.CreateNew("ACLineSegment"));
}
