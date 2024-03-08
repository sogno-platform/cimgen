from enum import Enum
from functools import cached_property


class BaseProfile(str, Enum):
    """
    Profile parent. Use it if you need your own profiles.

    All pycgmes objects requiring a Profile are actually asking for a `BaseProfile`. As
    Enum with fields cannot be inherited or composed, just create your own CustomProfile without
    trying to extend Profile. It will work.
    """

    @cached_property
    def long_name(self) -> str:
        """Return the long name of the profile."""
        return self.value


class Profile(BaseProfile):
    """
    Enum containing all CGMES profiles and their export priority.
    """

    # DI= "DiagramLayout" # Not too sure about that one
    DL = "DiagramLayout"
    DY = "Dynamics"
    EQ = "Equipment"
    EQ_BD = "EquipmentBoundary"  # Not too sure about that one
    GL = "GeographicalLocation"
    OP = "Operation"
    SC = "ShortCircuit"
    SSH = "SteadyStateHypothesis"
    SV = "StateVariables"
    TP = "Topology"
    TP_BD = "TopologyBoundary"  # Not too sure about that one
