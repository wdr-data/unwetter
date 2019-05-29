from functools import partial

import pyproj
from shapely.geometry import MultiPolygon
from shapely.ops import transform
from PIL import Image, ImageDraw, ImageFont
import yaml

from .data.shapes import STATE_SHAPES
from .config import STATES_FILTER


TARGET_HEIGHT = 1080


COLORS = {
    'SEVERITIES': {
        'Minor': '#ffcc00b0',
        'Moderate': '#ff6600b0',
        'Severe': '#ff0000b0',
        'Extreme': '#cc3399b0',
    }
}

ERROR_FONT = ImageFont.truetype('assets/fonts/VT323-Regular.ttf', 300)

TARGET_PROJECTION = pyproj.Proj(init='epsg:3857')
project = partial(
    pyproj.transform,
    pyproj.Proj(init='epsg:4326'),  # source coordinate system
    TARGET_PROJECTION
)


states = []  # fill with polys, then convert to multi-polygon
surroundings = []

# Create projected copy
for name, shape in STATE_SHAPES.items():

    projected = transform(project, shape)

    if name in STATES_FILTER:
        states.extend(projected.geoms)
    else:
        surroundings.extend(projected.geoms)

states = MultiPolygon(states)
surroundings = MultiPolygon(surroundings)


bbox = states.bounds

img_padding = 75000  # in meters
bbox = (
    bbox[0] - img_padding,
    bbox[1] - img_padding,
    bbox[2] + img_padding,
    bbox[3] + img_padding,
)

dist_x = bbox[2] - bbox[0]
dist_y = bbox[3] - bbox[1]
img_width_ = int(dist_x / 250)
img_height_ = int(dist_y / 250)
img_height = max(img_height_, img_width_)
img_width = max(img_height_, img_width_)
ratio_x = img_width_ / dist_x
ratio_y = img_height_ / dist_y


def to_image_coords(x, y):
    px = int(img_width - ((bbox[2] - x) * ratio_x) + abs(img_width_ - img_width) / 2)
    py = int((bbox[3] - y) * ratio_y + int(abs(img_height_ - img_height) / 2))
    return px, py


def resize(img):
    return img.resize((TARGET_HEIGHT, TARGET_HEIGHT), resample=Image.CUBIC)


background_image = resize(Image.open('assets/images/bg_square.png').convert("RGBA"))
overlay = resize(Image.open('assets/images/overlay_square.png').convert("RGBA"))


def generate_base_map():
    img = Image.new("RGBA", (img_width, img_height), 'black')
    draw = ImageDraw.Draw(img)

    for poly in states:
        points = [to_image_coords(x, y) for x, y in poly.exterior.coords]
        draw.polygon(points, outline=None, fill='white')

        for interior in poly.interiors:
            points = [to_image_coords(x, y) for x, y in interior.coords]
            draw.polygon(points, outline=None, fill='black')

    return img

def draw_event(event, draw):
    if event:
        for geo in event['geometry']:
            for poly in geo['polygons']:
                projected = [to_image_coords(*TARGET_PROJECTION(lng, lat)) for lat, lng in poly]
                draw.polygon(projected, outline=None, fill=COLORS['SEVERITIES'][event['severity']])

            for poly in geo['exclude_polygons']:
                projected = [to_image_coords(*TARGET_PROJECTION(lng, lat)) for lat, lng in poly]
                draw.polygon(projected, outline=None, fill='rgba(0, 0, 0, 0)')

    else:
        draw.text((200, img_height / 2 - 150), "Event not found", font=ERROR_FONT, fill='black')


def severity_key(event):

    mapped = {
        'Minor': 0,
        'Moderate': 1,
        'Severe': 2,
        'Extreme': 3,
    }

    return mapped.get(event['severity'], 100)


def generate_map(events):
    from datetime import datetime
    start = datetime.now()

    img = background_image.copy()
    print('bg', datetime.now() - start)


    event_img = Image.new("RGBA", (img_width, img_height))
    print('created event image', datetime.now() - start)
    draw = ImageDraw.Draw(event_img)
    print('created event draw', datetime.now() - start)

    for event in sorted(events, key=severity_key):
        draw_event(event, draw)
        print('drew event', datetime.now() - start)

    img.alpha_composite(resize(event_img))
    print('first composite/resize', datetime.now() - start)

    img.alpha_composite(overlay)
    print('second composite', datetime.now() - start)

    return img
