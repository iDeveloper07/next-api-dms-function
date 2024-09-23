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

def get_user_active_status(iam, user_name):
    try:
        # Get the user's access keys to determine if they are active
        response = iam.list_access_keys(UserName=user_name)
        for key in response['AccessKeyMetadata']:
            if key['Status'] == 'Active':
                return True  # If at least one key is active, user is considered active
        return False  # No active keys found, user is considered inactive
    except Exception as e:
        print(f"Error fetching access keys for {user_name}: {str(e)}")
        return False  # If there's an error, assume inactive

def get_user_mfa_status(iam, user_name):
    try:
        # List MFA devices for the user to check MFA status
        response = iam.list_mfa_devices(UserName=user_name)
        return len(response['MFADevices']) > 0  # True if MFA devices exist
    except Exception as e:
        print(f"Error fetching MFA devices for {user_name}: {str(e)}")
        return False  # If there's an error, assume no MFA devices

def list_users():
    try:
        # Initialize IAM client for Wasabi
        iam = boto3.client(
            'iam',
            aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
            aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
            region_name='us-east-1',  # Adjust the region if needed
            endpoint_url='https://iam.wasabisys.com',  # Wasabi IAM endpoint
            api_version='2010-05-08'  # IAM API version (compatible with AWS)
        )

        # Get the list of users
        response = iam.list_users()
        users = response.get('Users', [])

        # Enhanced list to include active and MFA status
        enhanced_users = []
        for user in users:
            user_name = user['UserName']
            # Get active status and MFA status for each user
            active_status = get_user_active_status(iam, user_name)
            mfa_status = get_user_mfa_status(iam, user_name)

            # Add these details to the user object
            user['Active'] = active_status
            user['MFAEnabled'] = mfa_status

            enhanced_users.append(user)

        # Return the list of users with additional information
        return json.dumps(enhanced_users, cls=DateTimeEncoder)
        # return {
        #     'statusCode': 200,
        #     'body': json.dumps(enhanced_users, cls=DateTimeEncoder)  # Use custom encoder for datetime
        # }

    except (BotoCoreError, ClientError) as e:
        # Log and return any error
        print(f"Error fetching Wasabi users: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
