import json
from time import sleep
from br.parser2 import parse_br2, load_br_links
from br.util import skip_if_cached
from plot_builder.output import build_scatter
from plot_builder.to_json import generate_output_totals
import os

os.environ["PYPPETEER_CHROMIUM_REVISION"] = "1263111"


def parse_battles2(br_links):
    PROCESS_LIST = br_links  # new

    first = True
    battle_data = None
    for idx, br in enumerate(PROCESS_LIST):
        if first:
            battle_data = parse_br2(br, battle_data)
            first = False
        else:
            if not skip_if_cached(br):
                sleep(3)
            print(f"Retrieving and parsing {br}...")
            parse_br2(br, battle_data)
            print(f"...Done (Completed {idx} of {len(PROCESS_LIST)-1}) \n")

    return battle_data


if __name__ == "__main__":
    existing_battles = None  # future for picking battle data

    br_links = load_br_links()

    if existing_battles is None or len(existing_battles.battles) > len(br_links):
        battles = parse_battles2(br_links)
        print("Saving data...\n")

        with open("output/structure_owners.json", "w") as f:
            json.dump(battles.get_station_owners(), f, indent=4)

        generate_output_totals(battles)

        # with open(pickled_data_file, "wb") as f:
        #     pickle.dump(battles, f)
        # with open("output/war_to_date.json", "w") as f:
        #     json.dump(battles.convert(), f, indent=4)
    else:
        print("No new BR links found, loading cache")
        battles = existing_battles

    # print("Generating calculations...\n")
    # alliances, systems, holding_corps, probable_friends, ships, probably_just_trash = calculate_lists(battles)

    # content = {
    #     "probably_just_trash": probably_just_trash,
    #     "trash_list": [k for k in probably_just_trash.keys()],
    #     "probable_friends": probable_friends,
    #     "known_alliances": alliances,
    #     "known_systems": systems,
    #     "known_holding_corps": holding_corps,
    #     "known_ships": ships,
    # }
    # with open("output/war_lists.json", "w") as f:
    #     json.dump(content, f, indent=4)

    print("creating timeline plot")

    fig = build_scatter(battles)
