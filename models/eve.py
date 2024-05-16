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

    @property
    def appearances(self) -> int:
        return len(self.seen_in)

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
    members: Dict[str, int] = {}
    structures: Dict[str, Dict[str, dict]] = {}  # system name, station type, {(s)een, (d)estroyed, (g)unner}
    is_only_corp: bool = False
    total_lost_isk: float = 0.0
    total_lost_ships: int = 0

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
    members: Dict[str, int] = {}
    pilots_per_battle: Dict[str, int] = {}  # br_link, total_pilots
    ships: Dict[str, int] = {}  # ship name, appearances
    structures: Dict[str, Dict[str, dict]] = {}  # system name, station type, {(s)een, (d)estroyed, (g)unner}
    holding_for: Optional[str] = None
    total_lost_isk: float = 0.0
    total_lost_ships: int = 0

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
    ships: Dict[str, int] = {}
    podded_in: Set[str] = set()
    zkill_link: Optional[str] = None

    @field_serializer("podded_in")
    def serialize_set(self, v: Set, _info):
        return list(v)

    @property
    def podded(self) -> int:
        return len(self.podded_in)


class EveShip(EveEntity):
    """
    An Eve Ship

    inherited:
        name [str]: name of this Alliance
        image_link [str]: url to the image for this alliance
        id_num [str]: id for this entity
        seen_in [List[str]]: a list of BR_identifiers this entity has been seen in



    used: [int]: total number used (sum of all used in all battles)
    destroyed [int]: # destroyed (sum of all battles)
    total_value_destroyed [float]: total isk value of all destroyed
    """

    used: int = 0
    destroyed: int = 0
    total_value_destroyed: float = 0.0


class EveStructure(EveEntity):
    """
    An Eve Structure

    inherited:
        name [str]: name of this Alliance
        image_link [str]: url to the image for this alliance
        id_num [str]: id for this entity
        seen_in [List[str]]: a list of BR_identifiers this entity has been seen in

    is_gunner_entry [bool]: this list on the BR was from a Gunner, not the station itself
    gunner_name [str]: the name of the gunner
    gunner_corp [str]: the corp of the gunner
    gunner_alliance [str]: the alliance of the gunner, may be none
    multiple_killed [str]: if the br said x#
    """

    type: StructureType
    structure_history_id: Optional[str]
    destroyed_here: bool = False
    value: float = 0.0
    is_gunner_entry: bool = False
    gunner_name: Optional[str] = None
    gunner_corp: Optional[str] = None
    gunner_alliance: Optional[str] = None
    multiple_killed: Optional[int] = None

    @property
    def multiple(self) -> str:
        if self.multiple_killed > 1:
            return f"x{self.multiple_killed}"
        return ""


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
    def static_str(self) -> str:
        if self.statics is None or len(self.statics) == 0:
            return ""
        return self.j_class + "/" + "-".join([s["destination"].replace("C", "") for s in self.statics])

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
    type: StructureType
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


class StructureType(Enum):
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


LARGE_STRUCTURES = [StructureType.FORTIZAR, StructureType.KEEPSTAR, StructureType.SOTIYO, StructureType.TATARA]


class EntityType(Enum):
    SYSTEM = "System"
    SHIP = "Ship"
    PILOT = "Pilot"
    CORP = "Corporation"
    ALLY = "Alliance"
    STRUCTURE = "Structure"
    OTHER = "Other/Unknown"
