import json
import boto3

def lambda_handler(event, context):
    # get the url from the frontend and convert it into the path of the file from S3
    url = event["rawQueryString"]
    old_path = url.split("amazonaws.com/")
    old_path = old_path[1]
    old_path = old_path.replace("+"," ")
    
    bucket_name = "painterstorage"
    s3 = boto3.resource("s3")
    
    try:
        s3.Object(bucket_name, old_path).delete()
        # ^ this also deletes the folder if the folder is empty
                
        # here we maybe should call the endpoint to generate another photo, we will see
        return "Deleted: " + old_path
    except:
        return "couldn't remove"