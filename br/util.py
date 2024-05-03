import json
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup

from models.eve import StationType
from data.sde import JSPACE_STATICS


def get_regex_groups(string, regex):
    r = re.compile(regex)
    try:
        return r.match(string).groupdict()
    except Exception as e:
        print(f"Failure in Regex: {string}")
        raise e


def cached_key(url):
    if "composition" in url or url.split("/")[-2] == "br":
        return url.split("/")[-1].split("?")[0]
    return "_".join(url.split("/")[-2:])


def save_cache(url, data, as_json: bool = False):
    key = cached_key(url)
    Path(f"cache/{key}").mkdir(exist_ok=True)
    if as_json:
        with open(f"cache/{key}/esi_data.json", "w") as f:

            json.dump(data, f, indent=4)
    else:
        with open(f"cache/{key}/br.html", "w", encoding="utf-8") as f:
            f.write(data.decode("utf-8"))

    return key


def get_cache(url, get_json: bool = False):
    key = cached_key(url)
    path = f"cache/{key}"

    if get_json:
        with open(f"{path}/esi_data.json", "r") as f:
            return json.load(f)
    else:
        with open(f"{path}/br.html", "r") as f:
            return BeautifulSoup(f, features="html.parser")


def skip_if_cached(url):
    key = cached_key(url)
    path = f"cache/{key}"
    return os.path.isdir(path) and len(os.listdir(path)) == 2


def get_cache_path(url):
    key = cached_key(url)
    path = f"cache/{key}"
    return path


def convert_isk(text):
    if isinstance(text, int):
        return text / 1000000000
    if "k" in text:
        return float(text.replace("k", "")) / 1000 / 1000
    if "m" in text:
        return float(text.replace("m", "")) / 1000
    if "b" in text:
        return float(text.replace("b", ""))
    else:
        try:
            return float(text)
        except:
            return text


def is_structure(name: str):
    return StationType.has_value(name) or "Control Tower" in name or "Customs Office" in name


def convert_to_zkill(url):
    return url.replace("kb.evetools.org", "zkillboard.com")


def convert_to_br(url):
    return url.replace("zkillboard.com", "br.evetools.org")


def get_id_from_link(url) -> str:
    if "character/structure-" in url:
        return url.split("-")[-1].replace("/", "")
    parts = url.split("/")
    idx = 1
    while idx < len(parts):
        if str.isdigit(parts[-idx]):
            return parts[-idx]
        idx += 1

    print(f"couldn't find id_num in {url}")

    return "0"


def is_saved_br(url):
    return "related" not in url


def get_statics(system_name: str) -> dict:

    statics = JSPACE_STATICS.get(system_name)

    if statics is not None:

        return statics
