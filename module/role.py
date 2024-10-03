import requests
import os
import json
import boto3
from datetime import datetime


def serialize_roles(roles):
    """Helper function to convert datetime objects to strings."""
    for role in roles:
        if "CreateDate" in role and isinstance(role["CreateDate"], datetime):
            role["CreateDate"] = role[
                "CreateDate"
            ].isoformat()  # Convert to ISO 8601 string
    return roles


def get_role_list():
    try:
        # Initialize the Wasabi IAM client
        iam = boto3.client(
            "iam",
            aws_access_key_id=os.environ[
                "WASABI_ACCESS_KEY"
            ],  # Fetch from environment variables
            aws_secret_access_key=os.environ[
                "WASABI_SECRET_KEY"
            ],  # Fetch from environment variables
            region_name="us-east-1",  # Adjust the region if needed
            endpoint_url="https://iam.wasabisys.com",  # Wasabi IAM endpoint
        )

        # List roles using the Wasabi IAM API
        response = iam.list_roles()

        # Log the entire response to check its structure
        print("IAM list_roles response:", response)

        # Check if 'Roles' is present in the response
        if "Roles" in response:
            roles = response["Roles"]

            # Serialize the roles list to handle datetime objects
            serialized_roles = serialize_roles(roles)

            print("Assigned Roles:", serialized_roles)
            return {
                "statusCode": 200,
                "body": json.dumps(serialized_roles),  # Convert to JSON-safe format
            }
        else:
            print("Roles key not found in response.")
            return {"statusCode": 500, "body": "Roles key not found in response."}

    except Exception as e:
        print("Error fetching roles:", e)
        return {"statusCode": 500, "body": f"Error fetching roles: {e}"}


def create_iam_role(role_name, assume_role_policy_document, description=None):
    try:
        # Initialize the Wasabi IAM client
        iam = boto3.client(
            "iam",
            aws_access_key_id=os.environ[
                "WASABI_ACCESS_KEY"
            ],  # Fetch from environment variables
            aws_secret_access_key=os.environ[
                "WASABI_SECRET_KEY"
            ],  # Fetch from environment variables
            region_name="us-east-1",  # Adjust the region if needed
            endpoint_url="https://iam.wasabisys.com",  # Wasabi IAM endpoint
        )

        # Create the IAM role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
            Description=description if description else f"Role created for {role_name}",
            MaxSessionDuration=3600,  # The maximum session duration (optional, defaults to 1 hour)
        )

        return {
            "statusCode": 200,
            # 'body': json.dumps({'message': f"Role {role_name} created successfully", 'role': response})
            "body": json.dumps({"message": f"Role {role_name} created successfully"}),
        }

    except Exception as e:
        # Log any error and return the error response
        print(f"Error creating role: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Error creating role: {e}"}),
        }
