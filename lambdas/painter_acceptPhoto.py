import json
import boto3

import os

import requests
from zipfile import ZipFile, ZIP_DEFLATED
import tempfile
import datetime

def delete_unused(artist_style):
    s3 = boto3.client('s3')
    bucket_name = "painterstorage"
    # artist_style = "vincent-van-gogh-realism/"
    
    resp = s3.list_objects_v2(Bucket=bucket_name, Prefix=artist_style)
    for current in resp['Contents']:
        if "generated/" not in current['Key'] and "retrain/" not in current['Key'] and current['Key'] != artist_style:
            s3_resource = boto3.resource("s3")
            try:
                print(current['Key'], " deleted")
                s3_resource.Object(bucket_name, current['Key']).delete()
            except:
                print(current['Key'], " could not be deleted")

def call_retrain(artist_style):
    url = "http://216.153.50.173:5000/retrain_model"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}
    
    #we use the last char index in order to revert the first find of the '-' sign
    last_char_index = artist_style.rfind("-")
    
    #we create all the needed variables to be sent
    style = artist_style[last_char_index+1:]
    artist = artist_style[:last_char_index]
    actual_date = datetime.date.today().strftime("%d-%m-%Y")
    zip_filename = artist + "_" + style + "_" + actual_date + ".zip"
    
    
    s3 = boto3.resource("s3")
    s3_client = boto3.client('s3')
    bucket_name = "painterstorage"
    
    path = artist_style + "/retrain/image_{}.png"
    
    files_to_zip = []
    
    #iterate through the files in the retrain folder and store their paths in a list
    for i in range(1, 500):
        try:
            test_filename = path.format(str(i))
            s3.Object(bucket_name, test_filename).load()
            image = s3_client.get_object(Bucket=bucket_name, Key=test_filename)
            files_to_zip.append(test_filename)
        except:
            break
    
    #we download all files to /tmp directory of lambda and save them as "image_COUNTER.png"
    
    counter = 1
    for KEY in files_to_zip:
        try:
            s3.Bucket(bucket_name).download_file(KEY, "image_{}.png".format(counter))
            counter += 1
        except Exception as e:
            print(e)
    
    #now create empty zip file in /tmp directory use suffix .zip or .tar.gz if you want, does not matter
    with tempfile.NamedTemporaryFile('w', suffix = '.zip', delete = False) as zip_file:
        with ZipFile(zip_file.name, 'w', compression = ZIP_DEFLATED, allowZip64 = True) as zip:
            counter = 1
            for file in files_to_zip:
                zip.write("image_{}.png".format(counter))
                counter += 1
                
    #now delete all of the images
    for KEY in files_to_zip:
        s3.Object(bucket_name, KEY).delete()
    
    #once zipped in temp , either copy it to your preferred s3 location, or just send the post methot to the api
    # s3.meta.client.upload_file(zip_file.name, bucket_name, zip_filename)
    print("Sending request")
    # requests.post(url, data = {"artist" : artist, "style" : style, "zip_filename" : zip_filename}, files={"archive": (zip_file.name, zip_file)})
    files = {'archive': open(zip_file.name,'rb')}
    requests.post(url, data = {"artist" : artist, "style" : style, "zip_filename" : zip_filename}, files=files)
    print("Request Sent")

def retrain(days_amount, current_photos_target, current_photos_actual, artist):
    os.chdir("/tmp")
    
    bucket_name = "painterstorage"
    path = artist + "/retrain/dates.txt"
    s3_client = boto3.client("s3")
    s3_client.download_file(bucket_name, path, "/tmp/dates.txt")
    
    file = open('dates.txt', 'r')
    lines = file.readlines();

    prev_line = lines[-2].split("'\'")[0]
    last_line = lines[-1]

    number = int(prev_line.split(".")[1].split("=")[0])

    latest_date = last_line.split("=")[1]
    latest_date = datetime.datetime(int(latest_date.split("/")[2]), int(latest_date.split("/")[1]), int(latest_date.split("/")[0]))

    time_between = datetime.datetime.today() - latest_date
    time_between = str(time_between).split(" day")[0]

    try:
        if(int(time_between) >= days_amount and current_photos_actual >= current_photos_target):
            file.close()
            
            latest_date = last_line.split("=")[1]
            new_number = int(number) + 1
            last_line = "date." + str(new_number) + "=" + latest_date

            file = open('dates.txt', 'r')
            lines = file.readlines()
            lines = lines[:-1]

            actual_date = datetime.date.today().strftime("%d/%m/%Y")
            new_line = "latest=" + str(actual_date)

            lines.append(last_line + "\n")
            lines.append(new_line)

            with open('dates.txt', 'w') as file:
                for line in lines:
                    file.write(line)

            print("Retraining started for " + artist)
            
            #START RETRAINING MAYBE
            call_retrain(artist)
            delete_unused(artist)
            
        else:
            file.close()
            if(current_photos_target >= current_photos_actual):
                print("Photos target of ", current_photos_target, " not reached. We have ", current_photos_actual, " photos")
            else:
                print("7 days have not passed")
    except:
        print("Not even one day has passed")
        
    s3_client.upload_file('/tmp/dates.txt', bucket_name, path)


def lambda_handler(event, context):
    #get the url from the frontend and convert it into the old path of the file from S3
    max_images = 500
    
    url = event["rawQueryString"]
    old_path = url.split("amazonaws.com/")
    old_path = old_path[1]
    old_path = old_path.replace("+"," ")
    
    #get the artist in order to add it to the path
    artist = old_path.split("generated")
    artist = artist[0]
    
    bucket_name = "painterstorage"
    
    path = artist.split("/")[0] + "/retrain/image_{}.png"
    s3 = boto3.resource("s3")
    
    #go into retrain and check for the first empty spot
    j = 0
    for i in range (1, max_images):
        try:
            filename = path.format(str(i))
            s3.Object(bucket_name, filename).load()
        except:
            j = i
            break
        
    #save the path of the first empty spot
    new_path = path.format(str(j))

    # # Copy object A as object B
    copy_source = {
      'Bucket': bucket_name,
      'Key': old_path
    }
    try:
        s3.meta.client.copy(copy_source, bucket_name, new_path)
        s3.Object(bucket_name, old_path).delete()
    except:
        print("Could not copy and delete photo")
    
    retrain(7,max_images / 5, j, artist.split("/")[0])
    
    
    return new_path
