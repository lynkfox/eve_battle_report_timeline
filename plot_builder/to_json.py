import json
from models.battle_report_2 import Battle2
from typing import List
from models.eve import EveAlliance, EveCorp, EvePilot, EveShip
from br.parser2 import AllData
from data.teams import WhoseWho
import json
from datetime import datetime
from dateutil import tz

WHOSE_WHO = WhoseWho()


def generate_output_totals(all_data: AllData):

    t_shirt(all_data.systems)

    print("saving all_battle_reports.json")
    battles_to_json(all_data.battles)

    print("\nbuilding alliance_appearances.json")
    alliance_appearances(all_data)

    print("\nbuilding corp_appearances.json")
    corp_appearances(all_data)

    print("saving systems.json")
    systems(all_data)

    print("filtering alliances to just the big names in major_players.json")
    big_names(all_data)


def t_shirt(systems):
    with open("docs/jsons/all_systems_tshirt.txt", "w") as f:
        f.write(" ".join(systems.keys()))


def battles_to_json(all_battles: List[Battle2]):
    battles = {battle.battle_identifier: battle.model_dump() for battle in all_battles.values()}

    output = {
        "description": "All battles compiled with top level relevant data",
        "last_compiled": datetime.today().strftime("%Y-%m-%d"),
        "battles": battles,
    }

    with open("docs/jsons/all_battle_reports.json", "w") as f:
        json.dump(output, f, indent=4)


def big_names(all_data):
    hawks_big_names = {
        "L A Z E R H A W K S": ["Rainbow Knights"],
        "Hard Knocks Citizens": ["Hard Knocks Associates"],
        "Rote Kapelle": [],
        "Breuvages Kiri": [],
        "New. Sig.": ["Sirius Krabs", "Sirius-Business", "Holdlings"],
        "Ugandan Death Squad": [],
        "Kingsparrow Wormhole Division": [
            "C U L T",
        ],
        "Turbo miners inc": [],
        "No Vacancies.": ["Caduceus.", "Wardec Mechanics"],
        "jeberbek": [],
        "1-800 Space Maids": [],
        "The Shire of Guinea Pigs": ["Guinea Pigs Appreciation Society"],
        "SL0W CHILDREN AT PLAY": ["SLOW Logistics Alliance", "SL0W. Holding"],
        "NeighbourRoach": [],
        "Blue Loot Not Included": [],
        "Czarna-Kompania.": [],
        "Seriously Suspicious": ["SUS Holding"],
    }

    coalition_big_names = {
        "Singularity Syndicate": ["SYNDE Associates", "ATLAS CORPORATION S.A", "ATLAS CORPORATION HOLDING"],
        "TURBOFEED OR GLORY": ["Koneko's Child Support Payments"],
        "Unchained Alliance": ["Outback Krabhouse"],
        "Wild Fat Cocks": [],
        "We Forsakened Few": ["FFEW Associates"],
        "Sugar.": ["Now You Don't", "Hyperglycemia Holdings", "Aspartame."],
        "Atrax Hollow": ["The Candy Shop"],
        "Stay Feral": [],
        "Hole Control": ["Operaatio MatoLuola"],
        "Disturbing Silence.": ["Top Shelf", "Top Shelf Holding"],
        "No Mercy For Percy.": [],
        "E.C.H.O": ["E.C.H.O Holding"],
        "Vapor Lock.": [],
        "Moss Piglet Preservation Society": [],
        "Turbo miners inc": [],
    }

    swappers = {"Seriously Suspicious": ["SUS Holding"], "Vapor Lock.": [], "Noob Corp Inc": []}

    hawks = {}
    coalition = {}

    for name, appearances in all_data.alliances.items():

        is_hawks = add_to_this_major_player(hawks_big_names, hawks, name, appearances)

        if not is_hawks:
            add_to_this_major_player(coalition_big_names, coalition, name, appearances)

    for name, appearances in all_data.corps.items():

        if appearances.alliance is not None:
            continue
        is_hawks = add_to_this_major_player(hawks_big_names, hawks, name, appearances)

        if not is_hawks:
            add_to_this_major_player(coalition_big_names, coalition, name, appearances)

    for v in hawks.values():

        find_last_battle(all_data, v)

    for v in coalition.values():
        find_last_battle(all_data, v)

    desc = "major players in the war"
    file_name = "docs/jsons/major_players.json"
    quick_reference = {"hawks": hawks_big_names, "coalition": coalition_big_names, "side_switchers": swappers}
    save_data(hawks, coalition, [], desc, file_name)


