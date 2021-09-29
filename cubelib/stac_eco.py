import hvplot.pandas
import hvplot.xarray
from pystac_client import Client

# plot size settings
frame_width = 600
frame_height = 600

# line width of polygons
line_width = 3

# plot polygons as lines on a slippy map with background tiles.
def _plot_polygons(data, *args, **kwargs):
    return data.hvplot.paths(*args, geo=True, tiles='OSM', xaxis=None, yaxis=None,
                             frame_width=frame_width, frame_height=frame_height,
                             line_width=line_width, **kwargs)

from copy import deepcopy
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
import geopandas as gpd
from shapely.geometry import mapping

# convert a list of STAC Items into a GeoDataFrame
def items_to_geodataframe(items):
    _items = []
    for i in items:
        _i = deepcopy(i)
        _i['geometry'] = shape(_i['geometry'])
        _items.append(_i)
    gdf = gpd.GeoDataFrame(pd.json_normalize(_items))
    for field in ['properties.datetime', 'properties.created', 'properties.updated']:
        if field in gdf:
            gdf[field] = pd.to_datetime(gdf[field])
    gdf.set_index('properties.datetime', inplace=True)
    return gdf


def geom_from_geojson( geojson_file ):
    aoi_filename = geojson_file

    # read in AOI as a GeoDataFrame
    aoi = gpd.read_file(aoi_filename)

    # get the geometry of the AOI as a dictionary for use with PySTAC Client
    geom = mapping(aoi.to_dict()['geometry'][0])
    return(geom)

def _get_items_dict(search_object):
    #get all items found in search
    items_dict = []
    for item in search_object.get_all_items_as_dict()['features']:
        for a in item['assets']:
            if 'alternate' in item['assets'][a] and 's3' in item['assets'][a]['alternate']:
                item['assets'][a]['href'] = item['assets'][a]['alternate']['s3']['href']
            item['assets'][a]['href'] = item['assets'][a]['href'].replace('usgs-landsat-ard', 'usgs-landsat')
        items_dict.append(item)
    return items_dict



def _get_items_gdf(search_object):

    # Create GeoDataFrame from resulting Items
    items_dict= _get_items_dict(search_object)
    items_gdf = items_to_geodataframe(items_dict)
    return(items_gdf)


import pandas as pd
def build_dancecard(items_s2_gen,requested_assets):
    print(requested_assets)
    records = []
    for item in items_s2_gen():
        key = item.id
        record = [key,
                  item.properties['landsat:scene_id'],
                  item.properties['instruments'],
                  item.properties['landsat:cloud_cover_land'],
#                   item.assets["thumbnail"]["href"],
#                   item.assets["metadata"]["href"],
#                   item.assets["info"]["href"],
#                   item.assets["B04"]["href"],item.assets["B03"]["href"],item.assets["B02"]["href"],
#                   item.assets["B08"]["href"],
#                   item.assets["overview"]["href"],
                 ]
        asset_records = []
        for rasset in requested_assets:
            asset_records.append(item.assets[rasset].extra_fields['alternate']['s3']['href'])
        for a in asset_records:
            record.append(a)
        records.append(record)

    col_names = ['key', 'productID', 'instruments', 'cloudPct']

    rdf = pd.DataFrame(records)
    for a in requested_assets:
        col_names.append(a)
    kdf2 = rdf.set_axis(col_names, axis=1, inplace=False)

    return(kdf2)



############## Stac_eco ##########################
class Stac_eco:
    curators = {'Landsat': 
            {'url': 'https://landsatlook.usgs.gov/stac-server', 'collection': 'landsat-c2l2-sr'}
            }

    def __init__(self, geojson_file, satellite_program = 'Landsat', collection = 'landsat-c2l2-sr'):
        self.curator=satellite_program
        self.geojson_file=geojson_file
        self.collection=collection
        self.curator=satellite_program

    def __repr__(self):
        rt = self.curator + ' ' + self.collection + ' ' + self.geojson_file
        return rt

    def search(self, datetime, cloud_cover=50, geo_operation="intersects"):
        collection = self.collection
        collection = self.collection
        url = "https://landsatlook.usgs.gov/stac-server"
        geom = geom_from_geojson(self.geojson_file)

    # Search parameters
        params = {
            "collections": [collection],
            geo_operation: geom,
            "datetime": datetime,
            "limit": 100,
            "query": ["platform=LANDSAT_8", f"eo:cloud_cover<{cloud_cover}"]
        }

        cat = Client.open(url)
        SEARCH_OBJ = cat.search(**params)

        return(SEARCH_OBJ)

    def plot_polygons(self,search_object):
        aoi = gpd.read_file(self.geojson_file)

        items_gdf = _get_items_gdf(search_object)
        a=aoi.hvplot.paths(geo=True, line_width=3, line_color='red')
        p=_plot_polygons(items_gdf) * a
        return(p)

    def items_gdf(self, search_object):
        items_gdf = _get_items_gdf(search_object)
        return(items_gdf)


    def df_assets(self,search_object):
        # use the first Item to see what assets are available

        items_dict = _get_items_dict(search_object)
        assets = pd.DataFrame.from_dict(items_dict[0]['assets'], orient='index')

        for f in ['alternate', 'file:checksum', 'proj:transform', 'rel']:
            if f in assets:
                del assets[f]
        return(assets)


    def dancecard(self, search_object):
        requested_assets =['thumbnail', 'reduced_resolution_browse', 'blue', 'green', 'red', 'nir08', 'ANG.txt', 'MTL.txt', 'MTL.xml', 'MTL.json', 'qa_pixel', 'qa_radsat']

        items_s2_gen = search_object.get_items

        kdf = build_dancecard(items_s2_gen, requested_assets)
        return kdf
