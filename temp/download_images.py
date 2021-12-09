import urllib.request
import re
from bs4 import BeautifulSoup
import time


def download_dataset(style, artist, dataset_size):
    base_url = "https://www.wikiart.org/"
    file_path = "/home/mauser/data/gan/images/"

    url = base_url + 'en/' + artist + '/all-works/text-list'

    artist_work_soup = BeautifulSoup(urllib.request.urlopen(url), "lxml")

    artist_main = artist_work_soup.find("main")
    image_count = 0

    lis = artist_main.find_all("li")

    for li in lis:
        if image_count == dataset_size:
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
                style_ = painting_soup.find("a", {"href": "/en/paintings-by-style/realism"})
                if style_ != None and style_.text == style:
                    # get the url
                    og_image = painting_soup.find("meta", {"property": "og:image"})
                    image_url = og_image["content"].split("!")[0]  # ignore the !Large.jpg at the end
                    print(image_url)
                    save_path = file_path + artist + "_" + str(image_count) + ".jpg"
                    # download the file
                    try:
                        print("downloading to " + save_path)
                        time.sleep(0.2)  # try not to get a 403
                        urllib.request.urlretrieve(image_url, save_path)
                        image_count = image_count + 1
                    except Exception as e:
                        print("failed downloading " + image_url, e)


if __name__ == '__main__':
    download_dataset("Realism", "vincent-van-gogh", 800)


