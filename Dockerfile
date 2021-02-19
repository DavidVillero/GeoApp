FROM python:3.7.7

COPY . /code/
WORKDIR /code
ENV FLASK_APP=run_app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
ENV PYTHONUNBUFFERED 1
ENV DOCKER_CONTAINER 1
# RUN apk add --no-cache gcc musl-dev linux-headers
RUN apt-get update 
#&& apt-get install libgeos++-dev -y && apt install python3-dev -y
RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh 

RUN conda --version

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
# RUN pip install matplotlib
# RUN pip install pygeos
RUN conda install geopandas
RUN conda install pandas fiona shapely pyproj rtree
RUN conda install geoplot -c conda-forge
# RUN pip install geoplot
EXPOSE 5000

