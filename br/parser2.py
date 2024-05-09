from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from dateutil import tz
from collections import Counter
from typing import List, Dict, Union

from br.mapping import *
from br.util import (
    convert_isk,
    convert_to_zkill,
    get_cache,
    get_regex_groups,
    is_structure,
    save_cache,
    skip_if_cached,
    get_id_from_link,
    is_saved_br,
    get_statics,
    get_structure_type,
)
from data.sde import SYSTEM_WEATHER
from data.teams import WhoseWho
from models.eve import (
    Weather,
    StructureType,
    SystemOwner,
    EveAlliance,
    EvePilot,
    EveShip,
    EveStructure,
    EveSystem,
    EveCorp,
    EveEntity,
    LARGE_STRUCTURES,
    StructureType,
)
from dataclasses import dataclass, field
from models.battle_report_2 import *
from requests_html import HTMLSession


def get_json(url, use_br: bool):
    if skip_if_cached(url):
        return get_cache(url, get_json=True)

    if use_br:
        url = (
            url.replace("https://br.evetools.org/br", "https://br.evetools.org/api/v1/composition/get") + "?short=true"
        )
    else:
        url = url.replace("https://br.evetools.org/", "https://br.evetools.org/api/v1/")

    page = requests.get(url)
    save_cache(url, page.json(), as_json=True)
    return page.json()


def get_page(url):
    if skip_if_cached(url):
        return get_cache(url)
    session = HTMLSession()
    r = session.get(url)
    r.html.render(sleep=8)
    save_cache(url, r.html.raw_html)
    return BeautifulSoup(r.html.raw_html, features="html.parser")


WHOSE_WHO = WhoseWho()


@dataclass
class AllData:
    alliances: Dict[str, EveAlliance] = field(default_factory=dict)
    corps: Dict[str, EveCorp] = field(default_factory=dict)
    pilots: Dict[str, EvePilot] = field(default_factory=dict)
    ships: Dict[str, EveShip] = field(default_factory=dict)
    systems: Dict[str, EveSystem] = field(default_factory=dict)
    battles: Dict[str, Battle2] = field(default_factory=dict)
    structures: Dict[str, StructureHistory] = field(default_factory=dict)
    structure_owners: Dict[str, List[dict]] = field(default_factory=dict)
    start_date: datetime = datetime(2999, 12, 31, tzinfo=tz.UTC)
    end_date = datetime(1900, 1, 1, tzinfo=tz.UTC)

    def __post_init__(self):
        self.__mapping = {
            "alliance": self.alliances,
            "corp": self.corps,
            "pilot": self.pilots,
            "ship": self.ships,
            "system": self.systems,
            "battle": self.battles,
        }

    def convert(self):
        return {
            "alliances": {k: v.model_dump() for k, v in self.alliances.items()},
            "corps": {k: v.model_dump() for k, v in self.corps.items()},
            "pilots": {k: v.model_dump() for k, v in self.pilots.items()},
            "ships": {k: v.model_dump() for k, v in self.ships.items()},
            "systems": {k: v.model_dump() for k, v in self.systems.items()},
            "battles": {k: v.model_dump() for k, v in self.battles.items()},
            "structures": {k: v.model_dump() for k, v in self.structures.items()},
        }

    def add(self, type: str, name: str, image_link: str, id_num: str = None, **kwargs):
        if "battle" in type.lower():
            raise ValueError(
                "Don't add battles this way. Create battle and setdefault(battleidentifier) to self.battles"
            )
        type = self._convert_type(type)
        if self.has(name, type):
            print(f"{name} already found in all_data.{type}")
            return

        dispatch = {"alliance": EveAlliance, "corp": EveCorp, "pilot": EvePilot, "ship": EveShip, "system": EveSystem}
        entity = dispatch.get(type)

        type_source = self.__mapping.get(type)

        type_source[name] = entity(
            name=name,
            image_link=image_link,
            id_num=id_num if id_num is not None else get_id_from_link(image_link),
            **kwargs,
        )

        return type_source[name]

    def has(self, identifier, type: str = None) -> Union[bool, str]:

        if type is None:
            for key, value in self.__mapping.items():
                if identifier in value.keys():
                    return key

            return False

        type_source = self.__mapping.get(self._convert_type(type))
        return type_source.get(identifier)

    def find(self, identifier: str, type: str = None) -> Union[EveEntity, Battle2]:

        if type is None:
            for value in self.__mapping.values():
                found_value = value.get(identifier)
                if found_value is not None:
                    return found_value

            return None

        type_source = self.__mapping.get(self._convert_type(type))
        return type_source.get(identifier)

    def _convert_type(self, type: str) -> str:
        if type[-1] == "s":
            type = type[:-1]

        if type.lower() not in self.__mapping.keys():
            raise ValueError(f"type of {type} not valid. Should be one of {list(self.__mapping.keys())}")
        return type.lower()

    def get_station_owners(self):
        output = {}
        for structure in self.structures.values():
            system_override = structure.team
            if structure.system in WHOSE_WHO.HawksSystems:
                system_override = Team.HAWKS
            if structure.system in WHOSE_WHO.CoalitionSystems:
                system_override = Team.COALITION
            output.setdefault(structure.system, []).append(
                {
                    "system": structure.system,
                    "type": structure.type.value,
                    "team": system_override.value,
                    "corp": structure.corp,
                    "ally": structure.alliance,
                    "dates": [d.strftime("%Y-%m-%d") for d in structure.dates],
                }
            )
            self.structure_owners.setdefault(structure.system, []).append(
                SystemOwner(
                    system=structure.system,
                    type=structure.type,
                    team=system_override,
                    corp=structure.corp,
                    ally=structure.alliance,
                    dates=[d.strftime("%Y-%m-%d") for d in structure.dates],
                )
            )

        return output


