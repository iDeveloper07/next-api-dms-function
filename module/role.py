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
