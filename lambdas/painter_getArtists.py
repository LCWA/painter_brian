import json
import boto3
import os

def lambda_handler(event, context):
    os.chdir("/tmp")
    
    bucket_name = "painterstorage"
    path = "styles.txt"
    s3_client = boto3.client("s3")
    s3_client.download_file(bucket_name, path, "/tmp/" + path)
    
    file = open(path, 'r')
    lines = file.readlines();
    
    styles = []
    
    for line in lines:
        style_nice = line.split(" / ")[0]
        style_key = line.split(" / ")[1]
        try:
            style_key = style_key.replace("\n", "")
        except:
            print("Last")
        style = [style_nice, style_key]
        styles.append(style)
    
    return styles
