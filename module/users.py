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

def get_user_info(iam, user_name):
    """ Get basic user information using get_user() """
    try:
        # Fetch the user information
        response = iam.get_user(UserName=user_name)
        return response['User']
    except Exception as e:
        print(f"Error fetching user info for {user_name}: {str(e)}")
        return None

def get_user_details(user_name):
    """ Main function to get detailed user info """
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

        # Fetch user basic information
        user_info = get_user_info(iam, user_name)
        if not user_info:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'User not found'})
            }

        # Fetch user's active status and MFA status
        active_status = get_user_active_status(iam, user_name)
        mfa_status = get_user_mfa_status(iam, user_name)

        # Fetch user's access keys
        # access_keys = get_user_access_keys(iam, user_name)

        # Combine all user details into one response
        user_details = {
            'UserInfo': user_info,
            'Active': active_status,
            'MFAEnabled': mfa_status
            # 'AccessKeys': access_keys
        }

        # Return the detailed user info
        return json.dumps(user_details, cls=DateTimeEncoder)  # Use custom encoder for datetime

    except (BotoCoreError, ClientError) as e:
        # Log and return any error
        print(f"Error fetching user details: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_assigned_policies(user_name):
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

        # List all managed policies attached to the user
        attached_policies_response = iam.list_attached_user_policies(UserName=user_name)
        attached_policies = attached_policies_response.get('AttachedPolicies', [])

        # List all inline policies attached to the user
        inline_policies_response = iam.list_user_policies(UserName=user_name)
        inline_policies = inline_policies_response.get('PolicyNames', [])

        # Combine the results
        user_policies = {
            'ManagedPolicies': attached_policies,
            'InlinePolicies': inline_policies
        }

        # Return the policies
        return json.dumps(user_policies)
        # return {
        #     'statusCode': 200,
        #     'body': json.dumps(user_policies)
        # }

    except (BotoCoreError, ClientError) as e:
        # Log and return any error
        print(f"Error fetching assigned policies for user {user_name}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    
def attach_policy_to_user(user_name, policy_arn):
    try:
        # Initialize IAM client for Wasabi (or AWS)
        iam = boto3.client(
            'iam',
            aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
            aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
            region_name='us-east-1',  # Adjust the region if needed
            endpoint_url='https://iam.wasabisys.com',  # Wasabi IAM endpoint (for Wasabi)
            api_version='2010-05-08'  # IAM API version (compatible with AWS)
        )

        # Attach the managed policy to the user
        iam.attach_user_policy(UserName=user_name, PolicyArn=policy_arn)
        
        return json.dumps({
                'message': f"Policy {policy_arn} attached successfully to user {user_name}"
        })

        # Return success response
        # return {
        #     'statusCode': 200,
        #     'body': json.dumps({
        #         'message': f"Policy {policy_arn} attached successfully to user {user_name}"
        #     })
        # }

    except (BotoCoreError, ClientError) as e:
        # Log and return any error
        print(f"Error attaching policy {policy_arn} to user {user_name}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def remove_policy_from_user(user_name, policy_arn):
    try:
        # Initialize IAM client for Wasabi (or AWS)
        iam = boto3.client(
            'iam',
            aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
            aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
            region_name='us-east-1',  # Adjust the region if needed
            endpoint_url='https://iam.wasabisys.com',  # Wasabi IAM endpoint (for Wasabi)
            api_version='2010-05-08'  # IAM API version (compatible with AWS)
        )

        # Detach the managed policy from the user
        iam.detach_user_policy(UserName=user_name, PolicyArn=policy_arn)

        # Return success response
        return json.dumps({
                'message': f"Policy {policy_arn} detached successfully from user {user_name}"
        })
        # return {
        #     'statusCode': 200,
        #     'body': json.dumps({
        #         'message': f"Policy {policy_arn} detached successfully from user {user_name}"
        #     })
        # }

    except (BotoCoreError, ClientError) as e:
        # Log and return any error
        print(f"Error detaching policy {policy_arn} from user {user_name}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def update_user_info(user_name, new_user_name=None, new_path='/', active_status=False):
    try:
        # Initialize IAM client for Wasabi (or AWS)
        iam = boto3.client(
            'iam',
            aws_access_key_id=os.environ['WASABI_ACCESS_KEY'],  # Fetch from environment variables
            aws_secret_access_key=os.environ['WASABI_SECRET_KEY'],  # Fetch from environment variables
            region_name='us-east-1',  # Adjust the region if needed
            endpoint_url='https://iam.wasabisys.com',  # Wasabi IAM endpoint (for Wasabi)
            api_version='2010-05-08'  # IAM API version (compatible with AWS)
        )

        # Update user name and path (if provided)
        if new_user_name or new_path:
            update_params = {
                'UserName': user_name
            }
            if new_user_name:
                update_params['NewUserName'] = new_user_name
            if new_path:
                update_params['NewPath'] = new_path

            # Call the update_user API to update name and path
            iam.update_user(**update_params)
            user_name = new_user_name if new_user_name else user_name

        # Update active status by enabling/disabling the user's access keys
        if active_status is not None:
            # Get all access keys for the user
            access_keys = iam.list_access_keys(UserName=user_name)['AccessKeyMetadata']
            
            # Update access keys to match the desired active status
            for key in access_keys:
                new_status = 'Active' if active_status else 'Inactive'
                iam.update_access_key(
                    UserName=user_name,
                    AccessKeyId=key['AccessKeyId'],
                    Status=new_status
                )

        return json.dumps({
                'message': f"User {user_name} updated successfully",
                'new_user_name': new_user_name,
                'new_path': new_path,
                'active_status': active_status
        })
        # return {
        #     'statusCode': 200,
        #     'body': json.dumps({
        #         'message': f"User {user_name} updated successfully",
        #         'new_user_name': new_user_name,
        #         'new_path': new_path,
        #         'active_status': active_status
        #     })
        # }

    except (BotoCoreError, ClientError) as e:
        # Log and return any error
        print(f"Error updating user {user_name}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
