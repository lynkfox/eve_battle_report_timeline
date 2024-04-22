# regex matching strings

DURATION_AND_TIME_REGEX = r"^((Battle |)(D|d)uration: )((?P<hour>\d{0,2}h)|0|)( |)(?P<minutes>\d{0,2}m|)(,|) from (?P<start_hour>\d{2}):(?P<start_minute>\d{2}) to (?P<end_hour>\d{2}):(?P<end_minute>\d{2}) ET$"
SINGLE_KM_DURATION_AND_TIME_REGEX = r"^Single killmail at (?P<start_hour>\d{2}):(?P<start_minute>\d{2})$"
TEAM_SIDE_AND_NUMBERS_REGEX = r"^Team (?P<side>[A-Z]) \((?P<count>\d{1,4})\)$"

# Mapping for the node class id's
RELATED_BR_DURATION = "_2d-LhPrD"
SAVED_BR_DURATION = "_1anghS2Q"
SINGLE_KM_DURATION = "_1anghS2Q"

TEAM_TOTALS = "aum0KuWu"
TEAM_SIDE = "_3AVG0Xn9"

INDIVIDUAL_PARTICIPANT = "_3PEJ5Tb5"
PARTICIPANT_SHIP_ICON = "_3b14lIup"
PARTICIPANT_SHIP_NAME = "sJjIioyT"
PARTICIPANT_NAME = "_2eGhW02W"  # for <a class="" href> tags

PARTICIPANT_GROUP = "_1VvYd_Ja"
PARTICIPANT_IMAGE_LINK = "_1IIktuec"  # for <img class=""> tags

ISK_VALUE = "YPFHsSZc"  # span\
ZKILL_LINK = "_310ORwlo"  # div above an a
MULTIPLE_LOST = "_15GP4_0d"

IS_NOT_KM = "_3FrwFg8t"
IS_DEATH = "_1R-Fyr0H"
