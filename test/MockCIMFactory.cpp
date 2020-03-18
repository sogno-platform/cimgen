#include "gtest/gtest.h"
#include "CIMFactory.hpp"
#include "String.hpp"

TEST(CIMFactory, CanCreateSomething) {
  CIMFactory factory;
  String name("ACLineSegment");
  EXPECT_EQ(factory.IsCIMClass(name), true);
  BaseClass *bc = factory.CreateNew(name);
  ASSERT_NE(bc, nullptr);
}
