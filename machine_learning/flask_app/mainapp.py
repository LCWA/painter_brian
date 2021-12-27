from flask import Flask, Response
from PIL import Image
from io import BytesIO

import tensorflow as tf
import base64
import gc
import os
import numpy as np
import random
import dnnlib
import pickle
import dnnlib.tflib as tflib

app = Flask(__name__)

os.environ["CUDA_VISIBLE_DEVICES"]="0"
gan_vangogh = "./models/vangogh_5kimgs_1st_model.pkl"
gan_monet = "./models/monet_5kimgs_2nd_model.pkl"

def _sanitize_tf_config(config_dict: dict = None) -> dict:
    # Defaults.
    cfg = dict()
    cfg["rnd.np_random_seed"]               = None      # Random seed for NumPy. None = keep as is.
    cfg["rnd.tf_random_seed"]               = "auto"    # Random seed for TensorFlow. 'auto' = derive from NumPy random state. None = keep as is.
    cfg["env.TF_CPP_MIN_LOG_LEVEL"]         = "1"       # 0 = Print all available debug info from TensorFlow. 1 = Print warnings and errors, but disable debug info.
    cfg["env.HDF5_USE_FILE_LOCKING"]        = "FALSE"   # Disable HDF5 file locking to avoid concurrency issues with network shares.
    cfg["graph_options.place_pruned_graph"] = True      # False = Check that all ops are available on the designated device. True = Skip the check for ops that are not used.
    cfg["gpu_options.allow_growth"]         = True      # False = Allocate all GPU memory at the beginning. True = Allocate only as much GPU memory as needed.

    # Remove defaults for environment variables that are already set.
    for key in list(cfg):
        fields = key.split(".")
        if fields[0] == "env":
            assert len(fields) == 2
            if fields[1] in os.environ:
                del cfg[key]

    # User overrides.
    if config_dict is not None:
        cfg.update(config_dict)
    return cfg

def init_session():

    config_dict = None
    cfg = _sanitize_tf_config(config_dict)
    config_proto = tf.ConfigProto()
    for key, value in cfg.items():
        fields = key.split(".")
        if fields[0] not in ["rnd", "env"]:
            obj = config_proto
            for field in fields[:-1]:
                obj = getattr(obj, field)
            setattr(obj, fields[-1], value)

    return tf.Session(config=config_proto)

@app.route("/generate_image/van-gogh-realism")
def predict_vangogh():

    session = init_session()

    with session:
        with dnnlib.util.open_url(gan_vangogh) as fp:
            _G, _D, model = pickle.load(fp)
    
        Gs_kwargs = {
            'output_transform': dict(func=tflib.convert_images_to_uint8, nchw_to_nhwc=True),
            'randomize_noise': False,
            'truncation_psi': 0.5
        }   

        rndNumber = random.randint(0 , 2**32 - 1)
        rnd = np.random.RandomState(rndNumber)
        z = rnd.randn(1, *model.input_shape[1:]) # [minibatch, component]

        images = model.run(z, None, **Gs_kwargs) # [minibatch, height, width, channel]
        image = Image.fromarray(images[0], 'RGB')

        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())

    tf.reset_default_graph()
    del session
    del model
    gc.collect()
    return Response(img_str, mimetype='text/plain')

    #return Response("test", mimetype='text/plain')

@app.route("/generate_image/claude-monet-impressionism")
def predict_monet():

    session = init_session()
    with session:

        with dnnlib.util.open_url(gan_monet) as fp:
            _G, _D, model = pickle.load(fp)

        Gs_kwargs = {
            'output_transform': dict(func=tflib.convert_images_to_uint8, nchw_to_nhwc=True),
            'randomize_noise': False,
            'truncation_psi': 0.5
        }

        rndNumber = random.randint(0 , 2**32 - 1)
        rnd = np.random.RandomState(rndNumber)
        z = rnd.randn(1, *model.input_shape[1:]) # [minibatch, component]

        images = model.run(z, None, **Gs_kwargs) # [minibatch, height, width, channel]
        image = Image.fromarray(images[0], 'RGB')
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
    tf.reset_default_graph()
    del session
    del model
    gc.collect()
    return Response(img_str, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000, debug=False, threaded = True)