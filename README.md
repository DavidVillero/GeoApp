# GeoHeatMap

The exploration is done in a Jupyer notebook, so let's start by setting up the environment with the following:

```bash
conda create -n heatmap python=3.6.7
conda activate heatmap
pip install notebook
pip install -r requirements.txt
conda install geopandas
conda install pandas fiona shapely pyproj rtree
conda install geoplot -c conda-forge
```

The notebook is found under the notebooks folder and it is named `Creating_Heat_Map.ipynb`

```bash
cd notebooks
jupyter notebbok
```

## Explanation:

I first tried to label all the data based on the rock_type and the unit_desc columns because I noticed that these columns contained the words 'serpentinite' and 'granodiorite'. If those names were not in the column, I labeled the record as 'other_rock_type'. Then, I sliced the data based on serpentinite and granodiorite and created two GeoDataFrames respectively.
Initially, to find the serpentinite polygons that are close to the granodiorite polygons up to the limit distance, I thought of doing a nested for loop. That is, for each polygon in both GeoDataFrames (serpentinite GeoDataFrame and granodiorite GeoDataFrame), I would calculate the distance between polygons as I loop through both arrays. If the polygons are within the limit distance, I would store them somewhere. This would be very slow. However, after doing some reasearch, I discovered that I could take advantage of R-trees to quickly find the closest polygons to a particular geometry. So, I leverage this and a "fat_polygon" strategy to create extra geometries that represent the interfaces or the areas inbetween the two rock types. The idea here is to increase the size of a polygon up to the input proximity distance (I called it a "fat polygon") and check if there are any polygons that overlap with it or touch it. If there are overlaps or any contact, I can create the geometry that represents the "area of interest" by taking the intersection between the fat polygon (i.e. serpentinite) and the nearby polygon (i.e. granodiorite). I also use the original polygon to calculate a proximity metric that relates to the likelihood of finding cobalt in that particular region.
To create the heat map, I use the KDE plot method in geoplot, so I need to vary a density of points in the areas of interest. The density of points is controlled by the distance proximity metric. To make sure that the points are placed inside the area where we would expect to find cobalt, I randomly generate a point within the bounds of the new polygon and use the polygon.intersects method to check if the point lies within the polygon itself.

## Sample:

![Test Image 1](/notebooks/test_heat.jpg)

After I noticed the test worked, I encapsulated the logic into a couple of functions that I placed in `app/geo_utils.py`.

## Run Tests:
I prefer to do functional testing and I tend to use pytest for this. I placed my test under the `test` folder. To run pytest:

```bash
python -m pytest
```

The script `create_heat_map.py` receives two parameters 'limit_distance' and 'maptype'. `maptype=heatmap` makes a a traditional heat map with geoplot.kdeplot and `maptype=topomap` makes a heatmap with level surfaces and overplotted centroids where the color scheme indicates the closeness of the two rock types. The legend goes from 0 to 1, where 0 represents regions where serpentinite and granodiorite are separated by exactly the limit distance and 1 where the two rock types are in contact.

```bash
python create_heat_map.py --maptype=heatmap
```

## Scaling tool. Welcome to Web GeoHeatMap!

One of the best ways of scaling a local tool is by making it a web application and run it on a highly available and highly resilient architecture. I architected the app as a distributed task system, where every request to create a heatmap gets processed by an isolated unit of compute, called a worker. The requests are queued up in some sort of message-queue (i.e. RabbitMQ, SQS) system and are handled asynchronously by each worker in our cluster. The workers in our cluster continuously poll the queue for a message to process. Once the worker is done, it will store the results in a common repository ().i.e a database, filesyste, S3, EFS). The states of the requests are labeled with a unique job id and are cached in an independent database (ideally a memory database like redis). This helps the client communicate with the server, transfer the status of the request and ultimately retrieve the results. This is a local setup so I use local open source technologies, such as celery, redis and flask for the web apis and encapsulated all the set up and docker.

### 1. Set up docker.

- Windows instructions: https://docs.docker.com/docker-for-windows/install/
- Linux instructions: (debian/ubuntu): https://docs.docker.com/engine/install/debian/
- Mac instructions: https://docs.docker.com/docker-for-mac/install/

### Build docker containers
I recommend to run the following command and then get a coffee as this might take a while to install all dependencies
```bash
docker-compose up
```

The webpage will be hosted locally. So, on your browser, go to:`http://0.0.0.0:5000/`. 

## Taking it all the way to production:
To further scale this and take it to production I would move it to AWS, but I would have to make some modifications first. Essentially, I would swap my queue system for SQS, my file system for S3, build and store my container in ECR and have a lambda that will scale up or down an ECS cluster running on Fargate based on the number of messages in the queue. The main page can also be hosted in a service in ECS behind a load balancer and a cloudfront distribution with an actual domain.
