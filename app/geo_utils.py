import geopandas as gpd
import geoplot
import numpy as np
from shapely.geometry import Point
from tqdm import tqdm

def process_geo_data(INPUT_FILE='notebooks/data/BedrockP.shp'):
    """This function will massage and slice and filte

    Args:
        file (str, optional): [description]. Defaults to 'notebooks/data/BedrockP.shp'.

    Returns:
        [type]: [description]
    """

    bedrock_data = gpd.read_file(INPUT_FILE)

    # relabelling records & Segmenting Data Based on Rock Type
    rocks_of_interest = {'serpentinite': [], 'granodiorite': []}
    for t in bedrock_data.rock_type.unique():
        if 'ultramafic' in t or 'serpentinite' in t:
            rocks_of_interest['serpentinite'].append(t)
        elif 'granodiorite' in t:
            rocks_of_interest['granodiorite'].append(t)

    for ud in bedrock_data.unit_desc.unique():
        if 'granodiorite' in ud:
            rocks_of_interest['granodiorite'].extend(
                list(bedrock_data.loc[bedrock_data['unit_desc'] == ud, 'rock_type'].unique()))
        elif 'ultramafic' in ud or 'serpentinite' in ud:
            rocks_of_interest['serpentinite'].extend(
                list(bedrock_data.loc[bedrock_data['unit_desc'] == ud, 'rock_type'].unique()))

    for rock in rocks_of_interest:
        rocks_of_interest[rock] = list(set(rocks_of_interest[rock]))

    rock_to_sp = {
        v: k for k in rocks_of_interest for v in rocks_of_interest[k]}

    # Adding extra column to slice data based on serpentinite_or_granodiorite
    bedrock_data['serpentinite_or_granodiorite'] = bedrock_data['rock_type']
    bedrock_data.replace(
        {"serpentinite_or_granodiorite": rock_to_sp}, inplace=True)
    bedrock_data.loc[~bedrock_data['serpentinite_or_granodiorite'].isin(
        ['serpentinite', 'granodiorite']), 'serpentinite_or_granodiorite'] = 'Other_rock_type'

    # Separating serpentinite and granodiorite geometry data

    return bedrock_data


def ceil_negative(a): return (abs(a)+a)/2


def calculate_fat_polygon(polygon_series, ind, limit_distance):
    """This function scales up the size of the polygon based on the limit distance

    Args:
        polygon_series ([type]): [description]
        ind ([type]): [description]
        limit_distance ([type]): [description]

    Returns:
        [type]: [description]
    """

    minx, miny, maxx, maxy = polygon_series[ind].envelope.bounds

    hight = maxy - miny
    width = maxx - minx
    xfact = ((2*limit_distance)+width)/width
    yfact = ((2*limit_distance)+hight)/hight

    return polygon_series.scale(xfact=xfact, yfact=yfact, origin='center')


def create_points(polygon, proximity_percetage):
    """This fucntion creates points within the polygon envelop bounds and makes sure they are placed inside the polygon

    Args:
        new_gdf ([type]): [description]
        limit_distance ([type]): [description]
        i ([type]): [description]

    Returns:
        geopandas.GeoDataFrame: GeoDataFrame with points
    """

    points = []
    minx, miny, maxx, maxy = polygon.envelope.bounds
    while len(points) < 10*proximity_percetage:
        x = (maxx - minx) * np.random.random_sample() + minx
        y = (maxy - miny) * np.random.random_sample() + miny
        p = Point(x, y)
        if polygon.intersects(p):
            points.append(p)
    return points


