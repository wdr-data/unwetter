import shapefile
from shapely.geometry import shape, MultiLineString
from shapely.ops import linemerge, unary_union
from shapely.geometry.multipolygon import MultiPolygon
from PIL import Image, ImageDraw


with shapefile.Reader("assets/shapes/dvg2krs_nw") as shp:
    bbox = shp.bbox
    shapes_ = [shape(s.__geo_interface__) for s in shp.shapes()]

shapes = []


for shape in shapes_:
    if isinstance(shape, MultiPolygon):
        for poly in shape.geoms:
            shapes.append(poly)
    else:
        shapes.append(shape)

borders = []

for shape in shapes:
    for test in shapes:
        if shape.touches(test):
            borders.append(shape.intersection(test))

all_poly = unary_union(shapes)


def draw_background():
    dist_x = bbox[2] - bbox[0]
    dist_y = bbox[3] - bbox[1]
    img_width = int(dist_x / 100)
    img_height = int(dist_y / 100)
    ratio_x = img_width / dist_x
    ratio_y = img_height / dist_y

    polys = []

    def to_image_coords(x, y):
        px = int(img_width - ((bbox[2] - x) * ratio_x))
        py = int((bbox[3] - y) * ratio_y)
        return px, py

    def to_pixels(poly, points):
        for i, (x, y) in enumerate(poly.exterior.coords):
            px, py = to_image_coords(x, y)
            points.append((px, py))

    for shape in all_poly.geoms:
        shape = shape.simplify(1000)
        points = []

        to_pixels(shape, points)
        polys.append(points)

    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)
    
    for points in polys:
        draw.polygon(points, outline=None, fill="rgb(0, 50, 93)")

    line_width = 6
    point_radius = int(line_width / 3)

    def draw_border(border):
        border = border.simplify(1000)

        points = [to_image_coords(*point) for point in border.coords]

        draw.line(points, fill='white', width=line_width)
        for point in points:
            draw.ellipse(
                (point[0] - point_radius,
                 point[1] - point_radius,
                 point[0] + point_radius,
                 point[1] + point_radius),
                fill="white")

    for border_ in borders:

        if isinstance(border_, MultiLineString):
            merged = linemerge(border_)

            if isinstance(merged, MultiLineString):
                for border in merged.geoms:
                    draw_border(border)
            else:
                draw_border(merged)

        else:
            draw_border(border_)

    return img


background_image = draw_background()


