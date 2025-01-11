from typing import Optional, Union

from pydantic import Field
from pydantic.dataclasses import dataclass

from ..resources.Currency import Currency
from ..resources.UnitMultiplier import UnitMultiplier
from ..resources.UnitSymbol import UnitSymbol
from .config import cgmes_resource_config
from .constants import NAMESPACES
from .profile import BaseProfile


@dataclass(config=cgmes_resource_config)
class Primitive:
    name: str = Field(frozen=True)
    type: object = Field(frozen=True)
    profiles: list[BaseProfile] = Field(frozen=True)
    namespace: str = Field(frozen=True, default=NAMESPACES["cim"])


@dataclass(config=cgmes_resource_config)
class CIMDatatype(Primitive):
    multiplier: Optional[UnitMultiplier] = Field(default=None, frozen=True)
    unit: Optional[Union[UnitSymbol, Currency]] = Field(default=None, frozen=True)
    denominatorMultiplier: Optional[UnitMultiplier] = Field(default=None, frozen=True)
    denominatorUnit: Optional[UnitSymbol] = Field(default=None, frozen=True)
