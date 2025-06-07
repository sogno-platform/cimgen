# Generates modern Python (3.9+)

- [Generates modern Python (3.9+)](#generates-modern-python-39)
  - [Description](#description)
  - [Warning](#warning)
  - [Examples](#examples)
    - [Python](#python)
    - [Modern Python](#modern-python)

## Description

It mostly uses dataclasses (pydantic one, to get data checks) and adds some attribute walking
directly into the class. See for instance `cgmes_attributes_in_profile` in [base.py](utils/base.py).

## Warning

This is a major change compared to `python`, and makes it not compatible with cimexport. But by adding
the attribute walk and adding the profiles as metadata from the attributes, it would make cimexport (or any
other code using these classes) much simpler.

## Examples

Example of ACLineSegment (generated with --cgmes_version cgmes_v3_0_0).

### Python

```python
from .Conductor import Conductor
from .CGMESProfile import Profile


class ACLineSegment(Conductor):
    """
    A wire or combination of wires, with consistent electrical characteristics, building a single electrical system, used to carry alternating current between points in the power system. For symmetrical, transposed three phase lines, it is sufficient to use attributes of the line segment, which describe impedances and admittances for the entire length of the segment.  Additionally impedances can be computed by using length and associated per length impedances. The BaseVoltage at the two ends of ACLineSegments in a Line shall have the same BaseVoltage.nominalVoltage. However, boundary lines may have slightly different BaseVoltage.nominalVoltages and variation is allowed. Larger voltage difference in general requires use of an equivalent branch.

    :Clamp: The clamps connected to the line segment. Default: "list"
    :Cut: Cuts applied to the line segment. Default: "list"
    :b0ch: Zero sequence shunt (charging) susceptance, uniformly distributed, of the entire line section. Default: 0.0
    :bch: Positive sequence shunt (charging) susceptance, uniformly distributed, of the entire line section.  This value represents the full charging over the full length of the line. Default: 0.0
    :g0ch: Zero sequence shunt (charging) conductance, uniformly distributed, of the entire line section. Default: 0.0
    :gch: Positive sequence shunt (charging) conductance, uniformly distributed, of the entire line section. Default: 0.0
    :r: Positive sequence series resistance of the entire line section. Default: 0.0
    :r0: Zero sequence series resistance of the entire line section. Default: 0.0
    :shortCircuitEndTemperature: Maximum permitted temperature at the end of SC for the calculation of minimum short-circuit currents. Used for short circuit data exchange according to IEC 60909. Default: 0.0
    :x: Positive sequence series reactance of the entire line section. Default: 0.0
    :x0: Zero sequence series reactance of the entire line section. Default: 0.0
    """

    possibleProfileList = {
        "class": [Profile.EQ.value, Profile.SC.value, ],
        "Clamp": [Profile.EQ.value, ],
        "Cut": [Profile.EQ.value, ],
        "b0ch": [Profile.SC.value, ],
        "bch": [Profile.EQ.value, ],
        "g0ch": [Profile.SC.value, ],
        "gch": [Profile.EQ.value, ],
        "r": [Profile.EQ.value, ],
        "r0": [Profile.SC.value, ],
        "shortCircuitEndTemperature": [Profile.SC.value, ],
        "x": [Profile.EQ.value, ],
        "x0": [Profile.SC.value, ],
    }

    serializationProfile = {}

    recommendedClassProfile = Profile.EQ.value

    __doc__ += "\nDocumentation of parent class Conductor:\n" + Conductor.__doc__

    def __init__(self, Clamp = "list", Cut = "list", b0ch = 0.0, bch = 0.0, g0ch = 0.0, gch = 0.0, r = 0.0, r0 = 0.0, shortCircuitEndTemperature = 0.0, x = 0.0, x0 = 0.0, *args, **kw_args):
        super().__init__(*args, **kw_args)

        self.Clamp = Clamp
        self.Cut = Cut
        self.b0ch = b0ch
        self.bch = bch
        self.g0ch = g0ch
        self.gch = gch
        self.r = r
        self.r0 = r0
        self.shortCircuitEndTemperature = shortCircuitEndTemperature
        self.x = x
        self.x0 = x0

    def __str__(self):
        str = "class=ACLineSegment\n"
        attributes = self.__dict__
        for key in attributes.keys():
            str = str + key + "={}\n".format(repr(attributes[key]))
        return str
```

### Modern Python

```python
"""
Generated from the CGMES files via cimgen: https://github.com/sogno-platform/cimgen
"""

from functools import cached_property
from typing import Optional

from pydantic import Field
from pydantic.dataclasses import dataclass

from ..utils.profile import BaseProfile, Profile
from .Conductor import Conductor


@dataclass
class ACLineSegment(Conductor):
    """
    A wire or combination of wires, with consistent electrical characteristics, building a single electrical system,
      used to carry alternating current between points in the power system. For symmetrical, transposed three phase
      lines, it is sufficient to use attributes of the line segment, which describe impedances and admittances for
      the entire length of the segment.  Additionally impedances can be computed by using length and associated per
      length impedances. The BaseVoltage at the two ends of ACLineSegments in a Line shall have the same
      BaseVoltage.nominalVoltage. However, boundary lines may have slightly different BaseVoltage.nominalVoltages
      and variation is allowed. Larger voltage difference in general requires use of an equivalent branch.

    Clamp: The clamps connected to the line segment.
    Cut: Cuts applied to the line segment.
    b0ch: Zero sequence shunt (charging) susceptance, uniformly distributed, of the entire line section.
    bch: Positive sequence shunt (charging) susceptance, uniformly distributed, of the entire line section.  This value
      represents the full charging over the full length of the line.
    g0ch: Zero sequence shunt (charging) conductance, uniformly distributed, of the entire line section.
    gch: Positive sequence shunt (charging) conductance, uniformly distributed, of the entire line section.
    r: Positive sequence series resistance of the entire line section.
    r0: Zero sequence series resistance of the entire line section.
    shortCircuitEndTemperature: Maximum permitted temperature at the end of SC for the calculation of minimum short-
      circuit currents. Used for short circuit data exchange according to IEC 60909.
    x: Positive sequence series reactance of the entire line section.
    x0: Zero sequence series reactance of the entire line section.
    """

    Clamp: list = Field(
        default_factory=list,
        json_schema_extra={
            "in_profiles": [
                Profile.EQ,
            ],
            "is_used": False,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": False,
            "is_enum_attribute": False,
            "is_list_attribute": True,
            "is_primitive_attribute": False,
        },
    )

    Cut: list = Field(
        default_factory=list,
        json_schema_extra={
            "in_profiles": [
                Profile.EQ,
            ],
            "is_used": False,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": False,
            "is_enum_attribute": False,
            "is_list_attribute": True,
            "is_primitive_attribute": False,
        },
    )

    b0ch: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.SC,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Susceptance",
        },
    )

    bch: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.EQ,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Susceptance",
        },
    )

    g0ch: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.SC,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Conductance",
        },
    )

    gch: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.EQ,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Conductance",
        },
    )

    r: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.EQ,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Resistance",
        },
    )

    r0: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.SC,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Resistance",
        },
    )

    shortCircuitEndTemperature: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.SC,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Temperature",
        },
    )

    x: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.EQ,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Reactance",
        },
    )

    x0: float = Field(
        default=0.0,
        json_schema_extra={
            "in_profiles": [
                Profile.SC,
            ],
            "is_used": True,
            "namespace": "http://iec.ch/TC57/CIM100#",  # NOSONAR
            "is_class_attribute": False,
            "is_datatype_attribute": True,
            "is_enum_attribute": False,
            "is_list_attribute": False,
            "is_primitive_attribute": False,
            "attribute_class": "Reactance",
        },
    )

    @cached_property
    def possible_profiles(self) -> set[BaseProfile]:
        """
        A resource can be used by multiple profiles. This is the set of profiles
        where this element can be found.
        """
        return {
            Profile.EQ,
            Profile.SC,
        }

    @cached_property
    def recommended_profile(self) -> BaseProfile:
        """
        This is the profile with most of the attributes.
        It should be used to write the data to as few as possible files.
        """
        return Profile.EQ
```
