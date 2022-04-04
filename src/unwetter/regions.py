#!/user/bin/env python3.6

import yaml

with open("config/regions.yml", "r", encoding="utf-8") as fp:
    REGIONS = {
        key: value
        for key, value in yaml.safe_load(fp.read()).items()
        if value.get("districts")
    }

for name, region in REGIONS.items():
    region["name"] = name


def best_match(districts):
    """
    Takes a list of districts and finds the region(s) that contains them all and the coverage of
    those regions
    :param districts: List of district names
    :return: List of tuples of (region name, relevance)
    """
    districts_set = set(districts)

    def key_function(region):
        size = len(region[1]["districts"])
        not_covered = len(districts_set - set(region[1]["districts"]))
        return not_covered, size

    match = sorted(REGIONS.items(), key=key_function)[0]

    not_covered = len(districts_set - set(match[1]["districts"]))
    relevance = (len(districts) - not_covered) / len(match[1]["districts"])

    if not_covered == 0:
        return [(match[0], relevance)]
    elif not_covered == len(districts):
        print(f'Unkown districts "{list(districts)}"')
        return []
    else:
        return [(match[0], relevance)] + best_match(
            districts_set - set(match[1]["districts"])
        )
