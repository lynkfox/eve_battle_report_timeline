from datetime import datetime, timedelta
from typing import List, Union

from pydantic import BaseModel

from models.battle_report import StationKill
from models.eve import System, Weather


class TimelineNode(BaseModel):
    date: datetime
    duration: timedelta
    system: System
    hawks_pilots: int = 0
    hawks_losses: float = 0
    hawks_ships: int = 0
    hawks_primary_ships: List[str] = []
    hawks_destroyed_excluding_trash: float = 0
    hawks_pilots_excluding_trash: int = 0
    hawks_ships_excluding_trash: int = 0
    not_guaranteed_to_be_hawks: bool = False
    hawks_is_third_party: bool = False
    coalition_pilots: int = 0
    coalition_losses: float = 0
    coalition_ships: int = 0
    coalition_primary_ships: List[str] = []
    coalition_destroyed_excluding_trash: float = 0
    coalition_pilots_excluding_trash: int = 0
    coalition_ships_excluding_trash: int = 0
    not_guaranteed_to_be_coalition: bool = False
    coalition_is_third_party: bool = False
    battle_report_link: str
    color: Union[str, int, None]

    @classmethod
    def extra_properties(cls):
        return ["system_name", "total_pilots_involved", "hover_text", "symbol"]

    @property
    def symbol(self) -> str:
        mapping = {
            Weather.VANILLA: "circle",
            Weather.BLACK_HOLE: "circle-x",
            Weather.CATACLYSMIC_VARIABLE: "star",
            Weather.MAGNETAR: "star-triangle-up",
            Weather.PULSAR: "diamond",
            Weather.RED_GIANT: "pentagon",
            Weather.WOLF_RAYET: "hourglass",
        }

        return mapping[self.system.weather]

    @property
    def system_name(self) -> str:
        return self.system.name

    @property
    def total_isk_destroyed(self) -> float:
        return self.hawks_destroyed_excluding_trash + self.coalition_destroyed_excluding_trash

    @property
    def total_pilots_involved(self) -> int:
        return self.hawks_pilots_excluding_trash + self.coalition_pilots_excluding_trash

    @property
    def total_ships_involved(self) -> int:
        return self.hawks_ships_excluding_trash + self.coalition_ships_excluding_trash

    @property
    def hover_text(self) -> str:
        if self.system.weather is not Weather.VANILLA:
            weather = f" [{self.system.weather.value}] "
        else:
            weather = " "
        if self.system.statics is not None:
            short_static = (
                "-".join([s["destination"] for s in self.system.statics])
                .replace("Highsec", "HS")
                .replace("Lowsec", "LS")
                .replace("Nullsec", "NS")
            )
            title = f"<b>{self.system_name}{weather}- {self.system.j_class}/{short_static}</b>"
        else:
            title = f"<b>{self.system_name}{weather}- {self.system.j_class}</b>"

        date = f"<b>Date:</b> {self.date.strftime('%a, %b %d, %Y - %H:%M')}"
        isk = f"Isk (Destroyed): {'%.2f' % self.total_isk_destroyed}B"
        pilots = f"Pilots (Involved): {self.total_pilots_involved}"
        ships = f"Ships (Involved): {self.total_ships_involved}"

        return (title, date, isk, pilots, ships)


class StationTimerBars(BaseModel):
    date: datetime
    system: str
    stations_killed: List[StationKill] = []
