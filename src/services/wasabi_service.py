import os
import boto3
import secrets
import string
from threading import Lock
from enum import Enum
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from services.logging_service import log_execution_time
import requests

logger = Logger()

class WasabiService:

    @staticmethod
    @log_execution_time
    def create_wasabi_subuser(tenant_access_key, tenant_secret_key, user_name, is_admin=False):
        """
        Creates a Wasabi user and optionally attaches an admin policy.

        Args:
            tenant_access_key (str): Access key for the Wasabi tenant.
            tenant_secret_key (str): Secret key for the Wasabi tenant.
            user_id (str): ID of the user to create.
            is_admin (bool): Whether to grant admin access to the user.

        Returns:
            dict: User information, including access keys.
        """
        try:
            # Initialize IAM client for Wasabi
            iam_client = boto3.client(
                "iam",
                aws_access_key_id=tenant_access_key,
                aws_secret_access_key=tenant_secret_key,
                region_name=os.getenv('WASABI_REGION', 'us-east-1'),
                endpoint_url="https://iam.wasabisys.com",
                api_version="2010-05-08",
            )

            # Create the IAM user in Wasabi
            logger.info(f"Creating Wasabi user: {user_name}")
            user_response = iam_client.create_user(UserName=user_name)

            if is_admin:
                logger.info(f"Attaching admin policy to user: {user_name}")
                admin_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
                iam_client.attach_user_policy(UserName=user_name, PolicyArn=admin_policy_arn)

            # Create access keys for the user
            logger.info(f"Creating access keys for user: {user_name}")
            access_key_response = iam_client.create_access_key(UserName=user_name)

            return {
                "userName": user_name,
                "userArn": user_response['User']['Arn'],
                "userId": user_response["User"]["UserId"],
                "accessKeyId": access_key_response["AccessKey"]["AccessKeyId"],
                "secretAccessKey": access_key_response["AccessKey"]["SecretAccessKey"],
                "isAdmin": is_admin
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "EntityAlreadyExists":
                logger.error(f"User {user_name} already exists.")
                return {"error": f"User {user_name} already exists"}, 409
            else:
                logger.error(f"Unexpected error during Wasabi user creation: {str(e)}")
                raise e
        except Exception as e:
            logger.error(f"General error during Wasabi user creation: {str(e)}")
            raise e
        
    @staticmethod
    @log_execution_time
    def update_wasabi_user_role(tenant_access_key, tenant_secret_key, user_name, is_admin=False):
        """
        Updates the role of a Wasabi user by attaching or detaching an admin policy.

        Args:
            tenant_access_key (str): Access key for the Wasabi tenant.
            tenant_secret_key (str): Secret key for the Wasabi tenant.
            user_name (str): The user to update.
            is_admin (bool): Whether to grant or revoke admin access for the user.

        Returns:
            dict: Information about the role update.
        """
        try:
            iam_client = boto3.client(
                "iam",
                aws_access_key_id=tenant_access_key,
                aws_secret_access_key=tenant_secret_key,
                region_name=os.getenv('WASABI_REGION', 'us-east-1'),
                endpoint_url="https://iam.wasabisys.com",
                api_version="2010-05-08",
            )

            admin_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"

            if is_admin:
                logger.info(f"Attaching admin policy to user: {user_name}")
                iam_client.attach_user_policy(UserName=user_name, PolicyArn=admin_policy_arn)
                return {"userName": user_name, "isAdmin": True, "message": "Admin policy attached successfully."}

            else:
                logger.info(f"Detaching admin policy from user: {user_name}")
                iam_client.detach_user_policy(UserName=user_name, PolicyArn=admin_policy_arn)
                return {"userName": user_name, "isAdmin": False, "message": "Admin policy detached successfully."}

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"Unexpected error while updating user role: {str(e)}")
            return {"error": f"Error {error_code}: {str(e)}"}, 500
        except Exception as e:
            logger.error(f"General error while updating user role: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def create_wasabi_subaccount(account_name, quota, is_trial, enable_ftp):
        if not account_name:
            logger.error("Seed user ID not provided.")
            raise ValueError("Seed user ID not provided.")
        
        url = os.getenv("WASABI_ACM_URL") + "/v1/accounts"

        wasabi_api_key = os.getenv("WASABI_ACM_KEY")

        if not wasabi_api_key:
            logger.error("Wasabi API key not found.")
            raise ValueError("Wasabi API key not found.")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": wasabi_api_key
        }

        password = WasabiService._generate_secure_password()

        # Define the request payload
        payload = {
            "AcctName": account_name,
            "IsTrial": is_trial,
            "QuotaGB": quota,
            "Password": password,
            "EnableFTP": enable_ftp,
        }

        # Send the PUT request to create the subaccount
        response = requests.put(url, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info(f"Wasabi subaccount created successfully: {account_name}, Sub account details: {response.json()}")

            return {
                "account_name": account_name,
                "account_number": response.json()["AcctNum"],
                "access_key": response.json()["AccessKey"],
                "secret_key": response.json()["SecretKey"],
                "password": password,
            }

        else:
            logger.error(f"Failed to create Wasabi subaccount: {response.text}")
            raise ValueError(f"Failed to create Wasabi subaccount: {response.text}")
    
    @log_execution_time
    def _generate_secure_password(length=16):
        """
        Generates a secure random password using letters, digits, and punctuation.

        Args:
            length (int, optional): The length of the password to generate. Defaults to 16.

        Returns:
            str: A randomly generated secure password.
        """
        # Define the character set: letters, digits, and punctuation
        characters = string.ascii_letters + string.digits + string.punctuation
        
        # Use secrets.choice to pick characters securely
        password = ''.join(secrets.choice(characters) for i in range(length))
        
        return password

