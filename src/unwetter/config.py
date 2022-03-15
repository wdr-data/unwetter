#!/user/bin/env python3.6

import yaml


with open("config/config.yml", "r", encoding="utf-8") as fp:
    CONFIG = yaml.safe_load(fp.read())

SEVERITY_FILTER = CONFIG["SEVERITY_FILTER"]
STATES_FILTER = CONFIG["STATES_FILTER"]
URGENCY_FILTER = CONFIG["URGENCY_FILTER"]


def filter_event(event):
    return (
        event["severity"] in SEVERITY_FILTER
        and event["urgency"] in URGENCY_FILTER
        and len(set(event["states"]) - set(STATES_FILTER)) < len(event["states"])
    )
