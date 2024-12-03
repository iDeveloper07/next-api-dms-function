import boto3
import re
import os
import json
from datetime import datetime
from botocore.exceptions import BotoCoreError, ClientError
from managers.user_manager import UserManager
from managers.tenant_manager import TenantManager
from services.logging_service import log_execution_time


# Custom JSON encoder to handle datetime serialization
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO format string
        return super(DateTimeEncoder, self).default(obj)


class PolicyManager:
    @classmethod
    @log_execution_time
    def list_policies(cls, user_name):
        try:
            wasabi_key = UserManager.get_user_keys(user_name)

            # Initialize the IAM client for Wasabi (or AWS)
            iam = boto3.client(
                "iam",
                aws_access_key_id=wasabi_key["accessKey"],
                aws_secret_access_key=wasabi_key["secretKey"],
                region_name=os.getenv('WASABI_REGION', 'us-east-1'),  # Adjust the region if needed
                endpoint_url="https://iam.wasabisys.com",  # Wasabi IAM endpoint (for Wasabi)
                api_version="2010-05-08",  # IAM API version (compatible with AWS)
            )

            # List all policies
            paginator = iam.get_paginator("list_policies")
            policies = []

            #Paginate through all the policies available
            for page in paginator.paginate(Scope="Local", OnlyAttached=False):
                policies.extend(page["Policies"])
                
            # Get AdministratorAccess policy by ARN
            admin_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"  # Adjust if necessary for Wasabi
            try:
                admin_policy = iam.get_policy(PolicyArn=admin_policy_arn)
                policies.append(admin_policy["Policy"])
            except ClientError as e:
                print(f"AdministratorAccess policy not found: {e}")

            # Return the list of policies
            return json.dumps(policies, cls=DateTimeEncoder)

        except (BotoCoreError, ClientError) as e:
            # Log and return any error
            print(f"Error fetching policies: {e}")
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    @classmethod
    @log_execution_time
    def create_s3_policy(cls, bucket_permissions, policy_name, user_name):
        wasabi_key = UserManager.get_user_keys(user_name)

        statements = []

        iam_client = boto3.client(
            "iam",
            aws_access_key_id=wasabi_key["accessKey"],
            aws_secret_access_key=wasabi_key["secretKey"],
            region_name=os.getenv('WASABI_REGION', 'us-east-1'),  # Adjust the region if needed
            endpoint_url="https://iam.wasabisys.com",  # Wasabi IAM endpoint
        )

        # Include s3:ListAllMyBuckets to allow the user to see readable and writable buckets in the console
        statements = [
            {
                "Effect": "Allow",
                "Action": "s3:ListAllMyBuckets",
                "Resource": "*",  # Allows the listing of all buckets but does not grant further access
            },
            {
                "Effect": "Allow",
                "Action": "s3:GetBucketLocation",
                "Resource": "*",  # Allows the listing of all buckets but does not grant further access
            }
        ]

        for bucket in bucket_permissions:
            bucket_name = bucket["bucketName"]
            can_read = bucket["canRead"]
            can_write = bucket["canWrite"]

            bucket_arn = f"arn:aws:s3:::{bucket_name}"
            bucket_objects_arn = f"{bucket_arn}/*"

            # Allow viewing and retrieving objects and their versions if canRead is true
            if can_read:
                statements.append(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:ListBucket",
                            "s3:GetObject",
                            "s3:GetObjectVersion",
                            "s3:GetObjectTagging",
                            "s3:GetBucketTagging",
                            "s3:GetBucketLocation",
                            "s3:ListBucketVersions",
                        ],
                        "Resource": [bucket_arn, bucket_objects_arn],
                    }
                )

            # Allow modifying objects and deleting object versions if canWrite is true
            if can_write:
                statements.append(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:PutObject",
                            "s3:DeleteObject",
                            "s3:DeleteObjectVersion",
                            "s3:PutObjectTagging",
                            "s3:PutBucketTagging",
                            "s3:AbortMultipartUpload",
                        ],
                        "Resource": [bucket_arn, bucket_objects_arn],
                    }
                )

        if not statements:
            return {
                "statusCode": 400,
                "body": "No valid permissions provided to create policy.",
            }

        policy_document = {"Version": "2012-10-17", "Statement": statements}

        try:
            response = iam_client.create_policy(
                PolicyName=policy_name, PolicyDocument=json.dumps(policy_document)
            )
            return {
                "statusCode": 200,
                "body": "Role created successfully",
            }
        except Exception as e:
            return {"statusCode": 400, "body": f"Error creating policy: {e}"}

    @classmethod
    @log_execution_time
    def get_bucket_permissions_from_policy(cls, policy_document, wasabi_buckets):
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
            bucket_name = bucket["Name"]
            can_read = False
            can_write = False

            # Check each statement in the policy
            for statement in policy_document["Statement"]:
                actions = (
                    statement["Action"]
                    if isinstance(statement["Action"], list)
                    else [statement["Action"]]
                )
                resources = (
                    statement["Resource"]
                    if isinstance(statement["Resource"], list)
                    else [statement["Resource"]]
                )

                # Check if the bucket is mentioned in the policy's resource
                for resource in resources:
                    if f"arn:aws:s3:::{bucket_name}" in resource:
                        # Check read actions
                        if (
                            any(action in read_actions for action in actions)
                            and statement["Effect"] == "Allow"
                        ):
                            can_read = True
                        # Check write actions
                        if (
                            any(action in write_actions for action in actions)
                            and statement["Effect"] == "Allow"
                        ):
                            can_write = True

            # Append permissions for this bucket
            bucket_permissions.append(
                {"bucketName": bucket_name, "canRead": can_read, "canWrite": can_write}
            )

        return bucket_permissions

    @classmethod
    @log_execution_time
    def get_wasabi_buckets(cls, user_name):
        wasabi_key = UserManager.get_user_keys(user_name)

        # Set up the boto3 client for Wasabi with the correct region
        s3_client = boto3.client(
            "s3",
            endpoint_url="https://s3.wasabisys.com",
            aws_access_key_id=wasabi_key["accessKey"],
            aws_secret_access_key=wasabi_key["secretKey"],
            region_name=os.getenv('WASABI_REGION', 'us-east-1'),  # Explicitly specify the correct region
        )

        try:
            # List all Wasabi buckets
            response = s3_client.list_buckets()
            return response["Buckets"]  # Returns a list of bucket objects

        except Exception as e:
            raise Exception(f"Error fetching Wasabi buckets: {e}")

    @classmethod
    @log_execution_time
    def generate_policy_input_from_existing(cls, policy_arn, user_name):
        wasabi_key = UserManager.get_user_keys(user_name)

        iam_client = boto3.client(
            "iam",
            aws_access_key_id=wasabi_key["accessKey"],
            aws_secret_access_key=wasabi_key["secretKey"],
            region_name=os.getenv('WASABI_REGION', 'us-east-1'),  # Adjust the region if needed
            endpoint_url="https://iam.wasabisys.com",  # Wasabi IAM endpoint
        )

        try:
            # Get the list of all Wasabi buckets
            wasabi_buckets = PolicyManager.get_wasabi_buckets(user_name)

            # Get the policy details (metadata)
            policy_details = iam_client.get_policy(PolicyArn=policy_arn)

            # Get the policy version details (to access the document itself)
            policy_version = iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=policy_details["Policy"]["DefaultVersionId"],
            )

            policy_document = policy_version["PolicyVersion"]["Document"]

            # Generate permissions from the policy for each Wasabi bucket
            bucket_permissions = PolicyManager.get_bucket_permissions_from_policy(
                policy_document, wasabi_buckets
            )

            # Output the result in the required format
            result = {
                "policy_name": policy_arn.split("/")[
                    -1
                ],  # Extract policy name from the ARN
                "bucket_permissions": bucket_permissions,
            }

            return {"statusCode": 200, "body": json.dumps(result, indent=4)}

        except Exception as e:
            return {"statusCode": 500, "body": f"Error: {str(e)}"}

    @classmethod
    @log_execution_time
    def update_s3_policy(cls, bucket_permissions, policy_arn, user_name):
        statements = []

        wasabi_key = UserManager.get_user_keys(user_name)
        iam_client = boto3.client(
            "iam",
            aws_access_key_id=wasabi_key["accessKey"],
            aws_secret_access_key=wasabi_key["secretKey"],
            region_name=os.getenv('WASABI_REGION', 'us-east-1'),  # Adjust the region if needed
            endpoint_url="https://iam.wasabisys.com",  # Wasabi IAM endpoint
        )

        # Include s3:ListAllMyBuckets to allow the user to see readable and writable buckets in the console
        statements = [
            {
                "Effect": "Allow",
                "Action": "s3:ListAllMyBuckets",
                "Resource": "*",  # Allows the listing of all buckets but does not grant further access
            },
            {
                "Effect": "Allow",
                "Action": "s3:GetBucketLocation",
                "Resource": "*",  # Allows the listing of all buckets but does not grant further access
            }
        ]

        # Loop through each bucket and set permissions
        for bucket in bucket_permissions:
            bucket_name = bucket["bucketName"]
            can_read = bucket["canRead"]
            can_write = bucket["canWrite"]

            bucket_arn = f"arn:aws:s3:::{bucket_name}"
            bucket_objects_arn = f"{bucket_arn}/*"

            # Allow viewing and retrieving objects and their versions if canRead is true
            if can_read:
                statements.append(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:ListBucket",
                            "s3:GetObject",
                            "s3:GetObjectVersion",
                            "s3:GetObjectTagging",
                            "s3:GetBucketTagging",
                            "s3:GetBucketLocation",
                            "s3:ListBucketVersions",
                        ],
                        "Resource": [bucket_arn, bucket_objects_arn],
                    }
                )

            # Allow modifying objects and deleting object versions if canWrite is true
            if can_write:
                statements.append(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:PutObject",
                            "s3:DeleteObject",
                            "s3:DeleteObjectVersion",
                            "s3:PutObjectTagging",
                            "s3:PutBucketTagging",
                            "s3:AbortMultipartUpload",
                        ],
                        "Resource": [bucket_arn, bucket_objects_arn],
                    }
                )

        if not statements:
            return {
                "statusCode": 400,
                "body": "No valid permissions provided to create policy.",
            }

        policy_document = {"Version": "2012-10-17", "Statement": statements}

        try:
            # Check the number of existing versions of the policy
            versions = iam_client.list_policy_versions(PolicyArn=policy_arn)
            if len(versions["Versions"]) >= 5:
                # If there are 5 versions, delete the oldest version that isn't the default
                for version in versions["Versions"]:
                    if not version["IsDefaultVersion"]:
                        iam_client.delete_policy_version(
                            PolicyArn=policy_arn, VersionId=version["VersionId"]
                        )
                        break

            # Create a new policy version
            response = iam_client.create_policy_version(
                PolicyArn=policy_arn,
                PolicyDocument=json.dumps(policy_document),
                SetAsDefault=True,  # Set the new version as the default
            )

            return {
                "statusCode": 200,
                "body": "Role updated successfully",
            }

        except Exception as e:
            return {"statusCode": 400, "body": f"Error updating policy: {e}"}

    @staticmethod
    @log_execution_time
    def extract_bucket_names_from_policy(policy_document):
        # Regex pattern to match the bucket ARN
        pattern = r"arn:aws:s3:::([a-zA-Z0-9.-]+)"

        # Initialize list for storing bucket names
        bucket_names = []

        # Loop through each statement in the policy
        for statement in policy_document.get("Statement", []):
            resources = statement.get("Resource", [])

            # If the resource is a string, convert it to a list
            if isinstance(resources, str):
                resources = [resources]

            # Find all bucket names in each resource using the regex pattern
            for resource in resources:
                matches = re.findall(pattern, resource)
                bucket_names.extend(matches)

        # Return unique bucket names
        return list(set(bucket_names))

    @staticmethod
    @log_execution_time
    def get_available_buckets(user_name):
        tenant_keys = TenantManager.get_tenant_keys()
        iam = boto3.client(
            "iam",
            aws_access_key_id=tenant_keys["accessKey"],
            aws_secret_access_key=tenant_keys["secretKey"],
            region_name=os.getenv('WASABI_REGION', 'us-east-1'),  # Adjust the region if needed
            endpoint_url="https://iam.wasabisys.com",  # Wasabi IAM endpoint (for Wasabi)
            api_version="2010-05-08",  # IAM API version (compatible with AWS)
        )

        attached_policies = iam.list_attached_user_policies(UserName=user_name)

        allowed_buckets = set()

        for policy in attached_policies.get("AttachedPolicies"):
            policy_arn = policy.get("PolicyArn")
            policy_details = iam.get_policy(PolicyArn=policy_arn)

            policy_version = iam.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=policy_details["Policy"]["DefaultVersionId"],
            )

            policy_document = policy_version["PolicyVersion"]["Document"]
            extracted_bucket_names = PolicyManager.extract_bucket_names_from_policy(
                policy_document
            )
            allowed_buckets.update(extracted_bucket_names)

        return sorted(list(allowed_buckets))
