from flask import Flask
from flask import request, jsonify
import os
import base64
app = Flask(__name__)

os.environ["CUDA_VISIBLE_DEVICES"]="0"
gan_vangogh = "../flask/models/vangogh_5kimgs_1st_model.pkl"
gan_monet = "../flask/models/monet_5kimgs_2nd_model.pkl"

@app.route("/retrain_model" , methods = ['POST'])
def retrain_vangoh():
    if request.method == 'POST':
        artist = request.form['artist']
        style = request.form['style']
        zip_filename = request.form['zip_filename']

        for key,value in request.files.items():
            value.save("/home/mauser/data/gan/images/" + str(artist) + "/" + str(style) + "/" + str(zip_filename))

        with open("/home/mauser/queue.dat", "a") as fout:
            fout.writelines([str(artist) + " " + str(style) + " " + str(zip_filename) + " True" + " new"])

        resp = jsonify(success=True)
        resp.status_code = 200
        return resp
    else:
        resp = jsonify(success=False)
        resp.status_code = 405
        return resp