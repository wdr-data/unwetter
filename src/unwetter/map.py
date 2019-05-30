from functools import partial
from math import tan, radians

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
        'Minor': '#ffcc00a0',
        'Moderate': '#ff6600a0',
        'Severe': '#ff0000a0',
        'Extreme': '#cc3399a0',
    },
    'WDRA_TEXT_BACKGROUND': '#00335dcc',
}

FONT_ERROR = ImageFont.truetype('assets/fonts/VT323-Regular.ttf', 150)

TARGET_PROJECTION = pyproj.Proj(init='epsg:3857')
project = partial(
    pyproj.transform,
    pyproj.Proj(init='epsg:4326'),  # source coordinate system
    TARGET_PROJECTION
)

states = []  # fill with polys, then convert to multi-polygon

# Create projected copy
for name, shape in STATE_SHAPES.items():
    if name in STATES_FILTER:
        projected = transform(project, shape)
        states.extend(projected.geoms)

states = MultiPolygon(states)

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
studios = resize(Image.open('assets/images/overlay_square.png').convert("RGBA"))
mask = resize(Image.open('assets/images/mask_square.png').convert("RGBA"))
logo_wdra = resize(Image.open('assets/images/logo_wdra_square.png').convert("RGBA"))

overlay = mask.copy()
overlay.alpha_composite(studios)
overlay.alpha_composite(logo_wdra)


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
    for geo in event['geometry']:
        for poly in geo['polygons']:
            projected = [to_image_coords(*TARGET_PROJECTION(lng, lat)) for lat, lng in poly]
            draw.polygon(projected, outline=None, fill=COLORS['SEVERITIES'][event['severity']])

        for poly in geo['exclude_polygons']:
            projected = [to_image_coords(*TARGET_PROJECTION(lng, lat)) for lat, lng in poly]
            draw.polygon(projected, outline=None, fill='rgba(0, 0, 0, 0)')


def draw_text(draw, text, corner, size):
    align = 'left' if corner.endswith('w') else 'right'
    font = ImageFont.truetype('assets/fonts/WDR Sans Bold.ttf', size=size)
    spacing = int(size / 5)

    calc_size = draw.textsize(text, font=font, spacing=spacing)
    y_offset = int(img_height * .054)

    x0 = 0 if align == 'left' else img_width - calc_size[0] - spacing * 2
    y0 = y_offset if corner.startswith('n') else img_height - calc_size[1] - y_offset - spacing
    x1 = calc_size[0] + spacing * 2 if align == 'left' else img_width
    y1 = y_offset + calc_size[1] + spacing if corner.startswith('n') else img_height - y_offset

    draw.rectangle(((x0, y0), (x1, y1)), fill=COLORS['WDRA_TEXT_BACKGROUND'])

    triangle_offset = tan(radians(15)) * (y1 - y0)
    x2 = x1 + triangle_offset if align == 'left' else x0 - triangle_offset
    y2 = y1  # if align == 'left' else y0

    if align == 'left':
        draw.polygon(((x1, y0), (x1, y1), (x2, y2)), fill=COLORS['WDRA_TEXT_BACKGROUND'])
    else:
        draw.polygon(((x0, y0), (x0, y1), (x2, y2)), fill=COLORS['WDRA_TEXT_BACKGROUND'])

    x = spacing if align == 'left' else img_width - calc_size[0] - spacing
    y = y_offset if corner.startswith('n') else img_height - calc_size[1] - spacing - y_offset

    draw.text((x, y), text, align='left', fill='white', font=font, spacing=spacing)

def severity_key(event):

    mapped = {
        'Minor': 0,
        'Moderate': 1,
        'Severe': 2,
        'Extreme': 3,
    }

    return mapped.get(event['severity'], 100)


def generate_map(events, *, text=None, text_corner='se', text_size=50):
    event_img = Image.new("RGBA", (img_width, img_height))
    draw = ImageDraw.Draw(event_img)

    img = background_image.copy()

    try:
        for event in sorted(events, key=severity_key):
            draw_event(event, draw)

        img.alpha_composite(resize(event_img))
    except TypeError:
        draw = ImageDraw.Draw(img)
        draw.text((90, TARGET_HEIGHT / 2 - 80), "Event not found", font=FONT_ERROR, fill='black')
    else:
        img.alpha_composite(overlay)

    if text:
        text_img = Image.new("RGBA", (img_height, img_width))
        draw = ImageDraw.Draw(text_img)
        draw_text(draw, text, text_corner, text_size)
        img.alpha_composite(resize(text_img))

    return img
