from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from typing import List, Tuple

from data.teams import Team, WhoseWho
from models.battle_report import *
from models.timeline import StationTimerBars, TimelineNode
import plotly.express as px
from data import load_json
import json

WHOSE_WHO = WhoseWho()


@dataclass
class BattleMapping:
    systems: dict  # system_name: battles_identifier
    alliances: dict  # alliance/corp name: battles_identifier
    stations: dict  # system_name:stations timers
    days: dict  # datetime iso format: battles_identifier
    battles: dict  # battle_identifier: battle
    j_class: dict


def build_timelines(battles: List[Battle]) -> List[TimelineNode]:

    mapping_of_battles = map_battles(battles)

    nodes = build_timeline_nodes(battles, mapping_of_battles)

    return nodes, mapping_of_battles


def map_battles(battles: List[Battle]):

    systems = {}
    alliances = {}
    stations = {}
    battles_per_day = {}
    battle_identifiers = {}
    j_class = {}
    for battle in battles:
        battle_identifiers[battle.battle_identifier] = battle
        battles_per_day.setdefault(battle.time_data.start_time_as_key, []).append(battle)
        systems.setdefault(battle.system.name, []).append(battle)
        if len(battle.structures) > 0:
            for station in battle.structures.values():
                stations.setdefault(battle.system.name, []).append(station)

        for team in battle.teams.values():
            for name in team.keys():
                alliances.setdefault(name, []).append(battle.battle_identifier)

        j_class.setdefault(battle.system.j_class, []).append(battle)

    for key, value in battles_per_day.items():
        battles_per_day[key] = [
            b.battle_identifier for b in sorted(value, key=lambda x: datetime.timestamp(x.time_data.started))
        ]

    return BattleMapping(
        systems=systems,
        alliances=alliances,
        stations=stations,
        days=battles_per_day,
        battles=battle_identifiers,
        j_class=j_class,
    )


def build_timeline_nodes(battles: List[Battle], battle_mapping: BattleMapping):

    battle_data = []

    colors = build_colors(battle_mapping)

    for battle in battles:

        battle_data.append(build_battle_node(battle, colors[battle.system.name]))

        if len(battle.structures) > 0:
            pass

    return battle_data


def build_colors(battle_mapping: BattleMapping):
    output = {}

    for j_class, battles in battle_mapping.j_class.items():
        unique_systems = list(set([b.system.name for b in battles]))
        n_colors = len(unique_systems)
        if n_colors <= 1:
            n_colors += 2

        colors = px.colors.sample_colorscale("Turbo", [n / (n_colors - 1) for n in range(n_colors)])

        for idx, name in enumerate(unique_systems):
            output[name] = colors[idx]

    return output


def build_battle_node(battle: Battle, color) -> TimelineNode:
    output = determine_team(battle.teams, battle.time_data.started)

    for team, team_name in output.items():

        if team == Team.HAWKS:
            hawks_results = battle.team_results.get(team_name)
            hawks_top_three_ships = get_top_three_ships(battle.team_participants[team_name])
            hawks_suspect = output.get(team_name, {}).get("sus", False)
            hawks_trash_isk = battle.trash_lost_totals.get(team_name, {}).get("value", 0)
            hawks_pilots_in_trash = battle.trash_lost_totals.get(team_name, {}).get("pilots", 0)
            hawks_ships_in_trash = battle.trash_lost_totals.get(team_name, {}).get("ships", 0)
            hawks_team = team_name
            hawks_is_third_party = output.get(team_name, {}).get("unk", False)
        elif team == Team.COALITION:
            coalition_result = battle.team_results.get(team_name)
            coalition_top_three_ships = get_top_three_ships(battle.team_participants[team_name])
            coalition_suspect = output.get(team_name, {}).get("sus", False)
            coalition_trash_isk = battle.trash_lost_totals.get(team_name, {}).get("value", 0)
            coalition__pilots_in_trash = battle.trash_lost_totals.get(team_name, {}).get("pilots", 0)
            coalition_ships_in_trash = battle.trash_lost_totals.get(team_name, {}).get("ships", 0)
            coalition_team = team_name
            coalition_is_third_party = output.get(team_name, {}).get("unk", False)

    if coalition_team == hawks_team:
        raise Exception(f"SAME TEAMS!!!! {battle.battle_identifier}")

    return TimelineNode(
        date=battle.time_data.started,
        duration=battle.time_data.duration,
        system=battle.system,
        hawks_pilots=hawks_results.total_pilots,
        hawks_losses=hawks_results.isk_lost,
        hawks_ships=hawks_results.ships_lost,
        hawks_primary_ships=list(hawks_top_three_ships.keys()),
        not_guaranteed_to_be_hawks=hawks_suspect or hawks_is_third_party,
        hawks_is_third_party=hawks_is_third_party,
        hawks_destroyed_excluding_trash=hawks_results.isk_lost - hawks_trash_isk,
        hawks_pilots_excluding_trash=hawks_results.total_pilots - hawks_pilots_in_trash,
        hawks_ships_excluding_trash=hawks_results.ships_lost - hawks_ships_in_trash,
        coalition_pilots=coalition_result.total_pilots,
        coalition_losses=coalition_result.isk_lost,
        coalition_ships=coalition_result.ships_lost,
        coalition_primary_ships=list(coalition_top_three_ships.keys()),
        coalition_destroyed_excluding_trash=coalition_result.isk_lost - coalition_trash_isk,
        coalition_pilots_excluding_trash=coalition_result.total_pilots - coalition__pilots_in_trash,
        coalition_ships_excluding_trash=coalition_result.ships_lost - coalition_ships_in_trash,
        not_guaranteed_to_be_coalition=coalition_suspect or coalition_is_third_party,
        coalition_is_third_party=coalition_suspect,
        battle_report_link=battle.br_link,
        color=color,
    )


