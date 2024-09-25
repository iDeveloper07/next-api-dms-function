import requests
import os
import json
import boto3
from datetime import datetime

def serialize_roles(roles):
    """ Helper function to convert datetime objects to strings. """
    for role in roles:
        if 'CreateDate' in role and isinstance(role['CreateDate'], datetime):
            role['CreateDate'] = role['CreateDate'].isoformat()  # Convert to ISO 8601 string
    return roles

def get_role_list():
    try:
        # Initialize the Wasabi IAM client
        iam = boto3.client(
            'iam',
            aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
            aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
            region_name='us-east-1',  # Adjust the region if needed
            endpoint_url='https://iam.wasabisys.com'  # Wasabi IAM endpoint
        )
        
        # List roles using the Wasabi IAM API
        response = iam.list_roles()
        
        # Log the entire response to check its structure
        print('IAM list_roles response:', response)
        
        # Check if 'Roles' is present in the response
        if 'Roles' in response:
            roles = response['Roles']
            
            # Serialize the roles list to handle datetime objects
            serialized_roles = serialize_roles(roles)
            
            print('Assigned Roles:', serialized_roles)
            return {
                'statusCode': 200,
                'body': json.dumps(serialized_roles)  # Convert to JSON-safe format
            }
        else:
            print('Roles key not found in response.')
            return {
                'statusCode': 500,
                'body': 'Roles key not found in response.'
            }
    
    except Exception as e:
        print('Error fetching roles:', str(e))
        return {
            'statusCode': 500,
            'body': f"Error fetching roles: {str(e)}"
        }


def create_iam_role(role_name, assume_role_policy_document, description=None):
    try:
        # Initialize the Wasabi IAM client
        iam = boto3.client(
            'iam',
            aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
            aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
            region_name='us-east-1',  # Adjust the region if needed
            endpoint_url='https://iam.wasabisys.com'  # Wasabi IAM endpoint
        )

        # Create the IAM role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
            Description=description if description else f"Role created for {role_name}",
            MaxSessionDuration=3600  # The maximum session duration (optional, defaults to 1 hour)
        )

        return {
            'statusCode': 200,
            # 'body': json.dumps({'message': f"Role {role_name} created successfully", 'role': response})
            'body': json.dumps({'message': f"Role {role_name} created successfully"})
        }

    except Exception as e:
        # Log any error and return the error response
        print(f"Error creating role: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Error creating role: {str(e)}"})
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