def parse_br2(url, database: AllData):
    if database is None:
        database = AllData()
    # saved br has different mapping than related quick generation br
    use_br = is_saved_br(url)

    # pages and jsons cached after pulled once
    raw_data = get_json(url, use_br)
    rendered_page = get_page(url)

    system, br_id = get_system_and_br_id(raw_data, use_br, database)
    date_and_duration = parse_battle_time_values(rendered_page, raw_data, use_br)

    if date_and_duration.started < database.start_date:
        database.start_date = date_and_duration.started
    if date_and_duration.ended > database.end_date:
        database.end_date = date_and_duration.ended

    battle_totals = get_battle_totals(raw_data, use_br)

    raw_teams = get_raw_teams(rendered_page)

    teams = parse_teams(raw_teams, database, system, br_id, date_and_duration.started)
    for t in teams:
        battle_totals.ships_lost += t.totals.ships_lost
    battle = Battle2(
        battle_identifier=br_id,
        br_link=url,
        time_data=date_and_duration,
        system=system,
        teams=teams,
        br_totals=battle_totals,
        raw_json=raw_data,
    )

    database.battles[br_id] = battle
    return database


def parse_teams(
    raw_teams: dict, all_data: AllData, system: EveSystem, br_id: str, battle_date: datetime
) -> List[TeamReport]:
    """
    parses the teams for individual pilots, ships, kills, structures. Returns a list of TeamReport objects
    as well as updates all_data with new pilots, ships, alliances, corps
    """

    output = []
    for side, raw in raw_teams.items():
        team = TeamReport(br_team_letter=side, totals=get_team_totals(raw["team"], raw["header"]))

        all_suspected_teams = []
        known_teams = []
        structure_team = None
        for participant in raw["participants"]:

            ship, km_link = get_ship_and_km_link(participant, all_data, br_id)
            pilot, pod_link = get_pilot_and_pod_zkill_link(participant, all_data, br_id)
            alliance, corp, loss_value, multiple_killed = get_ally_corp_value_killed(participant, all_data, br_id)

            faction, suspected = hawks_or_not(alliance, corp, battle_date)
            if suspected:
                all_suspected_teams.append(faction)
            else:
                known_teams.append(faction)

            team._ships.append(ship)
            team.km_links.append(km_link)
            if pilot is not None:
                pilot.alliance = alliance.name if alliance is not None else None
                pilot.corp = corp.name
                team._pilots.append(pilot)
            if pod_link is not None:
                team.pilots_podded.append(pilot.name)
                team.km_links.append(pod_link)

            if alliance is not None:
                team._alliances.append(alliance)
            team._corps.append(corp)

            increment_entity_values(pilot, ship, corp, alliance, br_id)

            if is_structure(ship.name):
                structure_team = WHOSE_WHO.known_team(alliance.name if alliance is not None else corp.name)

                is_gunner = pilot is not None and pilot.name != ship.name

                structure_history_id = None
                if not is_gunner:
                    structure_history_id = note_structure_event(
                        ship,
                        structure_team,
                        pilot,
                        alliance,
                        corp,
                        system,
                        battle_date,
                        loss_value,
                        multiple_killed,
                        all_data,
                        br_id,
                    )
                    team.structure_history_ids.append(structure_history_id)
                structure_type = get_structure_type(ship.name)
                structure_entry = EveStructure(
                    name=pilot.name if is_gunner else ship.name,
                    id_num=pilot.id_num if is_gunner else ship.id_num,
                    image_link=pilot.image_link if is_gunner else ship.image_link,
                    type=structure_type,
                    structure_history_id=structure_history_id,
                    destroyed_here=loss_value > 0,
                    loss_value=loss_value,
                    is_gunner_entry=is_gunner,
                    gunner_name=pilot.name if is_gunner else None,
                    gunner_corp=pilot.corp if is_gunner else None,
                    gunner_alliance=pilot.alliance if is_gunner else None,
                    multiple_killed=multiple_killed,
                )

                team._structures.append(structure_entry)
                structure_entry.seen_in.add(br_id)
                team.structure_destroyed = loss_value > 0

                corp.structures.setdefault(system.name, {}).setdefault(structure_type.value, {"s": 0, "d": 0, "g": 0})
                if is_gunner:
                    corp.structures[system.name][structure_type.value]["g"] += 1
                else:
                    corp.structures[system.name][structure_type.value]["s"] += 1
                if loss_value > 0:
                    corp.structures[system.name][structure_type.value]["d"] += 1

                if alliance is not None:
                    alliance.structures.setdefault(system.name, {}).setdefault(
                        structure_type.value, {"s": 0, "d": 0, "g": 0}
                    )
                    if is_gunner:
                        alliance.structures[system.name][structure_type.value]["g"] += 1
                    else:
                        alliance.structures[system.name][structure_type.value]["s"] += 1
                    if loss_value > 0:
                        alliance.structures[system.name][structure_type.value]["d"] += 1

        if structure_team is not None and structure_team is not Team.UNKNOWN:
            team.team = structure_team
        elif len(known_teams) > 0:
            if len(set(known_teams)) == 1:
                team.team = known_teams[0]
            else:
                team_counts = dict(Counter(known_teams))
                team.team = max(team_counts, key=team_counts.get)
        else:

            team_counts = dict(Counter(all_suspected_teams))
            if len(team_counts) == 0:
                print("No team")
            else:
                team.team = max(team_counts, key=team_counts.get)

        output.append(team)

    return output


