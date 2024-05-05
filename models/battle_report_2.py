from __future__ import annotations

from datetime import datetime, timedelta
from math import floor
from typing import Any, Dict, List, Optional, Tuple, Set

from pydantic import BaseModel, field_serializer

from models.eve import (
    EveAlliance,
    EveCorp,
    EvePilot,
    EveShip,
    EveStructure,
    EveSystem,
    LARGE_STRUCTURES,
    StructureType,
    System,
)
from data.teams import Team, WhoseWho
from functools import cached_property

WHOSE_WHO = WhoseWho()


class BattleBaseModel(BaseModel):
    def __getattribute__(self, __name: str) -> Any:
        prop_name = f"_{__name}"
        if hasattr(self, prop_name):
            attr = getattr(self, prop_name)
            if hasattr(attr, "name"):
                return [a.name for a in attr]

        elif hasattr(self, __name):
            return getattr(self, __name)

        else:
            raise ValueError(f"{type(self)} has no property {__name}")


class Battle2(BaseModel):
    battle_identifier: str
    br_link: str
    time_data: BattleTime
    system: EveSystem
    teams: List[TeamReport]
    br_totals: BattleReportTotals
    raw_json: Optional[dict]


class BattleReportResults(BaseModel):
    isk_lost: float
    ships_lost: int
    total_pilots: int

    def increase(self, loss_value=0):
        self.total_pilots += 1
        if loss_value > 0:
            self.isk_lost += loss_value
            self.ships_lost += 1


class BattleTime(BaseModel):
    started: datetime
    duration: timedelta
    ended: datetime

    @property
    def start_time_as_key(self) -> str:
        return self.started.strftime("%Y-%m-%d")

    @field_serializer("started", "ended")
    def serialize_ended(self, dt: datetime, _info):
        return self.serialize_dt(dt, _info)

    @field_serializer("duration")
    def serialize_duration(self, td: timedelta, _info):
        seconds = td.seconds
        hours = ""
        if seconds > 3600:
            hours = floor(seconds / 3600)
            seconds = seconds - (hours * 3600)
            hours = f"{hours}h"

        mins = floor(seconds / 60)

        if seconds == 0 or (mins == 0 and hours == ""):
            return "0"
        return f"{hours} {mins}m".strip()

    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat()


class TeamReport(BaseModel):
    br_team_letter: str
    team: Team = Team.UNKNOWN
    _alliances: List[EveAlliance] = []
    _corps: List[EveCorp] = []
    _pilots: List[EvePilot] = []
    _ships: List[EveShip] = []
    km_links: List[str] = []
    pilots_podded: List[str] = []
    _structures: List[EveStructure] = []
    structure_history_ids: List[str] = []  # list of id's for Structure History entries
    totals: BattleReportResults = BattleReportResults(isk_lost=0, ships_lost=0, total_pilots=0)
    structure_destroyed: bool = False

    @property
    def alliances(self):
        return [a.name for a in self._alliances]

    @property
    def corps(self):
        return [a.name for a in self._corps]

    @property
    def pilots(self):
        return [a.name for a in self._pilots]

    @property
    def ships(self):
        return [a.name for a in self._ships]

    @property
    def structures(self):
        return [a.name for a in self._structures]


class BattleReportTotals(BaseModel):
    """
    totals between both teams
    """

    pilots: int
    isk_lost: int
    killmails: int
    ships_lost: int = 0
    ships: Optional[int] = None
    shipTypes: Optional[int] = None
    groups: Optional[int] = None


class BattleReportGroup(EveAlliance):
    group_results: Optional[BattleReportResults]
    group_killmails: Optional[List[str]]
    is_holding: bool = False
    holding_for: Optional[Tuple[str, str]] = None
    ships: Dict[str, BattleReportCount]
    pilots: Dict[str, BattleReportCount]


class AssociatedCount(BaseModel):
    t: int = 0
    l: int = 0
    p: int = 0
    brs: List[str] = []


class BattleReportCount(BaseModel):
    name: str
    image_link: str
    total: int = 0
    lost: int = 0
    total_lost_value: float = 0
    killmails: List[str] = []
    pods: int = 0
    pod_killmails: List[str] = []
    associated: Dict[str, AssociatedCount] = {}

    def increase(
        self,
        value: float = 0,
        killmail_id: int = None,
        multiple: int = None,
        associated_name: str = None,
        br: str = None,
    ):
        self.total += 1

        if self._is_valid_associated_name(associated_name):
            related = self.associated.setdefault(associated_name, AssociatedCount())
        else:
            related = self.associated.setdefault("Unknown Pilot", AssociatedCount())

        related.t += 1

        if value > 0:
            self.lost = self.lost + 1 if multiple is not None else self.lost + multiple
            self.total_lost_value += value
            self.killmails.append(killmail_id)
            related.l += 1

        if br is not None:
            related.brs.append(br)

    def podded(self, killmail: str, associated_name: str):
        self.pods += 1
        self.pod_killmails.append(killmail)
        if self._is_valid_associated_name(associated_name):
            self.associated[associated_name].p += 1

    def _is_valid_associated_name(self, associated_name):
        return associated_name is not None and "\u00a0" not in associated_name


