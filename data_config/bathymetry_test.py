import dask.array as da
import netCDF4
import numpy as np
import xarray as xr

from osgeo import gdal
from osgeo import ogr


def ncdump(nc_fid, verb=True):
    """
    ncdump outputs dimensions, variables and their attribute information.
    The information is similar to that of NCAR's ncdump utility.
    ncdump requires a valid instance of Dataset.

    Parameters
    ----------
    nc_fid : netCDF4.Dataset
        A netCDF4 dateset object
    verb : Boolean
        whether or not nc_attrs, nc_dims, and nc_vars are printed

    Returns
    -------
    nc_attrs : list
        A Python list of the NetCDF file global attributes
    nc_dims : list
        A Python list of the NetCDF file dimensions
    nc_vars : list
        A Python list of the NetCDF file variables
    """
    def print_ncattr(key):
        """
        Prints the NetCDF file attributes for a given key

        Parameters
        ----------
        key : unicode
            a valid netCDF4.Dataset.variables key
        """
        try:
            print("\t\ttype:", repr(nc_fid.variables[key].dtype))
            for ncattr in nc_fid.variables[key].ncattrs():
                print('\t\t%s:' % ncattr, repr(nc_fid.variables[key].getncattr(ncattr)))
        except KeyError:
            print("\t\tWARNING: %s does not contain variable attributes" % key)

    # NetCDF global attributes
    nc_attrs = nc_fid.ncattrs()
    if verb:
        print("NetCDF Global Attributes:")
        for nc_attr in nc_attrs:
            print('\t%s:' % nc_attr, repr(nc_fid.getncattr(nc_attr)))
    nc_dims = [dim for dim in nc_fid.dimensions]  # list of nc dimensions
    # Dimension shape information.
    if verb:
        print("NetCDF dimension information:")
        for dim in nc_dims:
            print("\tName:", dim)
            print("\t\tsize:", len(nc_fid.dimensions[dim]))
            print_ncattr(dim)
    # Variable information.
    nc_vars = [var for var in nc_fid.variables]  # list of nc variables
    if verb:
        print("NetCDF variable information:")
        for var in nc_vars:
            if var not in nc_dims:
                print('\tName:', var)
                print("\t\tdimensions:", nc_fid.variables[var].dimensions)
                print("\t\tsize:", nc_fid.variables[var].size)
                print_ncattr(var)
    return nc_attrs, nc_dims, nc_vars





# # Open data as read-only
# fp = 'C:/dev/data/gebco_2020_netcdf/' + 'GEBCO_2020.nc'
# fp_TID = 'C:/dev/data/gebco_2020_tid_netcdf/' + 'GEBCO_2020_TID.nc'
# # TID = xr.open_dataset(fp_TID, chunks={'lon': 16000, 'lat': 8000})
# ds = xr.open_dataset(fp, chunks={'lon': 11313, 'lat': 5657})
# ds = da.from_array(ds.to_array())
# print(ds)
# print(ds[0, 20000, 40000].compute())
#
# bins = np.int8([-5, -10, -20])
#
# inds = np.digitize(ds, bins)

# print(inds[0, 20000, 40000].compute())

# print(inds[1, 20000, 40000].compute())
#
# print(ds2.isel(lon=40000, lat=20000).compute())
# # print(ds2)
#
# # Get longitudes and latitudes
# lons = ds.variables['lon']
# lats = ds.variables['lat']
#
#
# # tid = TID.variables['tid']
# # elevation = data.variables['elevation'][:]
# # TID.close()

# Read in data
src_fp = 'C:/dev/data/gebco_2020_netcdf/' + 'GEBCO_2020.'
dst_filename = 'C:/dev/projects/naval_route_planner/output/contours/cont'
dataset = gdal.Open(src_fp, gdal.GA_ReadOnly)

if not dataset:
    print("Driver: {}/{}".format(dataset.GetDriver().ShortName, dataset.GetDriver().LongName))
    print("Size is {} x {} x {}".format(dataset.RasterXSize, dataset.RasterYSize, dataset.RasterCount))
    print("Projection is {}".format(dataset.GetProjection()))
    geo_transform = dataset.GetGeoTransform()

    if geo_transform:
        print("Origin = ({}, {})".format(geo_transform[0], geo_transform[3]))
        print("Pixel Size = ({}, {})".format(geo_transform[1], geo_transform[5]))

    band = dataset.GetRasterBand(1)
    print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))

    min = band.GetMinimum()
    max = band.GetMaximum()
    if not min or not max:
        (min, max) = band.ComputeRasterMinMax(True)
    print("Min={:.3f}, Max={:.3f}".format(min, max))

    if band.GetOverviewCount() > 0:
        print("Band has {} overviews".format(band.GetOverviewCount()))

    if band.GetRasterColorTable():
        print("Band has a color table with {} entries".format(band.GetRasterColorTable().GetCount()))

    # Generate layer to save Contourlines in
    ogr_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(dst_filename)
    contour_shp = ogr_ds.CreateLayer('contour')

    field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
    contour_shp.CreateField(field_defn)
    field_defn = ogr.FieldDefn("elev", ogr.OFTReal)
    contour_shp.CreateField(field_defn)

    # Generate contour lines
    """ContourGenerate(Band srcBand, double contourInterval, double contourBase, int fixedLevelCount, int useNoData, 
    double noDataValue, Layer dstLayer, int idField, int elevField, GDALProgressFunc callback=0, 
    void * callback_data=None) -> int"""
    gdal.ContourGenerate(band, 100, 0, [], 0, 0, contour_shp, 0, 1)
    ogr_ds = None
    del ogr_ds

