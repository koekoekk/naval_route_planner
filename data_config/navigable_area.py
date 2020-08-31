import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import fiona
import os
import pickle

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from pathlib import Path
from shapely.geometry import (box, Polygon, MultiPolygon,
                              GeometryCollection, shape, LineString, Point)
from shapely.strtree import STRtree
from shapely.prepared import prep


class NavigableAreaGenerator:
    def __init__(self, parameters):
        self.resolution = parameters['res']
        self.maxGeoSize = parameters['splits']
        self.avoidAntarctic = parameters['avoidAntarctic']
        self.avoidArctic = parameters['avoidArctic']
        self.get_eca_tree = get_eca_rtree()

    def get_shoreline_tree(self, exteriorOnly=False):
        gshhgDir = Path('data/gshhg-shp-2.3.7/GSHHS_shp')
        shorelinesFP = gshhgDir / '{0}/GSHHS_{0}_L1.shp'.format(self.resolution)
        antarcticFP = gshhgDir / '{0}/GSHHS_{0}_L6.shp'.format(self.resolution)

        shorelines = self.get_shorelines(shorelinesFP, antarcticFP, exteriorOnly)
        if exteriorOnly:
            exteriors = []
            for polygon in shorelines:
                cutLines = cut(polygon.exterior, self.maxGeoSize)
                exterior = [cutLines[0]]
                while len(cutLines) > 1:
                    cutLines = cut(cutLines[-1], 10)
                    exterior.append(cutLines[0])
                exteriors.extend(exterior)

            shorelines = exteriors

        return populate_rtree(shorelines)

    def get_shorelines(self, shoreShapePath, antarcticShapePath, exteriorOnly):
        aC = aAc = 'incl'
        if self.avoidAntarctic and self.avoidArctic:
            aC = aAc = 'avoid'
        elif self.avoidAntarctic:
            aAc = 'avoid'
        elif self.avoidArctic:
            aC = 'avoid'

        saveDir = Path('data/split_polygons')
        saveFP = saveDir / 'res_{}_threshold_{}_{}Antarctic_{}Arctic'.format(self.resolution, self.maxGeoSize, aAc, aC)

        if not exteriorOnly and os.path.exists(saveFP):
            with open(saveFP, 'rb') as f:
                return pickle.load(f)

        shorelines = [shape(shoreline['geometry']) for shoreline in iter(fiona.open(shoreShapePath))]

        # If Antarctic circle is to be avoided; include as impassable area (latitude < -66),
        if self.avoidAntarctic:
            antarcticCircle = Polygon([(-181, -66), (181, -66), (181, -91), (-181, -91)])
            shorelines.append(antarcticCircle)
        else:  # Otherwise; include Antarctica in shoreline list
            antarctica = [shape(shoreline['geometry']) for shoreline in iter(fiona.open(antarcticShapePath))]
            shorelines.extend(antarctica)

        # If Arctic circle is to be avoided; include as impassable area (latitude > 66)
        if self.avoidArctic:
            arcticCircle = Polygon([(-181, 66), (181, 66), (181, 91), (-181, 91)])
            shorelines.append(arcticCircle)

        if not exteriorOnly:
            splitShorelines = self.split_polygons(shorelines)
            # Save result
            with open(saveFP, 'wb') as f:
                pickle.dump(splitShorelines, f)
            print('Saved to: ', saveFP)

            return splitShorelines

        return shorelines

    def split_polygons(self, geometries):
        print('Splitting polygons')
        splitPolys = []
        for polygon in geometries:
            splitPolys.extend(self.split_polygon(polygon))
        return splitPolys

    def split_polygon(self, geo, cnt=0):
        """Split a Polygon into two parts across it's shortest dimension"""
        (minx, miny, maxx, maxy) = geo.bounds
        width = maxx - minx
        height = maxy - miny
        # if max(width, height) <= threshold or cnt == 250:
        if geo.envelope.area < self.maxGeoSize ** 2 or cnt == 250:
            # either the polygon is smaller than the threshold, or the maximum
            # number of recursions has been reached
            return [geo]
        if height >= width:
            # split left to right
            a = box(minx, miny, maxx, miny + height/2)
            b = box(minx, miny + height / 2, maxx, maxy)
        else:
            # split top to bottom
            a = box(minx, miny, minx+width/2, maxy)
            b = box(minx + width / 2, miny, maxx, maxy)
        result = []
        for d in (a, b,):
            c = geo.intersection(d)
            if not isinstance(c, GeometryCollection):
                c = [c]
            for e in c:
                if isinstance(e, (Polygon, MultiPolygon)):
                    result.extend(self.split_polygon(e, cnt+1))
        if cnt > 0:
            return result
        # convert multi part into single part
        finalResult = []
        for g in result:
            if isinstance(g, MultiPolygon):
                finalResult.extend(g)
            else:
                finalResult.append(g)
        return finalResult

    def split_linearring(self, geo, cnt=0):
        """Split a Polygon into two parts across it's shortest dimension"""
        (minx, miny, maxx, maxy) = geo.bounds
        width = maxx - minx
        height = maxy - miny
        # if max(width, height) <= threshold or cnt == 250:
        if geo.envelope.area < self.maxGeoSize ** 2 or cnt == 250:
            # either the polygon is smaller than the threshold, or the maximum
            # number of recursions has been reached
            return [geo]
        if height >= width:
            # split left to right
            a = box(minx, miny, maxx, miny + height/2)
            b = box(minx, miny + height / 2, maxx, maxy)
        else:
            # split top to bottom
            a = box(minx, miny, minx+width/2, maxy)
            b = box(minx + width / 2, miny, maxx, maxy)
        result = []
        for d in (a, b,):
            c = geo.intersection(d)
            if not isinstance(c, GeometryCollection):
                c = [c]
            for e in c:
                if isinstance(e, (Polygon, MultiPolygon)):
                    result.extend(self.split_linearring(e, cnt+1))
        if cnt > 0:
            return result
        # convert multi part into single part
        finalResult = []
        for g in result:
            if isinstance(g, MultiPolygon):
                finalResult.extend(g)
            else:
                finalResult.append(g)
        return finalResult


def get_eca_rtree():
    fn = 'seca_areas'
    fp = 'data/{}'.format(fn)
    if os.path.exists(fp):
        with open(fp, 'rb') as f:
            ecas = pickle.load(f)
    else:
        raise FileNotFoundError("File '{}' not found".format(fn))

    return populate_rtree(ecas)


def populate_rtree(geos):
    # Populate R-tree index with bounds of polygons
    tree = STRtree(geos)

    # Create dict of original indexes for querying prepared polygons.
    indexByID = {id(geo): i for i, geo in enumerate(geos)}

    prepGeos = [prep(poly) for poly in geos]  # Prepare polygons
    return {'tree': tree, 'indexByID': indexByID, 'polys': prepGeos}


def plot_geometries(geometries):
    fig, ax = plt.subplots(figsize=(9, 13),
                           subplot_kw=dict(projection=ccrs.PlateCarree()))
    gl = ax.gridlines(draw_labels=True)
    gl.top_labels = gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    ax.add_geometries(geometries, ccrs.PlateCarree(), facecolor='lightgray',
                      edgecolor='black')


def cut(line, distance):
    # Cuts a line in two at a distance from its starting point
    if distance <= 0.0:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords[:-1]):
        pd = line.project(Point(p))
        if pd >= distance:
            return [LineString(coords[:i+1]), LineString(coords[i:])]
    return [LineString(line)]