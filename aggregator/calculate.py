from models.eve import EveAlliance, EveCorp, EvePilot, EveShip
from br.parser2 import AllData
from data.teams import WhoseWho
import json
from datetime import datetime

WHOSE_WHO = WhoseWho()


def generate_output_totals(all_data: AllData):

    print("\nbuilding alliance_appearances.json")
    alliance_appearances(all_data)
    print("\nbuilding corp_appearances.json")
    corp_appearances(all_data)


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
            hawks.setdefault(corp.alliance, {}).setdefault(corp.name, 0)
            hawks[corp.alliance][corp.name] += 1
        elif corp.alliance in WHOSE_WHO.all_coalition or corp.name in WHOSE_WHO.all_coalition:
            coalition.setdefault(corp.alliance, {}).setdefault(corp.name, 0)
            coalition[corp.alliance][corp.name] += 1
        else:
            other.setdefault(corp.alliance, {}).setdefault(corp.name, 0)
            other[corp.alliance][corp.name] += 1

    desc = "Number of appearances for each corp in each alliance"
    file_name = "docs/jsons/corporation_appearances.json"
    save_data(hawks, coalition, other, desc, file_name)


def save_data(hawks, coalition, other, desc, file_name):
    output = {
        "Description": desc,
        "Last Compiled": datetime.today().strftime("%Y-%m-%d"),
        "Hawks and Friends": hawks,
        "The Coalition": coalition,
        "Unknown": other,
    }

    with open(file_name, "w") as f:
        json.dump(output, f, indent=4)
