from dataclasses import dataclass
from datetime import datetime

from data.sde import STATION_FIGHTERS
from models.eve import StationType


@dataclass
class StructureKillTime:
    qualifier: int
    type: StationType
    timer: datetime


def aggregate_additional_data(battles: list):
    for battle in battles:
        attempt_trash_filter(battle)
        add_station_timer_for_fighter(battle)


def attempt_trash_filter(battle: Battle):
    if len(battle.structures) == 0:
        return {}

    all_structure_kill_times = {}
    for team, stations in battle.structures.items():
        for idx, station in enumerate([s for s in stations if s.destroyed_on is not None]):
            station_killmail = find_killmail(battle.raw_json.get("kms", []), url=station.zkill_link)
            km_timestamp = station_killmail.get("time")
            # ship_id = station_killmail.get("victim", {}).get("ship")

            if len(station_killmail.keys()) > 0 and km_timestamp is not None:  # and ship_id in KNOWN_STATION_IDs
                all_structure_kill_times.setdefault(team, []).append(
                    StructureKillTime(
                        qualifier=idx + 1, type=station.type, timer=datetime.fromtimestamp(km_timestamp / 1000)
                    )
                )

    probable_trash = {}
    for team, structure_timers in all_structure_kill_times.items():
        for idx, timer in enumerate(structure_timers):
            for participant in battle.raw_json["kms"]:
                killmail_time = datetime.fromtimestamp(participant["time"] / 1000)
                if len(structure_timers) > idx + 1 and killmail_time >= structure_timers[idx + 1].timer:
                    break
                if timer.timer < killmail_time:
                    structures_that_died = probable_trash.setdefault(team, {})
                    structures_that_died.setdefault(f"{timer.type.value}-{timer.qualifier}", []).append(
                        participant["id"]
                    )

    output = {}
    for team, trash_data in probable_trash.items():
        for struct, ids in trash_data.items():
            output[struct] = [
                p for p in battle.team_participants[team] if get_killmail_id(p.zkill_link) in ids and not p.podded
            ]

    return output


def find_fighters(battle: Battle):
    for team, participants in battle.team_participants.items():
        for p in participants:
            if p.ship in STATION_FIGHTERS.values():
                return p, team, True

    killmails = []
    if "relateds" in battle.raw_json.keys():
        relateds = battle.raw_json.get("relateds", [])
        if len("relateds") > 0:
            killmails = relateds[0].get("kms", [])
    else:
        killmails = battle.raw_json.get("kms", [])
    for km in killmails:
        victim = km.get("vict", km.get("victim", None))
        if victim is None:
            continue
        if victim["ship"] in STATION_FIGHTERS.keys():
            ally = victim["ally"]
            return ally if ally != 0 else victim["corp"], "X", True

    return None, None, False


def add_station_timer_for_fighter(battle: Battle):
    owner, team, has_fighters = find_fighters(battle)
    if len(battle.structures) == 0 and has_fighters:
        if isinstance(owner, int):
            owner = EveAlliance(name="", image_link=str(owner), corps={})  # get_esi_id(owner)
        else:
            owner = EveAlliance(name=owner.name, image_link=owner.zkill_link, corps={owner.corp: "0"})

        unknown_timer = StationKill(
            type=StationType.UNKNOWN,
            value=0.0,
            owner=owner,
            unknown_timer_on=battle.time_data.started,
            system=battle.system,
            zkill_link=None,
        )

        unknown_timer.estimate_timer()

        battle.structures.setdefault(team, []).append(unknown_timer)


def find_killmail(killmails: list, km_id: int = None, url: str = None) -> dict:
    if url is not None:
        km_id = get_killmail_id(url)
    elif km_id is not None:
        km_id = int(km_id)
    else:
        return {}

    for km in killmails:
        if km.get("id") == km_id:
            return km

    return {}


def get_killmail_id(url: str):
    if url is None:
        return None
    return int(url.split("/")[-2])
