from dataclasses import asdict, dataclass, field
from typing import List

from data.teams import WhoseWho
from models.battle_report import Battle


@dataclass
class Group:
    name: str
    corps: dict
    appears: int = 0
    potential_friends: list = field(default_factory=list)
    known_pilots: set = field(default_factory=set)
    num_unique_pilots: int = 0
    ships: dict = field(default_factory=dict)
    ships_lost: dict = field(default_factory=dict)


WHOSE_WHO = WhoseWho()


def calculate_lists(data):

    alliances, ally_as_json = get_all_alliances(data)
    systems = get_all_systems(data)
    holding_corps, lost_structures = get_all_station_owners(data)
    friends = {
        "L A Z E R H A W K S": get_potential_sides(alliances, "L A Z E R H A W K S"),
        "Rainbow Knights": get_potential_sides(alliances, "Rainbow Knights"),
        "Singularity Syndicate": get_potential_sides(alliances, "Singularity Syndicate"),
        "TURBOFEED OR GLORY": get_potential_sides(alliances, "TURBOFEED OR GLORY"),
    }

    all_ships_used = get_all_ships(alliances)
    probable_trash = get_probable_trash(all_ships_used, lost_structures)

    return ally_as_json, systems, holding_corps, friends, all_ships_used, probable_trash


def get_all_alliances(data: List[Battle]):
    known_alliances = {}
    alliances_as_json = {}
    for battle in data:
        for alliance in battle.teams.values():
            for entity, info in alliance.items():

                group = known_alliances.setdefault(entity, Group(entity, info.corps))
                group.potential_friends.extend([a for a in alliance.keys() if a != entity])
                group.known_pilots.update([pilot for pilot in info.pilots.keys()])
                group.appears += 1

                for k, v in info.ships.items():
                    group.ships.setdefault(k, 0)
                    group.ships[k] += v.total
                    if v.lost > 0:
                        group.ships_lost.setdefault(k, 0)
                        group.ships_lost[k] += v.lost

    for n, a in known_alliances.items():
        a.potential_friends = list(set(a.potential_friends))
        a.known_pilots = list(a.known_pilots)
        a.num_unique_pilots = len(a.known_pilots)
        alliances_as_json[n] = asdict(a)

    return known_alliances, alliances_as_json


def get_all_ships(alliances: dict) -> dict:
    ships = {}

    for ally in alliances.values():
        ally_ships = ships.setdefault(ally.name, {".battles": ally.appears})
        for name, value in ally.ships.items():
            ally_ships.setdefault(name, {"t": 0, "l": 0})
            ally_ships[name]["t"] += value
        for name, value in ally.ships_lost.items():
            ally_ships.setdefault(name, {"t": 0, "l": 0})
            ally_ships[name]["l"] += value

    return ships


def get_probable_trash(ships_by_alliance: dict, lost_structures: list) -> list:
    just_trash = {}

    for ally, ships in ships_by_alliance.items():
        possible_trash = []
        for s_name, amt in ships.items():
            if s_name == ".battles":
                continue

            possible_trash.append("Shuttle" in s_name or (amt["l"] <= 5 and amt["l"] == amt["t"]))

        if (
            all(possible_trash)
            and ally not in WHOSE_WHO.all_known
            and ally not in WHOSE_WHO.StarterCorps
            and ally not in lost_structures
        ):
            just_trash.setdefault(ally, ships)
            just_trash[ally][".battles"] = ships[".battles"]

    return just_trash


def get_potential_sides(alliances: dict, friend_to: str) -> list:
    ally: Group
    return [ally.name for ally in alliances.values() if friend_to in ally.potential_friends]


def get_all_systems(data: List[Battle]):
    systems = {}

    for battle in data:
        systems.setdefault(battle.system.name, {"count": 0, "brs": []})
        systems[battle.system.name]["count"] = systems[battle.system.name]["count"] + 1
        systems[battle.system.name]["brs"].append(battle.br_link)

    return systems


def get_all_station_owners(data: List[Battle]):
    known_owners = {}
    lost_structures = []
    for battle in data:
        for team, team_structures in battle.structures.items():
            for structure in team_structures:
                owner = known_owners.setdefault(structure.owner.name, {})
                by_station_type = owner.setdefault(structure.type.value, {"systems": [], "destroyed": 0})
                by_station_type["systems"].append(structure.system.name)
                if structure.value > 0:
                    by_station_type["destroyed"] += 1

    for name, structures in known_owners.items():
        if any(v["destroyed"] > 0 for v in structures.values()):
            lost_structures.append(name)

    return known_owners, lost_structures
