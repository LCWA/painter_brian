import glob
import shutil
import subprocess
import urllib.request
from multiprocessing import Process

from bs4 import BeautifulSoup
import time
from os import listdir
from os.path import isfile, join
import os
from PIL import Image
from tqdm.notebook import tqdm
import zipfile
import re


class TrainingManager:
    def __init__(self, artist, style, retrain, working_path, kimg, gpus):
        self.min_freq = 30
        self.gpus = gpus
        self.start_kimg = kimg
        self.artist = artist
        self.style = style
        self.retrain = retrain
        self.working_path = working_path
        self.images_path = f"{self.working_path}/data/gan/images/{artist}/{style}/"
        self.dataset_path = f"{self.working_path}/data/gan/datasets/{artist}/{style}"
        self.output_path = f"{self.working_path}/data/gan/experiments/{artist}/{style}/"
        self.latest_generating = f"{self.working_path}/data/gan/latest_generating/{artist}/{style}/"
        self.process_pid = None
        self.subprocess_pid = None
        # self.current_process = None

    def combine_sets(self, zip_name):
        with zipfile.ZipFile(self.images_path + zip_name, 'r') as zip_ref:
            zip_ref.extractall(self.images_path)
        os.remove(self.images_path + zip_name)

    def download_new_style(self, dataset_size=0):
        base_url = "https://www.wikiart.org/"

        url = base_url + 'en/' + self.artist + '/all-works/text-list'
        artist_work_soup = BeautifulSoup(urllib.request.urlopen(url), "lxml")

        artist_main = artist_work_soup.find("main")
        image_count = 0

        lis = artist_main.find_all("li")

        for li in lis:
            if (dataset_size > 0) and (image_count == dataset_size):
                break
            link = li.find("a")

            if link != None:
                painting = link.attrs["href"]

                # get the painting
                url = base_url + painting

                try:
                    painting_soup = BeautifulSoup(urllib.request.urlopen(url), "lxml")
                except:
                    continue
                # check the copyright
                if "Public domain" in painting_soup.text:

                    # check the genre
                    style_ = painting_soup.find("a", {"href": f"/en/paintings-by-style/{self.style}"})
                    if style_ is not None and style_.text.lower() == self.style:
                        # get the url
                        og_image = painting_soup.find("meta", {"property": "og:image"})
                        image_url = og_image["content"].split("!")[0]  # ignore the !Large.jpg at the end
                        print(image_url)
                        save_path = self.images_path + "_" + str(image_count) + ".jpg"
                        # download the file
                        try:
                            print("downloading to " + save_path)
                            time.sleep(0.2)  # try not to get a 403
                            urllib.request.urlretrieve(image_url, save_path)
                            image_count = image_count + 1
                        except Exception as e:
                            print("failed downloading " + image_url, e)

    def prepare_images(self, img_size):
        paths = [f for f in listdir(self.images_path) if isfile(join(self.images_path, f))]
        for p in tqdm(paths):
            f = os.path.join(self.images_path, p)
            print(f)
            img = Image.open(f)
            if img.mode == "RGB":
                imgResize = img.resize((img_size, img_size), Image.ANTIALIAS)
                imgResize.save(f, 'JPEG', quality=90)
            else:
                os.remove(f)
        # step 2. create different resolutions dataset as required by style-gan architecture
        prepare_path = self.working_path + "/stylegan2-ada/dataset_tool.py"
        cmd = ["create_from_images", self.dataset_path, self.images_path]
        p = subprocess.Popen(["python", prepare_path] + cmd)
        return p.wait()

    def __find_latest_subdir(self):
        all_subdirs = [self.output_path + d for d in
                       os.listdir(self.output_path) if
                       os.path.isdir(self.output_path + d)]
        return max(all_subdirs, key=os.path.getmtime)

    def get_log_file(self):
        latest_subdir = self.__find_latest_subdir()
        return glob.glob(latest_subdir + "/log.txt")[0]

    def __find_latest_model(self):
        latest_subdir = self.__find_latest_subdir()
        list_of_files = glob.glob(latest_subdir + "/*.pkl")

        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file

    def __switch_models(self, latest_model_path):
        copy_generating = self.working_path + self.latest_generating + '/latest.pkl'
        shutil.copyfile(latest_model_path, copy_generating)

    def train_fn(self, retrain=False, aug="ada", mirror=1, metrics="none", snap=1, kimg=5000):
        train_path = self.working_path + "/stylegan2-ada/train.py"
        cmd = ["--data=" + self.dataset_path, "--outdir=" + self.output_path, "--aug=" + aug, "--mirror=" + str(mirror),
               "--snap=" + str(snap), "--metrics=" + metrics, "--gpus=" + str(self.gpus), "--kimg=" + str(kimg)]
        if retrain is False:
            p = subprocess.Popen(["python", train_path] + cmd)
        else:
            resume_path = self.__find_latest_model()
            p = subprocess.Popen(["python", train_path] + cmd + ["--resume=" + resume_path])


