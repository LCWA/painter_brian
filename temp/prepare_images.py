from os import listdir
from os.path import isfile, join
import os
from PIL import Image
from tqdm.notebook import tqdm


def prepare_images(img_size):
    IMAGE_PATH = '/home/mauser/data/gan/images'
    paths = [f for f in listdir(IMAGE_PATH) if isfile(join(IMAGE_PATH, f))]
    base_size = None
    for p in tqdm(paths):
        f = os.path.join(IMAGE_PATH, p)
        print(f)
        img = Image.open(f)
        if img.mode=="RGB":
            imgResize = img.resize((img_size, img_size), Image.ANTIALIAS)
            imgResize.save(f, 'JPEG', quality=90)
        else:
            os.remove(f)


if __name__ == '__main__':
    prepare_images(512)


