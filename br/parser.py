from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from dateutil import tz
from requests_html import HTMLSession

from br.aggregate import add_station_timer_for_fighter, attempt_trash_filter
from br.mapping import *
from br.util import (
    convert_isk,
    convert_to_zkill,
    get_cache,
    get_regex_groups,
    is_structure,
    save_cache,
    skip_if_cached,
)
from data.sde import JSPACE_STATICS, SYSTEM_WEATHER
from models.battle_report import (
    AssociatedCount,
    Battle,
    BattleReportCount,
    BattleReportGroup,
    BattleReportParticipant,
    BattleReportResults,
    BattleTime,
    StationKill,
)
from models.eve import EveAlliance, StationType, System, Weather


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
    r.html.render(sleep=5)
    save_cache(url, r.html.raw_html)
    return BeautifulSoup(r.html.raw_html, features="html.parser")


def parse_br(url):
    # saved br has different mapping than related quick generation br
    use_br = is_saved_br(url)

    # pages and jsons cached after pulled once
    raw_data = get_json(url, use_br)
    rendered_page = get_page(url)

    date_and_duration = get_date_duration(rendered_page, raw_data, use_br)
    system = get_system(raw_data, use_br)
    team_totals = get_totals_per_side(rendered_page)
    participants, structures, individual_participants = get_participants_per_side(
        url, rendered_page, date_and_duration
    )

    structure_lost = False
    for teams_structures in structures.values():
        for s in teams_structures:
            s.system = system
            s.estimate_timer()
            if not structure_lost and s.value > 0:
                structure_lost = True

    battle = Battle(
        battle_identifier=raw_data.get("_id", raw_data.get("id", url)),
        br_link=url,
        time_data=date_and_duration,
        system=system,
        teams=participants,
        team_results=team_totals,
        team_killmails={},
        team_participants=individual_participants,
        structures=structures,
        station_killed=structure_lost,
        raw_json=raw_data,
    )

    battle.possible_trash = attempt_trash_filter(battle)
    add_station_timer_for_fighter(battle)
    return battle


def is_saved_br(url):
    return "related" not in url


def get_totals_per_side(page: BeautifulSoup) -> BattleReportResults:
    side_results = {}

    result_fields = page.find_all("div", attrs={"class": TEAM_TOTALS})
    result_headers = page.find_all("div", attrs={"class": TEAM_SIDE})
    for idx, team in enumerate(result_fields):
        team_header = get_regex_groups(result_headers[idx].findChildren("h4")[0].text, TEAM_SIDE_AND_NUMBERS_REGEX)

        results = BattleReportResults(isk_lost=0, ships_lost=0, total_pilots=team_header.get("count", 0))
        for div in team.findChildren("div"):
            spans = div.findChildren("span")
            key = spans[0].text
            value = spans[1].text
            if key == "ISK Lost:":
                results.isk_lost = convert_isk(value)
            elif key == "Ships Lost:":
                results.ships_lost = int(value.replace("ships", "").strip())

        side_results[team_header["side"]] = results

    return side_results


def get_participants_per_side(br_url, page: BeautifulSoup, battle_date: BattleTime):
    teams = {}
    side_column = page.find_all("div", attrs={"class": TEAM_SIDE})
    structures = {}
    participants_by_team = {}

    team_sides = ["A", "B", "C", "D", "E"]
    team_name_idx = 0

    for column in side_column:
        aggregate_side_participant_data = {}
        individual_participants = []
        # the same TEAM_SIDE class is used for both results and participants
        # but only results has a h4 value in it, so if that exists we can skip
        if len(column.findChildren("h4")) > 0:
            continue

        team_identifier = team_sides[team_name_idx]
        team_name_idx += 1

        all_participants = column.findChildren("div", attrs={"class": INDIVIDUAL_PARTICIPANT})

        for participant in all_participants:
            ship_image, ship_name, zkill_link = get_ship(participant)

            character_link, character_name, pod = get_character(participant)

            groups, loss_value, multiple_killed = get_groups_and_losses(participant)

            ally_link, ally_name, corp_link, corp_name = get_ally_and_corp(groups)

            participant = build_update_participants(
                br_url,
                aggregate_side_participant_data,
                ship_image,
                ship_name,
                character_link,
                character_name,
                corp_link,
                corp_name,
                ally_link,
                ally_name,
                loss_value,
                zkill_link,
                multiple_killed,
                pod,
            )

            individual_participants.append(participant)

            if is_structure(ship_name):
                top_name = ally_name if ally_name is not None else f"corporation - {corp_name}"
                if "Customs Office" in ship_name:
                    station_type = StationType.POCO
                elif "Control Tower" in ship_name:
                    station_type = StationType.POS
                else:
                    station_type = StationType(ship_name)
                structures.setdefault(team_identifier, []).append(
                    StationKill(
                        type=station_type,
                        value=loss_value,
                        owner=EveAlliance(
                            name=top_name,
                            image_link=ally_link if ally_name is not None else corp_link,
                            corps={corp_name: corp_link},
                        ),
                        destroyed_on=battle_date.started if loss_value > 0 else None,
                        unknown_timer_on=battle_date.started if loss_value == 0 else None,
                        zkill_link=zkill_link,
                    )
                )

        participants_by_team.setdefault(team_identifier, []).extend(
            [i for i in individual_participants if i is not None]
        )
        teams[team_identifier] = aggregate_side_participant_data
    return teams, structures, participants_by_team