def parse_battle_time_values(page: BeautifulSoup, raw_data: dict, use_br: bool) -> BattleTime:
    if use_br:
        date = datetime.fromtimestamp(raw_data["timings"][0]["start"], tz=tz.UTC)
        duration = page.find("div", attrs={"class": SAVED_BR_DURATION}).findChildren("div")
        if len(duration) == 0:
            full_string = page.find("div", attrs={"class": SAVED_BR_DURATION}).text
        else:
            full_string = " ".join([c.text for c in duration])
    else:
        date = datetime.strptime(raw_data["datetime"], "%Y%m%d%H%M").replace(tzinfo=tz.UTC)
        ended = page.find("div", attrs={"class": RELATED_BR_DURATION})
        full_string = ended.findNext("div").text

    if "Single killmail" in full_string:
        timing_data = get_regex_groups(full_string, SINGLE_KM_DURATION_AND_TIME_REGEX)
        timing_data["end_hour"] = timing_data["start_hour"]
        timing_data["end_minute"] = timing_data["start_minute"]
    else:
        timing_data = get_regex_groups(full_string, DURATION_AND_TIME_REGEX)

    date.replace(tzinfo=tz.UTC)
    timing_data["hour"] = 0 if timing_data.get("hour") is None else timing_data["hour"].replace("h", "")
    timing_data["minutes"] = (
        0
        if timing_data.get("minutes") is None or timing_data.get("minutes", "").strip() == ""
        else timing_data.get("minutes").replace("m", "")
    )
    return BattleTime(
        started=date.replace(hour=int(timing_data["start_hour"]), minute=int(timing_data["start_minute"])),
        ended=date.replace(hour=int(timing_data["end_hour"]), minute=int(timing_data["end_minute"])),
        duration=timedelta(hours=int(timing_data.get("hour")), minutes=int(timing_data.get("minutes", "0"))),
    )


