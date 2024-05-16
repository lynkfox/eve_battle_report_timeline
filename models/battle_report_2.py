from __future__ import annotations

from datetime import datetime, timedelta
from math import floor
from typing import Any, Dict, List, Optional, Tuple, Set

from pydantic import BaseModel, field_serializer, model_serializer

from models.eve import (
    EveAlliance,
    EveStructure,
    EveSystem,
    StructureType,
)
from data.teams import Team, WhoseWho

WHOSE_WHO = WhoseWho()


class Battle2(BaseModel):
    battle_identifier: str
    br_link: str
    time_data: BattleTime
    system: EveSystem
    teams: List[TeamReport]
    br_totals: BattleReportTotals
    raw_json: Optional[dict]

    @model_serializer
    def ser_model(self):
        return {
            "br_link": self.br_link,
            "time_data": self.time_data,
            "system": self.system.name,
            "teams": self.teams,
            "totals": self.br_totals,
        }


class BattleReportResults(BaseModel):
    isk_lost: float
    ships_lost: int
    total_pilots: int

    @model_serializer
    def ser_model(self):
        return {"pilots": self.total_pilots, "ships_destroyed": self.ships_lost, "isk_destroyed": self.isk_lost}

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

    @model_serializer
    def ser_model(self):
        return {
            "date": self.started.date().strftime("%Y-%m-%d"),
            "start": self.started.time().strftime("%H:%M"),
            "ended": self.ended.time().strftime("%H:%M"),
            "duration": self.serialize_duration(),
        }

    def serialize_duration(self):
        seconds = self.duration.seconds
        hours = ""
        if seconds > 3600:
            hours = floor(seconds / 3600)
            seconds = seconds - (hours * 3600)
            hours = f"{hours}h"

        mins = floor(seconds / 60)

        if seconds == 0 or (mins == 0 and hours == ""):
            return "0"
        return f"{hours} {mins}m".strip()


class TeamReport(BaseModel):
    br_team_letter: str
    team: Team = Team.UNKNOWN
    alliances: List[str] = []
    corps: List[str] = []
    pilots: List[str] = []
    ships: List[str] = []
    ships_destroyed: List[str] = []
    km_links: List[str] = []
    pilots_podded: List[str] = []
    _structures: List[EveStructure] = []
    structure_history_ids: List[str] = []  # list of id's for Structure History entries
    totals: BattleReportResults = BattleReportResults(isk_lost=0, ships_lost=0, total_pilots=0)
    structure_destroyed: bool = False

    @property
    def structures(self):
        return [a.name for a in self._structures]

    @model_serializer
    def ser_model(self):
        return {
            "team:": self.team.value,
            "alliances": list(set(self.alliances)),
            "corps": list(set(self.corps)),
            "pilots": list(set(self.pilots)),
            "pilots_podded": list(set(self.pilots_podded)),
            "ships": self.ships,
            "ships_destroyed": self.ships_destroyed,
            "structures": self.structures,
            "was_structure_destroyed": self.structure_destroyed,
            "totals": self.totals,
        }


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

    @model_serializer
    def ser_model(self):
        return {"pilots": self.pilots, "isk_destroyed": self.isk_lost, "ships_destroyed": self.ships_lost}


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
