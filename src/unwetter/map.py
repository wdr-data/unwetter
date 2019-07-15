from enum import Enum
from functools import partial
from math import tan, radians
import re

from colorutils import Color
import pyproj
from shapely.geometry import MultiPolygon
from shapely.ops import transform
from PIL import Image, ImageDraw, ImageFont
import yaml

from .data.shapes import STATE_SHAPES
from .config import STATES_FILTER


TARGET_HEIGHT = 1080
TARGET_WIDTH_SQUARE = TARGET_HEIGHT
TARGET_WIDTH_WIDE = 1920


COLORS = {
    'SEVERITIES': {
        'Minor': '#ffcc00a0',
        'Moderate': '#ff6600a0',
        'Severe': '#ff0000a0',
        'Extreme': '#b00087a3',
        'Disabled': '#999999e0',
    },
    'WDR_BLUE': '#00345e',
    'TEXT': '#5f5f5f',
    'GRADIENT': {
        'start': '#00345e',
        'end': '#0d4c80',
    }
}

FONT_ERROR = ImageFont.truetype('assets/fonts/VT323-Regular.ttf', 150)

TARGET_PROJECTION = pyproj.Proj(init='epsg:3857')
project = partial(
    pyproj.transform,
    pyproj.Proj(init='epsg:4326'),  # source coordinate system
    TARGET_PROJECTION
)


class Mode(Enum):
    WIDE = 'wide'
    SQUARE = 'square'


states = []  # fill with polys, then convert to multi-polygon

# Create projected copy
for name, shape in STATE_SHAPES.items():
    if name in STATES_FILTER:
        projected = transform(project, shape)
        states.extend(projected.geoms)

states = MultiPolygon(states)

bbox = states.bounds

img_padding = 75000
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
img_width_wide = int(img_width * (16 / 9))
ratio_x = img_width_ / dist_x
ratio_y = img_height_ / dist_y

vertical_offset = int(-0.075 * img_height)

img_widths = {
    Mode.SQUARE: img_width,
    Mode.WIDE: img_width_wide,
}


def to_image_coords(x, y, mode):
    px = int(img_width - ((bbox[2] - x) * ratio_x) + abs(img_width_ - img_widths[mode]) / 2)
    py = int((bbox[3] - y) * ratio_y + int(abs(img_height_ - img_height) / 2)) + vertical_offset
    return px, py


def resize(img, mode):
    if mode is Mode.SQUARE:
        return img.resize((TARGET_WIDTH_SQUARE, TARGET_HEIGHT), resample=Image.CUBIC)
    elif mode is Mode.WIDE:
        return img.resize((TARGET_WIDTH_WIDE, TARGET_HEIGHT), resample=Image.CUBIC)


images = {}

background_image = resize(Image.open('assets/images/bg_square.png').convert("RGBA"), Mode.SQUARE)
studios = resize(Image.open('assets/images/overlay_square.png').convert("RGBA"), Mode.SQUARE)
mask = resize(Image.open('assets/images/mask_square.png').convert("RGBA"), Mode.SQUARE)
logo_wdra = resize(Image.open('assets/images/logo_wdra_square.png').convert("RGBA"), Mode.SQUARE)

legend = resize(Image.open('assets/images/legend_se_square.png').convert("RGBA"), Mode.SQUARE)
legend_other = resize(Image.open('assets/images/legend_se_square_other.png').convert("RGBA"), Mode.SQUARE)

overlay = mask.copy()
overlay.alpha_composite(studios)
overlay.alpha_composite(logo_wdra)

overlay = overlay.copy()
overlay_other = overlay.copy()

overlay.alpha_composite(legend)
overlay_other.alpha_composite(legend_other)

images[Mode.SQUARE] = {
    'background': background_image,
    'overlay': {
        'regular': overlay,
        'other': overlay_other,
    }
}

background_image = resize(Image.open('assets/images/bg_wide.png').convert("RGBA"), Mode.WIDE)
studios = resize(Image.open('assets/images/overlay_wide.png').convert("RGBA"), Mode.WIDE)
mask = resize(Image.open('assets/images/mask_wide.png').convert("RGBA"), Mode.WIDE)
logo_wdra = resize(Image.open('assets/images/logo_wdra_wide.png').convert("RGBA"), Mode.WIDE)

legend = resize(Image.open('assets/images/legend_ne_wide.png').convert("RGBA"), Mode.WIDE)
legend_other = resize(Image.open('assets/images/legend_ne_wide_other.png').convert("RGBA"), Mode.WIDE)

overlay = mask.copy()
overlay.alpha_composite(studios)
overlay.alpha_composite(logo_wdra)

overlay = overlay.copy()
overlay_other = overlay.copy()

overlay.alpha_composite(legend)
overlay_other.alpha_composite(legend_other)

