from __future__ import annotations
import uuid
from functools import cached_property
from pydantic import ConfigDict, Field, field_validator, computed_field
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from shapely.geometry import Point
from datetime import date, datetime, time
from typing import Optional, Iterator, List
from pydantic.dataclasses import dataclass
from ..utils.base import Base
from ..utils.dataclassconfig import DataclassConfig, GeoDataclassConfig
from ..utils.profile import Profile, BaseProfile
from ..utils.validation import cyclic_references_validator
from .enum import *

@dataclass(config=GeoDataclassConfig)
class PositionPoint(Base):
    """
    Set of spatial coordinates that determine a point, defined in the coordinate system specified in 'Location.CoordinateSystem'. Use a single position point instance to desribe a point-oriented location. Use a sequence of position points to describe a line-oriented object (physical location of non-point oriented objects like cables or lines), or area of an object (like a substation or a geographical zone - in this case, have first and last position point with the same values).

        :Location: Location described by this position point.
        :sequenceNumber: Zero-relative sequence number of this point within a series of points.
        :xPosition: X axis position.
        :yPosition: Y axis position.
        :zPosition: (if applicable) Z axis position.
    """

    location: "Location" = Field(alias="Location", in_profiles = [Profile.GL, ])
    sequenceNumber: Optional[int] = Field(default=None, in_profiles = [Profile.GL, ])
    point: Point = Field(
        repr=False, in_profiles = [Profile.GL, ]
    )  # we introduce this field compared to CIM definition because we want to store a proper geometry "point" in the database

    @computed_field
    @property
    def xPosition(self) -> str:
        return str(self.point.x)

    @computed_field
    @property
    def yPosition(self) -> str:
        return str(self.point.y)

    @computed_field
    @property
    def zPosition(self) -> str:
        return str(self.point.z)

    @cached_property
    def possible_profiles(self)->set[Profile]:
        """
        A resource can be used by multiple profiles. This is the set of profiles
        where this element can be found.
        """
        return { Profile.GL,  }

    # Pydantic needs help to map GeoAlchemy classes to Shapely
    @field_validator("point", mode="before")
    def validate_point_format(cls, v):
        if isinstance(v, Point):
            return v
        elif isinstance(v, WKBElement):
            point = to_shape(v)
            if point.geom_type != "Point":
                raise ValueError("must be a Point")
            return Point(point)
        else:
            raise ValueError("must be a Point or a WKBElement")
