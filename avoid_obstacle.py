from shapely.geometry import Polygon, LineString, Point
from math import sqrt
import random
from solution import Route, Edge, Waypoint
import matplotlib.pyplot as plt
import numpy as np
from time import sleep

random.seed(16)

polygon1 = [(2, 1), (2.3, 1.3), (2, 3), (2.4, 3.3), (3, 2), (4, 3), (5, 2), (6, 3.1), (3.8, 4), (5.5, 5.5), (4.1, 6.5), (2.8, 5), (2.1, 5), (1.2, 2.9)]
polygon11 = [(2, 1), (2.3, 1.3), (2, 3), (2.4, 3.3), (3, 2), (4, 3), (5, 2), (6, 3.1), (3.8, 4), (5.5, 5.5), (4.1, 6.5), (2.8, 5),  (0, 15), (1.2, 2.9)]
polygon2 = [(7, 7), (8, 4), (9, 5), (10, 3), (11, 9), (8, 8), (6, 8)]
polygon22 = [(7, 7), (8, 4), (8, -5), (10, -1), (12, -5), (12, 7), (11, 9), (8, 8), (6, 8)]
polygon3 = [(1,0), (-2, -1), (-1, -2), (2, 0), (-2, 4), (-3, 2), (-2, 3)]
polygon4 = [(11, 10), (12, 12), (13, 11), (12, 8), (15, 0)]
IN_polygon = [Polygon(polygon11), Polygon(polygon22), Polygon(polygon4)]
# polygons = [Polygon(polygon1)]

waypoint_1 = Waypoint(-1, 1)
waypoint_2 = Waypoint(15, 10.5)

IN_route = Route([waypoint_1, waypoint_2], 16.7)
IN_edge = IN_route.edges[0]


