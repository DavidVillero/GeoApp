import geopandas as gpd
import numpy as np
from app.geo_utils import get_closest_polygon, process_geo_data
from shapely.geometry import Point

geo_file = 'notebooks/data/BedrockP.shp'


def test_process_geo_data():

    bedrock_data = process_geo_data(geo_file)
    ultramafic = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']
                                  == 'serpentinite']['geometry']
    granodiorite_pols = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']
                                         == 'granodiorite']['geometry']

    assert len(ultramafic) == 276
    assert len(granodiorite_pols) == 398


def test_get_closest_polygon():
    bedrock_data = process_geo_data(geo_file)
    ultramafic = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']
                                  == 'serpentinite']['geometry']
    granodiorite_pols = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']
                                         == 'granodiorite']['geometry']
    epsg_ultramafic = ultramafic.to_crs('EPSG:4326')
    epsg_granodiorite_pols = granodiorite_pols.to_crs('EPSG:4326')

    limit_distance = 100

    polygon_series = ultramafic[[2]]
    minx, miny, maxx, maxy = polygon_series[2].envelope.bounds

    hight = maxy - miny
    width = maxx - minx

    xfact = ((2*limit_distance)+width)/width
    yfact = ((2*limit_distance)+hight)/hight
    fat_u = polygon_series.scale(xfact=xfact,
                                 yfact=yfact,
                                 origin='center')

    spatial_index = granodiorite_pols.sindex

    close_matches, points, centroids = get_closest_polygon(
        polygon_series, spatial_index, granodiorite_pols, epsg_granodiorite_pols, limit_distance, 2, epsg_ultramafic)

    possible_matches_index = list(spatial_index.intersection(fat_u[2].bounds))
    possible_matches = granodiorite_pols.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.intersects(fat_u[2])]

    pm_df = gpd.GeoDataFrame({'geometry': epsg_granodiorite_pols.loc[list(precise_matches.index)], 'proximity_percentage': [
                             1-(polygon_series[2].distance(p)/(limit_distance)) for p in precise_matches]})
    new_gdf = gpd.overlay(pm_df, gpd.GeoDataFrame(
        {'geometry': fat_u}).to_crs('EPSG:4326'), how='intersection')

    test_df = gpd.GeoDataFrame(epsg_ultramafic[[2]])

    test_df = test_df.append(gpd.GeoDataFrame(
        epsg_granodiorite_pols.loc[list(precise_matches.index)]))
    test_df['proximity_percentage'] = 0
    test_df = test_df.append(new_gdf).reset_index()

    polygon = test_df.loc[2, 'geometry']

    proximity_percetage = test_df.loc[2, 'proximity_percentage']
    ppoints = []
    minx, miny, maxx, maxy = polygon.envelope.bounds
    while len(ppoints) < 100*proximity_percetage:
        x = (maxx - minx) * np.random.random_sample() + minx
        y = (maxy - miny) * np.random.random_sample() + miny
        p = Point(x, y)
        if polygon.intersects(p):
            ppoints.append(p)

    points = gpd.GeoDataFrame(
        {'geometry': ppoints, 'proximity_percentage': proximity_percetage}, index=range(len(ppoints)))

    for i in close_matches.index:
        assert close_matches.loc[i, 'geometry'] == test_df.loc[i, 'geometry']
