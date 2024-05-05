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

    def _structures_destroyed(self, battle: Battle2) -> str:
        names = []
        output = {}
        for team in battle.teams:
            for structure in team._structures:
                if structure.destroyed_here:
                    structure_name = structure.type.value
                    names.append(f"{structure_name}")
                    total = output.setdefault(structure_name, 0)
                    output[structure_name] = total + structure.multiple_killed

        if len(names) > 0:
            formatted = [f"{k} {'x'+str(total) if total > 1 else ''}" for k, total in output.items()]
            return f"<i>Structures Destroyed:</i><br>   - " + "<br>   - ".join(formatted) + "<br>"
        return ""

    def _build_custom_data(self, battle: Battle2) -> tuple:

        system = battle.system.name
        date = battle.time_data.started.strftime("%a, %b %d, %Y - %H:%M")
        weather = f" [{battle.system.weather.value}]" if battle.system.weather != Weather.VANILLA else ""
        isk_destroyed = f"{convert_isk(battle.br_totals.isk_lost):.2f}B"
        pilots = battle.br_totals.pilots
        ships = battle.br_totals.ships_lost
        structures = self._structures_destroyed(battle)
        br_link = battle.br_link
        br_link_display = battle.br_link.replace("https://", "")
        statics = f" [{battle.system.static_str}]"
        return (
            br_link,
            system,
            statics,
            weather,
            date,
            isk_destroyed,
            pilots,
            ships,
            structures,
            br_link_display,
        )

    @property
    def hovertemplate(self) -> str:
        return (
            "<b>%{customdata[1]}</b><sup>%{customdata[2]}%{customdata[3]}</sup><br>"
            + "<i>On %{customdata[4]}<br>"
            + "<br><b>Totals:</b><br>"
            + "<i>Isk Destroyed:</i> <b>%{customdata[5]}</b><br>"
            + "<i>Pilots:</i> <b>%{customdata[6]}</b><br>"
            + "<i>Ships Destroyed:</i> <b>%{customdata[7]}</b><br>"
            + "%{customdata[8]}"
            + "<br><b>Click this node to go to br:</b><br>"
            + "<sup>%{customdata[9]}</sup>"
            + "<extra></extra>"
            # customdata[0] = br link, used by the on_click event
        )


class BattleNode(BaseModel):
    battle: Battle2
    _owner: Team = Team.UNKNOWN
    _destroyed: bool = False
    _refed: bool = False

    def set_station_info(self, all_data) -> BattleNode:
        stations = all_data.structure_owners.get(self.system)

        self._owner = Team.UNKNOWN if stations is None else stations[0].team

        self._destroyed = any(team.structure_destroyed for team in self.battle.teams)

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
    def structures_destroyed(self) -> List[str]:
        names = []
        for team in self.battle.teams:
            for structure in team._structures:
                if structure.destroyed_here:
                    names.append(f"{structure.type.value} {structure.multiple}")

        if len(names) > 0:
            return names
        return None

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
