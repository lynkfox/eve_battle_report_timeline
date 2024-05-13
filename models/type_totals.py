from __future__ import annotations
from models.battle_report_2 import Battle2
from models.eve import EntityType, EveEntity, EveShip
from data.teams import Team
from models.battle_report_2 import TeamReport
from models.timeline2 import (
    HAWKS_COLOR,
    COALITION_COLOR,
    UNKNOWN_COLOR,
    HAWKS_BORDER,
    COALITION_BORDER,
    UNKNOWN_BORDER,
)
from models.daily_totals import SingleBattleTotal
from br.util import is_structure
from dataclasses import dataclass, field
from typing import List, Any, Dict, Union
import plotly.graph_objects as go
from pandas import DataFrame


@dataclass
class yValue:
    team: Team
    y: List[Any] = field(default_factory=list)
    totals: dict = field(default_factory=dict)
    color: str = ""

    def __post_init__(self):
        if self.team == Team.HAWKS:
            self.color = HAWKS_COLOR
        elif self.team == Team.COALITION:
            self.color = COALITION_COLOR
        else:
            self.color = UNKNOWN_COLOR

    def build_traces(self, x_values, dividing_index=1, offset_value=0):
        raise NotImplementedError

    def calculate_y_totals(self, x_values):
        raise NotImplementedError

    def __add__(self, other):
        new = yValue(team=self.Team, color=self.color)

        for k in self.totals.keys():
            new.totals[k] = self.totals[k] + other.totals.get(k, 0)

        for k2 in other.totals.keys():
            if k2 not in new.totals.keys():
                new.totals[k2] = other.totals[k2]

        if len(self.y) == 0 or len(other.y) == 0:
            new.y = [*self.y, other.y]
        else:
            smallest = self.y if len(self.y) <= len(other.y) else other.y
            largest = self.y if len(self.y) > len(other.y) else other.y

            for value in smallest:
                new.y.append(value + largest.pop(0))

            new.y.extend(largest.y)

        return new


@dataclass
class EntityTraceTotal:
    data: List[Union[EveEntity, Battle2]]
    entity_type: EntityType
    _nodes: List[SingleBattleTotal] = None
    x: List[str] = None
    y_values: Dict[Team, yValue] = field(default_factory=dict)

    def post_init_callable(self):
        for battle in self.data:
            for team in battle.teams:
                self.count_types(team)

        x = []
        for team in self.y_values.values():
            x.extend(team.totals.keys())

        self.x = sorted(list(set(x)))

        for team in self.y_values.values():
            team.calculate_y_values(self.x)

    def count_types(self, team: TeamReport):
        """
        Implement this in order to make the counts for the graphs

        should count whatever is necessary out of the team and add it to the dictionary of self.y_values[Team.Enum] a child class
        of yValue.

        """

        raise NotImplementedError()


@dataclass
class ShipYValues(yValue):
    # y: List[int] = None # total ships
    totals_destroyed: Dict[str, int] = field(default_factory=dict)
    y_destroyed: List[int] = None
    y_survived: List[int] = None

    def __post_init__(self):
        if self.team == Team.HAWKS:
            self.color_d = HAWKS_BORDER
        elif self.team == Team.COALITION:
            self.color_d = COALITION_BORDER
        else:
            self.color_d = UNKNOWN_BORDER
        return super().__post_init__()

    def build_traces(self, x_values, dividing_index=1, offset_value=0):
        marker = dict(color=self.color, line=dict(color="#dedede", width=1))
        marker_d = dict(color=self.color_d, line=dict(color="#dedede", width=1))

        df = DataFrame({"names": x_values, "survived": self.y_survived, "destroyed": self.y_destroyed})

        first = [
            go.Bar(
                base=0 if offset_value < 0 else None,
                name=self.team.value,
                x=df["names"][:dividing_index],
                y=df["survived"][:dividing_index],
                marker=marker,
                showlegend=True,
                hovertemplate="%{x}: %{y}<extra></extra>",
                width=0.4,
                legendgroup=self.team.value,
                offset=offset_value,
            ),
            go.Bar(
                base=df["survived"][:dividing_index] if offset_value < 0 else None,
                name=f"{self.team.value} (Destroyed)",
                x=df["names"][:dividing_index],
                y=df["destroyed"][:dividing_index],
                marker=marker_d,
                showlegend=True,
                customdata=self.y_destroyed[:dividing_index],
                hovertemplate="%{x}: %{customdata}<extra></extra>",
                width=0.4,
                legendgroup=self.team.value,
                offset=offset_value,
            ),
        ]

        second = [
            go.Bar(
                base=0 if offset_value < 0 else None,
                name=self.team.value,
                x=df["names"][dividing_index:],
                y=df["survived"][dividing_index:],
                marker=marker,
                showlegend=False,
                hovertemplate="%{x}: %{y}<extra></extra>",
                width=0.4,
                legendgroup=self.team.value,
                offset=offset_value,
            ),
            go.Bar(
                base=df["survived"][dividing_index:] if offset_value < 0 else None,
                name=f"{self.team.value} (Destroyed)",
                x=df["names"][dividing_index:],
                y=df["destroyed"][dividing_index:],
                marker=marker_d,
                showlegend=False,
                customdata=self.y_destroyed[dividing_index:],
                hovertemplate="%{x}: %{customdata}<extra></extra>",
                width=0.4,
                legendgroup=self.team.value,
                offset=offset_value,
            ),
        ]

        return first, second

    def calculate_y_values(self, x_values):
        self.y = [self.totals.get(k, 0) + self.totals_destroyed.get(k, 0) for k in x_values]
        self.y_destroyed = [self.totals_destroyed.get(k, 0) for k in x_values]
        self.y_survived = [self.totals.get(k, 0) - self.totals_destroyed.get(k, 0) for k in x_values]

    def __add__(self, other):
        new = ShipYValues(team=self.team, color=self.color)

        for k in self.totals.keys():
            new.totals[k] = self.totals[k] + other.totals.get(k, 0)

        for k2 in other.totals.keys():
            if k2 not in new.totals.keys():
                new.totals[k2] = other.totals[k2]

        for k in self.totals_destroyed.keys():
            new.totals_destroyed[k] = self.totals_destroyed[k] + other.totals_destroyed.get(k, 0)

        for k2 in other.totals_destroyed.keys():
            if k2 not in new.totals_destroyed.keys():
                new.totals_destroyed[k2] = other.totals_destroyed[k2]

        if len(self.y) == 0 or len(other.y) == 0:
            new.y = [*self.y, other.y]
        else:
            smallest = self.y if len(self.y) <= len(other.y) else other.y
            largest = self.y if len(self.y) > len(other.y) else other.y

            for value in smallest:
                new.y.append(value + largest.pop(0))

            new.y.extend(largest)

        return new