def avoid_obstacle(edge, polygons_input):
    def get_route_segment(line_vw, polygons, end_point, area, extend, segments=[], checked_polygons=dict(),
                          direction=None):
        def intersect_polygon(line, polygon_list):
            for a_polygon in iter(polygon_list):
                intersect = line.intersection(a_polygon)
                if intersect:
                    return a_polygon
            return False

        v, w = line_vw.coords
        v, w = Point(v), Point(w)

        line_v_end = LineString([v, end_point])
        if not intersect_polygon(line_v_end, polygons):
            segments.append(line_v_end)
            x_s, y_s = line_v_end.coords.xy
            ax.plot(x_s, y_s, color='black')
            plt.pause(0.1)
            return segments

        polygon = intersect_polygon(line_vw, polygons)

        if not polygon:
            segments.append(line_vw)
            x_s, y_s = line_vw.coords.xy
            ax.plot(x_s, y_s, color='black')
            plt.pause(0.1)
            return segments
        else:
            # Create points a and b, intersections of edge and polygon
            line_ab = polygon.intersection(line_vw)
            if line_ab.geom_type == 'MultiLineString':
                line_ab = line_ab[0]
            x_ab, y_ab = line_ab.coords.xy
            x_c, y_c = line_ab.centroid.coords.xy

            # Create perpendicular bisector of line ab
            slope_ab = (y_ab[1] - y_ab[0]) / (x_ab[1] - x_ab[0])
            envelope = polygon.envelope
            big_m = envelope.length
            x_1 = x_c[0] + sqrt(big_m ** 2 / (1 + 1 / slope_ab ** 2))
            x_2 = x_c[0] - sqrt(big_m ** 2 / (1 + 1 / slope_ab ** 2))
            y_1 = -(1 / slope_ab) * (x_1 - x_c[0]) + y_c[0]
            y_2 = -(1 / slope_ab) * (x_2 - x_c[0]) + y_c[0]
            perpendicular_bisector = LineString([(x_1, y_1), (x_2, y_2)])

            # Create points g and h, intersections of perpendicular bisector and polygon
            line_gh = polygon.intersection(perpendicular_bisector)

            if line_gh.geom_type == 'MultiLineString':
                x_first, y_first = line_gh[0].coords.xy
                x_last, y_last = line_gh[-1].coords.xy
                line_gh = LineString([(x_first[0], y_first[0]), (x_last[-1], y_last[-1])])
            x_gh, y_gh = line_gh.coords.xy
            x_g, x_h = x_gh[0], x_gh[1]
            y_g, y_h = y_gh[0], y_gh[1]

            # Create points d and f, intersections of perpendicular bisector and envelope
            bounds = polygon.envelope.bounds
            x1_mbr = bounds[0] - extend
            x2_mbr = bounds[2] + extend
            y1_mbr = bounds[1] - extend
            y2_mbr = bounds[3] + extend
            extended_mbr = Polygon([(x1_mbr, y1_mbr), (x2_mbr, y1_mbr), (x2_mbr, y2_mbr), (x1_mbr, y2_mbr)])
            line_df = extended_mbr.intersection(perpendicular_bisector)
            x_df, y_df = line_df.coords.xy
            x_d, x_f = x_df[0], x_df[1]
            y_d, y_f = y_df[0], y_df[1]

            # Randomly choose points g1 and g1 from line segments dg and hf, respectively
            while True:
                u_1 = random.uniform(0, 1)
                x_g1 = u_1 * (x_d - x_g) + x_g
                y_g1 = u_1 * (y_d - y_g) + y_g
                g1 = Point(x_g1, y_g1)
                for poly in iter(polygons):
                    if not g1.within(poly):  # ADD: shape()
                        continue
                break
            while True:
                u_2 = random.uniform(0, 1)
                x_h1 = u_2 * (x_f - x_h) + x_h
                y_h1 = u_2 * (y_f - y_h) + y_h
                h1 = Point(x_h1, y_h1)
                for poly in iter(polygons):
                    if not h1.within(poly):  # ADD: shape()
                        continue
                break

            # Create vg1 and vh1
            line_vg1 = LineString([v, g1])
            line_vh1 = LineString([v, h1])

            # Determine directions
            direction_g1 = np.sign((x_ab[1] - x_ab[0]) * (y_g1 - y_ab[0]) - (y_ab[1] - y_ab[0]) * (x_g1 - x_ab[0]))
            direction_h1 = np.sign((x_ab[1] - x_ab[0]) * (y_h1 - y_ab[0]) - (y_ab[1] - y_ab[0]) * (x_h1 - x_ab[0]))

            # If polygon partly outside designated range OR Polygon already created two separate route_dict
            if polygon.boundary.intersects(area.boundary):
                pt = polygon.boundary.intersection(area.boundary)[0]
                x_pt, y_pt = pt.coords.xy
                side_outside_polygon = np.sign(
                    (x_ab[1] - x_ab[0]) * (y_pt[0] - y_ab[0]) - (y_ab[1] - y_ab[0]) * (x_pt[0] - x_ab[0]))
                if direction_h1 == side_outside_polygon:
                    checked_polygons[polygon.area] = direction_g1
                    segments = get_route_segment(line_vg1, polygons, end_point, area,
                                                 extend, segments, checked_polygons, direction_g1)
                    if not segments[-1].intersects(end_point):
                        line_g1w = LineString([g1, w])
                        segments = get_route_segment(line_g1w, polygons, end_point, area,
                                                     extend, segments, checked_polygons, direction_g1)
                else:
                    checked_polygons[polygon.area] = direction_h1
                    segments = get_route_segment(line_vh1, polygons, end_point, area,
                                                 extend, segments, checked_polygons, direction_h1)
                    if not segments[-1].intersects(end_point):
                        line_h1w = LineString([h1, w])
                        segments = get_route_segment(line_h1w, polygons, end_point, area,
                                                     extend, segments, checked_polygons, direction_h1)
            elif polygon.area in checked_polygons:
                if checked_polygons[polygon.area] == direction_g1:
                    segments = get_route_segment(line_vg1, polygons, end_point, area,
                                                 extend, segments, checked_polygons, direction_g1)
                    if not segments[-1].intersects(end_point):
                        line_g1w = LineString([g1, w])
                        segments = get_route_segment(line_g1w, polygons, end_point, area,
                                                     extend, segments, checked_polygons, direction_g1)
                else:
                    segments = get_route_segment(line_vh1, polygons, end_point, area,
                                                 extend, segments, checked_polygons, direction_h1)
                    if not segments[-1].intersects(end_point):
                        line_h1w = LineString([h1, w])
                        segments = get_route_segment(line_h1w, polygons, end_point, area,
                                                     extend, segments, checked_polygons, direction_h1)
            else:
                checked_polygons[polygon.area] = direction_g1
                segments = get_route_segment(line_vg1, polygons, end_point, area,
                                             extend, segments, checked_polygons, direction_g1)
                if not segments[-1].intersects(end_point):
                    line_g1w = LineString([g1, w])
                    segments = get_route_segment(line_g1w, polygons, end_point, area,
                                                 extend, segments, checked_polygons, direction_g1)

                checked_polygons[polygon.area] = direction_h1
                segments = get_route_segment(line_vh1, polygons, end_point, area,
                                             extend, segments, checked_polygons, direction_h1)
                if not segments[-1].intersects(end_point):
                    line_h1w = LineString([h1, w])
                    segments = get_route_segment(line_h1w, polygons, end_point, area,
                                                 extend, segments, checked_polygons, direction_h1)

            return segments
    v_input = Point(edge.v.x, edge.v.y)
    w_input = Point(edge.w.x, edge.w.y)
    line_vw_input = LineString([v_input, w_input])
    extend_input = 0.5
    area_radius = 0.5 * line_vw_input.length
    area_input = line_vw_input.centroid.buffer(area_radius)

    # # PLOT
    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot()
    x, y = polygons_input[0].exterior.xy
    for p in polygons_input:
        x_p, y_p = p.exterior.xy
        ax.plot(x_p, y_p, color='darkgrey')
    xx, yy = line_vw_input.coords.xy
    ax.plot(xx, yy)

    plt.grid()
    plt.show()

    x_area, y_area = area_input.exterior.coords.xy
    ax.plot(x_area, y_area)

    segment_list = get_route_segment(line_vw_input, polygons_input, w_input, area_input, extend_input)

    segments_dict = dict()
    routes_dict = dict()
    route_nr = 0
    for segment in segment_list:
        # Create route for every segment ending in the end_point
        if Point(segment.coords[1]) == w_input:
            route_nr += 1
            segments_dict[route_nr] = []
            # Construct route in reverse order
            for i, item in enumerate(reversed(segment_list[:segment_list.index(segment) + 1])):
                # Append the last edge (i == 0) in the route list
                if i == 0:
                    segments_dict[route_nr].append(item)
                # If end point of current segment is equal to start point of previous segment, append segment to list
                elif item.coords[1] == segments_dict[route_nr][-1].coords[0]:
                    segments_dict[route_nr].append(item)
                    if Point(segments_dict[route_nr][-1].coords[0]) == v_input:
                        segments_dict[route_nr] = reversed(segments_dict[route_nr])
                        # Create Waypoint and Edge classes
                        waypoints = []
                        edges = []
                        for idx, route_segment in enumerate(segments_dict[route_nr]):
                            if idx == 0:
                                v = Waypoint(route_segment.coords[0][0], route_segment.coords[0][1])
                                w = Waypoint(route_segment.coords[1][0], route_segment.coords[1][1])
                                waypoints.append(v)
                            else:
                                v = waypoints[-1]
                                w = Waypoint(route_segment.coords[1][0], route_segment.coords[1][1])
                            waypoints.append(w)
                            edges.append(Edge(v, w, edge.speed))

                        routes_dict[route_nr] = {'waypoints': waypoints,
                                                 'edges': edges}
                        break
                else:
                    continue

    return routes_dict


routes_value = avoid_obstacle(IN_edge, IN_polygon)