def get_raw_teams(page: BeautifulSoup):
    teams = {}
    result_fields = page.find_all("div", attrs={"class": TEAM_TOTALS})
    side_column = page.find_all("div", attrs={"class": TEAM_SIDE})
    offset = int(len(side_column) / 2)
    for idx, team in enumerate(result_fields):
        team_header = get_regex_groups(side_column[idx].findChildren("h4")[0].text, TEAM_SIDE_AND_NUMBERS_REGEX)
        teams[team_header["side"]] = {
            "header": team_header,
            "team": team,
            "participants": side_column[idx + offset].findChildren("div", attrs={"class": INDIVIDUAL_PARTICIPANT}),
        }

    return teams


def get_team_totals(team, team_header):
    results = BattleReportResults(isk_lost=0, ships_lost=0, total_pilots=team_header.get("count", 0))
    for div in team.findChildren("div"):
        spans = div.findChildren("span")
        key = spans[0].text
        value = spans[1].text
        if key == "ISK Lost:":
            results.isk_lost = convert_isk(value)
        elif key == "Ships Lost:":
            results.ships_lost = int(value.replace("ships", "").strip())
    return results


def get_battle_totals(raw_data: dict, use_br: bool) -> BattleReportTotals:
    pilots = raw_data["totalPilots"]
    lost = raw_data["totalLost"]
    km_count = raw_data["kmsCount"]

    if not use_br:
        unique_ships = set()
        unique_allys = set()
        for km in raw_data["kms"]:
            victim = km["victim"].get("ship")
            v_ally = km["victim"].get("ally")
            if v_ally == 0:
                v_ally = km["victim"].get("corp")
            if victim is not None:
                unique_ships.add(victim)
            unique_allys.add(v_ally)

            for a in km["attackers"]:
                a_ship = a.get("ship")
                if a_ship is not None:
                    unique_ships.add(a_ship)
                a_ally = a.get("ally")
                if a_ally == 0:
                    a_ally = a.get("corp")
                unique_allys.add(a_ally)

        ship_types = len(list(unique_ships))
        allys = len(list(unique_allys))
    else:
        ship_types = raw_data["totalShipTypes"]
        allys = raw_data["totalAllys"]

    return BattleReportTotals(
        pilots=pilots,
        isk_lost=lost,
        killmails=km_count,
        ships=raw_data.get("totalShips"),
        shipTypes=ship_types,
        groups=allys,
    )


