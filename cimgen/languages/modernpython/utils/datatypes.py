from pydantic import Field
from typing import List

from .constants import NAMESPACES
from pydantic.dataclasses import dataclass

from .config import cgmes_resource_config
from .profile import BaseProfile
from ..resources.UnitMultiplier import UnitMultiplier
from ..resources.UnitSymbol import UnitSymbol


@dataclass(config=cgmes_resource_config)
class Primitive:

    name: str = Field(frozen=True)
    type: object = Field(frozen=True)
    namespace: str = Field(frozen=True, default=NAMESPACES["cim"])
    profiles: List[BaseProfile] = Field(frozen=True)


@dataclass(config=cgmes_resource_config)
class CIMDatatype(Primitive):

    multiplier: UnitMultiplier = Field(frozen=True)
    symbol: UnitSymbol = Field(frozen=True)
