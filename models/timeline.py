from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel

from models.battle_report import StationKill
from models.eve import System


class TimelineNode(BaseModel):
    date: datetime
    duration: timedelta
    system: System
    hawks_pilots: int = 0
    hawks_losses: float = 0
    hawks_primary_ships: List[str] = []
    hawks_destroyed_excluding_trash: float = 0
    not_guaranteed_to_be_hawks: bool = False
    hawks_is_third_party: bool = False
    coalition_pilots: int = 0
    coalition_losses: float = 0
    coalition_primary_ships: List[str] = []
    coalition_destroyed_excluding_trash: float = 0
    not_guaranteed_to_be_coalition: bool = False
    coalition_is_third_party: bool = False
    battle_report_link: str
    battle_order_value: int = 0

    @classmethod
    def extra_properties(cls):
        return [
            "hawks_won",
            "total_isk_lost",
            "total_pilots_involved",
            "system_name",
            "system_weather",
            "system_statics",
            "system_class",
            "total_isk_destroyed",
        ]

    @property
    def hawks_won(self) -> int:
        if self.hawks_destroyed_excluding_trash > self.coalition_destroyed_excluding_trash:
            return 1
        else:
            return 0

    @property
    def system_name(self) -> str:
        return self.system.name

    @property
    def system_weather(self) -> str:
        return self.system.weather.value

    @property
    def system_statics(self) -> str:
        return self.system.statics

    @property
    def total_isk_lost(self) -> float:
        return self.hawks_losses + self.coalition_losses

    @property
    def total_isk_destroyed(self) -> float:
        return self.hawks_destroyed_excluding_trash + self.coalition_destroyed_excluding_trash

    @property
    def total_pilots_involved(self) -> int:
        return self.hawks_pilots + self.coalition_pilots

    @property
    def system_class(self) -> int:
        if self.system.j_class == "CNone":
            return "K-Space"
        return self.system.j_class


class StationTimerBars(BaseModel):
    date: datetime
    system: str
    stations_killed: List[StationKill] = []
