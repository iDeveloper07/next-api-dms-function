from services.rds_service import RDSService
from helpers.common import get_tenant_id
from aws_lambda_powertools import Logger

logger = Logger()


class Activity:
    def __init__(
        self,
        id=None,
        first_name=None,
        last_name=None,
        bucket_name=None,
        folder_name=None,
        document_name=None,
        action=None,
        user_name=None,
        time_stamp=None,
    ):
        self.id = id
        self.tenant_id = get_tenant_id()
        self.first_name = first_name
        self.last_name = last_name
        self.bucket_name = bucket_name
        self.folder_name = folder_name
        self.document_name = document_name
        self.action = action
        self.user_name = user_name
        self.time_stamp = time_stamp

    def to_dict(self):
        """
        Convert the Activity object to a dictionary.
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "bucket_name": self.bucket_name,
            "folder_name": self.folder_name,
            "document_name": self.document_name,
            "action": self.action,
            "user_name": self.user_name,
            "time_stamp": self.time_stamp,
        }

    @classmethod
    def get_all(cls, is_admin=False, allowed_buckets=None):
        """
        Retrieve all activities from the Activity table, optionally filtered by allowed buckets.

        Args:
            allowed_buckets (list): List of allowed bucket names to filter activities.

        Returns:
            list: List of activity objects.
        """
        try:
            # Base query
            select_query = "SELECT * FROM Activity"

            # If allowed_buckets is provided, add filtering condition
            if allowed_buckets:
                # Create placeholders for bucket names in the query
                placeholders = ", ".join(["%s"] * len(allowed_buckets))
                select_query += f" WHERE bucketname IN ({placeholders})"

            # Execute query with or without allowed_buckets filtering
            if is_admin:
                results = RDSService.execute_query(select_query)
            elif allowed_buckets:
                results = RDSService.execute_query(select_query, allowed_buckets)
            else : 
                return []
                

            # Process the query results into activity objects
            activities = [
                cls(
                    id=activity["id"],
                    first_name=activity["firstname"],
                    last_name=activity["lastname"],
                    bucket_name=activity["bucketname"],
                    folder_name=activity["foldername"],
                    document_name=activity["documentname"],
                    action=activity["action"],
                    time_stamp=activity["timestamp"],
                    user_name=activity["username"],
                )
                for activity in results
            ]

            return activities

        except Exception as e:
            logger.error(f"Error retrieving activities: {str(e)}")
            raise e

    def save(self):
        """
        Save the current Activity object to the database.

        Returns:
            None
        """
        try:
            insert_query = (
                "INSERT INTO Activity (firstName, lastName, bucketName, folderName, documentName, action, userName) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s);"
            )
            params = (
                self.first_name,
                self.last_name,
                self.bucket_name,
                self.folder_name,
                self.document_name,
                self.action,
                self.user_name,
            )
            RDSService.execute_query(insert_query, params)
        except Exception as e:
            logger.error(f"Error saving activity: {str(e)}")
            raise e
