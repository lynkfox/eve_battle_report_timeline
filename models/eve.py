from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Set
from data.teams import Team
from datetime import datetime
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


class EveEntity(BaseModel):
    name: Optional[str]
    image_link: Optional[str] = None
    id_num: str
    seen_in: Set[str] = set()

    @field_validator("id_num")
    @classmethod
    def is_str(cls, v):
        if isinstance(v, str):
            return v
        return str(v)

    @field_serializer("seen_in")
    def serialize_set(self, seen_in: Set, _info):
        return list(seen_in)


class EveAlliance(EveEntity):
    """
    An eve Alliance

    inherited:
        name [str]: name of this Alliance
        image_link [str]: url to the image for this alliance
        id_num [str]: id for this entity
        seen_in [List[str]]: a list of BR_identifiers this entity has been seen in

    corp [List[str]]: a list of corp names
    """

    corps: Set[str] = set()
    holding_for: Optional[str] = None
    is_only_corp: bool = False

    @field_serializer("corps")
    def serialize_set(self, v: Set, _info):
        return list(v)


class EveCorp(EveEntity):
    """
    An Eve Corporation

    inherited:
        name [str]: name of this Alliance
        image_link [str]: url to the image for this alliance
        id_num [str]: id for this entity
        seen_in [List[str]]: a list of BR_identifiers this entity has been seen in

    alliance[Optional[str]]: name of the alliance
    has_no_alliance[bool]: if alliance is none, this is true
    """

    alliance: Optional[str] = None
    holding_for: Optional[str] = None

    @property
    def has_no_alliance(self) -> bool:
        return self.alliance is None


class EvePilot(EveEntity):
    """
    An Eve Pilot

    inherited:
        name [str]: name of this Alliance
        image_link [str]: url to the image for this alliance
        id_num [str]: id for this entity
        seen_in [List[str]]: a list of BR_identifiers this entity has been seen in

    corp [str]: the pilots corporation
    alliance [Optional[str]]: alliance for the pilot. Can be None
    podded_in [set[str]] - br_ids that this pilot was podded in
    zkill_link[optional[str]] zkillboard link
    """

    corp: str
    alliance: str
    podded_in: Set[str] = set()
    zkill_link: Optional[str] = None

    @field_serializer("podded_in")
    def serialize_set(self, v: Set, _info):
        return list(v)


class EveShip(EveEntity):
    """
    An Eve Ship

    inherited:
        name [str]: name of this Alliance
        image_link [str]: url to the image for this alliance
        id_num [str]: id for this entity
        seen_in [List[str]]: a list of BR_identifiers this entity has been seen in
    """


class EveSystem(EveEntity):
    """
    An Eve System

    inherited:
        name [str]: name of this Alliance
        image_link [str]: url to the image for this alliance
        id_num [str]: id for this entity
        seen_in [List[str]]: a list of BR_identifiers this entity has been seen in
    region: region if known
    constellation: constellation if known
    weather - wormhole weather
    j_class_number - the jclass number only (no C) - 0 for Kspace
    statics: any static connections - None for Kspace
    """

    region: Optional[str] = None
    constellation: Optional[str] = None
    weather: Optional[Weather] = None
    j_class_number: Union[str, int, None] = None
    statics: Optional[list] = None

    @property
    def j_class(self) -> str:
        if self.j_class_number == "0":
            return "K-Space"
        return f"C{self.j_class_number}"

    @field_validator("j_class_number")
    @classmethod
    def is_string(cls, v) -> str:
        return str(v)

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


class TeamDesignation(BaseModel):
    team: Team
    corp: str
    ally: Optional[str]


class SystemOwner(TeamDesignation):
    system: str
    type: StationType
    dates: List[datetime]


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
