from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, field_serializer, field_validator, ValidationError


class System(BaseModel):
    """
    An Eve System

    attributes:
    name(str): name of the system
    id_num(str): eve sde/esi ID number of system
    region(Optional str): the region the system is in
    constellation(Optional str): the constellation the system belongs to
    weather(Optional, Weather): None if vanilla, else Weather(Enum)
    j_class(Optional, str): C1-C25
    statics(Optional, str): static of the system C1 or HS or C5 - multiple statics are comma string C1, C3
    """

    name: str
    id_num: str
    region: Optional[str] = None
    constellation: Optional[str] = None
    weather: Optional[Weather] = None
    j_class: Optional[str] = None
    statics: Optional[list] = None

    @field_validator("weather")
    @classmethod
    def weather_enum(cls, v: str) -> Weather:
        if isinstance(v, str) and Weather.has_value(v):
            return Weather(v)
        if isinstance(v, Weather):
            return v

        raise ValidationError(f"Value of {v} is not a valid weather")

    @field_serializer("weather")
    def serialize_weather(self, weather: Weather, _info):
        return weather.value


class EveAlliance(BaseModel):
    """
    An eve Alliance

    attributes:
    name(Optional, str): Name of the alliance. If None, then all corps listed have no alliance and are nominally independent
    iimage_link(optional, str): the link to an image for the alliance/corp. Can be None
    corps:(Dict(str, str)): dict that are the name, link to the image for the corp
    """

    name: Optional[str]
    image_link: Optional[str] = None
    corps: Dict[str, str]


class Weather(Enum):
    PULSAR = "Pulsar"
    BLACK_HOLE = "Black Hole"
    CATACLYSMIC_VARIABLE = "Cataclysmic Variable"
    MAGNETAR = "Magnetar"
    RED_GIANT = "Red Giant"
    WOLF_RAYET = "Wolf-Rayet Star"
    VANILLA = "Vanilla"

    @classmethod
    def has_value(cls, test):
        return test.upper() in cls.__members__.keys()


class StationType(Enum):
    ASTRAHUS = "Astrahus"
    FORTIZAR = "Fortizar"
    KEEPSTAR = "Keepstar"
    ATHANOR = "Athanor"
    TATARA = "Tatara"
    RAITARU = "Raitaru"
    AZBEL = "Azbel"
    SOTIYO = "Sotiyo"
    POS = "Control Tower"
    POCO = "Customs Office"
    UNKNOWN = "Unknown"

    @classmethod
    def has_value(cls, test):
        return test.upper() in cls.__members__.keys()


LARGE_STRUCTURES = [StationType.FORTIZAR, StationType.KEEPSTAR, StationType.SOTIYO, StationType.TATARA]
