import argparse
import logging
import geoplot
import matplotlib.pyplot as plt

from app.geo_utils import get_interface_geometries, process_geo_data

geo_file = 'notebooks/data/BedrockP.shp'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_heat_map(limit_distance, fig_id=1):
    """This function will create a heat map for cobalt regions based on the limit distance between serpentinite and granodiorite

    Args:
        limit_distance ([type]): [description]

    Returns:
        [type]: [description]
    """
    print("In task: Loading Data")
    bedrock_data = process_geo_data(INPUT_FILE=geo_file)
    print("In task: Data Loaded")

    ultramafic = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']
                                  == 'serpentinite']['geometry']
    granodiorite_pols = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']
                                         == 'granodiorite']['geometry']
    epsg_ultramafic = ultramafic.to_crs('EPSG:4326')
    epsg_granodiorite_pols = granodiorite_pols.to_crs('EPSG:4326')

    print("In task: getting interfaces")
    close_matches, points, centroids = get_interface_geometries(
        limit_distance, ultramafic, granodiorite_pols, epsg_ultramafic, epsg_granodiorite_pols)

    print("In task: creating figure")

    ax = geoplot.kdeplot(
        points,  # clip=test_df.geometry,
        shade=True, cmap='Reds',
        projection=geoplot.crs.AlbersEqualArea())
    ax = geoplot.pointplot(
        centroids, hue='proximity_percentage', legend=True, ax=ax, cmap='Reds')

    fig = geoplot.polyplot(bedrock_data.to_crs('EPSG:4326'), ax=ax, zorder=1)
    fig_file = 'images/heat_map_{}.jpg'.format(fig_id)
    print('In task: saving image in {}'.format('app/'+fig_file))
    plt.savefig('app/'+fig_file)


def create_topog_map(limit_distance, fig_id=1):
    """This function will create a heat topographic for cobalt regions based on the limit distance between serpentinite and granodiorite
    Args:
        limit_distance ([type]): [description]

    Returns:
        [type]: [description]
    """
    print("In task: Loading Data")
    bedrock_data = process_geo_data(INPUT_FILE=geo_file)
    print("In task: Data Loaded")
    print("In task: Loading Data")
    ultramafic = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']=='serpentinite']['geometry']
    granodiorite_pols = bedrock_data.loc[bedrock_data['serpentinite_or_granodiorite']== 'granodiorite']['geometry']
    epsg_ultramafic = ultramafic.to_crs('EPSG:4326')
    epsg_granodiorite_pols = granodiorite_pols.to_crs('EPSG:4326')

    print("In task: getting interfaces")
    close_matches, points, centroids = get_interface_geometries(limit_distance, ultramafic, granodiorite_pols, epsg_ultramafic, epsg_granodiorite_pols)


    ax = geoplot.kdeplot(points,projection=geoplot.crs.AlbersEqualArea(), n_levels=20, cmap='Blues', figsize=(20, 20))
    ax = geoplot.pointplot(points, hue='proximity_percentage', legend=True, ax=ax)
    fig = geoplot.polyplot(bedrock_data.to_crs('EPSG:4326'), ax=ax)

    fig_file = 'images/topo_map_{}.jpg'.format(fig_id)
    print('In task: saving image in {}'.format('app/'+fig_file))
    plt.savefig('app/'+fig_file)


if __name__ == "__main__":
    print("HeatMap Creator STARTING")
    parser = argparse.ArgumentParser()

    parser.add_argument("--limit_distance", default=1500)
    parser.add_argument("--maptype", default='heatmap') #options topo

    inputs = parser.parse_args()
    if inputs.maptype == 'heatmap':
        create_heat_map(float(inputs.limit_distance))
    elif inputs.maptype == 'topomap':
        create_topog_map(float(inputs.limit_distance))

    print("HeatMap Created")
