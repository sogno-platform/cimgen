from typing import List, Optional, Union

from pydantic import Field
from pydantic.dataclasses import dataclass
from .constants import NAMESPACES

from .config import cgmes_resource_config
from .profile import BaseProfile
from ..resources.types.UnitMultiplier import UnitMultiplier
from ..resources.types.UnitSymbol import UnitSymbol
from ..resources.types.Currency import Currency


@dataclass(config=cgmes_resource_config)
class Primitive:
    name: str = Field(frozen=True)
    type: object = Field(frozen=True)
    namespace: str = Field(frozen=True, default=NAMESPACES["cim"])
    profiles: List[BaseProfile] = Field(frozen=True)


@dataclass(config=cgmes_resource_config)
class CIMDatatype(Primitive):
    multiplier: Optional[UnitMultiplier] = Field(default=None, frozen=True)
    unit: Optional[Union[UnitSymbol, Currency]] = Field(default=None, frozen=True)
    denominatorMultiplier: Optional[UnitMultiplier] = Field(default=None, frozen=True)
    denominatorUnit: Optional[UnitSymbol] = Field(default=None, frozen=True)
