from functools import partial

import pyproj
from shapely.geometry import MultiPolygon
from shapely.ops import transform
from PIL import Image, ImageDraw, ImageFont
import yaml

from .data.shapes import STATE_SHAPES
from .config import STATES_FILTER


with open('config/studios.yml', 'r') as fp:
    STUDIOS = yaml.safe_load(fp.read())


COLORS = {
    'BACKGROUND': 'rgb(242, 238, 226)',
    'STATE': '#81db51',
    'SURROUNDINGS': 'rgb(242, 238, 226)',
    'BORDERS': 'white',
    'STUDIOS': 'rgba(44, 44, 44, 77)',
    'SEVERITIES': {
        'Minor': '#ffcc00',
        'Moderate': '#ff6600',
        'Severe': '#ff0000',
        'Extreme': '#cc3399',
    }
}


target_projection = pyproj.Proj(init='epsg:3857')
project = partial(
    pyproj.transform,
    pyproj.Proj(init='epsg:4326'),  # source coordinate system
    target_projection
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
img_width_ = int(dist_x / 150)
img_height_ = int(dist_y / 150)
img_height = max(img_height_, img_width_)
img_width = max(img_height_, img_width_)
ratio_x = img_width_ / dist_x
ratio_y = img_height_ / dist_y


def to_image_coords(x, y):
    px = int(img_width - ((bbox[2] - x) * ratio_x) + abs(img_width_ - img_width) / 2)
    py = int((bbox[3] - y) * ratio_y + int(abs(img_height_ - img_height) / 2))
    return px, py


def draw_background():
    img = Image.new("RGBA", (img_width, img_height), COLORS['BACKGROUND'])
    draw = ImageDraw.Draw(img)

    for poly in states:
        points = [to_image_coords(x, y) for x, y in poly.exterior.coords]
        draw.polygon(points, outline=None, fill=COLORS['STATE'])

        for interior in poly.interiors:
            points = [to_image_coords(x, y) for x, y in interior.coords]
            draw.polygon(points, outline=None, fill=COLORS['BACKGROUND'])

    return img


def draw_surroundings(img):
    draw = ImageDraw.Draw(img)

    for poly in surroundings:
        points = [to_image_coords(x, y) for x, y in poly.exterior.coords]
        draw.polygon(points, outline=None, fill=COLORS['SURROUNDINGS'])


def draw_studios(img):
    draw = ImageDraw.Draw(img, 'RGBA')
    size = 15

    for name, studio in STUDIOS.items():
        coords = studio['coordinates']
        point = to_image_coords(*target_projection(coords['lat'], coords['lon']))
        draw.rectangle(
            [(point[0] - size, point[1] - size),
             (point[0] + size, point[1] + size)],
            fill=COLORS['STUDIOS'])


def draw_borders(img, width=3):
    draw = ImageDraw.Draw(img)

    line_width = width
    point_radius = int(line_width / 3)

    for poly in states.geoms:
        for line in list(poly.interiors) + [poly.exterior]:
            points = [to_image_coords(*point) for point in line.coords]

            draw.line(points, fill=COLORS['BORDERS'], width=line_width)
            for point in points:
                draw.ellipse(
                    (point[0] - point_radius,
                     point[1] - point_radius,
                     point[0] + point_radius,
                     point[1] + point_radius),
                    fill=COLORS['BORDERS'])



def draw_overlay():
    img = Image.new("RGBA", (img_width, img_height))

    draw_surroundings(img)
    # draw_borders(img)
    draw_studios(img)

    return img


def draw_event(event):
    img = background_image.copy()
    draw = ImageDraw.Draw(img)

    if event:
        for geo in event['geometry']:

            for poly in geo['polygons']:
                projected = [to_image_coords(*target_projection(lng, lat)) for lat, lng in poly]
                draw.polygon(projected, outline=None, fill=COLORS['SEVERITIES'][event['severity']])

            for poly in geo['exclude_polygons']:
                projected = [to_image_coords(*target_projection(lng, lat)) for lat, lng in poly]
                draw.polygon(projected, outline=None, fill=COLORS['STATE'])

            img.alpha_composite(overlay)
    else:
        img.alpha_composite(overlay)
        fnt = ImageFont.truetype('assets/fonts/VT323-Regular.ttf', 300)
        draw.text((200, img_height / 2 - 150), "Event not found", font=fnt, fill=(0, 0, 0, 255))

    resized = img #.resize((int(img_width * .5), int(img_height * .5)), resample=Image.CUBIC)

    return resized


background_image = draw_background()
overlay = draw_overlay()