def get_ally_and_corp(groups):

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

    return ally_link, ally_name, corp_link, corp_name


def get_groups_and_losses(participant):
    groups = participant.findChildren("div", attrs={"class": PARTICIPANT_GROUP})
    value = participant.findChildren("span", attrs={"class": ISK_VALUE})
    loss_value = convert_isk(value[0].text) if len(value) > 0 else 0
    multiples = participant.findChildren("span", attrs={"class": MULTIPLE_LOST})
    multiple_killed = multiples[0].text if (multiples is not None and len(multiples) > 0) and loss_value > 0 else 1

    if multiple_killed != 1:
        multiple_killed = multiple_killed.replace("lost", "").replace("x", "").strip()

    return groups, loss_value, multiple_killed


def get_character(participant):
    character = participant.findChildren("a", href=True, attrs={"class": PARTICIPANT_NAME})[0]
    character_link = character.attrs["href"]
    character_link = convert_to_zkill(character_link)
    character_name = character.next_element

    while not isinstance(character_name, str):
        character_name = character_name.next_element

    if character_name.next_element is not None and character_name.next_element.text == "[pod]":
        pod = character_name.next_element.attrs["href"]
    else:
        pod = None
    return character_link, character_name, pod


def build_update_participants(
    br_url,
    side_participants,
    ship_image,
    ship_name,
    character_link,
    character_name,
    corp_link,
    corp_name,
    ally_link,
    ally_name,
    loss_value,
    zkill_link,
    multiple_killed,
    pod,
):

    top_name = ally_name if ally_name is not None else f"corporation - {corp_name}"

    alliance = side_participants.setdefault(
        top_name,
        BattleReportGroup(
            name=top_name,
            image_link=ally_link if ally_link is not None else f"corporation - {corp_link}",
            corps={},
            group_results=BattleReportResults(isk_lost=0, ships_lost=0, total_pilots=0),
            group_killmails=[],
            ships={},
            pilots={},
        ),
    )

    alliance.corps.setdefault(corp_name, corp_link)
    alliance.group_results.increase(loss_value)

    ship = alliance.ships.setdefault(
        ship_name,
        BattleReportCount(
            name=ship_name,
            image_link=ship_image,
        ),
    )

    ship.increase(
        value=loss_value, killmail_id=zkill_link, multiple=multiple_killed, associated_name=character_name, br=br_url
    )

    if "\u00a0" in character_name:
        return
    pilot = alliance.pilots.setdefault(
        character_name, BattleReportCount(name=character_name, image_link=character_link)
    )

    pilot.increase(
        value=loss_value, killmail_id=zkill_link, multiple=multiple_killed, associated_name=ship.name, br=br_url
    )

    if pod is not None:
        ship.podded(pod, pilot.name)
        pilot.podded(pod, ship.name)

    return BattleReportParticipant(
        name=pilot.name,
        ship=ship.name,
        alliance=top_name,
        corp=corp_name,
        zkill_link=zkill_link,
        value=loss_value,
        podded=pod is not None,
    )


def get_ship(participant: BeautifulSoup) -> (str, str):
    ship_image = participant.find("div", attrs={"class": PARTICIPANT_SHIP_ICON}).findChildren("img")[0]["src"]
    ship_name = participant.find("div", attrs={"class": PARTICIPANT_SHIP_NAME}).next_element
    if not isinstance(ship_name, str):
        ship_name = ship_name.next_element

    killmail_link = participant.find("div", attrs={"class": PARTICIPANT_SHIP_ICON}).parent.attrs.get("href")
    zkill_link = None
    if killmail_link is not None and "/kill/" in killmail_link:
        zkill_link = convert_to_zkill(killmail_link)

    return ship_image, ship_name, zkill_link


def get_date_duration(page: BeautifulSoup, raw_data: dict, use_br: bool) -> BattleTime:
    if use_br:
        date = datetime.fromtimestamp(raw_data["timings"][0]["start"])
        duration = page.find("div", attrs={"class": SAVED_BR_DURATION}).findChildren("div")
        if len(duration) == 0:
            full_string = page.find("div", attrs={"class": SAVED_BR_DURATION}).text
        else:
            full_string = " ".join([c.text for c in duration])
    else:
        date = datetime.strptime(raw_data["datetime"], "%Y%m%d%H%M")
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


def get_system(raw_data: dict, use_br: bool) -> System:
    system = raw_data["relateds"][0]["system"] if use_br else raw_data["system"]
    system_id = str(raw_data["relateds"][0]["systemID"] if use_br else raw_data["systemID"])
    return System(
        name=system["name"],
        id_num=system_id,
        region=system["region"],
        j_class=f"C{system.get('whClassID')}",
        weather=Weather(SYSTEM_WEATHER.get(system_id, "Vanilla")),
        statics=get_statics(system["name"]),
    )


def get_statics(system_name: str) -> dict:

    statics = JSPACE_STATICS.get(system_name)

    if statics is not None:

        return statics
