# post message example 'van-gogh/123871024'

import json
import boto3

import base64
from boto3 import client

import requests

def lambda_handler(event, context):
    artist = event["rawQueryString"].split("/")[0] + "/"
    user = event["rawQueryString"].split("/")[1] + "/"
    
    bucket_name = "painterstorage"
    s3_path = "generated/image ({}).png"
    s3_new_path = "image ({}).png"
    s3 = boto3.resource("s3")
    url = "https://painterstorage.s3.us-east-2.amazonaws.com/" + artist + user + "image+({}).png"
    
    new_url = "no photos left"
    
    url_list = []
    new_path_list = []
    old_path_list = []
    
    # try and load objects from the S3 in order to check if it exists, if it does, break and save the path
    j = 5 + 1
    i = 1
    
    done = True
    
    while i < j:
        try:
            path = artist + s3_path.format(str(i))
            print(path)
            s3.Object(bucket_name, path).load()
            
            new_url = url.format(str(i))
            url_list.append(new_url)
            
            new_path = artist + user + s3_new_path.format(str(i))
            new_path_list.append(new_path)
            old_path_list.append(path)
            
            i += 1
        except:
            if(j > 100 and len(url_list) < 1):
                # GENERATE MORE
                done = False
                break
            j += 1
            print("image ", i, " is not here...")
            i += 1
    
    if(done):
        # generate_api = ""
        # req = requests.get(generate_api)
        # add said photos in the place of these 5 photos
        
        
        for i in range(0, len(new_path_list)):
            try:
                copy = bucket_name + "/" + str(old_path_list[i])
                s3.Object(bucket_name, new_path_list[i]).copy_from(CopySource = copy)
            except Exception as e:
                print(e)
        
        for i in range(0, len(new_path_list)):
            try:
                s3.Object(bucket_name, old_path_list[i]).delete()
            except Exception as e:
                print(e)
                
        return url_list
    else:
        return "Not enough pictures generated"