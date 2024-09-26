import boto3
import os

def get_s3_client(bucket_name):
    """
    Get the S3 client with the correct endpoint and region based on the bucket's location.
    """
    # Create an S3 client with the default Wasabi endpoint (e.g., us-east-1)
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv("WASABI_ENDPOINT_URL", "https://s3.wasabisys.com"),
        aws_access_key_id=os.getenv("WASABI_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("WASABI_SECRET_KEY"),
        region_name="us-east-1"  # Default region for initial request
    )

    # Retrieve the bucket's region
    bucket_location = s3.get_bucket_location(Bucket=bucket_name)
    region = bucket_location.get('LocationConstraint')

    # Adjust endpoint if the region is not us-east-1
    if region:
        endpoint_url = f"https://s3.{region}.wasabisys.com"
    else:
        endpoint_url = "https://s3.wasabisys.com"  # us-east-1 endpoint

    # Return an S3 client with the correct endpoint based on the region
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("WASABI_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("WASABI_SECRET_KEY"),
        region_name=region or "us-east-1"
    )


def delete_bucket(bucket_name):
    try:
        s3_client = get_s3_client(bucket_name)

        # Get a list of all objects in the bucket (including folder contents)
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])

        # Delete the bucket after clearing objects
        s3_client.delete_bucket(Bucket=bucket_name)
        return {
            'statusCode': 200,
            'body': f"Bucket '{bucket_name}' deleted successfully."
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error deleting bucket: {str(e)}"
        }


def delete_folder(bucket_name, folder_key):
    try:
        s3_client = get_s3_client(bucket_name)

        # List all objects in the folder
        objects = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_key)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])

        return {
            'statusCode': 200,
            'body': f"Folder '{folder_key}' in bucket '{bucket_name}' deleted successfully."
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error deleting folder: {str(e)}"
        }


def delete_object(bucket_name, object_key):
    try:
        s3_client = get_s3_client(bucket_name)

        # Delete the object
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        return {
            'statusCode': 200,
            'body': f"Object '{object_key}' deleted successfully from bucket '{bucket_name}'."
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error deleting object: {str(e)}"
        }
