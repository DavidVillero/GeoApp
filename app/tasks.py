import geoplot
import matplotlib.pyplot as plt
import uuid
from io import BytesIO

from app import celery
import redis

from .geo_utils import get_interface_geometries, process_geo_data

geo_file = 'notebooks/data/BedrockP.shp'

rcache = redis.Redis(host='redis', port=6379, db=2)

@celery.task()
def create_heat_map(limit_distance, fig_id):
    """This function will create a heat map for cobalt regions based on the limit distance between serpentinite and granodiorite

    Args:
        limit_distance ([type]): [description]

    Returns:
        [type]: [description]
    """
    rcache.set('heat_{}'.format(fig_id), 'working')
    print("In task: Loading Data")
    bedrock_data = process_geo_data(INPUT_FILE=geo_file)
    print("In task: Data Loaded")

    ultramafic = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']=='serpentinite']['geometry']
    granodiorite_pols = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']== 'granodiorite']['geometry']
    epsg_ultramafic = ultramafic.to_crs('EPSG:4326')
    epsg_granodiorite_pols = granodiorite_pols.to_crs('EPSG:4326')

    print("In task: getting interfaces")
    close_matches, points, centroids = get_interface_geometries(limit_distance, ultramafic, granodiorite_pols, epsg_ultramafic, epsg_granodiorite_pols)

    print("In task: creating figure")

    ax = geoplot.kdeplot(
        points, #clip=test_df.geometry,
        shade=True, cmap='Reds',
        projection=geoplot.crs.AlbersEqualArea())
    ax = geoplot.pointplot(centroids, hue='proximity_percentage', legend=True, ax=ax, cmap='Reds')

    fig = geoplot.polyplot(bedrock_data.to_crs('EPSG:4326'), ax=ax, zorder=1)
    fig_file = 'images/heat_map_{}.jpg'.format(fig_id)
    print('In task: saving image')
    plt.savefig('app/'+fig_file)
    
    rcache.set('heat_{}'.format(fig_id), fig_file)


@celery.task()
def create_topog_map(limit_distance, fig_id):
    """This function will create a heat topographic for cobalt regions based on the limit distance between serpentinite and granodiorite
    Args:
        limit_distance ([type]): [description]

    Returns:
        [type]: [description]
    """
    rcache.set('topo_{}'.format(fig_id), 'working')
    bedrock_data = process_geo_data(INPUT_FILE=geo_file)

    ultramafic = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']=='serpentinite']['geometry']
    granodiorite_pols = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']== 'granodiorite']['geometry']
    epsg_ultramafic = ultramafic.to_crs('EPSG:4326')
    epsg_granodiorite_pols = granodiorite_pols.to_crs('EPSG:4326')

    close_matches, points, centroids = get_interface_geometries(limit_distance, ultramafic, granodiorite_pols, epsg_ultramafic, epsg_granodiorite_pols)


    ax = geoplot.kdeplot(points,projection=geoplot.crs.AlbersEqualArea(), n_levels=20, cmap='Blues', figsize=(20, 20))
    ax = geoplot.pointplot(points, hue='proximity_percentage', legend=True, ax=ax)
    fig = geoplot.polyplot(bedrock_data.to_crs('EPSG:4326'), ax=ax)

    fig_file = 'images/topo_map_{}.jpg'.format(fig_id)
    print('In task: saving image')
    plt.savefig('app/'+fig_file)

    rcache.set('topo_{}'.format(fig_id), fig_file)

