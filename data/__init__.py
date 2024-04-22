import json


def load_json(file_name):
    path = f"data/{file_name}"

    with open(path, "r") as f:
        return json.load(f)