def get_closest_polygon(polygon_series, spatial_index, target_rock_geometries, epsg_target_rock_geometries, limit_distance, ind, epsg_iterative_rock_geometry):
    """This function will get the closest polygons to polygon_series

    Args:
        polygon_series ([type]): [description]
        spatial_index ([type]): [description]
        target_rock_geometries ([type]): [description]
        epsg_target_rock_geometries ([type]): [description]
        limit_distance ([type]): [description]
        ind ([type]): [description]
        epsg_iterative_rock_geometry ([type]): [description]
    """

    fat_u = calculate_fat_polygon(polygon_series, ind, limit_distance)

    # Use R-tree to find close polygons
    possible_matches_index = list(
        spatial_index.intersection(fat_u[ind].bounds))
    possible_matches = target_rock_geometries.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.intersects(fat_u[ind])]
    proximity_metric = [ceil_negative(
        1-(polygon_series[ind].distance(p)/(limit_distance))) for p in precise_matches]

    pm_df = gpd.GeoDataFrame({
        'geometry': epsg_target_rock_geometries.loc[list(precise_matches.index)],
        'proximity_percentage': proximity_metric
    })

    if len(pm_df) == 0:
        return gpd.GeoDataFrame(), gpd.GeoDataFrame(), gpd.GeoDataFrame()
    else:
        micro_gdf = gpd.GeoDataFrame(epsg_iterative_rock_geometry[[ind]])
        micro_gdf = micro_gdf.append(gpd.GeoDataFrame(
            epsg_target_rock_geometries.loc[list(precise_matches.index)]))
        micro_gdf['proximity_percentage'] = 0
        new_gdf = gpd.overlay(pm_df, gpd.GeoDataFrame(
            {'geometry': fat_u}).to_crs('EPSG:4326'), how='intersection')
        micro_gdf = micro_gdf.append(new_gdf).reset_index()
        multiple_p = []
        for i in new_gdf.index:
            polygon = new_gdf.loc[i, 'geometry']
            proximity_percetage = new_gdf.loc[i, 'proximity_percentage']
            points = create_points(polygon, proximity_percetage)
            multiple_p.extend(points)

        points = gpd.GeoDataFrame(
            {'geometry': multiple_p, 'proximity_percentage': proximity_percetage}, index=range(len(multiple_p)))
        new_gdf['geometry'] = new_gdf.geometry.to_crs('EPSG:26910').centroid
        return micro_gdf, points, new_gdf


def get_interface_geometries(limit_distance, ultramafic, granodiorite_pols, epsg_ultramafic, epsg_granodiorite_pols):
    """This fucntion will generate polygons for the areas in between the two type of reocks that are within the limit_distance

    Args:
        limit_distance ([type]): [description]
        ultramafic ([type]): [description]
        granodiorite_pols ([type]): [description]

    Returns:
        geopandas.GeoDataFrame: interfaces geometry, points on geometry and centroids of geometry
    """

    if len(ultramafic) > len(granodiorite_pols):
        target_rock_geometries = ultramafic
        iterative_rock_geometry = granodiorite_pols
    else:
        target_rock_geometries = granodiorite_pols
        iterative_rock_geometry = ultramafic

    spatial_index = target_rock_geometries.sindex
    cobalt_regions = gpd.GeoDataFrame()
    centroids = gpd.GeoDataFrame()
    Points = gpd.GeoDataFrame()
    distances = []
    ind = []

    epsg_iterative_rock_geometry = iterative_rock_geometry.to_crs('EPSG:4326')
    epsg_target_rock_geometries = target_rock_geometries.to_crs('EPSG:4326')
    i = 0
    for ind in tqdm(iterative_rock_geometry.index):
        polygon_series = iterative_rock_geometry[[ind]]

        cobalt_region, points, centroid = get_closest_polygon(
            polygon_series, spatial_index, target_rock_geometries, epsg_target_rock_geometries, limit_distance, ind, epsg_iterative_rock_geometry)
        cobalt_regions = cobalt_regions.append(cobalt_region)
        Points = Points.append(points)
        centroids = centroids.append(centroid)

    cobalt_regions = cobalt_regions.drop_duplicates('geometry')
    Points = Points.drop_duplicates('geometry')
    return cobalt_regions, Points, centroids
