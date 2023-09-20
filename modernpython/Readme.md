# Generates modern Python (3.9+)

- [Generates modern Python (3.9+)](#generates-modern-python-39)
  - [Description](#description)
  - [Warning](#warning)
  - [Examples](#examples)
    - [Python](#python)
    - [Modern Python](#modern-python)
    - [Modern Python after black (formatting)](#modern-python-after-black-formatting)

## Description

It mostly uses dataclasses (pydantic one, to get data checks) and adds some attribute walking
directly into the class. See for instance `cgmes_attributes_in_profile` in [Base.py](./Base.py).

## Warning

This is a major change compared to `python`, and makes it not compatible with cimexport. But by adding
the attribute walk and adding the profiles as metadata from the attributes, it would make cimexport (or any
other code using these classes) much simpler.

## Examples

Example of ACLineSegment.

### Python

```python
from .Conductor import Conductor


class ACLineSegment(Conductor):
        '''
        A wire or combination of wires, with consistent electrical characteristics, building a single electrical system, used to carry alternating current between points in the power system. For symmetrical, transposed 3ph lines, it is sufficient to use  attributes of the line segment, which describe impedances and admittances for the entire length of the segment.  Additionally impedances can be computed by using length and associated per length impedances. The BaseVoltage at the two ends of ACLineSegments in a Line shall have the same BaseVoltage.nominalVoltage. However, boundary lines  may have slightly different BaseVoltage.nominalVoltages and  variation is allowed. Larger voltage difference in general requires use of an equivalent branch.

        :b0ch: Zero sequence shunt (charging) susceptance, uniformly distributed, of the entire line section. Default: 0.0
        :bch: Positive sequence shunt (charging) susceptance, uniformly distributed, of the entire line section.  This value represents the full charging over the full length of the line. Default: 0.0
        :g0ch: Zero sequence shunt (charging) conductance, uniformly distributed, of the entire line section. Default: 0.0
        :gch: Positive sequence shunt (charging) conductance, uniformly distributed, of the entire line section. Default: 0.0
        :r: Positive sequence series resistance of the entire line section. Default: 0.0
        :r0: Zero sequence series resistance of the entire line section. Default: 0.0
        :shortCircuitEndTemperature: Maximum permitted temperature at the end of SC for the calculation of minimum short-circuit currents. Used for short circuit data exchange according to IEC 60909 Default: 0.0
        :x: Positive sequence series reactance of the entire line section. Default: 0.0
        :x0: Zero sequence series reactance of the entire line section. Default: 0.0
                '''

        cgmesProfile = Conductor.cgmesProfile

        possibleProfileList = {'class': [cgmesProfile.EQ.value, ],
                                                'b0ch': [cgmesProfile.EQ.value, ],
                                                'bch': [cgmesProfile.EQ.value, ],
                                                'g0ch': [cgmesProfile.EQ.value, ],
                                                'gch': [cgmesProfile.EQ.value, ],
                                                'r': [cgmesProfile.EQ.value, ],
                                                'r0': [cgmesProfile.EQ.value, ],
                                                'shortCircuitEndTemperature': [cgmesProfile.EQ.value, ],
                                                'x': [cgmesProfile.EQ.value, ],
                                                'x0': [cgmesProfile.EQ.value, ],
                                                 }

        serializationProfile = {}

        __doc__ += '\n Documentation of parent class Conductor: \n' + Conductor.__doc__

        def __init__(self, b0ch = 0.0, bch = 0.0, g0ch = 0.0, gch = 0.0, r = 0.0, r0 = 0.0, shortCircuitEndTemperature = 0.0, x = 0.0, x0 = 0.0,  *args, **kw_args):
                super().__init__(*args, **kw_args)

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
                str = 'class=ACLineSegment\n'
                attributes = self.__dict__
                for key in attributes.keys():
                        str = str + key + '={}\n'.format(attributes[key])
                return str
```

### Modern Python

```python
"""
Generated from the CGMES 3 files via cimgen: https://github.com/sogno-platform/cimgen
"""

from functools import cached_property
from typing import Optional
from pydantic import Field
from pydantic.dataclasses import dataclass
from .Base import DataclassConfig, Profile
from .Conductor import Conductor

@dataclass(config=DataclassConfig)
class ACLineSegment(Conductor):
    """
    A wire or combination of wires, with consistent electrical characteristics, building a single electrical system,
      used to carry alternating current between points in the power system. For symmetrical, transposed three phase
      lines, it is sufficient to use attributes of the line segment, which describe impedances and admittances for
      the entire length of the segment.  Additionally impedances can be computed by using length and associated per
      length impedances. The BaseVoltage at the two ends of ACLineSegments in a Line shall have the same
      BaseVoltage.nominalVoltage. However, boundary lines may have slightly different BaseVoltage.nominalVoltages
      and variation is allowed. Larger voltage difference in general requires use of an equivalent branch.

    bch: Positive sequence shunt (charging) susceptance, uniformly distributed, of the entire line section.  This value
      represents the full charging over the full length of the line.
    gch: Positive sequence shunt (charging) conductance, uniformly distributed, of the entire line section.
    r: Positive sequence series resistance of the entire line section.
    x: Positive sequence series reactance of the entire line section.
    Clamp: The clamps connected to the line segment.
    Cut: Cuts applied to the line segment.
    b0ch: Zero sequence shunt (charging) susceptance, uniformly distributed, of the entire line section.
    g0ch: Zero sequence shunt (charging) conductance, uniformly distributed, of the entire line section.
    r0: Zero sequence series resistance of the entire line section.
    shortCircuitEndTemperature: Maximum permitted temperature at the end of SC for the calculation of minimum short-
      circuit currents. Used for short circuit data exchange according to IEC 60909.
    x0: Zero sequence series reactance of the entire line section.
    """

    bch : float = Field(default=0.0, in_profiles = [Profile.EQ, ])

    gch : float = Field(default=0.0, in_profiles = [Profile.EQ, ])

    r : float = Field(default=0.0, in_profiles = [Profile.EQ, ])

    x : float = Field(default=0.0, in_profiles = [Profile.EQ, ])

    # *Association not used*
    # Type M:0..n in CIM  # pylint: disable-next=line-too-long
    # Clamp : list = Field(default_factory=list, in_profiles = [Profile.EQ, ]) # noqa: E501

    # *Association not used*
    # Type M:0..n in CIM  # pylint: disable-next=line-too-long
    # Cut : list = Field(default_factory=list, in_profiles = [Profile.EQ, ]) # noqa: E501

    b0ch : float = Field(default=0.0, in_profiles = [Profile.SC, ])

    g0ch : float = Field(default=0.0, in_profiles = [Profile.SC, ])

    r0 : float = Field(default=0.0, in_profiles = [Profile.SC, ])

    shortCircuitEndTemperature : float = Field(default=0.0, in_profiles = [Profile.SC, ])

    x0 : float = Field(default=0.0, in_profiles = [Profile.SC, ])



    @cached_property
    def possible_profiles(self)->set[Profile]:
        """
        A resource can be used by multiple profiles. This is the set of profiles
        where this element can be found.
        """
        return { Profile.EQ, Profile.SC,  }
```

### Modern Python after black (formatting)

```python
"""
Generated from the CGMES 3 files via cimgen: https://github.com/sogno-platform/cimgen
"""

from functools import cached_property
from pydantic import Field
from pydantic.dataclasses import dataclass
from .Base import DataclassConfig, Profile
from .Conductor import Conductor


@dataclass(config=DataclassConfig)
class ACLineSegment(Conductor):
    """
    A wire or combination of wires, with consistent electrical characteristics, building a single electrical system,
      used to carry alternating current between points in the power system. For symmetrical, transposed three phase
      lines, it is sufficient to use attributes of the line segment, which describe impedances and admittances for
      the entire length of the segment.  Additionally impedances can be computed by using length and associated per
      length impedances. The BaseVoltage at the two ends of ACLineSegments in a Line shall have the same
      BaseVoltage.nominalVoltage. However, boundary lines may have slightly different BaseVoltage.nominalVoltages
      and variation is allowed. Larger voltage difference in general requires use of an equivalent branch.

    bch: Positive sequence shunt (charging) susceptance, uniformly distributed, of the entire line section.  This value
      represents the full charging over the full length of the line.
    gch: Positive sequence shunt (charging) conductance, uniformly distributed, of the entire line section.
    r: Positive sequence series resistance of the entire line section.
    x: Positive sequence series reactance of the entire line section.
    Clamp: The clamps connected to the line segment.
    Cut: Cuts applied to the line segment.
    b0ch: Zero sequence shunt (charging) susceptance, uniformly distributed, of the entire line section.
    g0ch: Zero sequence shunt (charging) conductance, uniformly distributed, of the entire line section.
    r0: Zero sequence series resistance of the entire line section.
    shortCircuitEndTemperature: Maximum permitted temperature at the end of SC for the calculation of minimum short-
      circuit currents. Used for short circuit data exchange according to IEC 60909.
    x0: Zero sequence series reactance of the entire line section.
    """

    bch: float = Field(
        default=0.0,
        in_profiles=[
            Profile.EQ,
        ],
    )

    gch: float = Field(
        default=0.0,
        in_profiles=[
            Profile.EQ,
        ],
    )

    r: float = Field(
        default=0.0,
        in_profiles=[
            Profile.EQ,
        ],
    )

    x: float = Field(
        default=0.0,
        in_profiles=[
            Profile.EQ,
        ],
    )

    # *Association not used*
    # Type M:0..n in CIM  # pylint: disable-next=line-too-long
    # Clamp : list = Field(default_factory=list, in_profiles = [Profile.EQ, ])

    # *Association not used*
    # Type M:0..n in CIM  # pylint: disable-next=line-too-long
    # Cut : list = Field(default_factory=list, in_profiles = [Profile.EQ, ])

    b0ch: float = Field(
        default=0.0,
        in_profiles=[
            Profile.SC,
        ],
    )

    g0ch: float = Field(
        default=0.0,
        in_profiles=[
            Profile.SC,
        ],
    )

    r0: float = Field(
        default=0.0,
        in_profiles=[
            Profile.SC,
        ],
    )

    shortCircuitEndTemperature: float = Field(
        default=0.0,
        in_profiles=[
            Profile.SC,
        ],
    )

    x0: float = Field(
        default=0.0,
        in_profiles=[
            Profile.SC,
        ],
    )

    @cached_property
    def possible_profiles(self) -> set[Profile]:
        """
        A resource can be used by multiple profiles. This is the set of profiles
        where this element can be found.
        """
        return {
            Profile.EQ,
            Profile.SC,
        }
```