def note_structure_event(
    ship: EveShip,
    team: Team,
    pilot: EvePilot,
    alliance: EveAlliance,
    corp: EveCorp,
    system: EveSystem,
    date: datetime,
    loss_value: float,
    multiple_lost: int,
    all_data: AllData,
    br_id: str,
) -> str:
    structure_type = get_structure_type(ship.name)

    history_id = structure_history_id(system, alliance, corp, ship)

    structure = all_data.structures.setdefault(
        history_id,
        StructureHistory(
            id_number=history_id,
            type=structure_type,
            is_large=structure_type in LARGE_STRUCTURES,
            system=system.name,
            team=team,
            alliance=alliance.name if alliance is not None else None,
            corp=corp.name,
            value=loss_value,
            multiple_in_system=int(multiple_lost),
            zkill_link=None if pilot is None else pilot.name,
        ),
    )

    structure.br_ids.add(br_id)

    if int(multiple_lost) > structure.multiple_in_system:
        structure.multiple_in_system = multiple_lost

    structure.dates.append(date)
    return history_id


def structure_history_id(system: EveSystem, alliance: EveAlliance, corp: EveCorp, ship: EveShip):
    return f"{system.id_num}-{ship.id_num}-{corp.id_num}-{alliance.id_num if alliance is not None else 0000}"


def get_system_and_br_id(raw_data: dict, use_br: bool, all_data: AllData) -> Tuple[System, str]:
    raw_system = raw_data["relateds"][0]["system"] if use_br else raw_data["system"]
    system_id = str(raw_data["relateds"][0]["systemID"] if use_br else raw_data["systemID"])
    br_id = raw_data.get("id", raw_data.get("_id"))
    if all_data.has(raw_system["name"], "system"):
        system = all_data.find(raw_system["name"], "system")
    else:
        system = all_data.add(
            "system",
            name=raw_system["name"],
            image_link="",
            id_num=system_id,
            region=raw_system["region"],
            j_class_number=raw_system.get("whClassID", 0),
            weather=Weather(SYSTEM_WEATHER.get(system_id, "Vanilla")),
            statics=get_statics(raw_system["name"]),
        )

    system.seen_in.add(br_id)

    return system, br_id


def get_ship_and_km_link(participant: BeautifulSoup, all_data: AllData, br_id: str) -> Tuple[EveShip, str]:
    """
    parses the participant for the ship and the zkill link. Adds the ship toi all_data if it is new
    """
    ship_image = participant.find("div", attrs={"class": PARTICIPANT_SHIP_ICON}).findChildren("img")[0]["src"]
    ship_name = participant.find("div", attrs={"class": PARTICIPANT_SHIP_NAME}).next_element
    if not isinstance(ship_name, str):
        ship_name = ship_name.next_element

    killmail_link = participant.find("div", attrs={"class": PARTICIPANT_SHIP_ICON}).parent.attrs.get("href")
    zkill_link = None
    if killmail_link is not None and "/kill/" in killmail_link:
        zkill_link = convert_to_zkill(killmail_link)

    ship = (
        all_data.find(ship_name, "ship")
        if all_data.has(ship_name, "ship")
        else all_data.add("ship", ship_name, ship_image)
    )

    ship.seen_in.add(br_id)
    return ship, zkill_link


def get_pilot_and_pod_zkill_link(participant: BeautifulSoup, all_data: AllData, br_id: str) -> Tuple[EvePilot, str]:
    character = participant.findChildren("a", href=True, attrs={"class": PARTICIPANT_NAME})[0]
    character_link = character.attrs["href"]
    character_link = convert_to_zkill(character_link)
    character_name = character.next_element

    while not isinstance(character_name, str):
        character_name = character_name.next_element

    if "\xa0" in character_name:
        return None, None
    if all_data.has(character_name, "pilot"):
        pilot = all_data.find(character_name, "pilot")
    else:
        pilot = all_data.add("pilot", character_name, character_link, corp="", alliance="", zkill_link=character_link)

    if character_name.next_element is not None and character_name.next_element.text == "[pod]":
        pod = character_name.next_element.attrs["href"]
        pilot.podded_in.add(br_id)
    else:
        pod = None

    pilot.seen_in.add(br_id)
    return pilot, pod


