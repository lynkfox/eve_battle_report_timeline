from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict

from pydantic import BaseModel
from models.eve import System, Weather
from models.battle_report_2 import Battle2
from data.teams import Team
import plotly.graph_objects as go
from dataclasses import dataclass
from br.util import convert_isk


HAWKS_COLOR = "orange"
HAWKS_BORDER = "maroon"
COALITION_COLOR = "cyan"
COALITION_BORDER = "dodgerblue"
UNKNOWN_COLOR = "palegreen"
UNKNOWN_BORDER = "darkgreen"


@dataclass
class TimelineTrace:
    name: str
    nodes: List[BattleNode]
    sizeref: float

    @property
    def x(self) -> list:
        return [x.date for x in self.nodes]

    @property
    def y(self) -> list:
        return [y.system for y in self.nodes]

    @property
    def marker(self) -> go.scatter.Marker:
        return go.scatter.Marker(
            color=[c.marker_color for c in self.nodes],
            size=[s.total_isk_destroyed for s in self.nodes],
            sizemode="area",
            sizeref=self.sizeref,
            sizemin=4,
            symbol="circle-dot",
            line=dict(color=[c.border_color for c in self.nodes], width=[w.border_width for w in self.nodes]),
        )

    @property
    def customdata(self) -> tuple:
        return [self._build_custom_data(t.battle) for t in self.nodes]

    def _build_custom_data(self, battle) -> tuple:
        system = battle.system.name
        date = battle.time_data.started.strftime("%a, %b %d, %Y - %H:%M")
        weather = f" [{battle.system.weather.value}]" if battle.system.weather != Weather.VANILLA else ""
        isk_destroyed = f"{convert_isk(battle.br_totals.isk_lost):.2f}B"
        pilots = battle.br_totals.pilots
        ships = battle.br_totals.ships_lost
        br_link = battle.br_link

        return system, weather, date, isk_destroyed, pilots, ships, br_link

    @property
    def hovertemplate(self) -> str:
        return (
            "<b>%{customdata[0]}</b>%{customdata[1]}<br>"
            + "<i>On %{customdata[2]}<br>"
            + "<br><b>Totals:</b><br>"
            + "<i>Isk Destroyed:</i> <b>%{customdata[3]}</b><br>"
            + "<i>Pilots:</i> <b>%{customdata[4]}</b><br>"
            + "<i>Ships Destroyed:</i> <b>%{customdata[5]}</b><br>"
            + "<br>Click this node to go to <b>%{customdata[6]}</b>"
            + "<extra></extra>"
        )


class BattleNode(BaseModel):
    battle: Battle2
    _owner: Team = Team.UNKNOWN
    _destroyed: bool = False
    _refed: bool = False

    def set_station_info(self, all_data) -> BattleNode:
        stations = all_data.structure_owners.get(self.system)

        self._owner = Team.UNKNOWN if stations is None else stations[0].team

        for team in self.battle.teams:
            for structure_history_id in team.structures:
                if all_data.structures.get(structure_history_id).value > 0:
                    self._destroyed = True

                # check ref?

        return self

    @property
    def system_owner(self) -> Team:
        return self._owner

    @property
    def date(self) -> datetime:
        return self.battle.time_data.started

    @property
    def system(self) -> str:
        return self.battle.system.name

    @property
    def structure_destroyed(self) -> bool:
        return self._destroyed

    @property
    def total_isk_destroyed(self) -> float:
        return self.battle.br_totals.isk_lost

    @property
    def marker_color(self) -> str:

        return (
            HAWKS_COLOR
            if self.system_owner == Team.HAWKS
            else COALITION_COLOR
            if self.system_owner == Team.COALITION
            else UNKNOWN_COLOR
        )

    @property
    def border_color(self) -> str:
        if self.structure_destroyed:
            return (
                HAWKS_BORDER
                if self.system_owner == Team.HAWKS
                else COALITION_BORDER
                if self.system_owner == Team.COALITION
                else UNKNOWN_BORDER
            )
        return "white"

    @property
    def border_width(self) -> int:
        return 3 if self.structure_destroyed else 1
