import boto3
import os
import json
from datetime import datetime
from botocore.exceptions import BotoCoreError, ClientError

# Custom JSON encoder to handle datetime serialization
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO format string
        return super(DateTimeEncoder, self).default(obj)

def list_policies():
    try:
        # Initialize the IAM client for Wasabi (or AWS)
        iam = boto3.client(
            'iam',
            aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
            aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
            region_name='us-east-1',  # Adjust the region if needed
            endpoint_url='https://iam.wasabisys.com',  # Wasabi IAM endpoint (for Wasabi)
            api_version='2010-05-08'  # IAM API version (compatible with AWS)
        )

        # List all policies
        paginator = iam.get_paginator('list_policies')
        policies = []
        
        # Paginate through all the policies available
        for page in paginator.paginate(Scope='All', OnlyAttached=False):
            policies.extend(page['Policies'])

        # Return the list of policies
        return json.dumps(policies, cls=DateTimeEncoder)
        # return {
        #     'statusCode': 200,
        #     'body': json.dumps(policies)
        # }

    except (BotoCoreError, ClientError) as e:
        # Log and return any error
        print(f"Error fetching policies: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def create_s3_policy(bucket_permissions, policy_name):
    statements = []

    iam_client = boto3.client(
        'iam',
        aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
        aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
        region_name='us-east-1',  # Adjust the region if needed
        endpoint_url='https://iam.wasabisys.com'  # Wasabi IAM endpoint
    )

    # Include s3:ListAllMyBuckets to allow the user to see readable and writable buckets in the console
    listable_buckets = []

    # Loop through each bucket and set permissions
    for bucket in bucket_permissions:
        bucket_name = bucket['bucketName']
        can_read = bucket['canRead']
        can_write = bucket['canWrite']
        
        bucket_arn = f"arn:aws:s3:::{bucket_name}"
        bucket_objects_arn = f"{bucket_arn}/*"

        # If can read, allow ListBucket, GetObject, and GetBucketTagging permissions
        if can_read:
            # Add the bucket to the list of listable buckets for console visibility
            listable_buckets.append(bucket_arn)
            
            # Allow ListBucket to make the bucket visible in the console
            statements.append({
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": bucket_arn
            })
            
            # Allow GetObject to read objects in the bucket
            statements.append({
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": bucket_objects_arn
            })

            # Allow GetBucketTagging to read the bucket tags
            statements.append({
                "Effect": "Allow",
                "Action": "s3:GetBucketTagging",
                "Resource": bucket_arn
            })

            # Explicitly deny write operations (create/update/delete objects, tagging)
            if not can_write:
                statements.append({
                    "Effect": "Deny",
                    "Action": [
                        "s3:PutObject",        # Prevent uploading/creating files
                        "s3:DeleteObject",     # Prevent deleting files
                        "s3:PutObjectTagging", # Prevent modifying object tags
                        "s3:PutBucketTagging"  # Prevent modifying bucket tags
                    ],
                    "Resource": bucket_objects_arn
                })

                statements.append({
                    "Effect": "Deny",
                    "Action": [
                        "s3:PutBucketTagging"  # Prevent modifying bucket tags
                    ],
                    "Resource": bucket_arn
                })

        # If can write, allow PutObject, DeleteObject, and PutBucketTagging permissions
        if can_write:
            # Add the bucket to the list of listable buckets for console visibility
            listable_buckets.append(bucket_arn)

            # Allow ListBucket to make the bucket visible in the console (if not already added)
            if bucket_arn not in listable_buckets:
                statements.append({
                    "Effect": "Allow",
                    "Action": "s3:ListBucket",
                    "Resource": bucket_arn
                })

            # Allow PutObject and DeleteObject to manage objects in the bucket
            statements.append({
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:DeleteObject"],
                "Resource": bucket_objects_arn
            })

            # Allow PutBucketTagging to manage the bucket tags
            statements.append({
                "Effect": "Allow",
                "Action": "s3:PutBucketTagging",
                "Resource": bucket_arn
            })

    # Include s3:ListAllMyBuckets to allow seeing only the readable and writable buckets
    if listable_buckets:
        statements.append({
            "Effect": "Allow",
            "Action": "s3:ListAllMyBuckets",
            "Resource": "*"
        })

    # Ensure there are statements in the policy
    if not statements:
        return {
            'statusCode': 400,
            'body': "No valid permissions provided to create policy."
        }

    # Create the full policy document with a valid version
    policy_document = {
        "Version": "2012-10-17",
        "Statement": statements
    }

    # Create the policy using the IAM client
    try:
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        return {
            'statusCode': 200,
            'body': f"Policy {policy_name} created successfully: {response['Policy']['Arn']}"
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': f"Error creating policy: {str(e)}"
        }

def get_bucket_permissions_from_policy(policy_document, wasabi_buckets):
    """
    Compare Wasabi buckets with the policy and generate `canRead` and `canWrite` for each.
    """
    # Define read and write actions
    read_actions = ["s3:ListBucket", "s3:GetObject", "s3:GetBucketTagging"]
    write_actions = ["s3:PutObject", "s3:DeleteObject", "s3:PutBucketTagging"]

    # Prepare the result list for bucket permissions
    bucket_permissions = []

    # Loop through Wasabi buckets and check permissions
    for bucket in wasabi_buckets:
        bucket_name = bucket['Name']
        can_read = False
        can_write = False

        # Check each statement in the policy
        for statement in policy_document["Statement"]:
            actions = statement["Action"] if isinstance(statement["Action"], list) else [statement["Action"]]
            resources = statement["Resource"] if isinstance(statement["Resource"], list) else [statement["Resource"]]
            
            # Check if the bucket is mentioned in the policy's resource
            for resource in resources:
                if f"arn:aws:s3:::{bucket_name}" in resource:
                    # Check read actions
                    if any(action in read_actions for action in actions) and statement["Effect"] == "Allow":
                        can_read = True
                    # Check write actions
                    if any(action in write_actions for action in actions) and statement["Effect"] == "Allow":
                        can_write = True

        # Append permissions for this bucket
        bucket_permissions.append({
            "bucketName": bucket_name,
            "canRead": can_read,
            "canWrite": can_write
        })

    return bucket_permissions

def get_wasabi_buckets():
    """
    Fetch all Wasabi buckets using the S3-compatible API.
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
        aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
        region_name='us-east-1',  # Adjust the region if needed
        endpoint_url='https://s3.wasabisys.com'  # Wasabi S3 endpoint
    )

    try:
        # List all Wasabi buckets
        response = s3_client.list_buckets()
        return response['Buckets']  # Returns a list of bucket objects

    except Exception as e:
        raise Exception(f"Error fetching Wasabi buckets: {str(e)}")

def generate_policy_input_from_existing(policy_arn):
    """
    Fetch the Wasabi buckets and policy, extract bucket permissions, and generate a new input format.
    """
    iam_client = boto3.client(
        'iam',
        aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
        aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
        region_name='us-east-1',  # Adjust the region if needed
        endpoint_url='https://iam.wasabisys.com'  # Wasabi IAM endpoint
    )

    try:
        # Get the list of all Wasabi buckets
        wasabi_buckets = get_wasabi_buckets()

        # Get the policy details (metadata)
        policy_details = iam_client.get_policy(PolicyArn=policy_arn)

        # Get the policy version details (to access the document itself)
        policy_version = iam_client.get_policy_version(
            PolicyArn=policy_arn,
            VersionId=policy_details['Policy']['DefaultVersionId']
        )

        policy_document = policy_version['PolicyVersion']['Document']

        # Generate permissions from the policy for each Wasabi bucket
        bucket_permissions = get_bucket_permissions_from_policy(policy_document, wasabi_buckets)

        # Output the result in the required format
        result = {
            "policy_name": policy_arn.split('/')[-1],  # Extract policy name from the ARN
            "bucket_permissions": bucket_permissions
        }

        return {
            'statusCode': 200,
            'body': json.dumps(result, indent=4)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }

def update_s3_policy(bucket_permissions, policy_arn):
    statements = []

    iam_client = boto3.client(
        'iam',
        aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
        aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
        region_name='us-east-1',  # Adjust the region if needed
        endpoint_url='https://iam.wasabisys.com'  # Wasabi IAM endpoint
    )

    # Include s3:ListAllMyBuckets to allow the user to see readable and writable buckets in the console
    listable_buckets = []

    # Loop through each bucket and set permissions
    for bucket in bucket_permissions:
        bucket_name = bucket['bucketName']
        can_read = bucket['canRead']
        can_write = bucket['canWrite']
        
        bucket_arn = f"arn:aws:s3:::{bucket_name}"
        bucket_objects_arn = f"{bucket_arn}/*"

        # If can read, allow ListBucket, GetObject, and GetBucketTagging permissions
        if can_read:
            # Add the bucket to the list of listable buckets for console visibility
            listable_buckets.append(bucket_arn)
            
            # Allow ListBucket to make the bucket visible in the console
            statements.append({
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": bucket_arn
            })
            
            # Allow GetObject to read objects in the bucket
            statements.append({
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": bucket_objects_arn
            })

            # Allow GetBucketTagging to read the bucket tags
            statements.append({
                "Effect": "Allow",
                "Action": "s3:GetBucketTagging",
                "Resource": bucket_arn
            })

            # Explicitly deny write operations (create/update/delete objects, tagging)
            if not can_write:
                statements.append({
                    "Effect": "Deny",
                    "Action": [
                        "s3:PutObject",        # Prevent uploading/creating files
                        "s3:DeleteObject",     # Prevent deleting files
                        "s3:PutObjectTagging", # Prevent modifying object tags
                        "s3:PutBucketTagging"  # Prevent modifying bucket tags
                    ],
                    "Resource": bucket_objects_arn
                })

                statements.append({
                    "Effect": "Deny",
                    "Action": [
                        "s3:PutBucketTagging"  # Prevent modifying bucket tags
                    ],
                    "Resource": bucket_arn
                })

        # If can write, allow PutObject, DeleteObject, and PutBucketTagging permissions
        if can_write:
            # Add the bucket to the list of listable buckets for console visibility
            listable_buckets.append(bucket_arn)

            # Allow ListBucket to make the bucket visible in the console (if not already added)
            if bucket_arn not in listable_buckets:
                statements.append({
                    "Effect": "Allow",
                    "Action": "s3:ListBucket",
                    "Resource": bucket_arn
                })

            # Allow PutObject and DeleteObject to manage objects in the bucket
            statements.append({
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:DeleteObject"],
                "Resource": bucket_objects_arn
            })

            # Allow PutBucketTagging to manage the bucket tags
            statements.append({
                "Effect": "Allow",
                "Action": "s3:PutBucketTagging",
                "Resource": bucket_arn
            })

    # Include s3:ListAllMyBuckets to allow seeing only the readable and writable buckets
    if listable_buckets:
        statements.append({
            "Effect": "Allow",
            "Action": "s3:ListAllMyBuckets",
            "Resource": "*"
        })

    # Ensure there are statements in the policy
    if not statements:
        return {
            'statusCode': 400,
            'body': "No valid permissions provided to update policy."
        }

    # Create the full policy document with a valid version
    policy_document = {
        "Version": "2012-10-17",
        "Statement": statements
    }

    try:
        # Check the number of existing versions of the policy
        versions = iam_client.list_policy_versions(PolicyArn=policy_arn)
        if len(versions['Versions']) >= 5:
            # If there are 5 versions, delete the oldest version that isn't the default
            for version in versions['Versions']:
                if not version['IsDefaultVersion']:
                    iam_client.delete_policy_version(
                        PolicyArn=policy_arn,
                        VersionId=version['VersionId']
                    )
                    break

        # Create a new policy version
        response = iam_client.create_policy_version(
            PolicyArn=policy_arn,
            PolicyDocument=json.dumps(policy_document),
            SetAsDefault=True  # Set the new version as the default
        )

        return {
            'statusCode': 200,
            'body': f"Policy {policy_arn} updated successfully. New version: {response['PolicyVersion']['VersionId']}"
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': f"Error updating policy: {str(e)}"
        }