def get_ally_corp_value_killed(
    participant: BeautifulSoup, all_data: AllData, br_id: str
) -> Tuple[EveAlliance, EveCorp, str, str, Team]:

    groups = participant.findChildren("div", attrs={"class": PARTICIPANT_GROUP})
    value = participant.findChildren("span", attrs={"class": ISK_VALUE})
    loss_value = convert_isk(value[0].text) if len(value) > 0 else 0
    multiples = participant.findChildren("span", attrs={"class": MULTIPLE_LOST})
    multiple_killed = multiples[0].text if (multiples is not None and len(multiples) > 0) and loss_value > 0 else 1

    if multiple_killed != 1:
        multiple_killed = multiple_killed.replace("lost", "").replace("x", "").strip()

    for v in groups:
        possible_imgs = v.findChildren("img")
        if len(possible_imgs) == 0:
            ally_link = None
            ally_name = None
        else:
            img = possible_imgs[0]
            if "corp" in img.attrs["alt"]:
                corp_link = img.attrs["src"].strip()
                corp_name = v.attrs["title"].replace("corporation:", "").strip()

            if "ally" in img.attrs["alt"]:
                ally_link = img.attrs["src"].strip()
                ally_name = v.attrs["title"].strip()

    if ally_name is not None:
        if all_data.has(ally_name, "alliance"):
            alliance = all_data.find(ally_name, "alliance")
        else:
            alliance = all_data.add(
                "alliance",
                name=ally_name,
                image_link=ally_link,
            )
            alliance.corps.add(corp_name)

        alliance.seen_in.add(br_id)
    else:
        alliance = None

    if all_data.has(corp_name, "corp"):
        corp = all_data.find(corp_name, "corp")
    else:
        corp = all_data.add("corp", name=corp_name, image_link=corp_link, alliance=ally_name)

    # TODO: Add Holding Corp determination here

    corp.seen_in.add(br_id)

    return alliance, corp, loss_value, multiple_killed


def hawks_or_not(alliance: EveAlliance, corp: EveCorp, date: datetime) -> Tuple[Team, bool]:

    if (alliance is not None and alliance.name in WHOSE_WHO.Switchers) or corp.name in WHOSE_WHO.Switchers:
        return WHOSE_WHO.which_team_for_switchers(corp.name if alliance is None else alliance.name, date), False
    suspected = False
    if alliance is None:
        team = WHOSE_WHO.known_team(corp.name)
    else:
        team = WHOSE_WHO.known_team(alliance.name)

    if team == Team.UNKNOWN:
        if alliance is None:
            team = WHOSE_WHO.known_team(corp.name)
        else:
            team = WHOSE_WHO.known_team(alliance.name)

        suspected = True

    return team, suspected


def increment_entity_values(pilot: EvePilot, ship: EveShip, corp: EveCorp, alliance: Optional[EveAlliance], br_link):
    if pilot is not None and ship is not None:
        pilot.ships.setdefault(ship.name, 0)
        pilot.ships[ship.name] += 1

    if corp is not None and pilot is not None:
        corp.members.setdefault(pilot.name, 0)
        corp.members[pilot.name] += 1

        corp.pilots_per_battle.setdefault(br_link, 0)
        corp.pilots_per_battle[br_link] += 1

    if corp is not None and ship is not None:
        corp.ships.setdefault(ship.name, 0)
        corp.ships[ship.name] += 1

    if alliance is not None and corp is not None:
        alliance.members.setdefault(corp.name, 0)
        alliance.members[corp.name] += 1
