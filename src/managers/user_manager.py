import boto3
from aws_lambda_powertools import Logger
from managers.tenant_manager import TenantManager
from services.wasabi_service import WasabiService
from models.user_model import User
from services.logging_service import log_execution_time

logger = Logger()

class UserManager:
    
    @staticmethod
    @log_execution_time
    def get_all_users():
        """
        Retrieve all users from the database using the User model.

        Returns:
            list: List of User objects.
        """
        try:
            logger.info("Fetching all users.")
            users = User.get_all()
        
            return [user.to_dict() for user in users]
        except Exception as e:
            logger.error(f"Error retrieving all users: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def get_or_create_user(user_name, is_admin=False):
        """
        Retrieves user information from RDS. If the user doesn't exist, 
        creates the user in Wasabi and stores the user under the specific tenant in RDS.

        Args:
            user_name (str): The username of the user.
            is_admin (bool): Whether the user is an admin.

        Returns:
            dict: The user information if successful.
        """
        try:
            logger.info(f"Attempting to retrieve user {user_name} from RDS.")
            user_info = UserManager.get_user(user_name)
            
            if user_info:
                logger.info(f"User {user_name} found in RDS.")
                if user_info.is_admin == is_admin:
                    return {**user_info.to_dict()}

                logger.info(f"Updating user {user_name} to admin status {is_admin}.")

                tenant_keys = TenantManager.get_tenant_keys()
                WasabiService.update_wasabi_user_role(tenant_access_key=tenant_keys["accessKey"], tenant_secret_key=tenant_keys["secretKey"], user_name=user_name, is_admin=is_admin)

                user_info.is_admin = is_admin
                user_info.update()
                
                return {**user_info.to_dict()}

            logger.info(f"User {user_name} not found in RDS, creating in Wasabi.")
            tenant_keys = TenantManager.get_tenant_keys()
            wasabi_user_info = WasabiService.create_wasabi_subuser(tenant_access_key=tenant_keys["accessKey"], tenant_secret_key=tenant_keys["secretKey"], user_name=user_name, is_admin=is_admin)

            logger.info(f"Saving new Wasabi user {user_name} to RDS.")
            created_user = UserManager.create_user(wasabi_user_info)
            
            return {**created_user.to_dict()}

        except Exception as e:
            logger.error(f"Error retrieving or creating user {user_name}: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def get_user(user_name):
        """
        Retrieve user info by username using the User model.

        Args:
            user_name (str): The user's name.

        Returns:
            User: User object if found, otherwise None.
        """
        try:
            logger.info(f"Fetching user with username: {user_name}.")
            return User.get(user_name)
        except Exception as e:
            logger.error(f"Error retrieving user {user_name}: {str(e)}")
            raise e

    @staticmethod
    @log_execution_time
    def create_user(new_user_data):
        """
        Create a new user using the User model.

        Args:
            new_user_data (dict): Dictionary containing new user details.

        Returns:
            User: The newly created User object.
        """
        try:
            logger.info(f"Creating a new user with username: {new_user_data['userName']}.")
            new_user = User(
                user_name=new_user_data["userName"],
                wasabi_user_id=new_user_data["userId"],
                wasabi_user_arn=new_user_data["userArn"],
                access_key=new_user_data["accessKeyId"],
                secret_key=new_user_data["secretAccessKey"],
                is_admin=new_user_data["isAdmin"]
            )

            new_user.save()
            return new_user
        
        except Exception as e:
            logger.error(f"Error creating user {new_user_data['userName']}: {str(e)}")
            raise e

    
    @staticmethod
    @log_execution_time
    def get_user_keys(user_name):
        """
        Retrieve the access key and secret key of a user using the User model.

        Args:
            user_name (str): The user's name.

        Returns:
            dict: The user's access key and secret key.
        """
        try:
            logger.info(f"Fetching keys for user {user_name}.")
            user = UserManager.get_user(user_name)
            
            return {
                "accessKey": user.access_key,
                "secretKey": user.secret_key
            }
        except Exception as e:
            logger.error(f"Error retrieving keys for user {user_name}: {str(e)}")
            raise e
