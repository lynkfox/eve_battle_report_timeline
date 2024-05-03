from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from pydantic import BaseModel, field_serializer

from models.eve import EveAlliance, LARGE_STRUCTURES, StationType, System
from data.teams import Team


class StructureEntry(BaseModel):
    type: StationType
    team: Team
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