def find_last_battle(all_data, v):
    v["battles"] = list(v["battles"])
    last_seen = datetime(year=1900, month=1, day=1, tzinfo=tz.UTC)
    for battle in v["battles"]:
        battle_date = all_data.battles[battle].time_data.started
        if battle_date > last_seen:
            last_seen = battle_date
            br_link = all_data.battles[battle].br_link
            br_identifier = battle

    v["last_seen"] = {"br_identifier": br_identifier, "br_link": br_link, "date": last_seen.strftime("%Y-%m-%d")}


def add_to_this_major_player(team_affiliates, team_data, name, appearances):
    for k, v in team_affiliates.items():
        if name == k or name in v:
            if k not in team_data.keys():
                team_data[k] = {
                    "name": k,
                    "isk_lost": appearances.total_lost_isk,
                    "ships_lost": appearances.total_lost_ships,
                    "battles": appearances.seen_in,
                    "affiliated": [] if name == k else [name],
                }
            else:
                data = team_data[k]
                if name != k and name not in data["affiliated"]:
                    data["affiliated"].append(name)
                data["isk_lost"] += appearances.total_lost_isk
                data["ships_lost"] += appearances.total_lost_ships
                data["battles"].update(appearances.seen_in)

            return True

    return False


def alliance_appearances(all_data: AllData):
    hawks = {k: v.appearances for k, v in all_data.alliances.items() if k is not None and k in WHOSE_WHO.all_hawks}
    coalition = {
        k: v.appearances for k, v in all_data.alliances.items() if k is not None and k in WHOSE_WHO.all_coalition
    }
    other = {
        k: v.appearances
        for k, v in all_data.alliances.items()
        if k not in WHOSE_WHO.all_hawks and k not in WHOSE_WHO.all_coalition
    }

    desc = "Number of appearances for each alliance"
    file_name = "docs/jsons/alliance_appearances.json"
    save_data(hawks, coalition, other, desc, file_name)


def corp_appearances(all_data: AllData):
    hawks = {}
    coalition = {}
    other = {}
    for corp in all_data.corps.values():
        if corp.alliance in WHOSE_WHO.all_hawks or corp.name in WHOSE_WHO.all_hawks:
            hawks.setdefault(corp.alliance, {}).setdefault(corp.name, corp.appearances)
        elif corp.alliance in WHOSE_WHO.all_coalition or corp.name in WHOSE_WHO.all_coalition:
            coalition.setdefault(corp.alliance, {}).setdefault(corp.name, corp.appearances)
        else:
            other.setdefault(corp.alliance, {}).setdefault(corp.name, corp.appearances)

    desc = "Number of appearances for each corp in each alliance"
    file_name = "docs/jsons/corporation_appearances.json"
    save_data(hawks, coalition, other, desc, file_name)


def systems(all_data):

    output = [
        {
            "system": system.name,
            "j_class": system.j_class_number,
            "statics": system.static_str,
            "battles": len(system.seen_in),
        }
        for system in all_data.systems.values()
    ]

    with open("docs/jsons/system_appearances.json", "w") as f:
        json.dump(output, f, indent=4)


def save_data(hawks, coalition, other, desc, file_name):
    output = {
        "description": desc,
        "last_compiled": datetime.today().strftime("%Y-%m-%d"),
        "hawks_and_friends": hawks,
        "the_coalition": coalition,
        "unknown_or_other": other,
    }

    with open(file_name, "w") as f:
        json.dump(output, f, indent=4)