class StructureHistory(BaseModel):
    id_number: str
    name: Optional[str] = None
    type: StructureType
    is_large: bool
    system: str
    team: Team
    alliance: Optional[str] = None
    corp: str
    dates: List[datetime] = []
    value: float = 0
    zkill_link: Optional[str] = None
    multiple_in_system: int = 0
    shield_attacked_on: Optional[datetime] = None  # first time station attacked
    armor_attacked_on: Optional[datetime] = None  # medium station destroyed on
    hull_attacked_on: Optional[datetime] = None  # large_station destroyed on
    estimated_timers: Optional[List[StructureTimer]] = None
    br_ids: Set[str] = set()

    @property
    def destroyed_on(self) -> datetime:
        if self.is_large:
            return self.hull_attacked_on
        else:
            return self.armor_attacked_on


class StructureTimer(BaseModel):
    if_timer_believed_to_be: Optional[str] = None
    hull_attacked_on: Optional[datetime] = None
    armor_attacked_on: Optional[datetime] = None
    shield_attacked_on: Optional[datetime] = None
    hull_attacked_within_range: Optional[Tuple[datetime, datetime]] = None
    armor_attacked_within_range: Optional[Tuple[datetime, datetime]] = None
    shield_attacked_within_range: Optional[Tuple[datetime, datetime]] = None

    @field_serializer("hull_attacked_on", "armor_attacked_on", "shield_attacked_on")
    def serialize_dt(self, dt: datetime, _info):
        if dt is not None:
            return dt.isoformat()
        else:
            return None

    @field_serializer("hull_attacked_within_range", "armor_attacked_within_range", "shield_attacked_within_range")
    def serialize_dt_tuple(self, dt_tuple: Tuple[datetime, datetime], _info):
        if dt_tuple is not None:
            return f"{dt_tuple[0].isoformat()} - {dt_tuple[1].isoformat()}"
        else:
            return None

    def estimate_timer(self, medium: bool, unknown_timer: datetime, hp_type: str = "shield"):
        if medium:
            if hp_type == "shield":
                self.if_timer_believed_to_be = "medium - shield"
                self.shield_attacked_on = unknown_timer
                self.armor_attacked_within_range = unknown_timer + timedelta(
                    days=2, hours=12
                ), unknown_timer + timedelta(days=3)
            else:
                self.if_timer_believed_to_be = "medium - armor/hull"
                self.hull_attacked_on = unknown_timer
                self.armor_attacked_on = unknown_timer
                self.shield_attacked_within_range = unknown_timer - timedelta(
                    days=2, hours=12
                ), unknown_timer - timedelta(days=3)

        else:
            if hp_type == "shield":
                self.if_timer_believed_to_be = "large - shield"
                self.shield_attacked_on = unknown_timer
                self.armor_attacked_within_range = unknown_timer + timedelta(days=1), unknown_timer + timedelta(
                    days=1, hours=12
                )
                self.hull_attacked_within_range = self.armor_attacked_within_range[0] + timedelta(
                    days=2, hours=1
                ), self.armor_attacked_within_range[1] + timedelta(days=3)
            elif hp_type == "armor":
                self.if_timer_believed_to_be = "large - armor"
                self.shield_attacked_within_range = unknown_timer - timedelta(days=1), unknown_timer - timedelta(
                    days=1, hours=12
                )
                self.armor_attacked_on = unknown_timer
                self.hull_attacked_within_range = self.armor_attacked_on + timedelta(
                    days=2, hours=12
                ), self.armor_attacked_on + timedelta(days=3)
            else:
                self.if_timer_believed_to_be = "large - hull"
                self.hull_attacked_on = unknown_timer
                self.armor_attacked_within_range = unknown_timer - timedelta(
                    days=2, hours=12
                ), unknown_timer - timedelta(days=3)
                self.shield_attacked_within_range = self.armor_attacked_within_range[0] - timedelta(
                    days=1
                ), self.armor_attacked_within_range[1] - timedelta(days=1, hours=12)

        return self
