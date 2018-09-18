#!/user/bin/env python3.6

import yaml

with open('assets/regions.yml', 'r') as fp:
    REGIONS = yaml.safe_load(fp.read())


def best_match(districts):
    """
    Takes a list of districts and finds the region(s) that contains them all.
    :param districts: List of district names
    :return: List of region names
    """
    raise NotImplementedError