class TrainChecker:

    def __init__(self, train_manager):
        self.train_manager = train_manager
        if not os.path.exists(self.train_manager.output_path):
            os.makedirs(self.train_manager.output_path)
        self.log_path = f"{train_manager.output_path}" + "checker_logs.txt"
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w+") as f:
                f.write(f"-1 {train_manager.start_kimg}")
        self.training_pid = -1

    def __parse_tick(self, last_line):
        splits = last_line.split(" ")
        if splits[0] == "tick":
            tick = last_line.split(" ")[1]
            return int(tick)
        else:
            return -1

    def __parse_kimg(self, last_line):
        splits = last_line.split(" ")
        for line2 in splits:
                if re.match(r'^kimg', line2):
                    val = splits[splits.index(line2)+1]
        return val

    def __get_last_line(self, file):
        last_line = ""
        with open(file , 'r') as f:
            content = f.read()
            content_list = content.splitlines()

            for line in content_list:
                if re.match(r'^tick', line):
                    last_line = line

            return last_line

    def __find_pid(self):
        p = subprocess.run(['ps', '-ax'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = str(p.stdout).split("\\n")
        pid = -1
        for line in output:
            if line.find("stylegan2-ada/train.py") != -1:
                save_line = line
                pid = int(re.findall('[0-9]+', save_line)[0])
        return pid

    def __restart(self, remaining_kimg):
        try:
            pid = self.__find_pid()
            if pid != -1:
                os.kill(self.__find_pid(), 9)
            self.train_manager.train_fn(True, 'ada', 1, "none", 100, remaining_kimg)
        except OSError:
            self.train_manager.train_fn(True, 'ada', 1, "none", 100, remaining_kimg)

    def check(self):
        last_line = self.__get_last_line(self.train_manager.get_log_file())
        current_tick = self.__parse_tick(last_line)
        with open(self.log_path, "r") as f:
            content = f.readlines()[0].split(" ")
            last_tick = int(content[0])
            new_start_kimg = int(content[1])
        # if current_tick == -1:
        #     if last_tick == -1:
        #         print("Job hasn't started training yet. Check again in 10 minutes")
        #         return 3  
        current_kimg = int(float(self.__parse_kimg(last_line)))
        if new_start_kimg < current_kimg:
            remaining_kimg = int(new_start_kimg)
        else:
            remaining_kimg = int(new_start_kimg - current_kimg)
        if last_tick == current_tick:
            if remaining_kimg != 0.0:
                print("Restarting...")
                self.__restart(new_start_kimg)
                return 1
            else:
                print("Job has finished")
                return 2
        else:
            with open(self.log_path, "w") as f:
                f.write(str(current_tick)+" "+f"{str(remaining_kimg)}")
            print("Job is healthy")
            return 3

# 4914



