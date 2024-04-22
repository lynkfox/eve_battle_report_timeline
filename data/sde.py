from data import load_json

STATION_FIGHTERS = {
    47131: "Standup Cenobite I",
    47134: "Standup Cenobite II",
    47133: "Standup Dromi I",
    47137: "Standup Dromi II",
    47132: "Standup Scarab I",
    47135: "Standup Scarab II",
    47037: "Standup Siren I",
    47136: "Standup Siren II",
}

SYSTEM_WEATHER = load_json("system_weather.json")

JSPACE_STATICS = load_json("jspace_statics.json")
