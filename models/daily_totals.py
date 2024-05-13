from __future__ import annotations
from models.battle_report_2 import Battle2, TeamReport
from models.eve import EntityType, EveEntity
from data.teams import Team
from plot_builder.timeline import HAWKS_COLOR, COALITION_COLOR, UNKNOWN_COLOR
import plotly.graph_objects as go
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

dummy_team = TeamReport(
    br_team_letter="",
)


@dataclass
class SingleBattleTotal:
    battle: Battle2
    hawks: TeamReport = None
    coalition: TeamReport = None
    unknown: TeamReport = dummy_team
    system_name: str = None

    def __post_init__(self):
        self.system_name = self.battle.system.name
        for idx, t in enumerate(self.battle.teams):
            if t.team == Team.HAWKS:
                self.hawks = t
                continue
            if t.team == Team.COALITION:
                self.coalition = t
                continue
            # otherwise if unknown team...
            if idx + 1 < len(self.battle.teams):
                count = idx + 1
                while count < len(self.battle.teams):
                    lookahead_team = self.battle.teams[count].team
                    if lookahead_team == Team.HAWKS and self.coalition is None:
                        self.coalition = t
                        count += 1
                        break
                    elif lookahead_team == Team.COALITION and self.hawks is None:
                        self.hawks = t
                        count += 1
                        break
                    else:
                        count += 1

            else:
                if self.hawks is None:
                    self.coalition = t
                    continue
                if self.coalition is None:
                    self.hawks = t
                    continue

            self.unknown = t

        if self.hawks is None and self.coalition is not None:
            self.hawks = self.unknown
        elif self.hawks is not None and self.coalition is None:
            self.coalition = self.unknown

    @property
    def hawks_structures_lost(self) -> int:
        return [s.destroyed_here for s in self.hawks._structures].count(True)

    @property
    def coalition_structures_lost(self) -> int:
        return [s.destroyed_here for s in self.coalition._structures].count(True)


@dataclass
class DailyTotal:
    battles: List[Battle2]
    _nodes: List[SingleBattleTotal] = None

    def __post_init__(self):
        self._nodes = [SingleBattleTotal(b) for b in self.battles]

    @property
    def date(self) -> datetime:
        return self.battles[0].time_data.started

    @property
    def x(self):
        return self.date.strftime("%b %d")

    @property
    def hawks_ships_lost(self) -> int:

        return sum([a.hawks.totals.ships_lost for a in self._nodes])

    @property
    def hawks_isk_lost(self) -> int:

        return sum([a.hawks.totals.isk_lost for a in self._nodes])

    @property
    def hawks_structures_lost(self) -> int:

        return sum([a.hawks_structures_lost for a in self._nodes])

    @property
    def coalition_ships_lost(self) -> int:

        return sum([a.coalition.totals.ships_lost for a in self._nodes])

    @property
    def coalition_isk_lost(self) -> int:

        return sum([a.coalition.totals.isk_lost for a in self._nodes])

    @property
    def coalition_structures_lost(self) -> int:
        return sum([a.coalition_structures_lost for a in self._nodes])

    @property
    def hawks_systems_lost(self) -> int:
        return len(list(set([a.system_name for a in self._nodes if a.hawks_structures_lost > 0])))

    @property
    def coalition_systems_lost(self) -> int:
        return len(list(set([a.system_name for a in self._nodes if a.coalition_structures_lost > 0])))


