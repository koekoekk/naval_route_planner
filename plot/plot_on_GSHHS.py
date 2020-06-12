import matplotlib.pyplot as plt
import pickle
import cartopy.crs as ccrs
from operator import attrgetter
from cartopy.io import shapereader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from math import floor, ceil


def make_map(projection=ccrs.PlateCarree()):
    fig, ax = plt.subplots(figsize=(9, 13),
                           subplot_kw=dict(projection=projection))
    gl = ax.gridlines(draw_labels=True)
    gl.top_labels = gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    return fig, ax


def plot_on_gshhs(route):
    min_x, min_y = min(route.waypoints, key=attrgetter('lon')), min(route.waypoints, key=attrgetter('lat'))
    max_x, max_y = max(route.waypoints, key=attrgetter('lon')), max(route.waypoints, key=attrgetter('lat'))
    m = 5  # margin
    extent = [max(floor(min_x.lon) - m, -180), min(ceil(max_x.lon) + m, 180),
              max(floor(min_y.lat) - m, -90), min(ceil(max_y.lat) + m, 90)]  # [left, right, bottom, top)

    fig, ax = make_map(projection=ccrs.PlateCarree())
    ax.set_extent(extent, crs=ccrs.PlateCarree())

    # Plot shorelines
    shp = shapereader.Reader('C:/dev/data/gshhg-shp-2.3.7/GSHHS_shp/l/GSHHS_l_L1.shp')
    for record, geometry in zip(shp.records(), shp.geometries()):
        ax.add_geometries([geometry], ccrs.PlateCarree(), facecolor='lightgray', edgecolor='black')

    # Plot waypoints
    waypoints = [[point.lon, point.lat] for point in route.waypoints]
    edges = zip(waypoints[:-1], waypoints[1:])
    for e in edges:
        plt.plot([e[0][0], e[1][0]], [e[0][1], e[1][1]],
                 color='blue', linewidth=1, marker='o', markersize=3, transform=ccrs.PlateCarree())


# with open('C:/dev/projects/naval_route_planner/output/graph_route', 'rb') as f:
#     pareto_solutions = pickle.load(f)
# plot_on_gshhs(pareto_solutions)
# plt.show()