from io import BytesIO
import base64
import os
import random
import uuid

from flask import Blueprint, Flask, Response, render_template, request, send_file, jsonify, send_from_directory
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.image as mpimg
import redis

from .tasks import create_heat_map, create_topog_map

bp = Blueprint("all", __name__)


# @bp.route("/")
# def index():
#     return "Hello!"
rcache = redis.Redis(host='redis', port=6379, db=2)

import os
@bp.route("/")
def index():
    limit_distance = int(request.args.get("limit_distance", 1200))
    fig_id = str(uuid.uuid4()).replace('-','')
    return render_template("index.html", limit_distance=limit_distance, fig_id=fig_id)


@bp.route("/matplot-as-HeatMapimage-<fig_id>-<int:limit_distance>.png")
def plot_heat_map(fig_id, limit_distance=1200):
    """ renders heat plot.
    """
    status = rcache.get('heat_{}'.format(fig_id))
    

    if status:
        if status.decode() == 'working':
            return jsonify({'status': 'working on image'})
        else:
            # fig_file = status.decode()
            # fig = Figure()
            # img = mpimg.imread('app/'+fig_file)
            # fig.figimage(img)
            # output = BytesIO()
            # FigureCanvasAgg(fig).print_png(output)
            # print("In routes: HeatMap Created")
            uploads = 'images'
            filename = 'heat_map_{}.jpg'.format(fig_id)
            return send_from_directory(directory=uploads, filename=filename)#Response(output.getvalue(), mimetype="image/png")

    print("In routes:Creating HeatMap")

    create_heat_map.apply_async([limit_distance, fig_id])

    return jsonify({'status': 'Job Started, your image will start processing soon', 'Job_id': fig_id})


@bp.route("/matplot-as-TopoMapimage-<fig_id>-<int:limit_distance>.png")
def plot_topo_map(fig_id, limit_distance=1200):
    """ renders the topographic plot.
    """
    status = rcache.get('topo_{}'.format(fig_id))
    if status:
        if status.decode() == 'working':
            return jsonify({'status': 'working on image'})
        else:
            # fig_file = status.decode()
            # fig = Figure()
            # img = mpimg.imread('app/'+fig_file)
            # fig.figimage(img)
            # output = BytesIO()
            # FigureCanvasAgg(fig).print_png(output)
            # print("In routes: TopoMap Created")
            uploads = 'images'
            filename = 'topo_map_{}.jpg'.format(fig_id)
            return send_from_directory(directory=uploads, filename=filename)#Response(output.getvalue(), mimetype="image/png")

    print("In routes:Creating TopoMap")

    create_topog_map.apply_async([limit_distance, fig_id])

    return jsonify({'status': 'Job Started, your image will start processing soon', 'Job_id': fig_id})


@bp.route('/download/<path:fig_id>', methods=['GET', 'POST'])
def download(fig_id):
    uploads = 'images'
    filename = 'heat_map_{}.jpg'.format(fig_id)
    print(os.getcwd())
    try:
        f = open(f'app/images/{filename}')
    except IOError:
        filename = 'topo_map_{}.jpg'.format(fig_id)
    print('#############',filename)
    return send_from_directory(directory=uploads, filename=filename)


if __name__ == "__main__":
    import webbrowser

    webbrowser.open("http://127.0.0.1:8000/")
    bp.run(debug=True)