@dataclass
class ShipTotals(EntityTraceTotal):
    def __post_init__(self):
        self.post_init_callable()

    def count_types(self, team: TeamReport):
        if team.team == Team.NOT_INVOLVED:
            return

        if team.team == Team.THIRD_PARTY:
            use_team = Team.UNKNOWN
        else:
            use_team = team.team

        entity_totals = ShipYValues(
            team=use_team,
        )

        for ship in [v for v in team.ships]:
            if self._is_valid(ship):
                entity_totals.totals.setdefault(ship, 0)
                entity_totals.totals[ship] += 1

        for ship in [v for v in team.ships_destroyed]:
            if self._is_valid(ship):
                entity_totals.totals_destroyed.setdefault(ship, 0)
                entity_totals.totals_destroyed[ship] += 1

        if use_team in self.y_values:
            self.y_values[use_team] += entity_totals
        else:
            self.y_values[use_team] = entity_totals

    def _is_valid(self, name):

        # if name in [*IGNORE_IN_SHIPS]:
        #     return False

        if is_structure(name):
            return False

        for v in [
            "firbolg",
            "drifter",
            "quafe",
            "shuttle",
            "standup",
            "missile",
            "torpedo",
            "pulse",
            "beam",
            "autocannon",
            "artillery",
            "blaster",
            "railgun",
            "disintegrator",
            "webifier",
            "neutralizer",
            "ii",
            "mobile",
            "battery",
            "warp",
            "array",
            "sensor",
            "painter",
            "vespa",
            "ec-300",
            "curator",
        ]:
            if v in name.lower():
                return False

        if name in [
            "Algos",
            "Apocalypse",
            "Apotheosis",
            "Ares",
            "Atron",
            "Augoror",
            "Badger",
            "Barghest",
            "Bestower",
            "Blackbird",
            "Burst",
            "Bustard",
            "Caracal",
            "Catalyst",
            "Condor",
            "Claw",
            "Cheetah",
            "Corax",
            "Coercer",
            "Coercer Navy",
            "Cormorant",
            "Cormorant Navy",
            "Covetor",
            "Crane",
            "Crow",
            "Crucifier",
            "Crusader",
            "Dragoon",
            "Endurance",
            "Enyo",
            "Epithal",
            "Executioner",
            "Exequror",
            "Ferox",
            "Gnosis",
            "Griffin",
            "Harbinger",
            "Harbinger Navy",
            "Hawk",
            "Heron",
            "Heron Navy",
            "Hoarder",
            "Hurricane",
            "Ibis",
            "Imicus",
            "Imp Navy Slicer",
            "Impairor",
            "Impel",
            "Incursus",
            "Inquisitor",
            "Iteron Mark V",
            "Kestrel",
            "Leapard",
            "Maelstrom",
            "Magnate",
            "Magnate Navy",
            "Magus",
            "Malediction",
            "Maller",
            "Mammoth",
            "Mastodon",
            "Maulus",
            "Merlin",
            "Metamorphosis",
            "Moa",
            "Moros",
            "Myrmidon",
            "Myrmidon Navy",
            "Naga",
            "Navitas",
            "Nereus",
            "Nergal",
            "Ninazu",
            "Noctis",
            "Occator",
            "Omen",
            "Orca",
            "Osprey",
            "Panther",
            "Phantasm",
            "Phobos",
            "Pilgrim",
            "Pontifex",
            "Porpoise",
            "Probe",
            "Procurer",
            "Prophecy",
            "Prospect",
            "Providence",
            "Prowler",
            "Punisher",
            "Raptor",
            "Reaper",
            "Redeemer",
            "Rep Fleet Firetail",
            "Retriever",
            "Rifter",
            "Rokh",
            "Rook",
            "Rorqual",
            "Rapture",
            "Scalpel",
            "Scythe",
            "Scythe Fleet",
            "Sentinel" "Sigil",
            "SLasher",
            "Stabber",
            "Stabber Fleet",
            "Stork",
            "Stratios",
            "Succubus",
            "Sunesis",
            "Talos",
            "Talwar",
            "Tayra",
            "Tempest",
            "Thalia",
            "Thorax",
            "Thrasher",
            "Thrasher Fleet",
            "Tristan",
            "Velator",
            "Venture",
            "VViator",
            "Vigil",
            "Wolf",
            "Worm",
            "Wreath",
        ]:
            return False

        return True
