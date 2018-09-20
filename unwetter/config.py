#!/user/bin/env python3.6

import yaml

with open('config/config.yml', 'r') as fp:
    CONFIG = yaml.safe_load(fp.read())

SEVERITY_FILTER = CONFIG['SEVERITY_FILTER']
STATES_FILTER = CONFIG['STATES_FILTER']
