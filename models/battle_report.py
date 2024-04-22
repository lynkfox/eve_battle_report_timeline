from __future__ import annotations

from datetime import datetime, timedelta
from math import floor
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, field_serializer

from models.eve import EveAlliance, LARGE_STRUCTURES, StationType, System


class MultiSystemBattle(BaseModel):
    started: datetime
    duration: timedelta
    systems: List[System]
    battles: List[Battle]


class BattleReportResults(BaseModel):
    isk_lost: float
    ships_lost: int
    total_pilots: int

    def increase(self, loss_value=0):
        self.total_pilots += 1
        if loss_value > 0:
            self.isk_lost += loss_value
            self.ships_lost += 1


class Battle(BaseModel):
    battle_identifier: str
    br_link: str
    time_data: BattleTime
    teams: Dict[str, Dict[str, BattleReportGroup]]
    team_results: Dict[str, BattleReportResults] = BattleReportResults(isk_lost=0, ships_lost=0, total_pilots=0)
    team_killmails: Dict[str, List[str]] = {}
    team_participants: Dict[str, List[BattleReportParticipant]] = {}
    structures: Dict[str, List[StationKill]] = {}
    station_killed: bool = False
    possible_timer: bool = False
    third_party: bool = False
    doubt_if_war: bool = False
    system: System
    possible_trash: Dict[str, List[BattleReportParticipant]] = {}
    raw_json: Optional[dict]

    @property
    def trash_lost_totals(self):
        output = {}
        for team, trash in self.possible_trash.items():
            team_trash = output.setdefault(team, {})
            team_trash["value"] = sum([p.value for p in trash])
            team_trash["ships"] = len(trash)
        return output


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


class BattleReportParticipant(BaseModel):
    name: str
    ship: str
    alliance: Optional[str] = None
    corp: Optional[str] = None
    zkill_link: Optional[str] = None
    value: float = 0
    podded: bool = False


class StationKill(BaseModel):
    type: StationType
    value: float
    owner: EveAlliance
    destroyed_on: Optional[datetime] = None
    unknown_timer_on: Optional[datetime] = None
    estimated_timers: List[StationTimer] = []
    system: Optional[System] = None
    zkill_link: Optional[str] = None

    @field_serializer("destroyed_on", "unknown_timer_on")
    def serialize_dt(self, dt: datetime, _info):
        if dt is not None:
            return dt.isoformat()
        else:
            return None

    @field_serializer("type")
    def serialize_started(self, type: StationType, _info):
        return type.value

    def estimate_timer(self):
        if self.value > 0:
            if self.type in LARGE_STRUCTURES:
                self.estimated_timers.append(StationTimer().estimate_timer(False, self.destroyed_on, hp_type="hull"))
            else:
                self.estimated_timers.append(StationTimer().estimate_timer(True, self.destroyed_on, hp_type="hull"))
        else:
            if self.type in LARGE_STRUCTURES:
                self.estimated_timers.append(
                    StationTimer().estimate_timer(False, self.unknown_timer_on, hp_type="armor")
                )
                self.estimated_timers.append(
                    StationTimer().estimate_timer(False, self.unknown_timer_on, hp_type="shield")
                )
            elif self.type == StationType.UNKNOWN:
                self.estimated_timers.append(
                    StationTimer().estimate_timer(True, self.unknown_timer_on, hp_type="shield")
                )
                self.estimated_timers.append(
                    StationTimer().estimate_timer(False, self.unknown_timer_on, hp_type="hull")
                )
                self.estimated_timers.append(
                    StationTimer().estimate_timer(False, self.unknown_timer_on, hp_type="armor")
                )
                self.estimated_timers.append(
                    StationTimer().estimate_timer(False, self.unknown_timer_on, hp_type="shield")
                )
            else:
                self.estimated_timers.append(
                    StationTimer().estimate_timer(True, self.unknown_timer_on, hp_type="shield")
                )


class StationTimer(BaseModel):
    if_timer_believed_to_be: Optional[str] = None
    hull_timer_on: Optional[datetime] = None
    armor_timer_on: Optional[datetime] = None
    shield_timer_on: Optional[datetime] = None
    estimated_hull_timer_range: Optional[Tuple[datetime, datetime]] = None
    estimated_armor_timer_range: Optional[Tuple[datetime, datetime]] = None
    estimated_shield_timer_range: Optional[Tuple[datetime, datetime]] = None

    @field_serializer("hull_timer_on", "armor_timer_on", "shield_timer_on")
    def serialize_dt(self, dt: datetime, _info):
        if dt is not None:
            return dt.isoformat()
        else:
            return None

    @field_serializer("estimated_hull_timer_range", "estimated_armor_timer_range", "estimated_shield_timer_range")
    def serialize_dt_tuple(self, dt_tuple: Tuple[datetime, datetime], _info):
        if dt_tuple is not None:
            return f"{dt_tuple[0].isoformat()} - {dt_tuple[1].isoformat()}"
        else:
            return None

    def estimate_timer(self, medium: bool, unknown_timer: datetime, hp_type: str = "shield"):
        if medium:
            if hp_type == "shield":
                self.if_timer_believed_to_be = "medium - shield"
                self.shield_timer_on = unknown_timer
                self.estimated_armor_timer_range = unknown_timer + timedelta(
                    days=2, hours=12
                ), unknown_timer + timedelta(days=3)
            else:
                self.if_timer_believed_to_be = "medium - armor/hull"
                self.hull_timer_on = unknown_timer
                self.armor_timer_on = unknown_timer
                self.estimated_shield_timer_range = unknown_timer - timedelta(
                    days=2, hours=12
                ), unknown_timer - timedelta(days=3)

        else:
            if hp_type == "shield":
                self.if_timer_believed_to_be = "large - shield"
                self.shield_timer_on = unknown_timer
                self.estimated_armor_timer_range = unknown_timer + timedelta(days=1), unknown_timer + timedelta(
                    days=1, hours=12
                )
                self.estimated_hull_timer_range = self.estimated_armor_timer_range[0] + timedelta(
                    days=2, hours=1
                ), self.estimated_armor_timer_range[1] + timedelta(days=3)
            elif hp_type == "armor":
                self.if_timer_believed_to_be = "large - armor"
                self.estimated_shield_timer_range = unknown_timer - timedelta(days=1), unknown_timer - timedelta(
                    days=1, hours=12
                )
                self.armor_timer_on = unknown_timer
                self.estimated_hull_timer_range = self.armor_timer_on + timedelta(
                    days=2, hours=12
                ), self.armor_timer_on + timedelta(days=3)
            else:
                self.if_timer_believed_to_be = "large - hull"
                self.hull_timer_on = unknown_timer
                self.estimated_armor_timer_range = unknown_timer - timedelta(
                    days=2, hours=12
                ), unknown_timer - timedelta(days=3)
                self.estimated_shield_timer_range = self.estimated_armor_timer_range[0] - timedelta(
                    days=1
                ), self.estimated_armor_timer_range[1] - timedelta(days=1, hours=12)

        return self
