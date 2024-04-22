import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List


class Team(Enum):
    HAWKS = "Hawks"
    COALITION = "Coalition"
    THIRD_PARTY = "Third Party"
    NEUTRAL = "Neutral"
    NOT_INVOLVED = "Not Involved"


@dataclass
class SideSwitch:
    name: str
    start: datetime = datetime(1900, 1, 1)
    side: Team = Team.NOT_INVOLVED
    end: datetime = datetime(2999, 12, 31)

    def allegiance(self, at: datetime):
        """
        Returns the allegiance if the datetime provided is between the start (inclusive) and end (exclusive)

        otherwise returns None
        """
        if self.start <= at and at < self.end:
            return self.side
        return None

    def __lt__(self, other):
        if not isinstance(other, SideSwitch):
            raise TypeError(f"Cannot compare {type(other)} to SideSwitch")
        return self.end <= other.start


@dataclass
class WhoseWho:
    NotInvolved: List[str] = field(default_factory=list)
    StarterCorps: List[str] = field(default_factory=list)
    JustStationTrash: List[str] = field(default_factory=list)

    HawksKnown: List[str] = field(default_factory=list)
    HawksNull: List[str] = field(default_factory=list)
    HawksSuspected: List[str] = field(default_factory=list)

    CoalitionKnown: List[str] = field(default_factory=list)
    CoalitionNull: List[str] = field(default_factory=list)
    CoalitionSuspected: List[str] = field(default_factory=list)

    ThirdParty: List[str] = field(default_factory=list)

    SideSwitches: Dict[str, List[SideSwitch]] = field(default_factory=dict)
    Switchers: List[str] = field(default_factory=list)

    def __post_init__(self):
        with open("data\whosewho.json", "r") as f:
            data = json.load(f)

        # corps to ignore
        self.NotInvolved = data["Not Involved"]
        self.StarterCorps = data["Starter Corps"]
        self.JustStationTrash = data["Just Trash"]

        # corps known to start the war on Hawks side
        self.HawksKnown = data["Hawks"]["Known"]
        self.HawksNull = data["Hawks"]["Null"]
        self.HawksSuspected = data["Hawks"]["Suspected"]

        # corps known to start the war on Coalition side
        self.CoalitionKnown = data["Coalition"]["Known"]
        self.CoalitionNull = data["Coalition"]["Null"]
        self.CoalitionSuspected = data["Coalition"]["Suspected"]

        # corps known to have switched sides - see SideSwitches for details
        self.Switchers = data["Switcher"]

        # corps that were opportunistic
        self.ThirdParty = data["Third Party"]

        self.SideSwitches = {
            "corporation - Noob Corp Inc": [
                SideSwitch(name="corporation - Noob Corp Inc", side=Team.HAWKS, end=datetime(2024, 4, 1)),
                SideSwitch(
                    name="corporation - Noob Corp Inc",
                    start=datetime(2024, 4, 1),
                    side=Team.COALITION,
                ),
            ],
            "Seriously Suspicious": [
                SideSwitch(name="Seriously Suspicious", side=Team.COALITION, end=datetime(2024, 4, 17)),
                SideSwitch(name="Seriously Suspicious", side=Team.HAWKS, start=datetime(2024, 4, 17)),
            ],
            "corporation - Vapor Lock.": [
                SideSwitch(name="corporation - Vapor Lock.", side=Team.COALITION, end=datetime(2024, 3, 27)),
                SideSwitch(name="corporation - Vapor Lock.", side=Team.NEUTRAL, start=datetime(2024, 3, 27)),
            ],
        }

    @property
    def all_hawks(self) -> list:
        return [*self.HawksKnown, *self.HawksNull, *self.HawksSuspected]

    @property
    def all_coalition(self) -> list:
        return [*self.CoalitionKnown, *self.CoalitionNull, *self.CoalitionSuspected]

    @property
    def all_not_involved(self) -> list:
        return [*self.NotInvolved, *self.StarterCorps]

    @property
    def all_involved(self) -> list:
        return [*self.all_hawks, *self.all_coalition]

    @property
    def all_known(self) -> list:
        return [*self.all_involved, *self.NotInvolved, *self.ThirdParty, *self.JustStationTrash]

    def which_team_for_switchers(self, name, date: datetime):
        switch_dates = self.SideSwitches.get(name)

        if switch_dates is not None:
            for switch in switch_dates:
                if date >= switch.start and date < switch.end:
                    return switch.side

        return None
