from datetime import datetime, timedelta
from typing import List, Union

from pydantic import BaseModel

from models.battle_report import StationKill
from models.eve import System, Weather
from data.teams import Team


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
    system_owner: Team
    station_destroyed: bool
    station_owners: List[str]

    @classmethod
    def extra_properties(cls):
        return ["system_name", "raw_isk_destroyed", "hover_text", "owner_color", "border_color", "border_width"]

    @property
    def border_color(self) -> str:
        if self.system_owner == Team.HAWKS:
            return "maroon" if self.station_destroyed else "white"
        if self.system_owner == Team.COALITION:
            return "dodgerblue" if self.station_destroyed else "white"

        return "darkgreen" if self.station_destroyed else "white"

    @property
    def owner_color(self) -> str:
        if self.system_owner == Team.HAWKS:
            return "orange"
        if self.system_owner == Team.COALITION:
            return "cyan"

        return "palegreen"

    @property
    def border_width(self) -> int:
        return 3 if self.station_destroyed else 1

    @property
    def weather_color(self) -> str:
        mapping = {
            Weather.VANILLA: "#ffffff",  # white
            Weather.BLACK_HOLE: "#000000",  # black
            Weather.CATACLYSMIC_VARIABLE: "#a89527",  # goldenrodish
            Weather.MAGNETAR: "#990082",  # pink
            Weather.PULSAR: "#312ed1",  # blue
            Weather.RED_GIANT: "#540f00",  # red
            Weather.WOLF_RAYET: "#9635bd",  # purple
        }

        return mapping[self.system.weather]

    @property
    def system_name(self) -> str:
        return self.system.name

    @property
    def raw_isk_destroyed(self) -> float:
        return self.hawks_losses + self.coalition_losses

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

        br = f"Battle Report:<br>{self.battle_report_link}"
        extra = ""
        if len(self.station_owners) > 0:

            if self.station_destroyed:
                extra = "Station destroyed:"
            else:
                extra = "Possible Ref:"

            extra = extra + "<br>" + ", ".join(self.station_owners)
        return (title, date, isk, pilots, ships, br, extra)


class StationTimerBars(BaseModel):
    date: datetime
    system: str
    stations_killed: List[StationKill] = []