def determine_team(teams, battle_date: datetime) -> Tuple[str, bool]:
    """
    Attempts to return the team identifier letter (A, B, C, ect) that all the fields that have info
    based on team in Battle use. First checks the Know, then all, then switchers.

    returns a tuple of team_letter, bool - and the boolean is True if used all_values
    """
    mapping = {
        Team.HAWKS: {
            "known": WHOSE_WHO.HawksKnown,
            "all": WHOSE_WHO.all_hawks,
        },
        Team.COALITION: {
            "known": WHOSE_WHO.CoalitionKnown,
            "all": WHOSE_WHO.all_coalition,
        },
    }

    tmp = {}
    for team_letter, team in teams.items():
        tmp.setdefault(team_letter, {}).setdefault("total", len(team.keys()))

        for group_name in team.keys():
            for team_name, possible_members in mapping.items():

                if group_name in possible_members["known"]:
                    tmp[team_letter].setdefault("known", []).append(team_name)
                elif group_name in possible_members["all"]:
                    tmp[team_letter].setdefault("suspected", []).append(team_name)
                elif group_name in WHOSE_WHO.Switchers:
                    tmp[team_letter].setdefault("known", []).append(
                        WHOSE_WHO.which_team_for_switchers(group_name, battle_date)
                    )
                elif group_name in WHOSE_WHO.ThirdParty:
                    tmp[team_letter].setdefault("third", []).append(team_name)
                else:
                    tmp[team_letter].setdefault("unknown", []).append(team_name)

    output = {}
    for team_letter, values in tmp.items():
        if (len(values.get("known", [])) == values["total"] and len(set(values.get("known", []))) == 1) or (
            len(values.get("known", [])) > 0 and len(values.get("known", [])) >= len(values.get("suspected", []))
        ):
            output[values["known"][0]] = team_letter

        elif (
            len(values.get("known", [])) < len(values.get("suspected", []))
            and len(values.get("suspected", [])) > 0
            and len(set(values.get("suspected", []))) == 1
        ):
            output[values["suspected"][0]] = team_letter
            output.setdefault(team_letter, {})["sus"] = True

        elif len(values.get("third", [])) > 0:
            output[values["third"][0]] = team_letter
            output.setdefault(team_letter, {})["unk"] = True
        elif len(values.get("unknown", [])) > 0:
            output[values["unknown"][0]] = team_letter
            output.setdefault(team_letter, {})["unk"] = True

    if Team.HAWKS in output.keys() and Team.COALITION not in output.keys():
        output[Team.COALITION] = "B" if output[Team.HAWKS] == "A" else "A"
    elif Team.COALITION in output.keys() and Team.HAWKS not in output.keys():
        output[Team.HAWKS] = "B" if output[Team.COALITION] == "A" else "A"

    return output


def get_top_three_ships(participants: List[BattleReportParticipant]):
    ships_counts = {}
    for pilot in participants:
        ships_counts.setdefault(pilot.ship, 0)
        ships_counts[pilot.ship] += 1

    sorted_ships = {k: v for k, v in sorted(ships_counts.items(), key=lambda item: item[1])}

    count = 0
    output = {}
    for k, v in sorted_ships.items():
        if count < 3:
            output[k] = v
        count += 1

    return output
