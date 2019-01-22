import json
from collections import defaultdict

from shapely.geometry import shape, MultiPolygon

from unwetter.dwd import state_for_cell_id

with open('assets/shapes/map.json', 'r') as fp:
    collection = json.load(fp)

# One polygon or multi-polygon per district, sorted by state
DISTRICT_SHAPES = defaultdict(list)

for feature in collection['features']:
    district = {
        'name': feature['properties']['NAME'],
        'warn_cell_id': str(feature['properties']['WARNCELLID']),
        'geometry': shape(feature['geometry']),
    }

    DISTRICT_SHAPES[state_for_cell_id(district['warn_cell_id'])].append(district)

DISTRICT_SHAPES = dict(DISTRICT_SHAPES)


# One multi-polygon per state
STATE_SHAPES = {}

for name, state in DISTRICT_SHAPES.items():
    polys = []
    for district in state:
        geom = district['geometry']
        if isinstance(geom, MultiPolygon):
            polys.extend(geom.geoms)
        else:
            polys.append(geom)

    STATE_SHAPES[name] = MultiPolygon(polys)
