from services.rds_service import RDSService
from helpers.common import get_tenant_id
from aws_lambda_powertools import Logger

logger = Logger()

class User:
    def __init__(self, user_name=None, wasabi_user_id=None, wasabi_user_arn=None, access_key=None, secret_key=None, is_admin=False, created_at=None):
        self.tenant_id = get_tenant_id()
        self.user_name = user_name
        self.wasabi_user_id = wasabi_user_id
        self.wasabi_user_arn = wasabi_user_arn
        self.access_key = access_key
        self.secret_key = secret_key
        self.is_admin = is_admin
        self.created_at = created_at

    def to_dict(self):
        """
        Convert the User object to a dictionary.
        """
        return {
            'userName': self.user_name,
            'wasabiUserId': self.wasabi_user_id,
            'wasabiUserArn': self.wasabi_user_arn,
            'accessKey': self.access_key,
            'secretKey': self.secret_key,
            'isAdmin': self.is_admin
        }

    @classmethod
    def get(cls, user_name):
        """
        Retrieve user info by username from RDS.

        Args:
            user_name (str): The user's name.

        Returns:
            User: User object if found, otherwise None.
        """
        try:
            select_query = "SELECT wasabiUserId, wasabiUserArn, accessKey, secretKey, isAdmin, createdAt FROM Users WHERE userName = %s;"
            user_data = RDSService.execute_query(select_query, (user_name,))

            if user_data:
                return cls(
                    user_name=user_name,
                    wasabi_user_id=user_data[0]["wasabiuserid"],
                    wasabi_user_arn=user_data[0]["wasabiuserarn"],
                    access_key=user_data[0]["accesskey"],
                    secret_key=user_data[0]["secretkey"],
                    is_admin=user_data[0]["isadmin"],
                    created_at=user_data[0]["createdat"]
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving user from RDS: {e}")
            raise e

    @classmethod
    def get_all(cls):
        """
        Retrieve all users from the RDS Users table.

        Returns:
            list: List of User objects.
        """
        try:
            query = "SELECT userName, wasabiUserId, wasabiUserArn, accessKey, secretKey, isAdmin, createdAt FROM Users;"
            users_data = RDSService.execute_query(query)
            
            users = [cls(
                        user_name=user["username"],
                        wasabi_user_id=user["wasabiuserid"],
                        wasabi_user_arn=user["wasabiuserarn"],
                        access_key=user["accesskey"],
                        secret_key=user["secretkey"],
                        is_admin=user["isadmin"],
                        created_at=user["createdat"]
                    ) for user in users_data]

            logger.info(f"Retrieved {len(users)} users from the database.")
            return users
        except Exception as e:
            logger.error(f"Error retrieving users from RDS: {e}")
            raise e

    def save(self):
        """
        Save a Wasabi subuser's details to the RDS database in the Users table.

        Args:
            new_user_data (dict): Dictionary containing subuser details.
        
        Returns:
            User: The saved user object.
        """
        try:
            insert_query = """
                INSERT INTO Users (userName, wasabiUserId, wasabiUserArn, accessKey, secretKey, isAdmin)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenantId, userName) DO NOTHING;
            """
            params = (
                self.user_name,
                self.wasabi_user_id,
                self.wasabi_user_arn,
                self.access_key,
                self.secret_key,
                self.is_admin
            )

            RDSService.execute_query(insert_query, params)
            logger.info(f"Successfully saved user {self.user_name} to RDS under tenant {get_tenant_id()}.")
        except Exception as e:
            logger.error(f"Error saving user {self.user_name} to RDS: {e}")
            raise e

    def update(self):
        """
        Update the Wasabi subuser's details in the RDS database in the Users table.

        Returns:
            User: The updated user object.
        """
        try:
            update_query = """
                UPDATE Users 
                SET wasabiUserId = %s, wasabiUserArn = %s, accessKey = %s, secretKey = %s, isAdmin = %s
                WHERE tenantId = %s AND userName = %s;
            """
            params = (
                self.wasabi_user_id,
                self.wasabi_user_arn,
                self.access_key,
                self.secret_key,
                self.is_admin,
                self.tenant_id,
                self.user_name
            )

            RDSService.execute_query(update_query, params)
            logger.info(f"Successfully updated user {self.user_name} in RDS under tenant {self.tenant_id}.")
            return self
        except Exception as e:
            logger.error(f"Error updating user {self.user_name} in RDS: {e}")
            raise e