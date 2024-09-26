import boto3
import os
from rds_proxy import execute_query

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

def get_wasabi_user():
    """
    Retrieve the Wasabi user information using the access key and secret key from the IAM client.
    """
    iam_client = boto3.client(
        'iam',
        aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
        aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
        region_name='us-east-1',  # Adjust the region if needed
        endpoint_url='https://iam.wasabisys.com',  # Wasabi IAM endpoint
        api_version='2010-05-08'  # IAM API version (compatible with AWS)
    )

    try:
        # Get the user information associated with the access key
        user_info = iam_client.get_user()
        print("User Info:", user_info)
        
        # Extract account information from the Arn
        arn = user_info['User']['Arn']
        # Extract account ID from the Arn (example Arn: arn:aws:iam::100000281160:root)
        account_name = arn.split(":")[-1]
        # return "00000000-0000-0000-0000-000000000000"
        return account_name
        # return f"Account {account_id}"
    except Exception as e:
        print(f"Error retrieving user information: {str(e)}")
        return None

def log_audit(tenant_id, bucket_name, folder, file, action):
    """
    Log the delete operation to the bucket_audit table.
    """
    audit_query = """
    INSERT INTO bucket_audit (tenant_id, bucket_name, folder, file, action, user_id, username)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    # Dummy tenant ID, you can replace it with the real value
    tenant_id = tenant_id or '00000000-0000-0000-0000-000000000000'
    user_id = tenant_id or '00000000-0000-0000-0000-000000000000'
    user_name = get_wasabi_user()  # Get the user based on the access key and secret key
    execute_query(audit_query, (tenant_id, bucket_name, folder, file, action, user_id, user_name))


def delete_bucket(bucket_name, tenant_id=None):
    try:
        s3_client = get_s3_client(bucket_name)

        # Get a list of all objects in the bucket (including folder contents)
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])

        # Delete the bucket after clearing objects
        s3_client.delete_bucket(Bucket=bucket_name)
        
        # Log audit entry
        log_audit(tenant_id, bucket_name, None, None, "Delete bucket")

        return {
            'statusCode': 200,
            'body': f"Bucket '{bucket_name}' deleted successfully."
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error deleting bucket: {str(e)}"
        }

def delete_folder(bucket_name, folder_key, tenant_id=None):
    try:
        s3_client = get_s3_client(bucket_name)

        # List all objects in the folder
        objects = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_key)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
        
        # Log audit entry
        log_audit(tenant_id, bucket_name, folder_key, None, "Delete folder")

        return {
            'statusCode': 200,
            'body': f"Folder '{folder_key}' in bucket '{bucket_name}' deleted successfully."
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error deleting folder: {str(e)}"
        }

def delete_object(bucket_name, object_key, tenant_id=None):
    try:
        s3_client = get_s3_client(bucket_name)

        # Delete the object
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        
        # Log audit entry
        log_audit(tenant_id, bucket_name, None, object_key, "Delete file")

        return {
            'statusCode': 200,
            'body': f"Object '{object_key}' deleted successfully from bucket '{bucket_name}'."
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error deleting object: {str(e)}"
        }