@dataclass
class TotalsTraceData:
    team: Team
    daily_totals: List[DailyTotal]
    color: str = ""

    def __post_init__(self):
        if self.team == Team.HAWKS:
            self.color = HAWKS_COLOR
        elif self.team == Team.COALITION:
            self.color = COALITION_COLOR

    @property
    def x(self):
        return [a.x for a in self.daily_totals]

    @property
    def y_isk(self):
        if self.team == Team.HAWKS:
            return [a.hawks_isk_lost for a in self.daily_totals]
        return [a.coalition_isk_lost for a in self.daily_totals]

    @property
    def y_ships(self):
        if self.team == Team.HAWKS:
            return [a.hawks_ships_lost for a in self.daily_totals]
        return [a.coalition_ships_lost for a in self.daily_totals]

    @property
    def y_structures(self) -> List[int]:
        if self.team == Team.HAWKS:
            return [a.hawks_structures_lost for a in self.daily_totals]
        return [a.coalition_structures_lost for a in self.daily_totals]

    @property
    def isk_totals(self) -> List[int]:
        return self._cumulative(self.y_isk)

    @property
    def ship_totals(self) -> List[int]:
        return self._cumulative(self.y_ships)

    @property
    def structure_totals(self) -> List[int]:
        return self._cumulative(self.y_structures)

    @property
    def battles_per_day(self) -> List[int]:
        return [len(a._nodes) for a in self.daily_totals]

    @property
    def total_battles(self) -> List[int]:
        return self._cumulative(self.battles_per_day)

    @property
    def systems_lost(self) -> List[int]:
        if self.team == Team.HAWKS:
            return [a.hawks_systems_lost for a in self.daily_totals]
        return [a.coalition_systems_lost for a in self.daily_totals]

    @property
    def systems_lost_cumulative(self) -> List[int]:
        return self._cumulative(self.systems_lost)

    def _cumulative(self, values):
        output = []
        current_total = 0
        for day in values:
            current_total += day
            output.append(current_total)
        return output

    @property
    def all_plots(self) -> list:
        return TotalsTraces(
            isk=go.Bar(
                name=self.team.value,
                x=self.x,
                y=self.y_isk,
                marker_color=self.color,
                showlegend=False,
                hovertemplate="Isk: %{y:.2f}<extra></extra>",
            ),
            ships=go.Bar(
                name=self.team.value,
                x=self.x,
                y=self.y_ships,
                marker_color=self.color,
                showlegend=False,
                hovertemplate="Ships: %{y}<extra></extra>",
            ),
            structures=go.Bar(
                name=self.team.value,
                x=self.x,
                y=self.y_structures,
                marker_color=self.color,
                showlegend=False,
                hovertemplate="Structures: %{y}<extra></extra>",
            ),
            isk_cumulative=go.Scatter(
                x=self.x,
                y=self.isk_totals,
                name=self.team.value,
                mode="lines+markers",
                line=dict(color=self.color, width=3),
                showlegend=False,
                hovertemplate="Isk Lost To Date: %{y:.2f}<extra></extra>",
            ),
            ships_cumulative=go.Scatter(
                x=self.x,
                y=self.ship_totals,
                name=self.team.value,
                mode="lines+markers",
                line=dict(color=self.color, width=3),
                showlegend=False,
                hovertemplate="Ships Lost To Date: %{y}<extra></extra>",
            ),
            structures_cumulative=go.Scatter(
                x=self.x,
                y=self.structure_totals,
                name=self.team.value,
                mode="lines+markers",
                line=dict(color=self.color, width=3),
                showlegend=False,
                hovertemplate="Structures Lost To Date: %{y}<extra></extra>",
            ),
            systems_lost=go.Bar(
                x=self.x,
                y=self.systems_lost,
                name=f"{self.team.value} Daily",
                marker_color=self.color,
                hovertemplate='Systems "Lost": %{y}<extra></extra>',
            ),
            systems_cumulative=go.Scatter(
                x=self.x,
                y=self.systems_lost_cumulative,
                name=f"{self.team.value} Totals",
                mode="lines+markers",
                line=dict(color=self.color, width=3),
                hovertemplate='Systems "Lost" To Date: %{y}<extra></extra>',
            ),
        )


@dataclass
class TotalsTraces:
    isk: go.Bar
    ships: go.Bar
    structures: go.Bar
    isk_cumulative: go.Scatter
    ships_cumulative: go.Scatter
    structures_cumulative: go.Scatter
    systems_lost: go.Bar
    systems_cumulative: go.Scatter

    def get_traces(self, trace_type: str) -> list:
        if trace_type == "isk":
            return self.isk_cumulative, self.isk

        if trace_type == "ship":
            return self.ships_cumulative, self.ships

        if trace_type == "structure":
            return self.structures_cumulative, self.structures

        if trace_type == "system":
            return self.systems_cumulative, self.systems_lost