images[Mode.WIDE] = {
    'background': background_image,
    'overlay': {
        'regular': overlay,
        'other': overlay_other,
    }
}

del studios, mask, logo_wdra, legend, legend_other


def generate_base_map(mode=Mode.SQUARE):
    img = Image.new("RGBA", (img_widths[mode], img_height), 'black')

    draw = ImageDraw.Draw(img)

    for poly in states:
        points = [to_image_coords(x, y, mode) for x, y in poly.exterior.coords]
        draw.polygon(points, outline=None, fill='white')

        for interior in poly.interiors:
            points = [to_image_coords(x, y, mode) for x, y in interior.coords]
            draw.polygon(points, outline=None, fill='black')

    return img


def draw_event(event, draw, mode):
    for geo in event['geometry']:
        for poly in geo['polygons']:
            projected = [to_image_coords(*TARGET_PROJECTION(lng, lat), mode) for lat, lng in poly]
            draw.polygon(projected, outline=None, fill=COLORS['SEVERITIES'][event['severity']])

        for poly in geo['exclude_polygons']:
            projected = [to_image_coords(*TARGET_PROJECTION(lng, lat), mode) for lat, lng in poly]
            draw.polygon(projected, outline=None, fill='rgba(0, 0, 0, 0)')


def draw_text(draw, title, title_size, subtitle, subtitle_size):
    font_title = ImageFont.truetype('assets/fonts/WDRSlab-BoldVZ-v101.ttf', size=title_size)
    font_subtitle = ImageFont.truetype('assets/fonts/WDR Sans Book.ttf', size=subtitle_size)

    spacing_title = int(title_size / 5)
    spacing_subtitle = int(subtitle_size / 5)

    calc_size_title = draw.textsize(re.sub('.', 'M', title), font=font_title, spacing=spacing_title)
    calc_size_subtitle = draw.textsize(re.sub('.', 'M', subtitle), font=font_subtitle, spacing=spacing_subtitle)

    y_offset = int(img_height * .03) + spacing_title
    gradient_width = img_widths[Mode.SQUARE] / TARGET_WIDTH_SQUARE * 35

    x0 = 0
    y0 = (
        img_height
        - y_offset
        - ((calc_size_subtitle[1] + spacing_title * 2) if subtitle else 0)
        - calc_size_title[1]
        - spacing_title * 4
    )
    x1 = gradient_width
    y1 = img_height - y_offset

    start = Color(hex=COLORS['GRADIENT']['start']).rgb
    end = Color(hex=COLORS['GRADIENT']['end']).rgb

    for line in range(y0, y1):
        fac = (line - y0) / (y1 - y0)
        color = Color(tuple(s * fac + e * (1 - fac) for s, e in zip(start, end)))
        draw.line(((x0, line), (x1, line)), fill=color.hex)

    x = gradient_width + spacing_title * 2
    y = (
        img_height
        - y_offset
        - ((calc_size_subtitle[1] + spacing_title * 2) if subtitle else 0)
        - spacing_title * 2
        - calc_size_title[1]
    )
    draw.text((x, y), title, align='left', fill=COLORS['TEXT'], font=font_title, spacing=spacing_title)

    y = (
        img_height
        - y_offset
        - calc_size_subtitle[1]
        - spacing_title * 2
    )
    draw.text((x, y), subtitle, align='left', fill=COLORS['TEXT'], font=font_subtitle, spacing=spacing_subtitle)

def severity_key(event):

    mapped = {
        'Minor': 0,
        'Moderate': 1,
        'Severe': 2,
        'Extreme': 3,
    }

    return mapped.get(event['severity'], 100)


def generate_map(events, *, mode=Mode.SQUARE, disabled_events=None, title=None, title_size=130, subtitle=None, subtitle_size=110):
    if disabled_events is None:
        disabled_events = []
    
    event_img = Image.new("RGBA", (img_widths[mode], img_height))
    draw = ImageDraw.Draw(event_img)

    img = images[mode]['background'].copy()

    try:
        for event in disabled_events:
            event['severity'] = 'Disabled'
            draw_event(event, draw, mode)

        for event in sorted(events, key=severity_key):
            draw_event(event, draw, mode)

        img.alpha_composite(resize(event_img, mode))
    except TypeError:
        draw = ImageDraw.Draw(img)
        draw.text((90, TARGET_HEIGHT / 2 - 80), "Event not found", font=FONT_ERROR, fill='black')
    else:
        if disabled_events:
            img.alpha_composite(images[mode]['overlay']['other'])
        else:
            img.alpha_composite(images[mode]['overlay']['regular'])

    if title:
        text_img = Image.new("RGBA", (img_widths[mode], img_height))
        draw = ImageDraw.Draw(text_img)
        draw_text(draw, title, title_size, subtitle or '', subtitle_size)
        img.alpha_composite(resize(text_img, mode))

    return img
